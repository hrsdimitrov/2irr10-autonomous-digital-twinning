#!/usr/bin/env python3
"""RViz for /sim (loads sim_nav.rviz)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")
    rviz_config = os.path.join(nitrobot_sim_share, "rviz", "sim_nav.rviz")

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            Node(
                package="rviz2",
                executable="rviz2",
                arguments=[
                    "-d",
                    rviz_config,
                    "--ros-args",
                    "-p",
                    "use_sim_time:=true",
                    "-r",
                    "/tf:=/sim/tf",
                    "-r",
                    "/tf_static:=/sim/tf_static",
                ],
                parameters=[{"use_sim_time": use_sim_time}],
            ),
        ]
    )
