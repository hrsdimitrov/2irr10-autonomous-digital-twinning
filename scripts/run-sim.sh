#!/usr/bin/env bash
set -e

cd /ws

source /opt/ros/jazzy/setup.bash
source /opt/turtlebot3_ws/install/setup.bash

colcon build
source /ws/install/setup.bash

export TURTLEBOT3_MODEL=burger

ros2 launch my_tb3_world new_world.launch.py