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

## Physical robot lab

**On the TurtleBot (Raspberry Pi):**

```bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_bringup robot.launch.py
```

**On the laptop/container:**

```bash
ros2 launch nitrobot_bringup physical_system.launch.py
```

**Send a zone:**

```bash
ros2 run nitrobot_decision set_zone.sh zone_14
```

**Optional teleop:** `ros2 run nitrobot_real real_teleop.sh`

**Test battery (no robot):**

```bash
ros2 topic pub --once /battery_state sensor_msgs/msg/BatteryState "{voltage: 11.4, percentage: 0.82}"
```
