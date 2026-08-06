#!/usr/bin/env python3
import math
import os
import random

import rclpy
from rclpy.node import Node
import yaml

from nav_msgs.msg import Odometry
from ros_car_msgs.srv import WaypointService


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}


class WaypointManager(Node):
    """
    Waypoint Manager node for handling robot navigation waypoints.

    This node manages the robot's waypoints by providing a service to get the current,
    last, and next waypoints. It generates the next waypoint randomly within the specified
    bounds of the world and updates waypoints only when the robot reaches the current one.

    Configuration is loaded from the YAML files located in the `config_dir` parameter.
    """
    def __init__(self):
        super().__init__('waypoint_manager')

        self.declare_parameter('config_dir', '')
        config_dir = self.get_parameter('config_dir').value

        # Load configuration files
        world = load_yaml(os.path.join(config_dir, 'world_bounds.yaml'))
        secret = load_yaml(os.path.join(config_dir, 'secret_key.yaml'))

        self.current_waypoint = list(world.get('current_waypoint', [0.0, 0.0]))
        self.last_waypoint = list(world.get('last_waypoint', [-1.0, -1.0]))
        self.next_waypoint = list(world.get('next_waypoint', [2.0, 1.5]))
        self.arrival_threshold = world.get('arrival_threshold', 0.2)
        self.world_bounds = world.get('world_bounds', {
            'x_min': -5.0,
            'x_max': 5.0,
            'y_min': -5.0,
            'y_max': 5.0
        })
        self.secret_key = secret.get('secret_key', 'default')

        # Current position of the robot (updated by odometry)
        self.robot_position = [0.0, 0.0]

        # Subscriber to odometry topic
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10)

        # Service to get the next waypoint
        self.waypoint_service = self.create_service(
            WaypointService, '/waypoint_request', self.handle_waypoint_request)

        self.get_logger().info("Waypoint Manager started.")
        self.get_logger().info("Current waypoint: %s" % str(self.current_waypoint))
        self.get_logger().info("Next waypoint: %s" % str(self.next_waypoint))

    def has_reached_waypoint(self):
        dx = self.robot_position[0] - self.current_waypoint[0]
        dy = self.robot_position[1] - self.current_waypoint[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)
        return distance < self.arrival_threshold

    def generate_next_waypoint(self):
        rand_x = random.uniform(self.world_bounds['x_min'], self.world_bounds['x_max'])
        rand_y = random.uniform(self.world_bounds['y_min'], self.world_bounds['y_max'])
        return [rand_x, rand_y]

    def odom_callback(self, msg):
        self.robot_position[0] = msg.pose.pose.position.x
        self.robot_position[1] = msg.pose.pose.position.y

    def handle_waypoint_request(self, request, response):
        if request.secret_key != self.secret_key:
            self.get_logger().warn("Invalid secret key provided: %s" % request.secret_key)
            return None

        # Check if the robot has reached the current waypoint
        if self.has_reached_waypoint():
            self.last_waypoint = self.current_waypoint
            self.current_waypoint = self.next_waypoint
            self.next_waypoint = self.generate_next_waypoint()

            self.get_logger().info("Updated Waypoints:")
            self.get_logger().info("--Last Waypoint: %s" % str(self.last_waypoint))
            self.get_logger().info("--Current Waypoint: %s" % str(self.current_waypoint))
            self.get_logger().info("--Next Waypoint: %s" % str(self.next_waypoint))

        response.last_waypoint = self.last_waypoint
        response.current_waypoint = self.current_waypoint
        response.next_waypoint = self.next_waypoint
        return response


def main(args=None):
    rclpy.init(args=args)
    node = WaypointManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("WaypointManager node interrupted.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()