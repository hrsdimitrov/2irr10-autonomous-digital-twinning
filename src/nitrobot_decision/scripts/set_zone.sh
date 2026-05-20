#!/usr/bin/env bash
exec ros2 param set /nitrobot_decision_node target_zone "${1:?usage: set_zone.sh zone_1}"
