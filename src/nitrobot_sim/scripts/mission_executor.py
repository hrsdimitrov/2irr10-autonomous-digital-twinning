#!/usr/bin/env python3
"""Mission executor: sequential fertilization with battery simulation and RViz markers."""

import math
import os
import re
import threading
import time

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped, TwistStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray

MARKER_QOS = QoSProfile(
    depth=10,
    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
    reliability=QoSReliabilityPolicy.RELIABLE,
)

NAV_TIMEOUT_SEC    = 180.0  # 3 min total timeout per zone
RETRY_TIMEOUT_SEC  = 360.0  # 6 min timeout for retry
STUCK_TIME_SEC     = 15.0   # declare stuck after 15s no movement
STUCK_DIST_M       = 0.05   # movement threshold (m)
STUCK_ANGLE_RAD    = 0.05   # rotation threshold (rad)
BACKUP_SPEED       = -0.1   # m/s (negative = backward)
BACKUP_DURATION    = 3.0    # seconds to back up
TURN_SPEED         = -0.5   # rad/s (negative = right)
TURN_DURATION      = 1.0    # seconds to turn after backup (~28 deg)


def parse_world_colors(world_path: str) -> dict:
    colors = {}
    pattern = re.compile(
        r"<model name=\"(zone_\d+)\".*?<ambient>([\d.]+)\s+([\d.]+)\s+([\d.]+)",
        re.S,
    )
    with open(world_path) as f:
        text = f.read()
    for m in pattern.finditer(text):
        colors[m.group(1)] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
    return colors


class MissionExecutor(Node):
    def __init__(self):
        super().__init__("mission_executor")

        sim_share = get_package_share_directory("nitrobot_sim")
        mission_path = os.path.join(sim_share, "config", "mission.yaml")
        zones_path   = os.path.join(sim_share, "config", "zone_poses.yaml")
        world_path   = os.path.join(sim_share, "worlds", "farm_world.world")

        with open(mission_path) as f:
            mission_cfg = yaml.safe_load(f)["mission"]
        with open(zones_path) as f:
            zones_cfg = yaml.safe_load(f)

        self._fertilize_order    = mission_cfg["fertilize_order"]
        self._fertilize_duration = mission_cfg["fertilize_duration_sec"]
        self._battery            = mission_cfg["battery_capacity"]
        self._drain_per_sec      = mission_cfg["battery_drain_per_sec"]
        self._drain_per_meter    = mission_cfg["battery_drain_per_meter"]
        self._zones              = zones_cfg["zones"]
        self._frame_id           = zones_cfg.get("frame_id", "map")
        self._world_colors       = parse_world_colors(world_path)

        self._zones_done         = 0
        self._last_pose          = None
        self._dist_traveled      = 0.0
        self._mission_active     = True
        self._battery_depleted   = False   # flag: set when battery hits 0
        self._current_goal_handle = None   # track active nav goal for cancellation
        self._goal_lock          = threading.Lock()
        self._last_drain_time    = time.time()
        self._last_battery_log   = time.time()
        self._zone_colors        = dict(self._world_colors)

        # odom state for stuck detection
        self._odom_x   = 0.0
        self._odom_y   = 0.0
        self._odom_yaw = 0.0
        self._odom_lock = threading.Lock()

        self._nav_client  = ActionClient(self, NavigateToPose, "/sim/navigate_to_pose")
        self._marker_pub  = self.create_publisher(MarkerArray, "/sim/zone_markers", MARKER_QOS)
        self._battery_pub = self.create_publisher(String, "/sim/battery_state", 10)
        self._cmd_vel_pub = self.create_publisher(TwistStamped, "/sim/cmd_vel", 10)

        self.create_subscription(Odometry, "/sim/odom", self._odom_cb, 10)

        self._publish_markers()

        self.get_logger().info("=" * 60)
        self.get_logger().info("MISSION START")
        self.get_logger().info(
            f"Zones to fertilize ({len(self._fertilize_order)}): "
            + ", ".join(self._fertilize_order)
        )
        self.get_logger().info("=" * 60)

        self._battery_thread = threading.Thread(target=self._battery_loop, daemon=True)
        self._battery_thread.start()

        self._mission_thread = threading.Thread(target=self._run_mission, daemon=True)
        self._mission_thread.start()

    # ------------------------------------------------------------------ odom
    def _odom_cb(self, msg: Odometry):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        yaw = math.atan2(2*(q.w*q.z + q.x*q.y), 1 - 2*(q.y*q.y + q.z*q.z))

        with self._odom_lock:
            if self._last_pose is not None:
                dx = x - self._last_pose[0]
                dy = y - self._last_pose[1]
                self._dist_traveled += math.sqrt(dx * dx + dy * dy)
            self._last_pose = (x, y)
            self._odom_x   = x
            self._odom_y   = y
            self._odom_yaw = yaw

    # ------------------------------------------------------------------ battery
    def _battery_loop(self):
        while self._mission_active:
            time.sleep(1.0)
            self._battery_tick()

    def _battery_tick(self):
        if not self._mission_active:
            return
        now = time.time()
        elapsed = now - self._last_drain_time
        self._last_drain_time = now

        drain = elapsed * self._drain_per_sec
        with self._odom_lock:
            drain += self._dist_traveled * self._drain_per_meter
            self._dist_traveled = 0.0
        self._battery = max(0.0, self._battery - drain)

        msg = String()
        msg.data = f"{self._battery:.1f}%"
        self._battery_pub.publish(msg)

        if time.time() - self._last_battery_log >= 30.0:
            self.get_logger().info(f"[RX] Battery: {self._battery:.1f}%")
            self._last_battery_log = time.time()

        # Battery just hit 0: cancel active nav goal immediately
        if self._battery <= 0.0 and not self._battery_depleted:
            self._battery_depleted = True
            self.get_logger().warn("[RX] Battery depleted — cancelling navigation")
            with self._goal_lock:
                if self._current_goal_handle is not None:
                    self._current_goal_handle.cancel_goal_async()

    # ------------------------------------------------------------------ markers
    def _publish_markers(self):
        array = MarkerArray()
        for i, zone_name in enumerate(self._world_colors):
            if zone_name not in self._zones:
                continue
            zp = self._zones[zone_name]
            r, g, b = self._zone_colors.get(zone_name, (0.5, 0.5, 0.5))

            m = Marker()
            m.header.frame_id = self._frame_id
            m.header.stamp = self.get_clock().now().to_msg()
            m.ns = "fertilize_zones"
            m.id = i
            m.type = Marker.CUBE
            m.action = Marker.ADD
            m.pose.position.x = float(zp["x"])
            m.pose.position.y = float(zp["y"])
            m.pose.position.z = 0.05
            m.pose.orientation.w = 1.0
            m.scale.x = 0.4
            m.scale.y = 0.4
            m.scale.z = 0.05
            m.color.r = r
            m.color.g = g
            m.color.b = b
            m.color.a = 0.8
            array.markers.append(m)

        self._marker_pub.publish(array)

    # ------------------------------------------------------------------ backup
    def _do_backup(self):
        """直接发cmd_vel后退3秒脱墙。"""
        self.get_logger().info("[RX] Stuck — backing up to escape wall...")
        end = time.time() + BACKUP_DURATION
        while time.time() < end:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.twist.linear.x = BACKUP_SPEED
            self._cmd_vel_pub.publish(msg)
            time.sleep(0.1)
        stop = TwistStamped()
        stop.header.stamp = self.get_clock().now().to_msg()
        self._cmd_vel_pub.publish(stop)
        time.sleep(0.3)

        # Turn right slightly so Nav2 replans from a different angle
        self.get_logger().info("[RX] Turning right after backup...")
        turn_end = time.time() + TURN_DURATION
        while time.time() < turn_end:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.twist.angular.z = TURN_SPEED
            self._cmd_vel_pub.publish(msg)
            time.sleep(0.1)
        stop2 = TwistStamped()
        stop2.header.stamp = self.get_clock().now().to_msg()
        self._cmd_vel_pub.publish(stop2)
        time.sleep(0.5)
        self.get_logger().info("[RX] Backup complete.")

    # ------------------------------------------------------------------ terminate
    def _terminate_mission(self, reason: str):
        """统一任务终止：打印report，停机器人，清理状态。"""
        self._mission_active = False
        # Stop robot
        stop = TwistStamped()
        stop.header.stamp = self.get_clock().now().to_msg()
        self._cmd_vel_pub.publish(stop)

        self.get_logger().info("=" * 60)
        self.get_logger().info(f"[TX] Mission terminated — {reason}")
        self.get_logger().info(
            f"[TX] Zones completed: {self._zones_done}/{len(self._fertilize_order)}"
        )
        self.get_logger().info(f"[RX] Battery remaining: {self._battery:.1f}%")
        self.get_logger().info("=" * 60)

    # ------------------------------------------------------------------ navigate
    def _navigate_to(self, zone_name: str, timeout: float) -> bool:
        """Returns True on arrival, False on timeout/battery/rejection."""
        zp = self._zones[zone_name]

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = self._frame_id
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = float(zp["x"])
        goal.pose.pose.position.y = float(zp["y"])
        goal.pose.pose.position.z = 0.0
        yaw = float(zp.get("yaw", 0.0))
        goal.pose.pose.orientation.z = math.sin(yaw / 2)
        goal.pose.pose.orientation.w = math.cos(yaw / 2)

        send_future = self._nav_client.send_goal_async(goal)
        while not send_future.done():
            if self._battery_depleted:
                return False
            time.sleep(0.1)
        goal_handle = send_future.result()

        if not goal_handle.accepted:
            self.get_logger().error(f"[RX] Goal rejected for {zone_name}, skipping.")
            return False

        with self._goal_lock:
            self._current_goal_handle = goal_handle

        self.get_logger().info(f"[RX] Navigating to {zone_name}...")

        result_future = goal_handle.get_result_async()
        nav_start = time.time()

        # stuck detection state
        with self._odom_lock:
            last_check_x   = self._odom_x
            last_check_y   = self._odom_y
            last_check_yaw = self._odom_yaw
        last_check_time = time.time()
        stuck_since     = None

        while not result_future.done():
            now = time.time()

            # Battery depleted mid-navigation
            if self._battery_depleted:
                # goal already cancelled by _battery_tick; just wait briefly
                time.sleep(0.5)
                with self._goal_lock:
                    self._current_goal_handle = None
                return False

            # 3min total timeout
            if now - nav_start > timeout:
                goal_handle.cancel_goal_async()
                time.sleep(0.5)
                with self._goal_lock:
                    self._current_goal_handle = None
                self._do_backup()
                return False

            # stuck check every 1s
            if now - last_check_time >= 1.0:
                with self._odom_lock:
                    cx, cy, cyaw = self._odom_x, self._odom_y, self._odom_yaw

                dist   = math.sqrt((cx - last_check_x)**2 + (cy - last_check_y)**2)
                dangle = abs(cyaw - last_check_yaw)

                if dist < STUCK_DIST_M and dangle < STUCK_ANGLE_RAD:
                    if stuck_since is None:
                        stuck_since = now
                    elif now - stuck_since >= STUCK_TIME_SEC:
                        goal_handle.cancel_goal_async()
                        time.sleep(0.5)
                        with self._goal_lock:
                            self._current_goal_handle = None
                        self._do_backup()
                        stuck_since = None
                        remaining = timeout - (now - nav_start)
                        if remaining <= 0 or self._battery_depleted:
                            return False
                        return self._navigate_to(zone_name, remaining)
                else:
                    stuck_since = None

                last_check_x   = cx
                last_check_y   = cy
                last_check_yaw = cyaw
                last_check_time = now

            time.sleep(0.1)

        with self._goal_lock:
            self._current_goal_handle = None
        return True

    # ------------------------------------------------------------------ fertilize
    def _fertilize(self, zone_name: str):
        self.get_logger().info(f"[TX] Begin fertilizing {zone_name}")
        time.sleep(self._fertilize_duration)
        self.get_logger().info(f"[RX] Fertilization complete at {zone_name}")

        self._zones_done += 1
        self._zone_colors[zone_name] = (0.0, 1.0, 0.0)
        self._publish_markers()
        self.get_logger().info(
            f"[TX] Zones completed: {self._zones_done}/{len(self._fertilize_order)}"
        )

    # ------------------------------------------------------------------ mission
    def _run_mission(self):
        self.get_logger().info("Waiting for Nav2 action server...")
        self._nav_client.wait_for_server()
        self.get_logger().info("Nav2 ready — starting mission.")

        retry_list = []

        for zone_name in self._fertilize_order:
            if not self._mission_active or self._battery_depleted:
                break
            if zone_name not in self._zones:
                self.get_logger().warn(f"Zone '{zone_name}' not in zone_poses.yaml, skipping.")
                continue

            self.get_logger().info(
                f"[TX] Navigate to {zone_name}  "
                f"(x={self._zones[zone_name]['x']:.2f}, y={self._zones[zone_name]['y']:.2f})"
            )

            arrived = self._navigate_to(zone_name, NAV_TIMEOUT_SEC)

            if self._battery_depleted:
                break

            if not arrived:
                self.get_logger().warn(f"[RX] Navigation timeout, skipping {zone_name}")
                retry_list.append(zone_name)
                continue

            self.get_logger().info(f"[RX] Arrived at {zone_name}")
            self._fertilize(zone_name)

        if self._battery_depleted:
            self._terminate_mission("battery depleted")
            return

        if retry_list:
            self.get_logger().info("=" * 60)
            self.get_logger().info(f"[TX] Retrying zones: {', '.join(retry_list)}")
            self.get_logger().info("=" * 60)

            for zone_name in retry_list:
                if not self._mission_active or self._battery_depleted:
                    break

                self.get_logger().info(
                    f"[TX] Navigate to {zone_name} (retry)  "
                    f"(x={self._zones[zone_name]['x']:.2f}, y={self._zones[zone_name]['y']:.2f})"
                )

                arrived = self._navigate_to(zone_name, RETRY_TIMEOUT_SEC)

                if self._battery_depleted:
                    break

                if not arrived:
                    self.get_logger().warn(
                        f"[RX] Retry timeout, {zone_name} skipped permanently"
                    )
                    continue

                self.get_logger().info(f"[RX] Arrived at {zone_name}")
                self._fertilize(zone_name)

        if self._battery_depleted:
            self._terminate_mission("battery depleted")
            return

        self._terminate_mission("all zones complete")


def main(args=None):
    rclpy.init(args=args)
    node = MissionExecutor()
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