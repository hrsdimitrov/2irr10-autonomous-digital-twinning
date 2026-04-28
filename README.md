This repository contains all relevant code and documentation for the 2IRR10 Autonomous Digital Twinning project. 

# Deployment

1. Create Docker image: `docker compose build`
2. Start container: `docker compose up -d`

## Terminal 1 - Simulation
1. Open new bash: `docker exec -it turtlebot3_container bash`
2. Run simulation: `bash scripts/run-sim.sh`

## Terminal 2 - Teleop
1. Open new bash: `docker exec -it turtlebot3_container bash`
2. Run teleop: `bash scripts/teleop.sh`

## Terminal 3 - RViz
1. Open new bash: `docker exec -it turtlebot3_container bash`
2. Run RViz`bash scripts/rviz.sh`


## Stopping the container

To stop the container run `docker compose down`.
