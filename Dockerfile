FROM osrf/ros:jazzy-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV TURTLEBOT3_MODEL=burger

# Install ROS + build dependencies
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

# Install TurtleBot3 packages via apt (more stable on Mac ARM)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-turtlebot3 \
    ros-jazzy-turtlebot3-msgs \
    ros-jazzy-turtlebot3-simulations \
    && rm -rf /var/lib/apt/lists/*

# Install VNC for Mac compatibility
RUN apt-get update && apt-get install -y --no-install-recommends \
    x11vnc \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

RUN printf '#!/bin/bash\nXvfb :1 -screen 0 1280x800x24 &\nexport DISPLAY=:1\nx11vnc -display :1 -forever -nopw -listen 0.0.0.0 -rfbport 5901 &\nexec "$@"\n' > /entrypoint.sh && chmod +x /entrypoint.sh

WORKDIR /ws

# Automatically source ROS + TurtleBot3 when opening bash
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi" >> /root/.bashrc && \
    echo "export TURTLEBOT3_MODEL=burger" >> /root/.bashrc

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]