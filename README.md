# 2IRR10 Autonomous Digital Twinning

Simulation uses the **`/sim`** namespace. The **map frame matches the Gazebo world** (same origin as `zone_poses.yaml`).

## Setup

```bash
docker compose build && xhost +local:docker && docker compose up -d
docker exec -it turtlebot3_container bash
cd /ws && colcon build --symlink-install && source install/setup.bash
source /opt/turtlebot3_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
```

## Simulation (manual — run in order, separate terminals)

**1. Gazebo**

```bash
ros2 launch nitrobot_sim sim.launch.py
```

Wait for the world to load. If the GUI is paused, press Play.

**2. Robot** (publishes `/sim/tf` and locks `map` → `odom` to the spawn pose)

```bash
ros2 launch nitrobot_sim spawn.launch.py
```

Optional spawn offset: `ros2 launch nitrobot_sim spawn.launch.py x_pose:=0.0 y_pose:=0.0`

**3. Nav2 + RViz** (starts RViz ~15s after Nav2; map on `/sim/map`)

```bash
ros2 launch nitrobot_sim nav2.launch.py
```

RViz only: `ros2 launch nitrobot_sim rviz.launch.py`

**4. Decision**

```bash
ros2 launch nitrobot_decision decision.launch.py
```

**5. Mediator**

```bash
ros2 launch nitrobot_mediator mediator.launch.py
```

**Zone goal**

```bash
ros2 run nitrobot_decision set_zone.sh zone_5
```

## Gazebo vs RViz

- **Gazebo** shows the robot in the **world** (ground truth).
- **RViz** shows the robot via **TF** (`map` → `odom` → `base_footprint`).

They should match after **spawn** runs: `spawn.launch.py` publishes a fixed `map` → `odom` transform at the same `x_pose` / `y_pose` as Gazebo. If they still look wrong, restart spawn + nav2 (same spawn args) or use **2D Pose Estimate** once in RViz.

Kill stale processes:

```bash
pkill -9 -f 'gz sim|rviz2|ros2 launch|nav2_|nitrobot_' 2>/dev/null; ros2 daemon stop 2>/dev/null; true
```

## Physical robot

```bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_bringup robot.launch.py namespace:=real
```
