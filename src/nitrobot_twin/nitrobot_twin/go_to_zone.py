#!/usr/bin/env python3

import sys
import rclpy

from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped


ZONES = {
    "zone_1": (-0.7, 0.4),
    "zone_2": (-0.15, 0.4),
    "zone_3": (0.4, 0.4),

    "zone_4": (-0.7, -0.15),
    "zone_5": (-0.15, -0.15),
    "zone_6": (0.4, -0.15),

    "zone_7": (-0.7, -0.7),
    "zone_8": (-0.15, -0.7),
    "zone_9": (0.4, -0.7),

    "zone_10": (1.10, 0.65),
    "zone_11": (1.65, 0.65),
    "zone_12": (2.20, 0.65),

    "zone_13": (1.10, 0.05),
    "zone_14": (1.65, 0.05),
    "zone_15": (2.20, 0.05),

    "zone_16": (1.10, -0.5),
    "zone_17": (1.65, -0.5),
    "zone_18": (2.20, -0.5),

    "zone_19": (-0.6, -1.4),
    "zone_20": (0.0, -1.4),
    "zone_21": (0.6, -1.4),

    "zone_22": (-0.6, -2.35),
    "zone_23": (0.0, -2.35),
    "zone_24": (0.6, -2.35),

    "zone_25": (-0.6, -2.90),
    "zone_26": (0.0, -2.90),
    "zone_27": (0.6, -2.90),

    "zone_28": (-0.6, -3.45),
    "zone_29": (0.0, -3.45),
    "zone_30": (0.6, -3.45),

    "zone_31": (1.25, -1.15),
    "zone_32": (1.80, -1.15),
    "zone_33": (2.35, -1.15),

    "zone_34": (1.25, -1.70),
    "zone_35": (1.80, -1.70),
    "zone_36": (2.35, -1.70),

    "zone_37": (1.25, -2.25),
    "zone_38": (1.80, -2.25),
    "zone_39": (2.35, -2.25),

    "zone_40": (1.25, -2.80),
    "zone_41": (1.80, -2.80),
    "zone_42": (2.35, -2.80),

    "zone_43": (1.25, -3.35),
    "zone_44": (1.80, -3.35),
}


class GoToZoneNode(Node):
    def __init__(self):
        super().__init__("go_to_zone_node")
        self.client = ActionClient(self, NavigateToPose, "navigate_to_pose")

    def go_to_zone(self, zone_name):
        if zone_name not in ZONES:
            self.get_logger().error(f"Unknown zone: {zone_name}")
            self.get_logger().info(f"Available zones: {', '.join(ZONES.keys())}")
            rclpy.shutdown()
            return

        x, y = ZONES[zone_name]

        self.get_logger().info("Waiting for Nav2...")
        self.client.wait_for_server()

        goal = NavigateToPose.Goal()

        goal.pose = PoseStamped()
        goal.pose.header.frame_id = "map"
        goal.pose.header.stamp = self.get_clock().now().to_msg()

        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.position.z = 0.0
        goal.pose.pose.orientation.w = 1.0

        self.get_logger().info(f"Sending goal to {zone_name}: x={x}, y={y}")

        future = self.client.send_goal_async(goal)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected by Nav2")
            rclpy.shutdown()
            return

        self.get_logger().info("Goal accepted by Nav2")

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def result_callback(self, future):
        result = future.result()
        self.get_logger().info(f"Navigation finished with status: {result.status}")
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)

    node = GoToZoneNode()

    if len(sys.argv) < 2:
        node.get_logger().error("Usage: ros2 run nitrobot_twin go_to_zone zone_1")
        rclpy.shutdown()
        return

    node.go_to_zone(sys.argv[1])
    rclpy.spin(node)


if __name__ == "__main__":
    main()