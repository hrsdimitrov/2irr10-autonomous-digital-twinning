#!/usr/bin/env python3
"""Nav2 under /sim; optionally starts RViz (default on)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# map_server needs a few seconds; map->odom comes from spawn.launch.py
RVIZ_DELAY_SEC = 15.0


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_rviz = LaunchConfiguration("use_rviz")

    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")
    nav2_bringup_share = get_package_share_directory("nav2_bringup")

    map_file = os.path.join(nitrobot_sim_share, "maps", "map.yaml")
    nav2_params = os.path.join(nitrobot_sim_share, "config", "nav2_burger_sim.yaml")
    rviz_config = os.path.join(nitrobot_sim_share, "rviz", "sim_nav.rviz")

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_share, "launch", "bringup_launch.py")
        ),
        launch_arguments={
            "namespace": "sim",
            "use_namespace": "true",
            "slam": "False",
            "map": map_file,
            "use_sim_time": use_sim_time,
            "params_file": nav2_params,
            "autostart": "true",
            "use_composition": "False",
        }.items(),
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        condition=IfCondition(use_rviz),
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
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("use_rviz", default_value="true"),
            nav2,
            TimerAction(period=RVIZ_DELAY_SEC, actions=[rviz]),
        ]
    )
