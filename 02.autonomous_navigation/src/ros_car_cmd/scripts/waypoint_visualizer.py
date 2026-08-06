#!/usr/bin/env python3
import os

import rclpy
from rclpy.node import Node
import yaml

from visualization_msgs.msg import Marker
from ros_car_msgs.srv import WaypointService


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}


class WaypointVisualizer(Node):
    """
    Waypoint Visualizer node for displaying robot waypoints in RViz.

    This node communicates with the Waypoint Manager service to retrieve waypoints
    and publishes visualization markers for the last, current, and next waypoints.

    Configuration is loaded from the YAML files located in the `config_dir` parameter.
    """
    def __init__(self):
        super().__init__('waypoint_visualizer')

        self.declare_parameter('config_dir', '')
        config_dir = self.get_parameter('config_dir').value

        secret = load_yaml(os.path.join(config_dir, 'secret_key.yaml'))
        self.secret_key = secret.get('secret_key', 'default')

        # Publisher to the /visualization_marker topic
        self.pub = self.create_publisher(Marker, '/visualization_marker', 10)

        # Service proxy to the Waypoint Manager
        self.waypoint_request = self.create_client(
            WaypointService, '/waypoint_request')

        # In-flight waypoint request (non-blocking async service call)
        self._wp_future = None

        # Timer to trigger updates every second
        self.create_timer(1.0, self.timer_callback)

        self.get_logger().info("Waypoint Visualizer started.")

    def timer_callback(self):
        if self._wp_future is not None:
            # A request is already in flight; check whether it completed.
            if self._wp_future.done():
                try:
                    response = self._wp_future.result()
                    self.publish_markers(response)
                except Exception as e:
                    self.get_logger().error(
                        "Failed to publish waypoints: %s" % str(e))
                self._wp_future = None
            return

        if not self.waypoint_request.service_is_ready():
            self.get_logger().info("Waiting for waypoint service...")
            return

        req = WaypointService.Request()
        req.secret_key = self.secret_key
        self._wp_future = self.waypoint_request.call_async(req)

    def publish_markers(self, response):
        # Create and publish markers for each waypoint
        self.publish_marker(response.last_waypoint, [1.0, 1.0, 0.0], "last_waypoint", 0)       # Yellow
        self.publish_marker(response.current_waypoint, [0.0, 0.0, 1.0], "current_waypoint", 1)  # Blue
        self.publish_marker(response.next_waypoint, [1.0, 0.0, 0.0], "next_waypoint", 2)        # Red

    def publish_marker(self, wp, color, ns, id_):
        marker = Marker()
        marker.header.frame_id = "odom"          # Reference frame for the markers
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = ns                            # Namespace for the marker
        marker.id = id_                           # Unique ID for the marker
        marker.type = Marker.SPHERE               # Shape of the marker
        marker.action = Marker.ADD                # Add or modify the marker
        marker.scale.x = 0.1
        marker.scale.y = 0.1
        marker.scale.z = 0.1
        marker.color.r = float(color[0])
        marker.color.g = float(color[1])
        marker.color.b = float(color[2])
        marker.color.a = 1.0
        marker.pose.orientation.w = 1.0
        marker.pose.position.x = float(wp[0])
        marker.pose.position.y = float(wp[1])
        marker.pose.position.z = 0.0

        self.pub.publish(marker)


def main(args=None):
    rclpy.init(args=args)
    node = WaypointVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("WaypointVisualizer node interrupted.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()