#!/usr/bin/env python3

import random
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class StatusNode(Node):
    def __init__(self):
        super().__init__('status_node')

        # Simulated battery starts between 80-100%
        self.battery = float(random.randint(80, 100))
        self.mission_status = 'IN_PROGRESS'
        self.zones_done = 0

        self.status_pub = self.create_publisher(
            String, '/nitrobot/robot_status', 10)

        self.create_subscription(
            String, '/nitrobot/fertilized', self._on_fertilized, 10)
        self.create_subscription(
            String, '/nitrobot/mission_status', self._on_mission, 10)

        # Drain battery slowly, publish status every 5 seconds
        self.create_timer(5.0, self._publish_status)

        self.get_logger().info(
            f'StatusNode started, battery: {self.battery:.0f}%')

    def _on_fertilized(self, msg: String):
        zone_msg = msg.data.strip()
        
        # FIXED: 忽略暂时跳过的信号，只计算正常完成的 zone
        if ':SKIPPED' in zone_msg:
            return
        
        self.zones_done += 1
        # Each fertilization costs ~1-3% battery
        self.battery = max(0.0, self.battery - random.uniform(1.0, 3.0))

    def _on_mission(self, msg: String):
        self.mission_status = msg.data.strip()

    def _publish_status(self):
        # Slowly drain battery over time
        self.battery = max(0.0, self.battery - random.uniform(0.1, 0.3))
        if self.battery <= 0.0 and self.mission_status != 'COMPLETE':
            self.mission_status = 'ABORTED'
            self.status_pub.publish(String(data='ABORTED'))
            self.get_logger().warn('Battery depleted! Mission ABORTED.')

        if self.battery < 15.0:
            battery_status = 'CRITICAL'
        elif self.battery < 30.0:
            battery_status = 'LOW'
        else:
            battery_status = 'NORMAL'

        report = (
            f'mission:{self.mission_status} | '
            f'zones_done:{self.zones_done} | '
            f'battery:{self.battery:.1f}% ({battery_status})'
        )

        self.status_pub.publish(String(data=report))
        self.get_logger().info(report)


def main(args=None):
    rclpy.init(args=args)
    node = StatusNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()