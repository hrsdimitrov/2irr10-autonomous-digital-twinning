#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import BatteryState
from std_msgs.msg import String

FORWARD_LINEAR_X = 0.15
MOVE_DURATION_SEC = 5.0


class NitrobotMediatorNode(Node):
    def __init__(self):
        super().__init__("nitrobot_mediator_node")

        self.last_zone = None
        self.stop_timer = None

        self.declare_parameter("battery_state_topic", "/battery_state")

        self.sim_pub = self.create_publisher(Twist, "/sim/cmd_vel", 10)
        self.real_pub = self.create_publisher(Twist, "/real/cmd_vel", 10)
        self.battery_pub = self.create_publisher(String, "/nitrobot/battery_state", 10)

        self.create_subscription(
            String,
            "/nitrobot/target_zone",
            self._target_zone_callback,
            10,
        )

        battery_topic = self.get_parameter("battery_state_topic").value
        self.create_subscription(
            BatteryState,
            battery_topic,
            self._battery_state_callback,
            10,
        )

        self.get_logger().info(
            "Listening on /nitrobot/target_zone and "
            f"{battery_topic}; fan-out to /sim/cmd_vel and /real/cmd_vel"
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

    def _battery_state_callback(self, msg: BatteryState):
        battery_percent, status = self._normalize_battery(msg.percentage)

        out = String()
        if battery_percent is None:
            out.data = (
                f"source: real, battery_percent: unknown, "
                f"voltage: {msg.voltage:.1f}, status: {status}"
            )
        else:
            out.data = (
                f"source: real, battery_percent: {battery_percent:.1f}, "
                f"voltage: {msg.voltage:.1f}, status: {status}"
            )

        self.battery_pub.publish(out)

    def _normalize_battery(self, percentage: float):
        if percentage < 0.0 or math.isnan(percentage):
            return None, "unknown"

        if 0.0 <= percentage <= 1.0:
            battery_percent = percentage * 100.0
        else:
            battery_percent = percentage

        if battery_percent < 15.0:
            status = "critical"
        elif battery_percent < 30.0:
            status = "low"
        else:
            status = "normal"

        return battery_percent, status


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
