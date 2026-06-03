#!/usr/bin/env python3
"""Gazebo farm world (server + optional GUI). Run spawn.launch.py when the world is ready."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_gui = LaunchConfiguration("use_gui")

    turtlebot3_gazebo_share = get_package_share_directory("turtlebot3_gazebo")
    ros_gz_sim_share = get_package_share_directory("ros_gz_sim")
    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")

    world = os.path.join(nitrobot_sim_share, "worlds", "farm_world.world")
    gz_server_args = f"-s -v2 {world}"

    return LaunchDescription(
        [
            SetEnvironmentVariable(name="TURTLEBOT3_MODEL", value="burger"),
            DeclareLaunchArgument("use_gui", default_value="true"),
            AppendEnvironmentVariable(
                "GZ_SIM_RESOURCE_PATH",
                os.path.join(turtlebot3_gazebo_share, "models"),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(ros_gz_sim_share, "launch", "gz_sim.launch.py")
                ),
                launch_arguments={
                    "gz_args": gz_server_args,
                    "on_exit_shutdown": "true",
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(ros_gz_sim_share, "launch", "gz_sim.launch.py")
                ),
                condition=IfCondition(use_gui),
                launch_arguments={
                    "gz_args": "-g -v2",
                    "on_exit_shutdown": "false",
                }.items(),
            ),
        ]
    )
