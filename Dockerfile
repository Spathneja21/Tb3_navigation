# supermarketbot:humble (built from ../Ros-AMR-Mobile-Robot/dockerfile) already has
# ROS 2 Humble + Nav2 + slam_toolbox + RViz; this adds Gazebo Classic and TurtleBot3.
FROM supermarketbot:humble
RUN apt-get update && apt-get install -y \
      ros-humble-turtlebot3-description \
      ros-humble-turtlebot3-gazebo \
      ros-humble-joint-state-publisher \
    && rm -rf /var/lib/apt/lists/*
ENV TURTLEBOT3_MODEL=burger
# the base image's entrypoint sources /ros2_ws/install/setup.bash, which doesn't exist on a
# fresh mount and kills the container; clear it and source by hand in each shell instead
ENTRYPOINT []
CMD ["bash"]
