#!/usr/bin/env python3
"""Build map.pgm / map.yaml from farm_world.world wall boxes (map frame = Gazebo world)."""

from __future__ import annotations

import math
import re
import struct
from pathlib import Path

RESOLUTION = 0.05
PADDING_M = 0.35
FREE = 254
OCCUPIED = 0
UNKNOWN = 205


def parse_boxes(world_text: str) -> list[tuple[float, float, float, float, float, float]]:
    """Return (cx, cy, yaw, sx, sy, sz) for each wall box model."""
    boxes: list[tuple[float, float, float, float, float, float]] = []
    for block in re.finditer(r"<model name='([^']+)'>(.*?)</model>", world_text, re.S):
        name = block.group(1)
        if name in {"ground_plane"} or name.startswith("zone_"):
            continue
        body = block.group(2)
        pose_m = re.search(
            r"<pose>\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+"
            r"([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*</pose>",
            body,
        )
        size_m = re.search(
            r"<collision name='box_collision'>.*?<size>\s*"
            r"([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*</size>",
            body,
            re.S,
        )
        if not pose_m or not size_m:
            continue
        cx, cy, _, _, _, yaw = map(float, pose_m.groups())
        sx, sy, sz = map(float, size_m.groups())
        if sx < 0.2 and sy < 0.2:
            continue
        boxes.append((cx, cy, yaw, sx, sy, sz))
    return boxes


def rasterize(
    boxes: list[tuple[float, float, float, float, float, float]],
    resolution: float,
    padding: float,
) -> tuple[list[list[int]], float, float]:
    corners_x: list[float] = []
    corners_y: list[float] = []
    for cx, cy, yaw, sx, sy, _ in boxes:
        c = math.cos(yaw)
        s = math.sin(yaw)
        for lx, ly in (
            (-sx / 2, -sy / 2),
            (sx / 2, -sy / 2),
            (sx / 2, sy / 2),
            (-sx / 2, sy / 2),
        ):
            wx = cx + c * lx - s * ly
            wy = cy + s * lx + c * ly
            corners_x.append(wx)
            corners_y.append(wy)

    min_x = min(corners_x) - padding
    min_y = min(corners_y) - padding
    max_x = max(corners_x) + padding
    max_y = max(corners_y) + padding

    width = int(math.ceil((max_x - min_x) / resolution))
    height = int(math.ceil((max_y - min_y) / resolution))
    grid = [[FREE for _ in range(width)] for _ in range(height)]

    def mark(wx: float, wy: float) -> None:
        col = int((wx - min_x) / resolution)
        row = height - 1 - int((wy - min_y) / resolution)
        if 0 <= row < height and 0 <= col < width:
            grid[row][col] = OCCUPIED

    for cx, cy, yaw, sx, sy, _ in boxes:
        c = math.cos(yaw)
        s = math.sin(yaw)
        steps = max(int(max(sx, sy) / resolution) + 2, 4)
        for ix in range(steps):
            for iy in range(steps):
                lx = -sx / 2 + sx * ix / max(steps - 1, 1)
                ly = -sy / 2 + sy * iy / max(steps - 1, 1)
                wx = cx + c * lx - s * ly
                wy = cy + s * lx + c * ly
                mark(wx, wy)
                for dx in (-0.5, 0.0, 0.5):
                    for dy in (-0.5, 0.0, 0.5):
                        mark(wx + dx * resolution, wy + dy * resolution)

    return grid, min_x, min_y


def write_pgm(path: Path, grid: list[list[int]]) -> None:
    height = len(grid)
    width = len(grid[0])
    with path.open("wb") as f:
        f.write(f"P5\n{width} {height}\n255\n".encode("ascii"))
        for row in grid:
            f.write(struct.pack(f"{width}B", *row))


def write_yaml(path: Path, resolution: float, origin_x: float, origin_y: float) -> None:
    path.write_text(
        "\n".join(
            [
                "image: map.pgm",
                "mode: trinary",
                f"resolution: {resolution:.3f}",
                f"origin: [{origin_x:.3f}, {origin_y:.3f}, 0]",
                "negate: 0",
                "occupied_thresh: 0.65",
                "free_thresh: 0.196",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    pkg = Path(__file__).resolve().parents[1]
    world = pkg / "worlds" / "farm_world.world"
    maps_dir = pkg / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)

    boxes = parse_boxes(world.read_text(encoding="utf-8"))
    if not boxes:
        raise SystemExit(f"No wall boxes parsed from {world}")

    grid, origin_x, origin_y = rasterize(boxes, RESOLUTION, PADDING_M)
    write_pgm(maps_dir / "map.pgm", grid)
    write_yaml(maps_dir / "map.yaml", RESOLUTION, origin_x, origin_y)
    print(f"Wrote {maps_dir / 'map.pgm'} ({len(grid[0])}x{len(grid)})")
    print(f"origin=[{origin_x:.3f}, {origin_y:.3f}], walls={len(boxes)}")


if __name__ == "__main__":
    main()
