This repository contains all relevant code and documentation for the 2IRR10 Autonomous Digital Twinning project. 

# Setup

1. Create Docker image: `docker compose build`
2. Start container: `docker compose run --rm ros`

Inside the bash shell:
1. Build workspace: `colcon build`
2. Load workspace into ROS: `source install/setup.bash`
3. Start the robot system: `ros2 launch my_tb3_world new_world.launch.py`
