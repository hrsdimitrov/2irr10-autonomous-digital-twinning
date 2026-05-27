#!/usr/bin/env python3
"""Nav2 under a namespace + RViz that matches (fixes controller_server errors)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace


def generate_launch_description():
    namespace = LaunchConfiguration("namespace")
    use_sim_time = LaunchConfiguration("use_sim_time")
    map_yaml = LaunchConfiguration("map")
    use_rviz = LaunchConfiguration("use_rviz")
    rviz_delay_sec = LaunchConfiguration("rviz_delay_sec")

    nav2_bringup_share = get_package_share_directory("nav2_bringup")
    turtlebot3_nav2_share = get_package_share_directory("turtlebot3_navigation2")

    bringup_launch = os.path.join(nav2_bringup_share, "launch", "bringup_launch.py")
    rviz_launch = os.path.join(nav2_bringup_share, "launch", "rviz_launch.py")
    rviz_config = os.path.join(nav2_bringup_share, "rviz", "nav2_default_view.rviz")

    model = os.environ.get("TURTLEBOT3_MODEL", "burger")
    params_file = os.path.join(turtlebot3_nav2_share, "param", f"{model}.yaml")
    if not os.path.isfile(params_file):
        params_file = os.path.join(
            turtlebot3_nav2_share, "param", "jazzy", f"{model}.yaml"
        )

    nav2_stack = GroupAction(
        actions=[
            PushRosNamespace(namespace),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(bringup_launch),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "map": map_yaml,
                    "params_file": params_file,
                    "autostart": "true",
                    "use_namespace": "false",
                }.items(),
            ),
        ]
    )

    rviz_stack = GroupAction(
        condition=IfCondition(use_rviz),
        actions=[
            TimerAction(
                period=rviz_delay_sec,
                actions=[
                    IncludeLaunchDescription(
                        PythonLaunchDescriptionSource(rviz_launch),
                        launch_arguments={
                            "namespace": namespace,
                            "use_namespace": "true",
                            "use_sim_time": use_sim_time,
                            "rviz_config": rviz_config,
                        }.items(),
                    )
                ],
            )
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "namespace",
            description="Nav2 namespace (sim or real)",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation clock",
        ),
        DeclareLaunchArgument(
            "map",
            description="Full path to map.yaml",
        ),
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            description="Start namespaced RViz for this stack",
        ),
        DeclareLaunchArgument(
            "rviz_delay_sec",
            default_value="10.0",
            description="Wait before RViz so Nav2 services are ready",
        ),
        nav2_stack,
        rviz_stack,
    ])
