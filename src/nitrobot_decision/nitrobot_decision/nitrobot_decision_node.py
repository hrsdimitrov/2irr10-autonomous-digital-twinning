#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String


class NitrobotDecisionNode(Node):
    def __init__(self):
        super().__init__("nitrobot_decision_node")

        self.declare_parameter("target_zone", "zone_2")
        self.declare_parameter("battery_log_interval_sec", 30.0)

        self._last_published = None
        self._latest_battery_state = None
        self.publisher = self.create_publisher(String, "/nitrobot/target_zone", 10)
        self.add_on_set_parameters_callback(self._on_parameters_changed)

        self._publish_zone(self._current_target_zone())

        self.create_subscription(
            String,
            "/nitrobot/battery_state",
            self._battery_state_callback,
            10,
        )

        battery_log_interval = self.get_parameter("battery_log_interval_sec").value
        self.create_timer(battery_log_interval, self._log_battery_state)

        self.get_logger().info(
            "Publishing /nitrobot/target_zone "
            f"(current: {self.get_parameter('target_zone').value}); "
            f"battery logged every {battery_log_interval}s"
        )

    def _current_target_zone(self) -> str:
        return self.get_parameter("target_zone").get_parameter_value().string_value.strip()

    def _on_parameters_changed(self, params):
        for param in params:
            if param.name == "target_zone" and param.type_ == Parameter.Type.STRING:
                self._publish_zone(param.value.strip())
        return rclpy.node.SetParametersResult(successful=True)

    def _publish_zone(self, zone: str):
        zone = zone.strip()
        if not zone or zone == self._last_published:
            return

        msg = String()
        msg.data = zone
        self.publisher.publish(msg)
        self._last_published = zone
        self.get_logger().info(f"Published target zone: {zone}")

    def _battery_state_callback(self, msg: String):
        self._latest_battery_state = msg.data

    def _log_battery_state(self):
        if self._latest_battery_state is None:
            self.get_logger().info("Battery state: no data received yet")
            return
        self.get_logger().info(f"Battery state: {self._latest_battery_state}")


def main(args=None):
    rclpy.init(args=args)
    node = NitrobotDecisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
