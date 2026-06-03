#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")
    default_zones_config = os.path.join(nitrobot_sim_share, "config", "zone_poses.yaml")

    zones_config = LaunchConfiguration("zones_config")
    use_sim_navigation = LaunchConfiguration("use_sim_navigation")
    use_real_navigation = LaunchConfiguration("use_real_navigation")

    return LaunchDescription([
        DeclareLaunchArgument(
            "zones_config",
            default_value=default_zones_config,
            description="YAML file mapping zone names to map poses",
        ),
        DeclareLaunchArgument(
            "use_sim_navigation",
            default_value="true",
            description="Send Nav2 goals to the simulated robot",
        ),
        DeclareLaunchArgument(
            "use_real_navigation",
            default_value="false",
            description="Send Nav2 goals to the real robot (/real namespace)",
        ),
        Node(
            package="nitrobot_mediator",
            executable="nitrobot_mediator_node",
            name="nitrobot_mediator_node",
            output="screen",
            parameters=[{
                "zones_config": zones_config,
                "use_sim_navigation": ParameterValue(
                    use_sim_navigation, value_type=bool
                ),
                "use_real_navigation": ParameterValue(
                    use_real_navigation, value_type=bool
                ),
                "sim_navigate_action": "/sim/navigate_to_pose",
                "real_navigate_action": "/real/navigate_to_pose",
                "goal_frame_id": "map",
            }],
        ),
    ])
