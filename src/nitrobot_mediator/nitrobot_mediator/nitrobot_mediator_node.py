#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

FORWARD_LINEAR_X = 0.05
MOVE_DURATION_SEC = 1.0


class NitrobotMediatorNode(Node):
    def __init__(self):
        super().__init__("nitrobot_mediator_node")

        self.last_zone = None
        self.stop_timer = None

        self.sim_pub = self.create_publisher(Twist, "/sim/cmd_vel", 10)
        self.real_pub = self.create_publisher(Twist, "/real/cmd_vel", 10)

        self.create_subscription(
            String,
            "/nitrobot/target_zone",
            self._target_zone_callback,
            10,
        )

        self.get_logger().info(
            "Listening on /nitrobot/target_zone; "
            "fan-out to /sim/cmd_vel and /real/cmd_vel"
        )

    def _target_zone_callback(self, msg: String):
        zone = msg.data
        if zone == self.last_zone:
            return

        self.get_logger().info(
            f"Target zone changed: {self.last_zone} -> {zone}"
        )
        self.last_zone = zone

        if self.stop_timer is not None:
            self.stop_timer.cancel()
            self.stop_timer = None

        self._publish_twist(FORWARD_LINEAR_X, 0.0)
        self.stop_timer = self.create_timer(MOVE_DURATION_SEC, self._stop_after_move)

    def _stop_after_move(self):
        if self.stop_timer is not None:
            self.stop_timer.cancel()
            self.stop_timer = None

        self._publish_twist(0.0, 0.0)
        self.get_logger().info("Stopping sim and real robots")

    def _publish_twist(self, linear_x: float, angular_z: float):
        twist = Twist()
        twist.linear.x = linear_x
        twist.angular.z = angular_z

        self.sim_pub.publish(twist)
        self.real_pub.publish(twist)

        if linear_x != 0.0 or angular_z != 0.0:
            self.get_logger().info(
                f"Move command: linear.x={linear_x}, angular.z={angular_z}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = NitrobotMediatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
