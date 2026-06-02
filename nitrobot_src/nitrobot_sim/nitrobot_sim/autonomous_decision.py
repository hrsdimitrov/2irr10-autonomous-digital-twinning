#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class AutonomousDecisionNode(Node):
    def __init__(self):
        super().__init__('autonomous_decision_node')

        self.zone_states = {}
        self.current_target = None
        self.mission_complete = False

        # Zones that timed out — visited after all primary zones are done
        self.skipped_zones = []
        # False = primary phase (skip timed-out zones)
        # True  = retry phase  (only timed-out zones remain)
        self.in_retry_phase = False

        self.target_pub = self.create_publisher(
            String, '/nitrobot/target_zone', 10)
        self.mission_pub = self.create_publisher(
            String, '/nitrobot/mission_status', 10)

        self.create_subscription(
            String, '/nitrobot/zone_states', self._on_zone_states, 10)
        self.create_subscription(
            String, '/nitrobot/fertilized', self._on_fertilized, 10)

        # Single periodic timer — no nested timer creation
        self.create_timer(3.0, self._decide)

        self.get_logger().info('AutonomousDecisionNode started')

    # ------------------------------------------------------------------ #
    #  Subscriptions                                                       #
    # ------------------------------------------------------------------ #

    def _on_zone_states(self, msg: String):
        """Parse zone_states string → dict {zone: status}."""
        # Format: zone_1:red:25,zone_2:green:80,...
        self.zone_states = {}
        for entry in msg.data.split(','):
            parts = entry.split(':')
            if len(parts) == 3:
                zone, status, _ = parts
                self.zone_states[zone] = status

    def _on_fertilized(self, msg: String):
        """Handle completion or timeout from the mediator."""
        zone_msg = msg.data.strip()

        if ':SKIPPED' in zone_msg:
            # Mediator timed-out on this zone → defer it
            zone = zone_msg.split(':')[0]
            if zone not in self.skipped_zones:
                self.skipped_zones.append(zone)
            self.get_logger().info(
                f'{zone} timed out → deferred. '
                f'Pending retries: {self.skipped_zones}')
        else:
            # Zone successfully fertilized
            zone = zone_msg
            if zone in self.skipped_zones:
                # Completed on the retry pass — clean up the list
                self.skipped_zones.remove(zone)
                self.get_logger().info(
                    f'{zone} ✓ (retry). '
                    f'Remaining retries: {self.skipped_zones}')
            else:
                self.get_logger().info(f'{zone} ✓')

        self.current_target = None

    # ------------------------------------------------------------------ #
    #  Decision logic                                                      #
    # ------------------------------------------------------------------ #

    def _decide(self):
        """Pick the next target zone."""
        if self.mission_complete or self.current_target is not None:
            return
        if not self.zone_states:
            return

        non_green = [
            z for z, s in self.zone_states.items()
            if s in ('red', 'yellow')
        ]

        # ── Mission complete ─────────────────────────────────────────── #
        if not non_green:
            self.mission_complete = True
            self.get_logger().info('All zones fertilized! Mission COMPLETE.')
            self.mission_pub.publish(String(data='COMPLETE'))
            return

        # ── Primary phase: ignore skipped zones ──────────────────────── #
        if not self.in_retry_phase:
            available = [z for z in non_green if z not in self.skipped_zones]

            if available:
                target = self._pick(available)
            else:
                # Every remaining zone was previously skipped → retry pass
                self.in_retry_phase = True
                self.get_logger().info(
                    f'Primary phase done. '
                    f'Retrying {len(self.skipped_zones)} deferred zone(s): '
                    f'{self.skipped_zones}')
                retry_candidates = [z for z in self.skipped_zones if z in non_green]
                if not retry_candidates:
                    # Already all green (edge case)
                    return
                target = self._pick(retry_candidates)

        # ── Retry phase: work through previously skipped zones ──────── #
        else:
            retry_candidates = [z for z in self.skipped_zones if z in non_green]

            if not retry_candidates:
                # All retries done; fall back to primary phase for any
                # remaining zones (shouldn't normally happen, but safe)
                self.in_retry_phase = False
                remaining = [z for z in non_green if z not in self.skipped_zones]
                if not remaining:
                    return
                target = self._pick(remaining)
            else:
                target = self._pick(retry_candidates)

        self.current_target = target
        phase_label = 'RETRY' if self.in_retry_phase else 'PRIMARY'
        self.get_logger().info(f'[{phase_label}] → {target}')
        self.target_pub.publish(String(data=target))

    def _pick(self, candidates: list) -> str:
        """Return the first red zone, or the first yellow zone if none."""
        reds = [z for z in candidates if self.zone_states.get(z) == 'red']
        return reds[0] if reds else candidates[0]


def main(args=None):
    rclpy.init(args=args)
    node = AutonomousDecisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()