#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped
from sensor_msgs.msg import BatteryState
from std_msgs.msg import String

FORWARD_LINEAR_X = 0.15
MOVE_DURATION_SEC = 5.0
CMD_VEL_PUBLISH_HZ = 10.0


class NitrobotMediatorNode(Node):
    def __init__(self):
        super().__init__("nitrobot_mediator_node")

        self.last_zone = None
        self.stop_timer = None
        self.move_timer = None
        self._move_linear_x = 0.0
        self._move_angular_z = 0.0

        self.declare_parameter("battery_state_topic", "/battery_state")

        # Gazebo ros_gz bridge expects TwistStamped on cmd_vel
        self.sim_pub = self.create_publisher(TwistStamped, "/sim/cmd_vel", 10)
        # Physical TurtleBot3 expects Twist on cmd_vel
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
            f"{battery_topic}; fan-out to /sim/cmd_vel (TwistStamped) "
            "and /real/cmd_vel (Twist)"
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

        self._start_move(FORWARD_LINEAR_X, 0.0)
        self.stop_timer = self.create_timer(MOVE_DURATION_SEC, self._stop_after_move)

    def _stop_after_move(self):
        if self.stop_timer is not None:
            self.stop_timer.cancel()
            self.stop_timer = None

        self._stop_move()
        self.get_logger().info("Stopping sim and real robots")

    def _start_move(self, linear_x: float, angular_z: float):
        self._stop_move_timer()
        self._move_linear_x = linear_x
        self._move_angular_z = angular_z
        self._publish_twist(linear_x, angular_z)
        if linear_x != 0.0 or angular_z != 0.0:
            self.get_logger().info(
                f"Move command: linear.x={linear_x}, angular.z={angular_z} "
                f"({CMD_VEL_PUBLISH_HZ:.0f} Hz for {MOVE_DURATION_SEC:.0f}s)"
            )
        period = 1.0 / CMD_VEL_PUBLISH_HZ
        self.move_timer = self.create_timer(period, self._publish_move_tick)

    def _publish_move_tick(self):
        self._publish_twist(self._move_linear_x, self._move_angular_z)

    def _stop_move_timer(self):
        if self.move_timer is not None:
            self.move_timer.cancel()
            self.move_timer = None

    def _stop_move(self):
        self._stop_move_timer()
        self._publish_twist(0.0, 0.0)

    def _publish_twist(self, linear_x: float, angular_z: float):
        sim_msg = TwistStamped()
        sim_msg.header.stamp = self.get_clock().now().to_msg()
        sim_msg.twist.linear.x = linear_x
        sim_msg.twist.angular.z = angular_z
        self.sim_pub.publish(sim_msg)

        real_msg = Twist()
        real_msg.linear.x = linear_x
        real_msg.angular.z = angular_z
        self.real_pub.publish(real_msg)

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
