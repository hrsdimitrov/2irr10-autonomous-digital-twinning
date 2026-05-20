#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="nitrobot_decision",
            executable="nitrobot_decision_node",
            name="nitrobot_decision_node",
            output="screen",
        ),
    ])
