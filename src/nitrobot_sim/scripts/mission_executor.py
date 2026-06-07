#!/usr/bin/env python3
"""Mission executor: sequential fertilization with battery simulation and RViz markers."""

import math
import os
import re
import time

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray


def parse_world_colors(world_path: str) -> dict:
    """Parse zone colors from farm_world.world. Returns {zone_name: (r,g,b)}."""
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

        # ── Load configs ──────────────────────────────────────────────────────
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

        # ── State ─────────────────────────────────────────────────────────────
        self._zones_done     = 0
        self._last_pose      = None
        self._dist_traveled  = 0.0
        self._mission_active = True
        self._last_drain_time = time.time()
        self._last_battery_log = self.get_clock().now()

        # Track per-zone color: start from world colors, go green when done
        self._zone_colors = dict(self._world_colors)

        # ── ROS interfaces ────────────────────────────────────────────────────
        self._nav_client = ActionClient(
            self, NavigateToPose, "/sim/navigate_to_pose"
        )
        self._marker_pub  = self.create_publisher(MarkerArray, "/sim/zone_markers", 10)
        self._battery_pub = self.create_publisher(String, "/sim/battery_state", 10)

        self.create_subscription(Odometry, "/sim/odom", self._odom_cb, 10)
        self.create_timer(1.0, self._battery_tick)

        # Publish initial markers (all zones at their original world colors)
        self._publish_markers()

        # ── Start mission after short delay ───────────────────────────────────
        self.get_logger().info("=" * 60)
        self.get_logger().info("MISSION START")
        self.get_logger().info(
            f"Zones to fertilize ({len(self._fertilize_order)}): "
            + ", ".join(self._fertilize_order)
        )
        self.get_logger().info("=" * 60)

        self._mission_timer = self.create_timer(2.0, self._start_mission_once)

    # ── One-shot mission kickoff ───────────────────────────────────────────────
    def _start_mission_once(self):
        self._mission_timer.cancel()
        self._run_mission()

    # ── Odometry callback ─────────────────────────────────────────────────────
    def _odom_cb(self, msg: Odometry):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        if self._last_pose is not None:
            dx = x - self._last_pose[0]
            dy = y - self._last_pose[1]
            self._dist_traveled += math.sqrt(dx * dx + dy * dy)
        self._last_pose = (x, y)

    # ── Battery tick ──────────────────────────────────────────────────────────
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

        now_ros = self.get_clock().now()
        elapsed_log = (now_ros - self._last_battery_log).nanoseconds / 1e9
        if elapsed_log >= 10.0:
            self.get_logger().info(f"[RX] Battery: {self._battery:.1f}%")
            self._last_battery_log = now_ros

    # ── Marker publisher ──────────────────────────────────────────────────────
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

    # ── Main mission loop ─────────────────────────────────────────────────────
    def _run_mission(self):
        for zone_name in self._fertilize_order:
            if not self._mission_active:
                return

            # Battery check
            if self._battery <= 0.0:
                self.get_logger().warn(
                    "[TX] Mission terminated — battery depleted"
                )
                self._mission_active = False
                return

            if zone_name not in self._zones:
                self.get_logger().warn(
                    f"Zone '{zone_name}' not found in zone_poses.yaml, skipping."
                )
                continue

            zp = self._zones[zone_name]

            # ── TX: navigate ───────────────────────────────────────────────
            self.get_logger().info(
                f"[TX] Navigate to {zone_name}  (x={zp['x']:.2f}, y={zp['y']:.2f})"
            )

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

            self._nav_client.wait_for_server()
            send_future = self._nav_client.send_goal_async(goal)
            rclpy.spin_until_future_complete(self, send_future)
            goal_handle = send_future.result()

            if not goal_handle.accepted:
                self.get_logger().error(
                    f"[RX] Goal rejected for {zone_name}, skipping."
                )
                continue

            # ── RX: navigating ─────────────────────────────────────────────
            self.get_logger().info(f"[RX] Navigating to {zone_name}...")

            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result_future)

            # ── RX: arrived ────────────────────────────────────────────────
            self.get_logger().info(f"[RX] Arrived at {zone_name}")

            # ── TX: begin fertilizing ──────────────────────────────────────
            self.get_logger().info(f"[TX] Begin fertilizing {zone_name}")

            time.sleep(self._fertilize_duration)

            # ── RX: fertilization complete ─────────────────────────────────
            self.get_logger().info(f"[RX] Fertilization complete at {zone_name}")

            self._zones_done += 1
            self._zone_colors[zone_name] = (0.0, 1.0, 0.0)
            self._publish_markers()

            # ── TX: update count ───────────────────────────────────────────
            self.get_logger().info(
                f"[TX] Zones completed: {self._zones_done}/{len(self._fertilize_order)}"
            )

        # ── All zones done ─────────────────────────────────────────────────────
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