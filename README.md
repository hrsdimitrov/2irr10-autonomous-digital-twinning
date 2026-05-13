This repository contains all relevant code and documentation for the 2IRR10 Autonomous Digital Twinning project. 

# Docker Container

1. Create Docker image: `docker compose build`
2. Run `xhost +local:docker` before starting the container
3. Start container: `docker compose up -d`
4. Open new bash: `docker exec -it turtlebot3_container bash`
5. Stop the container: To stop the container run `docker compose down`.


# Inside the container

# Launch Gazebo world

`ros2 launch nitrobot_world farm_world.launch.py`
`ros2 launch nitrobot_world nitrobot_bringup.launch.py`

## Building the project

1. `cd /ws`
2. `colcon build --symlink-install`
3. `source install/setup.bash`

## Navigation

`ros2 run nitrobot_twin go_to_zone zone_40`

## Other

`export ROS_DOMAIN_ID=30`

```
export TURTLEBOT3_MODEL=burger

ros2 launch turtlebot3_bringup robot.launch.py \
  --ros-args \
  -r /cmd_vel:=/real/cmd_vel \
  -r /odom:=/real/odom \
  -r /scan:=/real/scan \
  -r /tf:=/real/tf \
  -r /tf_static:=/real/tf_static
```

`ros2 launch nitrobot_world real_robot_bridge.launch.py`