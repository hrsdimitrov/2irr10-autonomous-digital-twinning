# 2IRR10 Autonomous Digital Twinning

## Docker Container

1. Create Docker image: `docker compose build`
2. Run `xhost +local:docker` before starting the container
3. Start container: `docker compose up -d`
4. Open new bash: `docker exec -it turtlebot3_container bash`
5. Stop the container: To stop the container run `docker compose down`.

## Building the project

1. `cd /ws`
2. `colcon build --symlink-install`
3. `source install/setup.bash`

## On the Raspberry Pi

```bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_bringup robot.launch.py namespace:=real
```

## On the laptop / workstation

`ros2 launch nitrobot_sim sim.launch.py`
`ros2 launch nitrobot_sim spawn.launch.py` |
`ros2 launch nitrobot_sim nav2.launch.py` |
`ros2 launch nitrobot_bringup twin_system.launch.py` |


## Zone goal (both robots)

```bash
ros2 run nitrobot_decision set_zone.sh zone_5
```

## Simulation only (manual)

**1.** `ros2 launch nitrobot_sim sim.launch.py`  
**2.** `ros2 launch nitrobot_sim spawn.launch.py`  
**3.** `ros2 launch nitrobot_sim nav2.launch.py`  
**4.** `ros2 launch nitrobot_decision decision.launch.py`  
**5.** `ros2 launch nitrobot_mediator mediator.launch.py`


## Kill stale processes

```bash
pkill -9 -f 'gz sim|rviz2|ros2 launch|nav2_|nitrobot_' 2>/dev/null; ros2 daemon stop 2>/dev/null; true
```
