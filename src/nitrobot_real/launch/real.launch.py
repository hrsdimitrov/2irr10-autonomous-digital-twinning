#!/usr/bin/env python3
"""Nav2 stack for the physical TurtleBot (laptop). Expects hardware on /real/* from the Pi."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")

    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")
    turtlebot3_navigation2_share = get_package_share_directory("turtlebot3_navigation2")

    map_file = os.path.join(nitrobot_sim_share, "maps", "map.yaml")
    nav2_launch = os.path.join(
        turtlebot3_navigation2_share, "launch", "navigation2.launch.py"
    )

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation clock (false for physical robot)",
    )

    real_nav_group = GroupAction(
        actions=[
            PushRosNamespace("real"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav2_launch),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "map": map_file,
                }.items(),
            ),
        ]
    )

    return LaunchDescription([declare_use_sim_time, real_nav_group])
