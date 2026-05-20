#!/usr/bin/env bash
exec ros2 run turtlebot3_teleop teleop_keyboard --ros-args -r /cmd_vel:=/sim/cmd_vel
