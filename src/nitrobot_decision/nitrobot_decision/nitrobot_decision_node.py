#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String


class NitrobotDecisionNode(Node):
    def __init__(self):
        super().__init__("nitrobot_decision_node")

        self.declare_parameter("target_zone", "zone_1")

        self._last_published = None
        self.publisher = self.create_publisher(String, "/nitrobot/target_zone", 10)
        self.add_on_set_parameters_callback(self._on_parameters_changed)

        self._publish_zone(self.get_parameter("target_zone").value)
        self.create_timer(2.0, self._republish_zone)

        self.get_logger().info(
            "Publishing /nitrobot/target_zone "
            f"(current: {self.get_parameter('target_zone').value})"
        )

    def _on_parameters_changed(self, params):
        for param in params:
            if param.name == "target_zone" and param.type_ == Parameter.Type.STRING:
                self._publish_zone(param.value)
        return rclpy.node.SetParametersResult(successful=True)

    def _republish_zone(self):
        self._publish_zone(self.get_parameter("target_zone").value)

    def _publish_zone(self, zone: str):
        msg = String()
        msg.data = zone
        self.publisher.publish(msg)
        if zone != self._last_published:
            self._last_published = zone
            self.get_logger().info(f"Published target zone: {zone}")


def main(args=None):
    rclpy.init(args=args)
    node = NitrobotDecisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
