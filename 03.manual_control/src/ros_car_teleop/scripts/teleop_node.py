#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from ros_car_msgs.msg import MoveControls, SpeedControls


class TeleopNode(Node):
    """
    Teleoperation node for controlling the robot through commands and set speeds.

    Subscribes to movement commands (`MoveControls`) and speed updates
    (`SpeedControls`), converts them into `Twist` messages, and publishes to
    `/cmd_vel`.
    """
    def __init__(self):
        super().__init__('teleop_node')
        self.get_logger().info("TeleopNode started.")

        # Subscriber for movement commands
        self.sub_cmd = self.create_subscription(
            MoveControls, '/teleop_cmd', self.cmd_callback, 10)

        # Subscriber for setting linear/angular speeds
        self.sub_speed = self.create_subscription(
            SpeedControls, '/set_speed', self.speed_callback, 10)

        # Publisher for cmd_vel (Twist messages)
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Default speed values
        self.current_linear_speed = 0.0
        self.current_angular_speed = 0.0

    def cmd_callback(self, msg):
        # Create a Twist message to represent the movement command
        twist = Twist()

        if msg.command == MoveControls.FORWARD:
            twist.linear.x = self.current_linear_speed
        elif msg.command == MoveControls.BACKWARD:
            twist.linear.x = -self.current_linear_speed
        elif msg.command == MoveControls.LEFT:
            twist.angular.z = self.current_angular_speed
        elif msg.command == MoveControls.RIGHT:
            twist.angular.z = -self.current_angular_speed
        elif msg.command == MoveControls.STOP:
            pass  # all velocities stay zero
        else:
            self.get_logger().warn("Unknown MoveControls command: %d" % msg.command)

        self.pub.publish(twist)

    def speed_callback(self, msg):
        self.current_linear_speed = float(msg.linear_speed)
        self.current_angular_speed = float(msg.angular_speed)
        self.get_logger().info("Speed changed: linear=%.2f, angular=%.2f" %
                               (self.current_linear_speed, self.current_angular_speed))


def main(args=None):
    rclpy.init(args=args)
    node = TeleopNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("TeleopNode interrupted.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()