# TurtleBot3 + Nav2 in Gazebo

A TurtleBot3 Burger in Gazebo with the ROS 2 Navigation2 stack, navigating autonomously to a
goal in an environment with obstacles. ROS 2 Humble, Gazebo Classic, C++ for our own nodes.

## Setup

### Prerequisites

- Docker, and an X server (`$DISPLAY` set) for Gazebo and RViz.
- The `supermarketbot:humble` image (ROS 2 Humble, Nav2, slam_toolbox, RViz). Check with
  `docker images`. The host doesn't need to be Ubuntu 22.04, since everything runs in the
  container.

### 1. Build the image

Adds Gazebo Classic and the TurtleBot3 packages on top of `supermarketbot:humble`, and sets
`TURTLEBOT3_MODEL=burger`:
```bash
cd ~/projects/tb3_assignment
docker build -t tb3assign:humble .
```

### 2. Start the container

```bash
xhost +local:docker
docker run -it --name tb3assign --net=host \
  -e DISPLAY=$DISPLAY -e LIBGL_ALWAYS_SOFTWARE=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v ~/projects/tb3_assignment:/demo \
  tb3assign:humble
```
- `--net=host`: ROS 2 discovery is multicast-based, and bridged networks break it. Stop any
  other ROS container first, since both would share one ROS domain.
- `LIBGL_ALWAYS_SOFTWARE=1`: there is no GPU passthrough, so Gazebo and RViz render on the CPU.
- `xhost +local:docker` lets the container draw on your display. It doesn't survive a new
  login, so run it again if a window fails with `No protocol specified`.

Later sessions:
```bash
docker start -ai tb3assign       # resume the container
docker exec -it tb3assign bash   # extra shell in the running container
```

Every shell starts with:
```bash
source /opt/ros/humble/setup.bash
```
