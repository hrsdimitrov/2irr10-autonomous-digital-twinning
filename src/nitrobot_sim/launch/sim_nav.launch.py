#!/usr/bin/env python3
"""Gazebo sim (/sim topics) plus Nav2 using the farm 2D map."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")
    turtlebot3_navigation2_share = get_package_share_directory("turtlebot3_navigation2")

    sim_launch = os.path.join(nitrobot_sim_share, "launch", "sim.launch.py")
    map_file = os.path.join(nitrobot_sim_share, "maps", "map.yaml")
    nav2_launch = os.path.join(
        turtlebot3_navigation2_share, "launch", "navigation2.launch.py"
    )

    start_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(sim_launch),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    start_nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "map": map_file,
        }.items(),
    )

    return LaunchDescription([start_sim, start_nav2])
