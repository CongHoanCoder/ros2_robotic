#!/usr/bin/env python3
import math
import os

import rclpy
from rclpy.node import Node
import yaml

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from ros_car_msgs.srv import WaypointService


def euler_from_quaternion(x, y, z, w):
    """
    Extracts yaw (heading) from a quaternion without external dependencies.
    Assumes a body fixed frame with z up (standard for 2D robots).
    """
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    return math.atan2(t3, t4)


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}


class WaypointNavigator(Node):
    """
    A ROS node for autonomous robot navigation with wall-following obstacle avoidance.

    The node communicates with the Waypoint Manager service to retrieve waypoints
    and autonomously navigates towards them. If an obstacle is detected in front,
    the robot switches to wall-following mode to circumvent the obstacle before
    resuming navigation.

    Configuration is loaded from the YAML files located in the `config_dir` parameter.
    """
    # State machine definitions
    STATE_NAVIGATING = 0
    STATE_WALL_FOLLOWING = 1

    def __init__(self):
        super().__init__('waypoint_navigator')

        self.declare_parameter('config_dir', '')
        config_dir = self.get_parameter('config_dir').value

        # Load configuration files
        car_params = load_yaml(os.path.join(config_dir, 'car_params.yaml'))
        secret = load_yaml(os.path.join(config_dir, 'secret_key.yaml'))

        # Navigation parameters
        self.linear_speed = car_params.get('linear_speed', 0.3)
        self.angular_speed = car_params.get('angular_speed', 0.5)
        self.arrival_threshold = 0.3
        self.obstacle_threshold = car_params.get('obstacle_threshold', 0.5)
        self.wall_follow_distance = car_params.get('wall_follow_distance', 0.7)
        self.front_angle_width = math.radians(car_params.get('front_angle_width', 30.0))
        self.alignment_tolerance = 0.2

        # PID parameters
        self.kp_angular = car_params.get('kp_angular', 1.0)
        self.ki_angular = car_params.get('ki_angular', 0.0)
        self.kd_angular = car_params.get('kd_angular', 0.05)

        # Secret key for the service
        self.secret_key = secret.get('secret_key', 'default')

        # PID state
        self.error_yaw_integral = 0.0
        self.prev_error_yaw = 0.0

        # Robot state
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0

        # Current waypoint
        self.current_waypoint = None

        # Obstacle avoidance parameters
        self.regions = {}
        self.obstacle_detected = False
        self.state = self.STATE_NAVIGATING

        # Alignment state
        self.aligned = False

        # In-flight waypoint request (non-blocking async service call)
        self._wp_future = None

        # Publisher for velocity commands
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Subscriber for odometry
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10)

        # Subscriber for LaserScan
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)

        # Waypoint service client
        self.waypoint_request = self.create_client(
            WaypointService, '/waypoint_request')

        # Timer running the navigation control loop at 10 Hz
        self.create_timer(0.1, self.navigate)

        self.get_logger().info(
            "Waypoint Navigator with Wall-Following Obstacle Avoidance started "
            "(front_angle_width=%.3f rad)." % self.front_angle_width)

    def request_waypoint(self):
        """
        Non-blocking waypoint request.

        Sends an async request and, on a later tick, picks up the completed
        future. Called from the navigation timer callback, so it must never block.
        """
        if self._wp_future is not None:
            # A request is already in flight; check whether it completed.
            if self._wp_future.done():
                try:
                    response = self._wp_future.result()
                    self.current_waypoint = list(response.current_waypoint)
                    self.get_logger().info("New waypoint received: %s" % str(self.current_waypoint))
                except Exception as e:
                    self.get_logger().error("Failed to call waypoint service: %s" % str(e))
                    self.current_waypoint = None
                self._wp_future = None
            return

        if not self.waypoint_request.service_is_ready():
            self.get_logger().info("Waiting for waypoint service...")
            return
        req = WaypointService.Request()
        req.secret_key = self.secret_key
        self._wp_future = self.waypoint_request.call_async(req)

    def odom_callback(self, odom_msg):
        self.robot_x = odom_msg.pose.pose.position.x
        self.robot_y = odom_msg.pose.pose.position.y
        orientation_q = odom_msg.pose.pose.orientation
        self.robot_yaw = euler_from_quaternion(
            orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w)

    def scan_callback(self, scan_msg):
        ranges = scan_msg.ranges
        num_samples = len(ranges)
        angle_increment = scan_msg.angle_increment

        # Calculate indices for the front angle range
        center_index = num_samples // 2
        half_width = int(self.front_angle_width / angle_increment / 2)
        half_width = max(half_width, 1)
        front_indices = ranges[center_index - half_width: center_index + half_width + 1]

        self.regions = {
            'right': min(min(ranges[:num_samples // 3]), float('inf')),
            'front': min(min(front_indices), float('inf')),
            'left': min(min(ranges[2 * num_samples // 3:]), float('inf'))
        }
        self.obstacle_detected = self.regions['front'] < self.obstacle_threshold

    def navigate(self):
        if self.current_waypoint is None:
            self.get_logger().warn("No waypoint set. Requesting a new waypoint...")
            self.request_waypoint()
            return

        if self.state == self.STATE_WALL_FOLLOWING:
            self.wall_following()
            return

        if self.obstacle_detected:
            self.get_logger().warn("Obstacle detected! Switching to wall-following mode.")
            self.state = self.STATE_WALL_FOLLOWING
            return

        # Calculate the distance to the current waypoint
        dx = self.current_waypoint[0] - self.robot_x
        dy = self.current_waypoint[1] - self.robot_y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Check if the robot reached the waypoint
        if distance < self.arrival_threshold:
            self.get_logger().info("Reached waypoint: %s" % str(self.current_waypoint))
            self.stop()
            self.aligned = False
            self.request_waypoint()
            return

        # Otherwise, compute heading to the waypoint
        theta_des = math.atan2(dy, dx)
        error_yaw = theta_des - self.robot_yaw

        # Normalize the angle to [-pi, pi]
        error_yaw = math.atan2(math.sin(error_yaw), math.cos(error_yaw))

        cmd = Twist()

        # Adjust angular speed with PID control (assuming 10 Hz control loop)
        dt = 0.1

        self.error_yaw_integral += error_yaw * dt
        error_yaw_derivative = (error_yaw - self.prev_error_yaw) / dt
        self.prev_error_yaw = error_yaw

        angular_speed = (
            self.kp_angular * error_yaw +
            self.ki_angular * self.error_yaw_integral +
            self.kd_angular * error_yaw_derivative
        )

        # Saturate angular speed
        angular_speed = max(-self.angular_speed, min(self.angular_speed, angular_speed))

        cmd.angular.z = angular_speed

        # Allow forward motion if error_yaw is small enough
        if abs(error_yaw) < self.alignment_tolerance:
            cmd.linear.x = self.linear_speed
        else:
            cmd.linear.x = 0.0

        self.cmd_pub.publish(cmd)

    def wall_following(self):
        cmd = Twist()
        error = 0.0

        if self.regions['front'] < self.obstacle_threshold:
            # Turn away from the obstacle in front
            if self.regions['left'] > self.regions['right']:
                cmd.angular.z = self.angular_speed
                self.get_logger().debug("Turning left to follow the wall.")
            else:
                cmd.angular.z = -self.angular_speed
                self.get_logger().debug("Turning right to follow the wall.")
        else:
            # Follow the wall by maintaining a constant distance
            self.get_logger().debug("Following the wall.")
            error = self.wall_follow_distance - self.regions['left']
            cmd.linear.x = self.linear_speed
            cmd.angular.z = self.angular_speed * error

        if self.regions['front'] > self.obstacle_threshold and abs(error) < 0.1:
            self.get_logger().debug("Path clear. Switching back to navigation mode.")
            self.state = self.STATE_NAVIGATING

        self.cmd_pub.publish(cmd)

    def stop(self):
        cmd = Twist()
        self.cmd_pub.publish(cmd)
        self.get_logger().info("Robot stopped.")


def main(args=None):
    rclpy.init(args=args)
    node = WaypointNavigator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("WaypointNavigator node interrupted.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()