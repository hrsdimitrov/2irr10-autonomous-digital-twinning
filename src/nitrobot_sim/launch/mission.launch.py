#!/usr/bin/env python3
"""Mission launch: starts the mission executor node."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="nitrobot_sim",
                executable="mission_executor.py",
                name="mission_executor",
                output="screen",
                parameters=[{"use_sim_time": True}],
            )
        ]
    )