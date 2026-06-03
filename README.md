This repository contains all relevant code and documentation for the 2IRR10 Autonomous Digital Twinning project.

# Docker Container

1. Create Docker image: `docker compose build`
2. Run `xhost +local:docker` before starting the container
3. Start container: `docker compose up -d`
4. Open new bash: `docker exec -it turtlebot3_container bash`
5. Stop the container: To stop the container run `docker compose down`.

# Inside the container

## Building the project

1. `cd /ws`
2. `colcon build --symlink-install`
3. `source install/setup.bash`

## Bringup (simulation + digital twin)

Starts Gazebo, the decision node, and the mediator together (default target zone: `zone_2`):

```bash
ros2 launch nitrobot_bringup bringup.launch.py
```

Optional launch arguments: `target_zone:=zone_1`, `with_nav2:=true`, `x_pose:=0.0`, `y_pose:=0.0`.

## Simulation (individual)

`ros2 launch nitrobot_sim sim.launch.py`

Each launch loads the world fresh (Gazebo session restore is disabled). The robot is spawned at `x_pose` / `y_pose` (default `0`, `0`). Stop any previous launch with Ctrl+C before starting again.

If the sim still looks wrong after a crash, stop Gazebo manually, clear saved state, and relaunch:

```bash
pkill -9 -f "gz sim -s" || true
pkill -9 -f "gz sim -g" || true
rm -rf ~/.gz/sim/log/*
ros2 launch nitrobot_sim sim.launch.py
```

`ros2 run nitrobot_sim sim_teleop.sh`

## Digital twin (individual)

Do not run these if `nitrobot_bringup` is already running (you would get two decision nodes).

```bash
ros2 launch nitrobot_decision decision.launch.py
ros2 launch nitrobot_mediator mediator.launch.py
ros2 run nitrobot_decision set_zone.sh zone_2
```

`ros2 topic echo /nitrobot/battery_state`

## Physical robot

`ros2 run nitrobot_real real_teleop.sh`

# Inside the TurtleBot

`export TURTLEBOT3_MODEL=burger`


```
ros2 topic pub /battery_state sensor_msgs/msg/BatteryState \ "{voltage: 11.4, percentage: 0.82}" -r 1
```


CORRECT command for starting robot:
```
ros2 launch turtlebot3_bringup robot.launch.py namespace:=real
```