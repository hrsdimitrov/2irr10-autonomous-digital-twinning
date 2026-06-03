#!/usr/bin/env python3
"""Spawn TurtleBot3 under /sim and unpause the world. Run after sim.launch.py."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

TF_REMAPS = [("/tf", "tf"), ("/tf_static", "tf_static")]


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    x_pose = LaunchConfiguration("x_pose")
    y_pose = LaunchConfiguration("y_pose")

    model = os.environ.get("TURTLEBOT3_MODEL", "burger")
    model_folder = f"turtlebot3_{model}"

    turtlebot3_gazebo_share = get_package_share_directory("turtlebot3_gazebo")
    urdf_path = os.path.join(
        turtlebot3_gazebo_share, "models", model_folder, "model.sdf"
    )
    bridge_params = os.path.join(
        turtlebot3_gazebo_share, "params", f"{model_folder}_bridge.yaml"
    )

    with open(
        os.path.join(
            turtlebot3_gazebo_share, "urdf", f"turtlebot3_{model}.urdf"
        ),
        encoding="utf-8",
    ) as urdf_file:
        robot_desc = urdf_file.read()

    unpause = ExecuteProcess(
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
            "10000",
            "--req",
            "pause: false",
        ],
        output="screen",
    )

    create_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name",
            model,
            "-file",
            urdf_path,
            "-x",
            x_pose,
            "-y",
            y_pose,
            "-z",
            "0.01",
        ],
        output="screen",
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        namespace="sim",
        arguments=[
            "--ros-args",
            "-p",
            f"config_file:={bridge_params}",
        ],
        remappings=TF_REMAPS,
        output="screen",
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace="sim",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "robot_description": robot_desc,
            }
        ],
        remappings=TF_REMAPS,
    )

    # Lock map frame to Gazebo spawn: odom origin at spawn => map->odom = (x, y).
    map_odom_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        namespace="sim",
        arguments=[
            "--x",
            x_pose,
            "--y",
            y_pose,
            "--z",
            "0",
            "--yaw",
            "0",
            "--pitch",
            "0",
            "--roll",
            "0",
            "--frame-id",
            "map",
            "--child-frame-id",
            "odom",
        ],
        remappings=TF_REMAPS,
    )

    return LaunchDescription(
        [
            SetEnvironmentVariable(name="TURTLEBOT3_MODEL", value="burger"),
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("x_pose", default_value="0.0"),
            DeclareLaunchArgument("y_pose", default_value="0.0"),
            unpause,
            create_robot,
            bridge,
            robot_state_publisher,
            map_odom_tf,
        ]
    )
