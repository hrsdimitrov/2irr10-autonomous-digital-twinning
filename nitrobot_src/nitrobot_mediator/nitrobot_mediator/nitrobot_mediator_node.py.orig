#!/usr/bin/env python3

import math
import os

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from std_msgs.msg import String

NAV_ACTION = "/navigate_to_pose"


class NitrobotMediatorNode(Node):
    def __init__(self):
        super().__init__("nitrobot_mediator_node")

        self.last_zone = None
        self.zones = self._load_zones()

        self.nav_client = ActionClient(self, NavigateToPose, NAV_ACTION)
        self.battery_pub = self.create_publisher(String, "/nitrobot/battery_state", 10)

        self.create_subscription(
            String,
            "/nitrobot/target_zone",
            self._target_zone_callback,
            10,
        )
        self.create_subscription(
            BatteryState,
            "/battery_state",
            self._battery_state_callback,
            10,
        )

        self.get_logger().info(
            f"Loaded {len(self.zones)} zones; /nitrobot/target_zone -> {NAV_ACTION}; "
            "/battery_state -> /nitrobot/battery_state"
        )

    def _load_zones(self):
        zones_path = os.path.join(
            get_package_share_directory("nitrobot_mediator"),
            "config",
            "zones.yaml",
        )
        with open(zones_path, "r", encoding="utf-8") as zones_file:
            data = yaml.safe_load(zones_file)
        return data.get("zones", {})

    def _target_zone_callback(self, msg: String):
        zone = msg.data.strip()
        self.get_logger().info(f"Received target zone: {zone}")

        if zone == self.last_zone:
            self.get_logger().info(f"Ignored duplicate target zone: {zone}")
            return

        if zone not in self.zones:
            self.get_logger().error(f"Unknown zone: {zone}")
            return

        zone_data = self.zones[zone]
        x = float(zone_data["x"])
        y = float(zone_data["y"])
        yaw = float(zone_data.get("yaw", 0.0))

        self.get_logger().info(f"Resolved {zone} -> x={x}, y={y}, yaw={yaw}")
        self.last_zone = zone

        goal = self._make_nav_goal(x, y, yaw)
        self._send_nav_goal(goal)

    def _make_nav_goal(self, x: float, y: float, yaw: float) -> NavigateToPose.Goal:
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = "map"
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.position.z = 0.0
        goal.pose.pose.orientation = self._yaw_to_quaternion(yaw)
        return goal

    @staticmethod
    def _yaw_to_quaternion(yaw: float) -> Quaternion:
        quaternion = Quaternion()
        quaternion.z = math.sin(yaw / 2.0)
        quaternion.w = math.cos(yaw / 2.0)
        return quaternion

    def _send_nav_goal(self, goal: NavigateToPose.Goal):
        self.get_logger().info(f"Waiting for {NAV_ACTION} action server")

        if not self.nav_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error(
                f"{NAV_ACTION} action server not available after timeout"
            )
            return

        self.get_logger().info(f"Sent NavigateToPose goal to {NAV_ACTION}")
        send_future = self.nav_client.send_goal_async(goal)
        send_future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn("Goal rejected")
            return

        self.get_logger().info("Goal accepted")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _result_callback(self, future):
        result = future.result()
        self.get_logger().info(f"Goal finished: status={result.status}")

    def _battery_state_callback(self, msg: BatteryState):
        battery_percent, status = self._normalize_battery(msg.percentage)

        if battery_percent is None:
            out = (
                f"source: physical, battery_percent: unknown, "
                f"voltage: {msg.voltage:.1f}, status: {status}"
            )
        else:
            out = (
                f"source: physical, battery_percent: {battery_percent:.1f}, "
                f"voltage: {msg.voltage:.1f}, status: {status}"
            )

        self.battery_pub.publish(String(data=out))

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
