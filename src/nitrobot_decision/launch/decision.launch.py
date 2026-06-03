#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    target_zone = LaunchConfiguration("target_zone")

    declare_target_zone = DeclareLaunchArgument(
        "target_zone",
        default_value="zone_1",
        description="Target zone published on /nitrobot/target_zone",
    )

    decision_node = Node(
        package="nitrobot_decision",
        executable="nitrobot_decision_node",
        name="nitrobot_decision_node",
        output="screen",
        parameters=[
            {
                "target_zone": ParameterValue(target_zone, value_type=str),
            }
        ],
    )

    return LaunchDescription([declare_target_zone, decision_node])
