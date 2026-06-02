#!/usr/bin/env python3


import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray

# 44 zones from zones.yaml
ZONES = {
    "zone_1":  (-0.7,   0.4),  "zone_2":  (-0.15,  0.4),  "zone_3":  (0.4,   0.4),
    "zone_4":  (-0.7,  -0.15), "zone_5":  (-0.15, -0.15), "zone_6":  (0.4,  -0.15),
    "zone_7":  (-0.7,  -0.7),  "zone_8":  (-0.15, -0.7),  "zone_9":  (0.4,  -0.7),
    "zone_10": (1.10,   0.65), "zone_11": (1.65,   0.65), "zone_12": (2.20,  0.65),
    "zone_13": (1.10,   0.05), "zone_14": (1.65,   0.05), "zone_15": (2.20,  0.05),
    "zone_16": (1.10,  -0.5),  "zone_17": (1.65,  -0.5),  "zone_18": (2.20, -0.5),
    "zone_19": (-0.6,  -1.4),  "zone_20": (0.0,   -1.4),  "zone_21": (0.6,  -1.4),
    "zone_22": (-0.6,  -2.35), "zone_23": (0.0,   -2.35), "zone_24": (0.6,  -2.35),
    "zone_25": (-0.6,  -2.90), "zone_26": (0.0,   -2.90), "zone_27": (0.6,  -2.90),
    "zone_28": (-0.6,  -3.45), "zone_29": (0.0,   -3.45), "zone_30": (0.6,  -3.45),
    "zone_31": (1.25,  -1.15), "zone_32": (1.80,  -1.15), "zone_33": (2.35, -1.15),
    "zone_34": (1.25,  -1.70), "zone_35": (1.80,  -1.70), "zone_36": (2.35, -1.70),
    "zone_37": (1.25,  -2.25), "zone_38": (1.80,  -2.25), "zone_39": (2.35, -2.25),
    "zone_40": (1.25,  -2.80), "zone_41": (1.80,  -2.80), "zone_42": (2.35, -2.80),
    "zone_43": (1.25,  -3.35), "zone_44": (1.80,  -3.35),
}

# Nitrogen thresholds
RED_THRESHOLD = 40      # nitrogen < 40 → red (urgent)
YELLOW_THRESHOLD = 70   # nitrogen < 70 → yellow (needs attention)
ZONE_SIZE = 0.4         # marker size in metres


class ZoneStateNode(Node):
    def __init__(self):
        super().__init__('zone_state_node')

        # Fixed nitrogen levels matching farm_world.world colours
        # green(>=70)=80, yellow(40-69)=55, red(<40)=25
        self.nitrogen = {
            "zone_1":  80, "zone_2":  25, "zone_3":  55,
            "zone_4":  55, "zone_5":  80, "zone_6":  25,
            "zone_7":  80, "zone_8":  55, "zone_9":  25,
            "zone_10": 25, "zone_11": 80, "zone_12": 55,
            "zone_13": 55, "zone_14": 25, "zone_15": 80,
            "zone_16": 80, "zone_17": 55, "zone_18": 25,
            "zone_19": 55, "zone_20": 80, "zone_21": 25,
            "zone_22": 25, "zone_23": 55, "zone_24": 80,
            "zone_25": 80, "zone_26": 25, "zone_27": 55,
            "zone_28": 55, "zone_29": 80, "zone_30": 25,
            "zone_31": 25, "zone_32": 55, "zone_33": 80,
            "zone_34": 80, "zone_35": 25, "zone_36": 55,
            "zone_37": 55, "zone_38": 80, "zone_39": 25,
            "zone_40": 25, "zone_41": 55, "zone_42": 80,
            "zone_43": 80, "zone_44": 25,
        }

        self.marker_pub = self.create_publisher(
            MarkerArray, '/nitrobot/zone_markers', 10)
        self.state_pub = self.create_publisher(
            String, '/nitrobot/zone_states', 10)

        # Listen for fertilization completion
        self.create_subscription(
            String, '/nitrobot/fertilized', self._on_fertilized, 10)

        # Publish markers every 3 second
        self.create_timer(3.0, self._publish_markers)

        self.get_logger().info(
            f'ZoneStateNode started: {len(ZONES)} zones initialised')
        self._log_summary()

    def _colour(self, zone):
        """Return (status, r, g, b) for a zone based on nitrogen level."""
        n = self.nitrogen[zone]
        if n < RED_THRESHOLD:
            return 'red', 1.0, 0.0, 0.0
        elif n < YELLOW_THRESHOLD:
            return 'yellow', 1.0, 1.0, 0.0
        else:
            return 'green', 0.0, 1.0, 0.0

    def _on_fertilized(self, msg: String):
        """Handle fertilization signals (ignore SKIPPED signals)."""
        zone_msg = msg.data.strip()
        
        # NEW: 忽略暂时跳过的信号，不更新 nitrogen
        if ':SKIPPED' in zone_msg:
            zone = zone_msg.split(':')[0]
            self.get_logger().info(f'{zone} skipped temporarily, will retry later')
            return
        
        # 只处理正常完成的信号
        zone = zone_msg
        if zone in self.nitrogen:
            self.nitrogen[zone] = 100
            self.get_logger().info(
                f'{zone} fertilized → nitrogen restored to 100')
            self._publish_markers()

    def _publish_markers(self):
        array = MarkerArray()
        states = []

        for i, (zone, (x, y)) in enumerate(ZONES.items()):
            status, r, g, b = self._colour(zone)
            states.append(f'{zone}:{status}:{self.nitrogen[zone]}')

            m = Marker()
            m.header.frame_id = 'map'
            m.header.stamp = self.get_clock().now().to_msg()
            m.ns = 'zones'
            m.id = i
            m.type = Marker.CUBE
            m.action = Marker.ADD
            m.pose.position.x = x
            m.pose.position.y = y
            m.pose.position.z = 0.0
            m.pose.orientation.w = 1.0
            m.scale.x = ZONE_SIZE
            m.scale.y = ZONE_SIZE
            m.scale.z = 0.05
            m.color.a = 0.7
            m.color.r = r
            m.color.g = g
            m.color.b = b
            array.markers.append(m)
            # Text label showing zone ID
            t = Marker()
            t.header.frame_id = 'map'
            t.header.stamp = self.get_clock().now().to_msg()
            t.ns = 'zone_labels'
            t.id = i + 1000
            t.type = Marker.TEXT_VIEW_FACING
            t.action = Marker.ADD
            t.pose.position.x = x
            t.pose.position.y = y
            t.pose.position.z = 0.15
            t.pose.orientation.w = 1.0
            t.scale.z = 0.12
            t.color.a = 1.0
            t.color.r = 1.0
            t.color.g = 1.0
            t.color.b = 1.0
            t.text = zone.replace('zone_', '')
            array.markers.append(t)

        self.marker_pub.publish(array)
        self.state_pub.publish(String(data=','.join(states)))

    def _log_summary(self):
        red = sum(1 for z in ZONES if self.nitrogen[z] < RED_THRESHOLD)
        yellow = sum(
            1 for z in ZONES
            if RED_THRESHOLD <= self.nitrogen[z] < YELLOW_THRESHOLD)
        green = len(ZONES) - red - yellow
        self.get_logger().info(
            f'Initial state: {red} red, {yellow} yellow, {green} green')


def main(args=None):
    rclpy.init(args=args)
    node = ZoneStateNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()