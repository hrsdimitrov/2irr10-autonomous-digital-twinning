#!/usr/bin/env python3
"""Launch Gazebo farm world and TurtleBot3 with all ROS topics under /sim."""

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
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    x_pose = LaunchConfiguration("x_pose")
    y_pose = LaunchConfiguration("y_pose")

    turtlebot3_gazebo_share = get_package_share_directory("turtlebot3_gazebo")
    ros_gz_sim_share = get_package_share_directory("ros_gz_sim")
    nitrobot_sim_share = get_package_share_directory("nitrobot_sim")

    launch_file_dir = os.path.join(turtlebot3_gazebo_share, "launch")
    world = os.path.join(nitrobot_sim_share, "worlds", "farm_world.world")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation clock",
    )
    declare_x_pose = DeclareLaunchArgument(
        "x_pose",
        default_value="0.0",
        description="Initial robot x position",
    )
    declare_y_pose = DeclareLaunchArgument(
        "y_pose",
        default_value="0.0",
        description="Initial robot y position",
    )

    # Do not pass -r: it restores the previous Gazebo session from disk.
    gz_server_args = f"-s -v2 {world}"

    set_turtlebot_model_path = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        os.path.join(turtlebot3_gazebo_share, "models"),
    )

    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": gz_server_args,
            "on_exit_shutdown": "true",
        }.items(),
    )

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": "-g -v2",
            "on_exit_shutdown": "true",
        }.items(),
    )

    gzclient_cmd_delayed = TimerAction(period=2.0, actions=[gzclient_cmd])

    unpause_sim = TimerAction(
        period=5.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    "gz",
                    "service",
                    "-s",
                    "/world/default/control",
                    "--reqtype",
                    "gz.msgs.WorldControl",
                    "--reptype",
                    "gz.msgs.Boolean",
                    "--timeout",
                    "5000",
                    "--req",
                    "pause: false",
                ],
                output="screen",
            )
        ],
    )

    # TurtleBot3 spawn + ros_gz bridges + robot_state_publisher under /sim
    sim_robot_group = GroupAction(
        actions=[
            PushRosNamespace("sim"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(launch_file_dir, "robot_state_publisher.launch.py")
                ),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(launch_file_dir, "spawn_turtlebot3.launch.py")
                ),
                launch_arguments={
                    "x_pose": x_pose,
                    "y_pose": y_pose,
                }.items(),
            ),
        ]
    )

    return LaunchDescription(
        [
            declare_use_sim_time,
            declare_x_pose,
            declare_y_pose,
            set_turtlebot_model_path,
            gzserver_cmd,
            gzclient_cmd_delayed,
            unpause_sim,
            sim_robot_group,
        ]
    )
