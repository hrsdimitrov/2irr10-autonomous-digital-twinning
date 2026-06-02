#!/usr/bin/env python3

import math
import os

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


OBSTACLE_DIST = 0.35
FRONT_ANGLE = 0.52
ARRIVE_TOLERANCE = 0.15
WALL_FOLLOW_DIST = 0.45
WALL_FOLLOW_SIDE_ANGLE = 0.52

MOVING = 'MOVING'
WALL_FOLLOW = 'WALL_FOLLOW'


class NitrobotMediatorNode(Node):
    def __init__(self):
        super().__init__('nitrobot_mediator_node')

        self.last_zone = None
        self.current_zone = None
        self.zones = self._load_zones()

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.target = None
        self.obstacle_ahead = False
        self.right_dist = float('inf')
        self.state = MOVING
        self.target_start_time = None
        self.target_timeout = 20.0
        self.skipped_zones = []
        self.mission_active = True

        self.cmd_vel_pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.fertilized_pub = self.create_publisher(
            String, '/nitrobot/fertilized', 10)

        self.create_subscription(
            String, '/nitrobot/target_zone',
            self._target_zone_callback, 10)
        self.create_subscription(
            Odometry, '/odom',
            self._odom_callback, 10)
        self.create_subscription(
            LaserScan, '/scan',
            self._scan_callback, 10)
        self.create_subscription(
            String, '/nitrobot/robot_status',
            self._robot_status_callback, 10)

        self.create_timer(0.1, self._control_loop)
        self.get_logger().info(
            f'Loaded {len(self.zones)} zones | Bug0 wall-following navigation')

    def _load_zones(self):
        zones_path = os.path.join(
            get_package_share_directory('nitrobot_mediator'),
            'config', 'zones.yaml',
        )
        with open(zones_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data.get('zones', {})

    def _robot_status_callback(self, msg: String):
        data = msg.data.strip()
        if 'ABORTED' in data or 'COMPLETE' in data:
            if self.mission_active:
                self.mission_active = False
                self.target = None
                self.get_logger().warn(
                    f'Mission {data} — stopping robot.')

    def _odom_callback(self, msg: Odometry):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        self.current_yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        )

    def _scan_callback(self, msg: LaserScan):
        n = len(msg.ranges)
        angle_inc = msg.angle_increment

        front_steps = int(FRONT_ANGLE / angle_inc)
        side_steps = int(WALL_FOLLOW_SIDE_ANGLE / angle_inc)

        # Front sector
        front_indices = list(range(0, front_steps)) + list(range(n - front_steps, n))
        self.obstacle_ahead = any(
            0.05 < msg.ranges[i] < OBSTACLE_DIST
            for i in front_indices
            if not math.isnan(msg.ranges[i]) and not math.isinf(msg.ranges[i])
        )

        # Right sector (~270 degrees)
        right_center = int(n * 3 / 4)
        right_indices = range(
            max(0, right_center - side_steps),
            min(n, right_center + side_steps)
        )
        right_ranges = [
            msg.ranges[i] for i in right_indices
            if not math.isnan(msg.ranges[i]) and not math.isinf(msg.ranges[i])
        ]
        self.right_dist = min(right_ranges) if right_ranges else float('inf')

    def _target_zone_callback(self, msg: String):
        zone = msg.data.strip()
        if zone == self.last_zone:
            return
        if zone not in self.zones:
            self.get_logger().error(f'Unknown zone: {zone}')
            return
        zone_data = self.zones[zone]
        x = float(zone_data['x'])
        y = float(zone_data['y'])
        self.get_logger().info(f'New target: {zone} -> x={x:.2f}, y={y:.2f}')
        self.last_zone = zone
        self.current_zone = zone
        self.target = (x, y)
        self.target_start_time = self.get_clock().now().nanoseconds / 1e9
        self.state = MOVING

    def _control_loop(self):
        twist = TwistStamped()
        twist.header.stamp = self.get_clock().now().to_msg()

        if not self.mission_active:
            self.cmd_vel_pub.publish(twist)  # zero velocity — stop the robot
            return

        if self.target is None:
            self.cmd_vel_pub.publish(twist)
            return
        
        # Skip zone if stuck too long
        now = self.get_clock().now().nanoseconds / 1e9
        if self.target_start_time and (now - self.target_start_time) > self.target_timeout:
            self.get_logger().warn(f'Timeout reaching {self.current_zone}, will retry later.')
            self.fertilized_pub.publish(String(data=f'{self.current_zone}:SKIPPED'))
            self.skipped_zones.append(self.current_zone)
            self.target = None
            self.last_zone = None
            self.state = MOVING
            return

        tx, ty = self.target
        dx = tx - self.current_x
        dy = ty - self.current_y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist <= ARRIVE_TOLERANCE:
            self.get_logger().info(
                f'Arrived at {self.current_zone}, fertilizing...')
            self.fertilized_pub.publish(String(data=self.current_zone))
            self.target = None
            self.last_zone = None
            self.state = MOVING
            return

        angle_to_target = math.atan2(dy, dx)
        angle_error = angle_to_target - self.current_yaw
        while angle_error > math.pi:
            angle_error -= 2.0 * math.pi
        while angle_error < -math.pi:
            angle_error += 2.0 * math.pi

        if self.state == MOVING:
            if self.obstacle_ahead:
                self.state = WALL_FOLLOW
                self.get_logger().info('Obstacle hit - switching to wall-following')
            else:
                if abs(angle_error) > 0.3:
                    twist.twist.angular.z = 1.0 * angle_error
                else:
                    twist.twist.linear.x = min(0.3, dist)  # CHANGED: 从 0.2 改成 0.3
                    twist.twist.angular.z = 0.5 * angle_error

        elif self.state == WALL_FOLLOW:
            # Resume direct navigation if goal direction is clear
            if not self.obstacle_ahead and abs(angle_error) < FRONT_ANGLE:
                self.state = MOVING
                self.get_logger().info('Path clear - resuming direct navigation')
            else:
                if self.obstacle_ahead:
                    # Wall in front: turn left
                    twist.twist.linear.x = 0.0
                    twist.twist.angular.z = 0.8
                elif self.right_dist > WALL_FOLLOW_DIST + 0.1:
                    # Too far from right wall: turn right
                    twist.twist.linear.x = 0.2  # CHANGED: 从 0.15 改成 0.2
                    twist.twist.angular.z = -0.3
                elif self.right_dist < WALL_FOLLOW_DIST - 0.1:
                    # Too close to right wall: turn left
                    twist.twist.linear.x = 0.2  # CHANGED: 从 0.15 改成 0.2
                    twist.twist.angular.z = 0.3
                else:
                    # Maintain distance: go straight
                    twist.twist.linear.x = 0.2
                    twist.twist.angular.z = 0.0

        self.cmd_vel_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = NitrobotMediatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()