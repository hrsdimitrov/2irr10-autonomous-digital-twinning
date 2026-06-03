# 2IRR10 Autonomous Digital Twinning

## Quick start

```bash
docker compose build && xhost +local:docker && docker compose up -d
docker exec -it turtlebot3_container bash
cd /ws && colcon build --symlink-install && source install/setup.bash
ros2 launch nitrobot_bringup bringup.launch.py
```

Simulation and Nav2 use the **`/sim`** namespace. Gazebo GUI and RViz are on by default.

Simulation only (Gazebo + Nav2 + RViz):

```bash
ros2 launch nitrobot_sim sim_nav.launch.py
```

Startup order (fixed delays): Gazebo → unpause + robot (20s) → Nav2 (45s) → RViz (48s) → decision/mediator (58s with full bringup). Wait ~60s before sending zone goals. If Gazebo GUI looks paused, click Play once after the robot appears. Brief `TF_OLD_DATA` lines right after RViz opens usually mean RViz joined before sim time was synced; they should stop within a few seconds.

```bash
ros2 run nitrobot_decision set_zone.sh zone_5
```

Headless: `use_gui:=false use_rviz:=false`

## Physical robot

```bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_bringup robot.launch.py namespace:=real
```
