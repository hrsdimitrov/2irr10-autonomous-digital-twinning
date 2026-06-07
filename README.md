# 2IRR10 Autonomous Digital Twinning

## First-time Setup

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and enable WSL2 integration
2. Open CMD and enter WSL Ubuntu:
```bash
wsl -d Ubuntu-24.04
```
3. Clone the repository and build the Docker image:
```bash
cd ~
git clone https://github.com/zding1-tue/cbl-win-sim.git
cd cbl-win-sim
sudo docker compose build
```
This will take 10-20 minutes on the first run.

---

## Running the Simulation (2 terminals)

### Before starting — launch the container

Open CMD and enter WSL Ubuntu:
```bash
wsl -d Ubuntu-24.04
cd ~/cbl-win-sim
sudo docker compose up -d
```

### Terminal 1 — Enter container and start simulation

```bash
docker exec -it turtlebot3_container bash
git config --global --add safe.directory /ws
cd /ws
git pull
chmod +x /ws/src/nitrobot_sim/scripts/mission_executor.py
colcon build --symlink-install
source install/setup.bash
ros2 launch nitrobot_sim sim_full.launch.py
```

Wait until Gazebo and RViz are fully loaded with the map and robot visible,
and Nav2 has printed `Managed nodes are active` (~1 minute).

### Terminal 2 — Start mission executor

Open a new CMD and run:
```bash
wsl -d Ubuntu-24.04
docker exec -it turtlebot3_container bash
source /opt/ros/jazzy/setup.bash
source /opt/turtlebot3_ws/install/setup.bash
source /ws/install/setup.bash
ros2 launch nitrobot_sim mission.launch.py
```

The robot will automatically navigate to each fertilization zone in sequence.
Completed zones turn green in RViz. Terminal logs show full TX/RX communication.

---

## Kill stale processes

```bash
pkill -9 -f 'gz sim|rviz2|ros2 launch|nav2_|nitrobot_' 2>/dev/null; ros2 daemon stop 2>/dev/null; true
```
