#!/usr/bin/env python3
"""Digital twin (setup C): real Nav2 + decision + twin mediator on the workstation.

Run Gazebo sim (sim → spawn → nav2) separately, Pi bringup separately, then this launch.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_rviz = LaunchConfiguration("use_rviz")

    real_launch = os.path.join(
        get_package_share_directory("nitrobot_real"), "launch", "real.launch.py"
    )
    decision_launch = os.path.join(
        get_package_share_directory("nitrobot_decision"), "launch", "decision.launch.py"
    )
    mediator_twin_launch = os.path.join(
        get_package_share_directory("nitrobot_mediator"),
        "launch",
        "mediator_twin.launch.py",
    )

    real_nav = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(real_launch),
        launch_arguments={"use_rviz": use_rviz}.items(),
    )
    decision = IncludeLaunchDescription(PythonLaunchDescriptionSource(decision_launch))
    mediator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(mediator_twin_launch)
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_rviz",
                default_value="true",
                description="Open RViz for /real (2D Pose Estimate, /real/map, etc.)",
            ),
            real_nav,
            decision,
            mediator,
        ]
    )
