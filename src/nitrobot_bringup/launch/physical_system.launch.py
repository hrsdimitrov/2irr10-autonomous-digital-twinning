#!/usr/bin/env python3
"""Physical TurtleBot lab: Nav2 + decision + mediator (no simulation)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    real_launch = os.path.join(
        get_package_share_directory("nitrobot_real"), "launch", "real.launch.py"
    )
    decision_launch = os.path.join(
        get_package_share_directory("nitrobot_decision"), "launch", "decision.launch.py"
    )
    mediator_launch = os.path.join(
        get_package_share_directory("nitrobot_mediator"), "launch", "mediator.launch.py"
    )

    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(real_launch)),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(decision_launch)),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(mediator_launch)),
    ])
