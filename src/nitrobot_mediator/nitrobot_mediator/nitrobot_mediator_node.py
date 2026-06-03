#!/usr/bin/env python3

import math

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist, TwistStamped
from nav2_msgs.action import NavigateToPose
from sensor_msgs.msg import BatteryState
from std_msgs.msg import String

from nitrobot_mediator.zone_registry import ZoneRegistry

FORWARD_LINEAR_X = 0.15
MOVE_DURATION_SEC = 5.0
CMD_VEL_PUBLISH_HZ = 10.0
NAV_SERVER_WAIT_SEC = 10.0
NAV_RETRY_PERIOD_SEC = 3.0


class NavigationGoalClient:
    def __init__(self, node: Node, action_name: str, label: str):
        self._node = node
        self._label = label
        self._action_name = action_name
        self._client = ActionClient(node, NavigateToPose, action_name)
        self._goal_handle = None
        self._pending_goal = None
        self._retry_timer = None

    def _cancel_active_goal(self):
        if self._goal_handle is None:
            return
        self._goal_handle.cancel_goal_async()
        self._goal_handle = None

    def cancel(self):
        self._pending_goal = None
        if self._retry_timer is not None:
            self._retry_timer.cancel()
            self._retry_timer = None
        self._cancel_active_goal()

    def send_pose(self, pose, zone_name: str):
        if not self._client.wait_for_server(timeout_sec=NAV_SERVER_WAIT_SEC):
            self._pending_goal = (pose, zone_name)
            self._ensure_retry_timer()
            self._node.get_logger().info(
                f"{self._label} Nav2 not ready yet; "
                f"will retry goal to {zone_name}"
            )
            return

        self._pending_goal = None
        if self._retry_timer is not None:
            self._retry_timer.cancel()
            self._retry_timer = None

        self._cancel_active_goal()

        goal = NavigateToPose.Goal()
        goal.pose = pose
        goal.pose.header.stamp = self._node.get_clock().now().to_msg()

        send_future = self._client.send_goal_async(
            goal,
            feedback_callback=self._feedback_callback,
        )
        send_future.add_done_callback(
            lambda future, zone=zone_name: self._goal_response_callback(future, zone)
        )

    def _goal_response_callback(self, future, zone_name: str):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self._node.get_logger().warn(
                f"{self._label} navigation goal to {zone_name} was rejected"
            )
            return

        self._goal_handle = goal_handle
        self._node.get_logger().info(
            f"{self._label} navigation goal to {zone_name} accepted"
        )
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda result_future, zone=zone_name: self._result_callback(
                result_future, zone
            )
        )

    def _result_callback(self, future, zone_name: str):
        result = future.result().result
        self._goal_handle = None
        self._node.get_logger().info(
            f"{self._label} navigation to {zone_name} finished "
            f"(error code {result.error_code})"
        )

    def _feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self._node.get_logger().info(
            f"{self._label} distance remaining: "
            f"{feedback.distance_remaining:.2f} m",
            throttle_duration_sec=2.0,
        )

    def _ensure_retry_timer(self):
        if self._retry_timer is not None:
            return
        self._retry_timer = self._node.create_timer(
            NAV_RETRY_PERIOD_SEC, self._retry_pending_goal
        )

    def _retry_pending_goal(self):
        if self._pending_goal is None:
            return
        pose, zone_name = self._pending_goal
        if not self._client.wait_for_server(timeout_sec=1.0):
            return
        self._node.get_logger().info(
            f"{self._label} Nav2 ready; sending pending goal to {zone_name}"
        )
        self.send_pose(pose, zone_name)


class NitrobotMediatorNode(Node):
    def __init__(self):
        super().__init__("nitrobot_mediator_node")

        self.last_zone = None
        self.stop_timer = None
        self.move_timer = None
        self._move_linear_x = 0.0
        self._move_angular_z = 0.0

        self.declare_parameter("battery_state_topic", "/battery_state")
        self.declare_parameter("zones_config", "")
        self.declare_parameter("use_sim_navigation", True)
        self.declare_parameter("use_real_navigation", False)
        self.declare_parameter("sim_navigate_action", "/sim/navigate_to_pose")
        self.declare_parameter("real_navigate_action", "/real/navigate_to_pose")
        self.declare_parameter("goal_frame_id", "map")

        zones_config = self.get_parameter("zones_config").value
        if not zones_config:
            raise RuntimeError(
                "Parameter 'zones_config' must point to zone_poses.yaml"
            )
        self._zone_registry = ZoneRegistry(zones_config)

        use_sim_navigation = self.get_parameter("use_sim_navigation").value
        use_real_navigation = self.get_parameter("use_real_navigation").value

        self._sim_nav = None
        self._real_nav = None
        if use_sim_navigation:
            self._sim_nav = NavigationGoalClient(
                self,
                self.get_parameter("sim_navigate_action").value,
                "sim",
            )
        if use_real_navigation:
            self._real_nav = NavigationGoalClient(
                self,
                self.get_parameter("real_navigate_action").value,
                "real",
            )

        self.sim_pub = self.create_publisher(TwistStamped, "/sim/cmd_vel", 10)
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

        nav_modes = []
        if self._sim_nav is not None:
            nav_modes.append("sim Nav2 goals")
        if self._real_nav is not None:
            nav_modes.append("real Nav2 goals")
        if not nav_modes:
            nav_modes.append("timed cmd_vel fallback")

        self.get_logger().info(
            "Mediator ready: "
            f"{', '.join(nav_modes)}; zones from {zones_config}; "
            f"battery on {battery_topic}"
        )

    def _target_zone_callback(self, msg: String):
        zone = msg.data.strip()
        if not zone or zone == self.last_zone:
            return

        previous_zone = self.last_zone
        self.last_zone = zone
        if previous_zone is not None:
            self.get_logger().info(
                f"Target zone changed: {previous_zone} -> {zone}"
            )

        if not self._zone_registry.has_zone(zone):
            self.get_logger().error(
                f"Unknown zone '{zone}'. Known zones: "
                f"{', '.join(self._zone_registry.known_zones()[:8])}..."
            )
            return

        pose = self._zone_registry.to_pose_stamped(zone)
        pose.header.stamp = self.get_clock().now().to_msg()
        goal_frame = self.get_parameter("goal_frame_id").value
        pose.header.frame_id = goal_frame

        self._cancel_timed_move()

        if self._sim_nav is not None:
            self._sim_nav.send_pose(pose, zone)
        if self._real_nav is not None:
            real_pose = PoseStamped()
            real_pose.header = pose.header
            real_pose.pose = pose.pose
            self._real_nav.send_pose(real_pose, zone)

        if self._sim_nav is None and self._real_nav is None:
            self._start_timed_move(FORWARD_LINEAR_X, 0.0)

    def _cancel_timed_move(self):
        if self.stop_timer is not None:
            self.stop_timer.cancel()
            self.stop_timer = None
        self._stop_move_timer()

    def _start_timed_move(self, linear_x: float, angular_z: float):
        self._move_linear_x = linear_x
        self._move_angular_z = angular_z
        self._publish_twist(linear_x, angular_z)
        self.get_logger().info(
            f"Fallback move: linear.x={linear_x}, angular.z={angular_z} "
            f"({CMD_VEL_PUBLISH_HZ:.0f} Hz for {MOVE_DURATION_SEC:.0f}s)"
        )
        period = 1.0 / CMD_VEL_PUBLISH_HZ
        self.move_timer = self.create_timer(period, self._publish_move_tick)
        self.stop_timer = self.create_timer(MOVE_DURATION_SEC, self._stop_after_move)

    def _stop_after_move(self):
        if self.stop_timer is not None:
            self.stop_timer.cancel()
            self.stop_timer = None
        self._stop_move()
        self.get_logger().info("Stopping sim and real robots (fallback)")

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
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
