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

## Simulation

`ros2 launch nitrobot_sim sim.launch.py`

`ros2 run nitrobot_sim sim_teleop.sh`

## Digital twin (decision + mediator)

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

```bash
exec ros2 launch turtlebot3_bringup robot.launch.py --ros-args \
  -r /cmd_vel:=/real/cmd_vel \
  -r /odom:=/real/odom \
  -r /scan:=/real/scan
```

```
ros2 topic pub /battery_state sensor_msgs/msg/BatteryState \ "{voltage: 11.4, percentage: 0.82}" -r 1
```

```
ros2 launch turtlebot3_bringup robot.launch.py --ros-args \
  -r /cmd_vel:=/real/cmd_vel \
  -r /odom:=/real/odom \
  -r /scan:=/real/scan
```