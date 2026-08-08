#!/usr/bin/env python3
import select
import sys
import termios
import tty

import rclpy
from rclpy.node import Node

from ros_car_msgs.msg import MoveControls, SpeedControls

# Key bindings: move commands
MOVE_KEYS = {
    'i': (MoveControls.FORWARD, 'forward'),
    'k': (MoveControls.STOP, 'stop'),
    'j': (MoveControls.LEFT, 'left'),
    'l': (MoveControls.RIGHT, 'right'),
    ',': (MoveControls.BACKWARD, 'backward'),
}


class KeyboardControls(Node):
    """
    Reads keyboard input and publishes movement commands.

    Publishes `MoveControls` on `/teleop_cmd` and speed updates on
    `/set_speed`, which are consumed by `teleop_node`.
    """
    def __init__(self):
        super().__init__('keyboard_controls')
        self.cmd_pub = self.create_publisher(MoveControls, '/teleop_cmd', 10)
        self.speed_pub = self.create_publisher(SpeedControls, '/set_speed', 10)

        self.linear_speed = 0.2
        self.angular_speed = 0.5
        self.publish_speed()

        self.get_logger().info("Keyboard controls ready.")
        self.get_logger().info(
            "Keys: i=forward  j=left  k=stop  l=right  ,=backward  q=quit")
        self.get_logger().info(
            "Speeds: w/s linear +/-   a/d angular +/-   (current: "
            "linear=%.2f angular=%.2f)" % (self.linear_speed, self.angular_speed))

    def publish_speed(self):
        msg = SpeedControls()
        msg.linear_speed = float(self.linear_speed)
        msg.angular_speed = float(self.angular_speed)
        self.speed_pub.publish(msg)

    def run(self):
        old_attr = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin)
        try:
            while True:
                # Non-blocking key read (~10 Hz)
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1)
                    if key == 'q' or key == '\x03':
                        break
                    elif key in ('w', 's'):
                        self.linear_speed = max(
                            0.0, min(1.0,
                                     self.linear_speed + (0.1 if key == 'w' else -0.1)))
                        self.publish_speed()
                        self.get_logger().info(
                            "Linear speed: %.2f" % self.linear_speed)
                    elif key in ('a', 'd'):
                        self.angular_speed = max(
                            0.0, min(2.0,
                                     self.angular_speed + (0.1 if key == 'a' else -0.1)))
                        self.publish_speed()
                        self.get_logger().info(
                            "Angular speed: %.2f" % self.angular_speed)
                    elif key in MOVE_KEYS:
                        command, name = MOVE_KEYS[key]
                        msg = MoveControls()
                        msg.command = command
                        self.cmd_pub.publish(msg)
                        self.get_logger().info("Command: %s" % name)
        finally:
            # Restore terminal and send a final stop command
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_attr)
            msg = MoveControls()
            msg.command = MoveControls.STOP
            self.cmd_pub.publish(msg)
            self.get_logger().info("Stopped.")


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardControls()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()