#!/usr/bin/env bash
set -e

cd /ws

source /opt/ros/jazzy/setup.bash
source /opt/turtlebot3_ws/install/setup.bash

if [ -f /ws/install/setup.bash ]; then
  source /ws/install/setup.bash
fi

export TURTLEBOT3_MODEL=burger

ros2 run turtlebot3_teleop teleop_keyboard