#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    map_file = os.path.join(
        get_package_share_directory('nitrobot_world'),
        'maps', 'map.yaml'
    )

    return LaunchDescription([

        # ── 坐标系对齐 ──────────────────────────────────────────────
        # map frame = world frame
        # odom frame 起点 = robot spawn 位置 (-0.15, -0.15) in world
        # 所以 map→odom 的 offset = (-0.15, -0.15)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom',
            arguments=['0', '0', '0',   # x y z
                       '0', '0', '0',             # roll pitch yaw
                       'map', 'odom'],
            output='screen',
        ),

        # ── 地图 ────────────────────────────────────────────────────
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            parameters=[{
                'yaml_filename': map_file,
                'use_sim_time': True,
            }],
            output='screen',
        ),

        # map_server 需要 lifecycle 管理，用这个自动激活
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_map',
            parameters=[{
                'use_sim_time': True,
                'autostart': True,
                'node_names': ['map_server'],
            }],
            output='screen',
        ),

        # ── 业务节点 ─────────────────────────────────────────────────
        Node(
            package='nitrobot_sim',
            executable='zone_state_node',
            name='zone_state_node',
            output='screen',
        ),

        Node(
            package='nitrobot_sim',
            executable='autonomous_decision',
            name='autonomous_decision_node',
            output='screen',
        ),

        Node(
            package='nitrobot_sim',
            executable='status_node',
            name='status_node',
            output='screen',
        ),

        Node(
            package='nitrobot_mediator',
            executable='nitrobot_mediator_node',
            name='nitrobot_mediator_node',
            output='screen',
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', '/ws/src/nitrobot_sim/config/nitrobot.rviz'],
            output='screen',
        ),

    ])