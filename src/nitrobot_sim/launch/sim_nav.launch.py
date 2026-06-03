#!/usr/bin/env python3
"""Gazebo /sim, then Nav2 /sim, then RViz."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# Robot spawns at 20s in sim.launch; allow create + bridges to finish
NAV2_SEC = 45.0
RVIZ_SEC = 50.0


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    x_pose = LaunchConfiguration("x_pose")
    y_pose = LaunchConfiguration("y_pose")
    use_gui = LaunchConfiguration("use_gui")
    use_rviz = LaunchConfiguration("use_rviz")

    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")
    nav2_bringup_share = get_package_share_directory("nav2_bringup")

    map_file = os.path.join(nitrobot_sim_share, "maps", "map.yaml")
    nav2_params = os.path.join(nitrobot_sim_share, "config", "nav2_burger_sim.yaml")

    declare_use_sim_time = DeclareLaunchArgument("use_sim_time", default_value="true")
    declare_x_pose = DeclareLaunchArgument("x_pose", default_value="0.0")
    declare_y_pose = DeclareLaunchArgument("y_pose", default_value="0.0")
    declare_use_gui = DeclareLaunchArgument("use_gui", default_value="true")
    declare_use_rviz = DeclareLaunchArgument("use_rviz", default_value="true")

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
        namespace="sim",
        arguments=["-d", os.path.join(nitrobot_sim_share, "rviz", "sim_nav.rviz")],
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription(
        [
            declare_use_sim_time,
            declare_x_pose,
            declare_y_pose,
            declare_use_gui,
            declare_use_rviz,
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nitrobot_sim_share, "launch", "sim.launch.py")
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "x_pose": x_pose,
                    "y_pose": y_pose,
                    "use_gui": use_gui,
                }.items(),
            ),
            TimerAction(period=NAV2_SEC, actions=[nav2]),
            TimerAction(period=RVIZ_SEC, actions=[rviz]),
        ]
    )
