#!/usr/bin/env python3
"""Nav2 under /real for the physical TurtleBot (workstation). Pi runs bringup only."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

RVIZ_DELAY_SEC = 15.0


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_rviz = LaunchConfiguration("use_rviz")

    nitrobot_real_share = get_package_share_directory("nitrobot_real")
    nav2_bringup_share = get_package_share_directory("nav2_bringup")

    map_file = os.path.join(nitrobot_real_share, "maps", "map.yaml")
    nav2_params = os.path.join(nitrobot_real_share, "config", "nav2_burger_real.yaml")
    rviz_config = os.path.join(nitrobot_real_share, "rviz", "real_nav.rviz")

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_share, "launch", "bringup_launch.py")
        ),
        launch_arguments={
            "namespace": "real",
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
            "use_sim_time:=false",
            "-r",
            "/tf:=/real/tf",
            "-r",
            "/tf_static:=/real/tf_static"
        ],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("use_rviz", default_value="true"),
            nav2,
            TimerAction(period=RVIZ_DELAY_SEC, actions=[rviz]),
        ]
    )
