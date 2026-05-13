#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    cmd_vel_bridge = Node(
        package="nitrobot_twin",
        executable="cmd_vel_bridge",
        name="cmd_vel_bridge",
        output="screen",
    )

    return LaunchDescription([
        cmd_vel_bridge,
    ])