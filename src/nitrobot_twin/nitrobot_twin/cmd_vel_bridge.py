#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class CmdVelBridge(Node):
    def __init__(self):
        super().__init__("cmd_vel_bridge")

        self.publisher = self.create_publisher(Twist, "/real/cmd_vel", 10)

        self.subscription = self.create_subscription(
            Twist,
            "/cmd_vel",
            self.cmd_vel_callback,
            10
        )

        self.max_linear_speed = 0.08
        self.max_angular_speed = 0.4

        self.get_logger().info("cmd_vel bridge started: /cmd_vel -> /real/cmd_vel")

    def clamp(self, value, limit):
        return max(min(value, limit), -limit)

    def cmd_vel_callback(self, msg):
        safe_msg = Twist()

        safe_msg.linear.x = self.clamp(msg.linear.x, self.max_linear_speed)
        safe_msg.linear.y = 0.0
        safe_msg.linear.z = 0.0

        safe_msg.angular.x = 0.0
        safe_msg.angular.y = 0.0
        safe_msg.angular.z = self.clamp(msg.angular.z, self.max_angular_speed)

        self.publisher.publish(safe_msg)


def main(args=None):
    rclpy.init(args=args)

    node = CmdVelBridge()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()