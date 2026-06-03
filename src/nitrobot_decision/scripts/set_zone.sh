#!/usr/bin/env bash
set -euo pipefail

ZONE="${1:?usage: set_zone.sh <zone_name> (e.g. zone_5)}"

if ros2 node list 2>/dev/null | grep -qx '/nitrobot_decision_node'; then
  exec ros2 param set /nitrobot_decision_node target_zone "$ZONE"
fi

echo "nitrobot_decision_node is not running." >&2
echo "Start it: ros2 launch nitrobot_decision decision.launch.py" >&2
echo "Publishing once to /nitrobot/target_zone (mediator must be running)." >&2
exec ros2 topic pub --once /nitrobot/target_zone std_msgs/msg/String "{data: '$ZONE'}"
