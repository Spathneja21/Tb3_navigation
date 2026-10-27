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
- Dockerfile, container and the package skeleton come in the next steps.
