#!/usr/bin/env python3
"""Nav2 for physical TurtleBot on laptop. Expects /real/* hardware from the Pi."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_rviz = LaunchConfiguration("use_rviz")

    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")

    map_file = os.path.join(nitrobot_sim_share, "maps", "map.yaml")
    namespaced_nav2_launch = os.path.join(
        nitrobot_sim_share, "launch", "namespaced_nav2.launch.py"
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation clock (false for physical robot)",
        ),
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            description="Start namespaced RViz for real Nav2",
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(namespaced_nav2_launch),
            launch_arguments={
                "namespace": "real",
                "use_sim_time": use_sim_time,
                "map": map_file,
                "use_rviz": use_rviz,
            }.items(),
        ),
    ])
