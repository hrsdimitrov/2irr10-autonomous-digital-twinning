#!/usr/bin/env python3
"""Gazebo + Nav2 + RViz (/sim), then decision + mediator."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

# Nav2 at 45s, RViz at 50s inside sim_nav
TWIN_NODES_SEC = 58.0


def generate_launch_description():
    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")
    nitrobot_decision_share = get_package_share_directory("nitrobot_decision")
    nitrobot_mediator_share = get_package_share_directory("nitrobot_mediator")

    use_sim_time = LaunchConfiguration("use_sim_time")
    x_pose = LaunchConfiguration("x_pose")
    y_pose = LaunchConfiguration("y_pose")
    target_zone = LaunchConfiguration("target_zone")
    use_gui = LaunchConfiguration("use_gui")
    use_rviz = LaunchConfiguration("use_rviz")

    decision = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nitrobot_decision_share, "launch", "decision.launch.py")
        ),
        launch_arguments={"target_zone": target_zone}.items(),
    )

    mediator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nitrobot_mediator_share, "launch", "mediator.launch.py")
        ),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("x_pose", default_value="0.0"),
            DeclareLaunchArgument("y_pose", default_value="0.0"),
            DeclareLaunchArgument("target_zone", default_value="zone_2"),
            DeclareLaunchArgument("use_gui", default_value="true"),
            DeclareLaunchArgument("use_rviz", default_value="true"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nitrobot_sim_share, "launch", "sim_nav.launch.py")
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "x_pose": x_pose,
                    "y_pose": y_pose,
                    "use_gui": use_gui,
                    "use_rviz": use_rviz,
                }.items(),
            ),
            TimerAction(period=TWIN_NODES_SEC, actions=[decision, mediator]),
        ]
    )
