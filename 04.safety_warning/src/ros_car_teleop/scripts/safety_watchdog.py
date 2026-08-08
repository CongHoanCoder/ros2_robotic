#!/usr/bin/env python3
import math
import time

import rclpy
from rclpy.node import Node

from gazebo_msgs.msg import EntityState
from gazebo_msgs.srv import SetEntityState, SpawnEntity
from geometry_msgs.msg import Point, Pose, Quaternion, Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from visualization_msgs.msg import Marker


class SafetyWatchdog(Node):
    """
    Safety watchdog for manual driving.

    Watches the laser scan and, when an obstacle is too close, stops the car and
    shows a red warning beacon over it in the Gazebo GUI (plus an RViz marker).
    Control returns automatically a short time after the obstacle clears.
    """
    STATE_SAFE = 0
    STATE_WARNING = 1
    STATE_DANGER = 2

    def __init__(self):
        super().__init__('safety_watchdog')

        self.declare_parameter('stop_distance', 0.5)
        self.declare_parameter('warning_distance', 1.0)
        self.declare_parameter('hold_time', 1.0)
        self.declare_parameter('beacon_model_file', '')
        self.declare_parameter('beacon_name', 'warning_beacon')

        self.stop_distance = self.get_parameter('stop_distance').value
        self.warning_distance = self.get_parameter('warning_distance').value
        self.hold_time = self.get_parameter('hold_time').value
        self.beacon_name = self.get_parameter('beacon_name').value
        beacon_model_file = self.get_parameter('beacon_model_file').value
        self.beacon_xml = None
        if beacon_model_file:
            self.beacon_xml = self._load_model(beacon_model_file)
        if self.beacon_xml is None:
            self.get_logger().warn(
                "No beacon model given; warning marker only (no Gazebo beacon).")

        # Robot state (updated by odometry)
        self.robot_x = 0.0
        self.robot_y = 0.0

        # Watchdog state
        self.min_range = float('inf')
        self.state = self.STATE_SAFE
        self.brake_until = 0.0  # monotonic time the hard stop lasts until
        self.beacon_created = False
        self._spawn_future = None
        self._last_state_send = 0.0

        # Publisher for velocity commands (hard stop)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # RViz companion marker
        self.marker_pub = self.create_publisher(Marker, '/warning_marker', 10)

        # Subscriptions
        self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        # Gazebo service clients (async, non-blocking)
        self.spawn_client = self.create_client(SpawnEntity, '/spawn_entity')
        self.state_client = self.create_client(SetEntityState, '/set_entity_state')

        # Control loop
        self.create_timer(0.05, self.update)  # 20 Hz

        self.get_logger().info(
            "Safety Watchdog started (stop=%.2f m, warn=%.2f m, hold=%.1f s)."
            % (self.stop_distance, self.warning_distance, self.hold_time))

    @staticmethod
    def _load_model(path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except OSError as e:
            raise RuntimeError('Could not load beacon model %s: %s' % (path, e))

    def scan_callback(self, msg):
        valid = [r for r in msg.ranges
                 if not math.isinf(r) and not math.isnan(r) and r < msg.range_max]
        self.min_range = min(valid) if valid else float('inf')

    def odom_callback(self, msg):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y

    def update(self):
        now = time.monotonic()

        # Determine state from the closest obstacle
        if self.min_range < self.stop_distance:
            self.state = self.STATE_DANGER
            self.brake_until = now + self.hold_time
        elif self.min_range < self.warning_distance:
            self.state = self.STATE_WARNING
        else:
            self.state = self.STATE_SAFE

        # Brake while in danger, plus a short hold after the obstacle clears
        if now < self.brake_until:
            self.cmd_pub.publish(Twist())  # zero velocity => hard stop

        # Keep the beacon visible and on top of the car for the whole warning
        # zone (warning + danger); hide it when clear.
        self.update_beacon(now)

        self.publish_marker()

    def update_beacon(self, now):
        """Ensure the beacon exists, then move it to the car (visible) or far
        below the ground (hidden). It is spawned once and kept alive, so it
        always reappears when needed and reliably follows the car via
        set_entity_state (a dynamic, gravity-free model)."""
        if self.beacon_xml is None:
            return
        if not self.beacon_created:
            self.ensure_spawned()
            return
        if now - self._last_state_send < 0.2:
            return
        if not self.state_client.service_is_ready():
            return
        visible = self.min_range < self.warning_distance
        state = EntityState()
        state.name = self.beacon_name
        state.reference_frame = 'world'
        state.pose = Pose(
            position=Point(x=self.robot_x,
                           y=self.robot_y,
                           z=0.25 if visible else -50.0),
            orientation=Quaternion(w=1.0))
        req = SetEntityState.Request()
        req.state = state
        self.state_client.call_async(req)
        self._last_state_send = now

    def ensure_spawned(self):
        if self.beacon_xml is None:
            return
        if self._spawn_future is not None:
            if not self._spawn_future.done():
                return
            # Previous attempt finished: record success/failure.
            try:
                resp = self._spawn_future.result()
                ok = resp is not None and resp.success
            except Exception as e:
                self.get_logger().warn("Spawn beacon call failed: %s" % str(e))
                ok = False
            self._spawn_future = None
            if ok:
                self.beacon_created = True
                self.get_logger().info("Warning beacon active.")
                return
            self.get_logger().warn("Failed to spawn beacon; retrying.")
        if not self.spawn_client.service_is_ready():
            return
        req = SpawnEntity.Request()
        req.name = self.beacon_name
        req.xml = self.beacon_xml
        req.reference_frame = 'world'
        # Spawn hidden below the ground; update_beacon moves it into view.
        req.initial_pose = Pose(position=Point(x=0.0, y=0.0, z=-50.0),
                                orientation=Quaternion(w=1.0))
        self._spawn_future = self.spawn_client.call_async(req)
        self.get_logger().info("Spawning warning beacon.")

    def publish_marker(self):
        marker = Marker()
        marker.header.frame_id = 'odom'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'safety'
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.scale.x = marker.scale.y = marker.scale.z = 0.2
        marker.pose.position = Point(x=self.robot_x, y=self.robot_y, z=0.3)
        marker.pose.orientation.w = 1.0
        if self.state == self.STATE_DANGER:
            marker.color.r, marker.color.g, marker.color.b = 1.0, 0.0, 0.0
        elif self.state == self.STATE_WARNING:
            marker.color.r, marker.color.g, marker.color.b = 1.0, 0.5, 0.0
        else:
            marker.color.r, marker.color.g, marker.color.b = 0.0, 1.0, 0.0
        marker.color.a = 1.0
        self.marker_pub.publish(marker)


def main(args=None):
    rclpy.init(args=args)
    node = SafetyWatchdog()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Safety Watchdog interrupted.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()