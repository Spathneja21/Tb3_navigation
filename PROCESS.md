# Build Process Log — TurtleBot3 + Nav2 in Gazebo (assignment)

Step-by-step log of rebuilding the project in `tb3_assignment`: what was built, what went
wrong, and how it was fixed. One section per step, matching the commit history.

**Task:** set up a TurtleBot3 (Burger) in Gazebo with the ROS 2 Nav2 stack and show autonomous
navigation to a goal in an environment with obstacles. C++ is the base language for our own nodes.

**Environment:** Gazebo Classic with the `SC7a_clutter_field_low` world (30 × 30 m arena, 45 blocks),
Burger robot, ROS 2 Humble in Docker (host Ubuntu 20.04 is too old for Humble).

---

## Step 1. Repository

- Created the folder `~/projects/tb3_assignment`, to be connected to GitHub.
- `.gitignore`: ignores the colcon outputs (`build/`, `install/`, `log/`) and Python caches.
  This file is committed, and `PROCESS.md` is committed too, since it is part of the
  submission.
- `Dockerfile`, on top of the existing `supermarketbot:humble` image (ROS 2 Humble, Nav2,
  slam_toolbox, RViz). It adds `turtlebot3_description`, `turtlebot3_gazebo` (Gazebo Classic
  models and plugins) and `joint_state_publisher`, and sets `TURTLEBOT3_MODEL=burger` so it
  doesn't have to be exported in every shell.
- `ENTRYPOINT []`: the base image's entrypoint sources `/ros2_ws/install/setup.bash`, which
  doesn't exist on a fresh mount, so the container would exit immediately. Each shell sources
  `/opt/ros/humble/setup.bash` and the workspace by hand instead.
- `README.md`: setup instructions for the image and the container (flags explained). It will
  grow with each step.

## Step 2. The `tb3_bot` package

Same layout as the AMR project: a colcon workspace with `src/<package>/`, and inside the
package `src/ launch/ config/ scripts/ maps/` (empty folders hold a `.gitkeep`, since git
doesn't track empty directories).

- `package.xml`: ament_cmake package. Only run-time dependencies for now: the TurtleBot3
  description and Gazebo packages, `robot_state_publisher`, `joint_state_publisher`,
  `gazebo_ros`. The C++ dependencies (`rclcpp`, `sensor_msgs`, ...) come with the first C++
  node.
- `CMakeLists.txt`: no executables yet. It installs `launch/` and `config/` into the package
  share directory. **Those are copies**, so after editing a launch file or config the package
  needs a rebuild (or `--symlink-install`) before `ros2 launch` sees the change.

### Mistake: the container mounted the project at `/demo`

- The container had been started with `-v ~/projects/tb3_assignment:/demo`.
- `cd /ros2_ws && colcon build --packages-select tb3_bot` printed
  `WARNING: ignoring unknown package 'tb3_bot' in --packages-select` and
  `Summary: 0 packages finished`.
- Why: `/ros2_ws` is an empty folder that exists in the base image, and the project was
  mounted somewhere else (`/demo`), so `colcon` found nothing to build.
  `ls /demo/src` shows `tb3_bot`; `ls /ros2_ws` doesn't.
- Fix: a container's mounts are fixed when it is created, so it can't be edited in place.
  `docker rm -f tb3assign`, then `docker run` again with `-v ~/projects/tb3_assignment:/ros2_ws`.
  The files live on the host, so nothing is lost. The README's `docker run` command was
  corrected to match.
