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
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import BackUp, NavigateToPose
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

NAV_TIMEOUT_SEC   = 180.0   # 3 min first attempt
RETRY_TIMEOUT_SEC = 360.0   # 6 min retry attempt
BACKUP_DIST_M     = 0.3     # back up 0.3m after timeout


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

        self._zones_done       = 0
        self._last_pose        = None
        self._dist_traveled    = 0.0
        self._mission_active   = True
        self._last_drain_time  = time.time()
        self._last_battery_log = time.time()
        self._zone_colors      = dict(self._world_colors)

        self._nav_client    = ActionClient(self, NavigateToPose, "/sim/navigate_to_pose")
        self._backup_client = ActionClient(self, BackUp, "/sim/backup")
        self._marker_pub    = self.create_publisher(MarkerArray, "/sim/zone_markers", MARKER_QOS)
        self._battery_pub   = self.create_publisher(String, "/sim/battery_state", 10)

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

    def _odom_cb(self, msg: Odometry):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        if self._last_pose is not None:
            dx = x - self._last_pose[0]
            dy = y - self._last_pose[1]
            self._dist_traveled += math.sqrt(dx * dx + dy * dy)
        self._last_pose = (x, y)

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
        drain += self._dist_traveled * self._drain_per_meter
        self._dist_traveled = 0.0
        self._battery = max(0.0, self._battery - drain)

        msg = String()
        msg.data = f"{self._battery:.1f}%"
        self._battery_pub.publish(msg)

        if time.time() - self._last_battery_log >= 30.0:
            self.get_logger().info(f"[RX] Battery: {self._battery:.1f}%")
            self._last_battery_log = time.time()

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

    def _do_backup(self):
        """Back up 0.3m to escape wall, then pause briefly."""
        self.get_logger().info("[RX] Stuck — backing up to escape wall...")
        if not self._backup_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().warn("Backup action server not available, skipping backup.")
            return

        goal = BackUp.Goal()
        goal.target.x = BACKUP_DIST_M
        goal.speed = 0.1

        send_future = self._backup_client.send_goal_async(goal)
        start = time.time()
        while not send_future.done():
            if time.time() - start > 5.0:
                return
            time.sleep(0.1)

        goal_handle = send_future.result()
        if not goal_handle.accepted:
            return

        result_future = goal_handle.get_result_async()
        start = time.time()
        while not result_future.done():
            if time.time() - start > 10.0:
                break
            time.sleep(0.1)

        time.sleep(0.5)
        self.get_logger().info("[RX] Backup complete.")

    def _navigate_to(self, zone_name: str, timeout: float) -> bool:
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
            time.sleep(0.1)
        goal_handle = send_future.result()

        if not goal_handle.accepted:
            self.get_logger().error(f"[RX] Goal rejected for {zone_name}, skipping.")
            return False

        self.get_logger().info(f"[RX] Navigating to {zone_name}...")

        result_future = goal_handle.get_result_async()
        start = time.time()
        while not result_future.done():
            if time.time() - start > timeout:
                goal_handle.cancel_goal_async()
                time.sleep(0.5)
                self._do_backup()
                return False
            time.sleep(0.1)

        return True

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

    def _run_mission(self):
        self.get_logger().info("Waiting for Nav2 action server...")
        self._nav_client.wait_for_server()
        self.get_logger().info("Nav2 ready — starting mission.")

        retry_list = []

        for zone_name in self._fertilize_order:
            if not self._mission_active:
                return
            if self._battery <= 0.0:
                self.get_logger().warn("[TX] Mission terminated — battery depleted")
                self._mission_active = False
                return
            if zone_name not in self._zones:
                self.get_logger().warn(f"Zone '{zone_name}' not in zone_poses.yaml, skipping.")
                continue

            self.get_logger().info(
                f"[TX] Navigate to {zone_name}  "
                f"(x={self._zones[zone_name]['x']:.2f}, y={self._zones[zone_name]['y']:.2f})"
            )

            arrived = self._navigate_to(zone_name, NAV_TIMEOUT_SEC)

            if not arrived:
                self.get_logger().warn(f"[RX] Navigation timeout, skipping {zone_name}")
                retry_list.append(zone_name)
                continue

            self.get_logger().info(f"[RX] Arrived at {zone_name}")
            self._fertilize(zone_name)

        if retry_list:
            self.get_logger().info("=" * 60)
            self.get_logger().info(f"[TX] Retrying zones: {', '.join(retry_list)}")
            self.get_logger().info("=" * 60)

            for zone_name in retry_list:
                if not self._mission_active:
                    return
                if self._battery <= 0.0:
                    self.get_logger().warn("[TX] Mission terminated — battery depleted")
                    self._mission_active = False
                    return

                self.get_logger().info(
                    f"[TX] Navigate to {zone_name} (retry)  "
                    f"(x={self._zones[zone_name]['x']:.2f}, y={self._zones[zone_name]['y']:.2f})"
                )

                arrived = self._navigate_to(zone_name, RETRY_TIMEOUT_SEC)

                if not arrived:
                    self.get_logger().warn(
                        f"[RX] Retry timeout, {zone_name} skipped permanently"
                    )
                    continue

                self.get_logger().info(f"[RX] Arrived at {zone_name}")
                self._fertilize(zone_name)

        self._mission_active = False
        self.get_logger().info("=" * 60)
        self.get_logger().info(
            f"[TX] Mission terminated — all zones complete  "
            f"({self._zones_done}/{len(self._fertilize_order)} fertilized)"
        )
        self.get_logger().info("=" * 60)


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