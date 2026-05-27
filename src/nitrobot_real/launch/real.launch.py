#!/usr/bin/env python3
"""Single un-namespaced Nav2 stack for the physical TurtleBot (laptop)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")

    nitrobot_real_share = get_package_share_directory("nitrobot_real")
    turtlebot3_navigation2_share = get_package_share_directory("turtlebot3_navigation2")

    map_file = os.path.join(nitrobot_real_share, "maps", "map.yaml")
    nav2_launch = os.path.join(
        turtlebot3_navigation2_share, "launch", "navigation2.launch.py"
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation clock (false for physical robot)",
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch),
            launch_arguments={
                "use_sim_time": use_sim_time,
                "map": map_file,
            }.items(),
        ),
    ])
