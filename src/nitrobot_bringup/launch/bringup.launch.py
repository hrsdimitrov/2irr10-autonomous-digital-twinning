#!/usr/bin/env python3
"""Start Gazebo simulation plus digital-twin decision and mediator nodes."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    x_pose = LaunchConfiguration("x_pose")
    y_pose = LaunchConfiguration("y_pose")
    target_zone = LaunchConfiguration("target_zone")
    with_nav2 = LaunchConfiguration("with_nav2")

    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")
    nitrobot_decision_share = get_package_share_directory("nitrobot_decision")
    nitrobot_mediator_share = get_package_share_directory("nitrobot_mediator")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation clock",
    )
    declare_x_pose = DeclareLaunchArgument(
        "x_pose",
        default_value="0.0",
        description="Initial robot x position in simulation",
    )
    declare_y_pose = DeclareLaunchArgument(
        "y_pose",
        default_value="0.0",
        description="Initial robot y position in simulation",
    )
    declare_target_zone = DeclareLaunchArgument(
        "target_zone",
        default_value="zone_2",
        description="Initial target zone for the decision node",
    )
    declare_with_nav2 = DeclareLaunchArgument(
        "with_nav2",
        default_value="false",
        description="Also start Nav2 on top of Gazebo simulation",
    )

    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nitrobot_sim_share, "launch", "sim.launch.py")
        ),
        condition=UnlessCondition(with_nav2),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "x_pose": x_pose,
            "y_pose": y_pose,
        }.items(),
    )

    sim_nav_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nitrobot_sim_share, "launch", "sim_nav.launch.py")
        ),
        condition=IfCondition(with_nav2),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    decision_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nitrobot_decision_share, "launch", "decision.launch.py")
        ),
        launch_arguments={"target_zone": target_zone}.items(),
    )

    mediator_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nitrobot_mediator_share, "launch", "mediator.launch.py")
        ),
    )

    return LaunchDescription(
        [
            declare_use_sim_time,
            declare_x_pose,
            declare_y_pose,
            declare_target_zone,
            declare_with_nav2,
            sim_launch,
            sim_nav_launch,
            decision_launch,
            mediator_launch,
        ]
    )
