#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="nitrobot_mediator",
            executable="nitrobot_mediator_node",
            name="nitrobot_mediator_node",
            output="screen",
        ),
    ])
