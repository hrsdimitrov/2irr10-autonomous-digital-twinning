#!/usr/bin/env python3

import math
from pathlib import Path

import yaml
from geometry_msgs.msg import PoseStamped, Quaternion


def _yaw_to_quaternion(yaw: float) -> Quaternion:
    quat = Quaternion()
    quat.x = 0.0
    quat.y = 0.0
    quat.z = math.sin(yaw * 0.5)
    quat.w = math.cos(yaw * 0.5)
    return quat


class ZoneRegistry:
    """Loads nitrogen patch poses used as Nav2 goals."""

    def __init__(self, config_path: str):
        path = Path(config_path)
        if not path.is_file():
            raise FileNotFoundError(f"Zone config not found: {config_path}")

        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)

        self.frame_id = data.get("frame_id", "map")
        self._zones = data.get("zones", {})
        if not self._zones:
            raise ValueError(f"No zones defined in {config_path}")

    def known_zones(self) -> list[str]:
        return sorted(self._zones.keys(), key=lambda name: int(name.split("_")[1]))

    def has_zone(self, zone_name: str) -> bool:
        return zone_name in self._zones

    def to_pose_stamped(self, zone_name: str) -> PoseStamped:
        if zone_name not in self._zones:
            known = ", ".join(self.known_zones()[:5])
            raise KeyError(
                f"Unknown zone '{zone_name}'. "
                f"Expected names like zone_1 (known: {known}...)"
            )

        entry = self._zones[zone_name]
        pose = PoseStamped()
        pose.header.frame_id = self.frame_id
        pose.pose.position.x = float(entry["x"])
        pose.pose.position.y = float(entry["y"])
        pose.pose.position.z = float(entry.get("z", 0.0))
        pose.pose.orientation = _yaw_to_quaternion(float(entry.get("yaw", 0.0)))
        return pose
