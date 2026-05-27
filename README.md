# NitroBot Digital Twin (ROS 2 Jazzy)

**One command (laptop):** `ros2 launch nitrobot_bringup bringup.launch.py`

## Architecture

```text
Raspberry Pi                          Laptop / Docker
────────────────                      ─────────────────────────────────────
turtlebot3_bringup                    nitrobot_sim
  namespace:=real                       sim.launch.py -> Gazebo + /sim Nav2
  (hardware only)                       -> /sim/navigate_to_pose

                                      nitrobot_real
                                      real.launch.py -> Nav2 under /real
                                      -> /real/navigate_to_pose
                                      (uses /real/scan, /real/odom from Pi)
                                      (publishes /real/cmd_vel to Pi)

                                      nitrobot_decision
                                      -> /nitrobot/target_zone

                                      nitrobot_mediator
                                      <- /nitrobot/target_zone
                                      -> /sim/navigate_to_pose
                                      -> /real/navigate_to_pose
                                      <- /real/battery_state
                                      -> /nitrobot/battery_state
```

### Raspberry Pi (hardware only)

```bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_bringup robot.launch.py namespace:=real
```

Exposes: `/real/scan`, `/real/odom`, `/real/cmd_vel`, `/real/battery_state`  
Does **not** run: decision, mediator, Nav2, or NitroBot logic.

### Laptop — simulation

```bash
ros2 launch nitrobot_sim sim.launch.py      # Gazebo + /sim Nav2
ros2 run nitrobot_sim sim_teleop.sh         # manual teleop (optional)
```

### Laptop — physical robot navigation

Pi must be running bringup first. Same `ROS_DOMAIN_ID` on Pi and laptop.

```bash
ros2 launch nitrobot_real real.launch.py
```

Nav2 consumes `/real/scan` and `/real/odom`, publishes `/real/cmd_vel`, exposes `/real/navigate_to_pose`.

Optional manual drive (bypasses Nav2):

```bash
ros2 run nitrobot_real real_teleop.sh
```

### Laptop — everything at once

Pi must be running `turtlebot3_bringup namespace:=real` first.

```bash
ros2 launch nitrobot_bringup bringup.launch.py
ros2 run nitrobot_decision set_zone.sh zone_14
```

### Laptop — digital twin (separate terminals)

```bash
ros2 launch nitrobot_decision decision.launch.py
ros2 launch nitrobot_mediator mediator.launch.py
ros2 run nitrobot_decision set_zone.sh zone_14
```

### Zone → navigation flow

```text
decision  --/nitrobot/target_zone-->  mediator  --NavigateToPose-->
    /sim/navigate_to_pose  -->  sim Nav2  -->  /sim/cmd_vel  -->  Gazebo
    /real/navigate_to_pose -->  real Nav2 -->  /real/cmd_vel -->  Pi motors
```

## Docker

1. `docker compose build`
2. `xhost +local:docker`
3. `docker compose up -d`
4. `docker exec -it turtlebot3_container bash`

Inside container:

```bash
cd /ws && colcon build --symlink-install && source install/setup.bash
export TURTLEBOT3_MODEL=burger
```

## Test battery without a robot

```bash
ros2 topic pub /real/battery_state sensor_msgs/msg/BatteryState \
  "{voltage: 11.4, percentage: 0.82}" -r 1
```
