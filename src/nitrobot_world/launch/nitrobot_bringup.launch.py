#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    nitrobot_world_share = get_package_share_directory("nitrobot_world")
    turtlebot3_gazebo_share = get_package_share_directory("turtlebot3_gazebo")
    turtlebot3_navigation2_share = get_package_share_directory("turtlebot3_navigation2")

    farm_world_launch = os.path.join(
        nitrobot_world_share,
        "launch",
        "farm_world.launch.py"
    )

    nav2_launch = os.path.join(
        turtlebot3_navigation2_share,
        "launch",
        "navigation2.launch.py"
    )

    map_file = os.path.join(
        nitrobot_world_share,
        "maps",
        "map.yaml"
    )

    set_turtlebot_model_path = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        os.path.join(turtlebot3_gazebo_share, "models")
    )

    start_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(farm_world_launch),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "x_pose": "0.0",
            "y_pose": "0.0",
        }.items()
    )

    start_nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "map": map_file,
        }.items()
    )

    return LaunchDescription([
        set_turtlebot_model_path,
        start_gazebo,
        start_nav2,
    ])