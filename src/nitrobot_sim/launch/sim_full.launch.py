#!/usr/bin/env python3
"""Full simulation launch: Gazebo → spawn → Nav2 with proper delays."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


SPAWN_DELAY_SEC = 10.0   # wait for Gazebo to be ready
NAV2_DELAY_SEC  = 20.0   # wait for spawn to complete


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")

    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nitrobot_sim_share, "launch", "sim.launch.py")
        ),
    )

    spawn = TimerAction(
        period=SPAWN_DELAY_SEC,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nitrobot_sim_share, "launch", "spawn.launch.py")
                ),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
            )
        ],
    )

    nav2 = TimerAction(
        period=NAV2_DELAY_SEC,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nitrobot_sim_share, "launch", "nav2.launch.py")
                ),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
            )
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            sim,
            spawn,
            nav2,
        ]
    )