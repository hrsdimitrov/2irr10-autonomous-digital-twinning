FROM osrf/ros:jazzy-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV TURTLEBOT3_MODEL=burger

# install ROS + build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    python3-colcon-common-extensions \
    python3-rosdep \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-nav2-bringup \
    ros-jazzy-nav2-map-server \
    ros-jazzy-slam-toolbox \
    ros-jazzy-cartographer \
    ros-jazzy-cartographer-ros \
    ros-jazzy-xacro \
    ros-jazzy-rmw-fastrtps-cpp \
    && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-lc"]

# build TurtleBot3 packages inside the image
WORKDIR /opt/turtlebot3_ws

RUN mkdir -p src && cd src && \
    git clone --depth 1 https://github.com/ROBOTIS-GIT/turtlebot3_msgs.git && \
    git clone --depth 1 https://github.com/ROBOTIS-GIT/turtlebot3.git && \
    git clone --depth 1 https://github.com/ROBOTIS-GIT/turtlebot3_simulations.git

RUN source /opt/ros/jazzy/setup.bash && \
    rosdep update && \
    rosdep install --rosdistro jazzy --from-paths src --ignore-src -r -y || true

RUN source /opt/ros/jazzy/setup.bash && \
    colcon build --event-handlers console_direct+ \
    --packages-select \
    turtlebot3_msgs \
    turtlebot3_description \
    turtlebot3_gazebo \
    turtlebot3_teleop \
    turtlebot3_cartographer \
    turtlebot3_navigation2

# workspace for your custom package mounted by docker compose
WORKDIR /ws

# automatically source ROS + TurtleBot3 when opening bash
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "source /opt/turtlebot3_ws/install/setup.bash" >> /root/.bashrc && \
    echo "if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi" >> /root/.bashrc && \
    echo "export TURTLEBOT3_MODEL=burger" >> /root/.bashrc

CMD ["/bin/bash"]