# 2IRR10 Autonomous Digital Twinning

## Quick start

```bash
docker compose build && xhost +local:docker && docker compose up -d
docker exec -it turtlebot3_container bash
cd /ws && colcon build --symlink-install && source install/setup.bash
ros2 launch nitrobot_bringup bringup.launch.py
```

Simulation and Nav2 use the **`/sim`** namespace. Gazebo GUI and RViz are on by default.

Startup order (fixed delays): Gazebo → unpause + robot (20s) → Nav2 (45s) → RViz (50s) → decision/mediator (58s). Wait ~60s before sending zone goals. If Gazebo GUI looks paused, click Play once after the robot appears.

```bash
ros2 run nitrobot_decision set_zone.sh zone_5
```

Headless: `use_gui:=false use_rviz:=false`

## Physical robot

```bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_bringup robot.launch.py namespace:=real
```
