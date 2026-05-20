#!/usr/bin/env python3
"""Launch Gazebo farm world and TurtleBot3 with all ROS topics under /sim."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
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
    nitrobot_world_share = get_package_share_directory("nitrobot_world")

    launch_file_dir = os.path.join(turtlebot3_gazebo_share, "launch")
    world = os.path.join(nitrobot_world_share, "worlds", "farm_world.world")

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

    set_turtlebot_model_path = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        os.path.join(turtlebot3_gazebo_share, "models"),
    )

    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": f"-r -s -v2 {world}",
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
            gzclient_cmd,
            sim_robot_group,
        ]
    )
