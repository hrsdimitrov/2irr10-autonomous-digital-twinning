#!/usr/bin/env python3
"""Gazebo farm world + TurtleBot3 under /sim."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace

# Let the farm world finish loading before spawn + unpause
SPAWN_ROBOT_SEC = 20.0


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    x_pose = LaunchConfiguration("x_pose")
    y_pose = LaunchConfiguration("y_pose")
    use_gui = LaunchConfiguration("use_gui")

    turtlebot3_gazebo_share = get_package_share_directory("turtlebot3_gazebo")
    ros_gz_sim_share = get_package_share_directory("ros_gz_sim")
    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")

    launch_file_dir = os.path.join(turtlebot3_gazebo_share, "launch")
    world = os.path.join(nitrobot_sim_share, "worlds", "farm_world.world")

    declare_use_sim_time = DeclareLaunchArgument("use_sim_time", default_value="true")
    declare_x_pose = DeclareLaunchArgument("x_pose", default_value="0.0")
    declare_y_pose = DeclareLaunchArgument("y_pose", default_value="0.0")
    declare_use_gui = DeclareLaunchArgument("use_gui", default_value="true")

    gz_server_args = f"-s -v2 {world}"

    sim_robot = GroupAction(
        actions=[
            PushRosNamespace("sim"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(launch_file_dir, "spawn_turtlebot3.launch.py")
                ),
                launch_arguments={"x_pose": x_pose, "y_pose": y_pose}.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(launch_file_dir, "robot_state_publisher.launch.py")
                ),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
            ),
        ]
    )

    unpause = ExecuteProcess(
        cmd=[
            "gz", "service", "-s", "/world/default/control",
            "--reqtype", "gz.msgs.WorldControl",
            "--reptype", "gz.msgs.Boolean",
            "--timeout", "10000",
            "--req", "pause: false",
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            declare_use_sim_time,
            declare_x_pose,
            declare_y_pose,
            declare_use_gui,
            AppendEnvironmentVariable(
                "GZ_SIM_RESOURCE_PATH",
                os.path.join(turtlebot3_gazebo_share, "models"),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(ros_gz_sim_share, "launch", "gz_sim.launch.py")
                ),
                launch_arguments={
                    "gz_args": gz_server_args,
                    "on_exit_shutdown": "true",
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(ros_gz_sim_share, "launch", "gz_sim.launch.py")
                ),
                condition=IfCondition(use_gui),
                launch_arguments={
                    "gz_args": "-g -v2",
                    "on_exit_shutdown": "false",
                }.items(),
            ),
            TimerAction(period=SPAWN_ROBOT_SEC, actions=[unpause, sim_robot]),
        ]
    )
