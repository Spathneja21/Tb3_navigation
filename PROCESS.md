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
- Why: `/ros2_ws` already exists in the base image as the reference project's own workspace
  (`ls /ros2_ws` showed `build install log src`, none of it ours). The project was mounted
  somewhere else (`/demo`), so `colcon` looked in that workspace and didn't find `tb3_bot`.
  `ls /demo` shows our `Dockerfile README.md PROCESS.md src`.
- The first fix attempt failed too: the `docker rm -f` / `docker run` commands were typed
  inside the container, where `docker` doesn't exist (`bash: docker: command not found`).
  They have to run on the host.
- Fix: a container's mounts are fixed when it is created, so it can't be edited in place.
  `docker rm -f tb3assign`, then `docker run` again with `-v ~/projects/tb3_assignment:/ros2_ws`.
  The files live on the host, so nothing is lost. The README's `docker run` command was
  corrected to match.


### The mount fix took three attempts

- The first `docker rm -f` was typed inside the container (`docker: command not found`).
- A second run of the checks showed the mount list still had only
  `.../tb3_assignment -> /demo` and `colcon list` found only the base image's
  `supermarketbot` package: the old container was still the one in use.
- Telling the shells apart: the container prompt is `root@...:/ros2_ws#`, the host prompt is
  `(base) shubham@...:~$`. After `exit`, `docker rm -f tb3assign` and a new `docker run` on the
  host, `ls /ros2_ws/src` showed `tb3_bot` and `colcon build --packages-select tb3_bot`
  succeeded.

## Step 3. The clutter-field world

Copied `SC7a_clutter_field_low.sdf` into `src/tb3_bot/models/`, unchanged (byte-identical to the
original).

What it is (from its own header and contents):
- World `sc7a_clutter_field_low`: a 30 × 30 m arena with four 2 m tall outer walls and 45
  static boxes, 1.2 m tall and 0.5–2.0 m wide. 50 `<collision>` elements in total (ground, 4
  walls, 45 blocks); every one is a plain box (no meshes). Generated with seed 7100, at least 1.0 m between blocks,
  and nothing within 1.5 m of the origin, so the robot can spawn at (0, 0), where world and map
  coordinates will coincide.
- It is written for **Gazebo Harmonic** (gz-sim 8, SDF 1.9, `gz-sim-*-system` plugins). The rest
  of this project uses Gazebo Classic (Humble's `gazebo_ros`, the TurtleBot3 `model.sdf` with
  `libgazebo_ros_*` plugins), so it is not expected to load there as-is. It stays unconverted in
  this commit; the Classic-compatible copy comes when the world is first launched.
- `CMakeLists.txt` doesn't install `models/` yet.


## Step 4. Import the robot URDF (`rsp.launch.py`)

First layer of the bring-up, with no Gazebo: load the stock TurtleBot3 Burger URDF and publish
its TF tree, so the model can be checked in RViz before anything simulates it.

- `launch/rsp.launch.py` reads `turtlebot3_description/urdf/turtlebot3_<model>.urdf` (the model
  comes from `TURTLEBOT3_MODEL`, which the Dockerfile sets to `burger`) and hands the text to
  `robot_state_publisher` as the `robot_description` parameter. `joint_state_publisher` publishes
  zero joint states, so the wheels have something to render with no simulator running.
- The URDF stays in the TurtleBot3 apt package and is read from there; it is not copied into this
  repo.
- Removed `launch/.gitkeep`, since the folder now has a real file.
- The URDF is passed through unchanged in this first version. That turned out to be a mistake: the
  stock Humble URDF has a literal `${namespace}` in every link name. It only became visible once
  Gazebo was publishing scans, so it is written up under Step 5 ("Mistake: the `${namespace}`
  placeholder").
- Run it (container, workspace sourced, after a rebuild because launch files are installed copies):
  `ros2 launch tb3_bot rsp.launch.py`, then `rviz2` with a RobotModel display (Description Topic
  `/robot_description`) and a TF display.

- README: added a "Robot model: TurtleBot3 Burger" section with the exact commands (rebuild, launch
  `rsp.launch.py` in one shell, `rviz2` in another, both shells sourced) and an RViz screenshot,
  `models/robot_model.png` (479 × 419, about 33 KB; shows the Burger's wheels, stacked plates and
  lidar).

## Step 5. Start Gazebo and spawn the robot (`gazebo.launch.py`)

Second layer of the bring-up: put the robot into a running Gazebo.

- `launch/gazebo.launch.py` includes `gazebo_ros`'s own `gazebo.launch.py` (Gazebo Classic: `gzserver`
  plus `gzclient`, with the ROS factory plugin that provides `/spawn_entity`), starts
  `robot_state_publisher` on sim time, and runs `spawn_entity.py -topic robot_description` to
  create the robot at (0, 0, 0.01).
- `gui` launch argument (default `true`): `gui:=false` runs `gzserver` only. Under software
  rendering (`LIBGL_ALWAYS_SOFTWARE=1`) the Gazebo window is slow, and RViz can show everything
  the simulation publishes.
- It starts in Gazebo's default empty world. The clutter-field world is loaded in a later step,
  so that a world problem and a robot problem can't be confused.
- The robot is spawned from the same URDF `rsp.launch.py` reads (through the
  `/robot_description` topic that `robot_state_publisher` publishes).
- Run: `ros2 launch tb3_bot gazebo.launch.py` (or `gui:=false`), after a rebuild.

### Mistake: spawned the URDF, so there was no `/odom` and no `/scan`

- Symptom: Gazebo ran (`/clock` and `/performance_metrics` were published, which only a running
  `gzserver` does), but `ros2 topic list` showed no `/scan` and no `/odom`, and
  `ros2 topic echo /scan --once` said `topic does not appear to be published yet`.
- In Gazebo Classic, those topics come from plugins loaded with the robot model:
  `libgazebo_ros_diff_drive.so` (`/odom`, `/cmd_vel`, TF), `libgazebo_ros_ray_sensor.so`
  (`/scan`), the IMU plugin and the joint-state plugin.
- `grep` on the Burger's `turtlebot3_gazebo/models/turtlebot3_burger/model.sdf` found exactly
  those four plugins. The URDF's plugin count was not checked this time (for the Waffle's URDF
  it was 0); the fix below is what confirms it.
- Fix: spawn the robot from `model.sdf` (`spawn_entity.py -file`), and keep the URDF only for
  `robot_state_publisher`. The ROBOTIS launch files do the same.
- Added with the fix: `GAZEBO_MODEL_PATH` set to `turtlebot3_gazebo/models`, because the SDF loads
  its meshes from `model://turtlebot3_common/...`.

### Mistake: the `${namespace}` placeholder in the URDF (found in RViz while running Gazebo)

- Symptom: with `/scan` and `/odom` publishing, RViz printed
  `Message Filter dropping message: frame 'base_scan' ... because the queue is full`, repeating,
  and the RobotModel display showed no robot.
- Cause: the stock Humble TurtleBot3 URDF contains a literal `${namespace}` in every link name, and
  ROBOTIS's launch files substitute it before use. `rsp.launch.py` and `gazebo.launch.py` passed the
  text through unchanged, so `robot_state_publisher` published frames named
  `${namespace}base_footprint`, `${namespace}base_scan`, and so on (`got segment ${namespace}...`
  in its log). The scan messages from Gazebo use the plain name `base_scan`, so RViz could never
  find a transform for them, and RobotModel's links had no transform either.
- Fix: `f.read().replace('${namespace}', '')` in both launch files. The frames are now
  `base_footprint`, `base_link`, `base_scan`, and so on, and `odom -> base_footprint` comes from
  the Gazebo diff-drive plugin.
- It was first made in Step 4 and only showed once Gazebo published scans in the plain frame
  names. Checking `ros2 run tf2_ros tf2_echo odom base_scan` would also have shown it.

## Step 6. Launch the clutter-field world with the robot

- `gazebo.launch.py` gets a `world` launch argument, passed through to `gazebo_ros`'s launch. Its default
  is `<tb3_bot share>/models/SC7a_clutter_field_low.sdf`, the arena copied in Step 3, so
  `ros2 launch tb3_bot gazebo.launch.py gui:=false` now loads the arena and spawns the Burger at (0, 0),
  the clear spot at the arena's origin.
- First version, deliberately plain: the original SDF file is used as it is, and `CMakeLists.txt` is not
  touched. (`models/` was left out of the install on purpose in Step 3; the world file therefore
  isn't in the installed package yet.)

### Mistake: the world file wasn't installed, and Gazebo silently started an empty world

- Symptom: `gazebo.launch.py` ran cleanly (robot spawned, `/scan` and `/odom` published, no errors in
  the launch log; the only "errors" were the harmless ALSA sound-card lines), but every one of the
  360 scan beams read `inf`. With the robot at the origin, the arena's nearest blocks are about 2.5-2.8 m
  away (`block_033`, `block_001`, `block_008`), inside the lidar's 3.5 m range, so some beams should have
  hit something. The robot was alone in an empty world.
- Diagnosis, with three commands in the container:
  - `ps -eo args | grep [g]zserver` showed
    `gzserver /ros2_ws/install/tb3_bot/share/tb3_bot/models/SC7a_clutter_field_low.sdf ...`, so the launch
    file did pass the right path.
  - `grep -n world .../install/tb3_bot/share/tb3_bot/launch/gazebo.launch.py` showed the new `world`
    argument, so the installed launch file was current.
  - `ls /ros2_ws/install/tb3_bot/share/tb3_bot/models` -> `No such file or directory`.
- Cause: `CMakeLists.txt` installed only `launch` and `config`. Everything the launch files read at
  run time comes from the installed share directory, not from `src/`, so the world file didn't exist
  where the launch file pointed. Gazebo Classic started an empty world instead of failing, with no message.
- Fix: `install(DIRECTORY launch config models DESTINATION share/${PROJECT_NAME})`.
- Result: after `colcon build --packages-select tb3_bot` (which now installs `models/`) and a relaunch,
  the world loads and the robot runs inside the arena (reported as working). The launch output
  after the rebuild was not captured here, so whether Gazebo Classic printed any warnings about the
  Harmonic-format file (SDF 1.9, `gz-sim-*` plugins) is not recorded; the Step 3 note that the world
  might need converting stays open until that's checked.
- Lesson: an all-`inf` scan is not "nothing wrong". Checking what `gzserver` was started with
  (`ps`) and whether that path exists beat reading logs that had nothing in them.

## Step 7. View the robot in the Gazebo window and drive it

- No code change: `gazebo.launch.py gui:=true` (the default) starts `gzclient` along with `gzserver`.
  The question for this step is whether the window works under software rendering
  (`LIBGL_ALWAYS_SOFTWARE=1`, no GPU in the container), which was a problem with the office mesh
  in the earlier project. This world has no meshes or textures, only box primitives.
- Driving: `ros2 run teleop_twist_keyboard teleop_twist_keyboard` publishes `/cmd_vel`, which the
  Burger's diff-drive plugin subscribes to; the robot should move, and `/odom` should change.
- README: added "Watch it in the Gazebo window, and drive it".
- Outcome: to be recorded.

## Step 8. Add the autonomous explorer (`lidar_explorer.cpp`)

Copied `lidar_explorer.cpp` from the earlier `tb3_nav2_demo` project into `src/tb3_bot/src/`
(identical, 429 lines), instead of driving the robot by hand with teleop. Removed
`src/.gitkeep`, since the folder has a real file.

What it does (it is C++, using `rclcpp`, `tf2_ros` and the `sensor_msgs`/`nav_msgs`/`geometry_msgs`
types):
- Local layer, on every `/scan`: finds gaps in the lidar scan and steers into the one closest to its
  waypoint, publishing `/cmd_vel`. It slows near obstacles and escapes by reversing and rotating
  if stuck.
- Global layer, once a second, on `/map`: picks the nearest reachable frontier (a free cell next to
  unknown space) on the SLAM map and sets the waypoint toward it. It needs `/map` and a
  `map -> base_link` transform, so this half only works once `slam_toolbox` is running.
- Without a map it falls back to going toward the widest, deepest gap in the scan.
- It also publishes the travelled path (`/explorer_path`) and the current waypoint (`/explorer_goal`).

This copy is the version from `tb3_nav2_demo`, not the original `amr_bot` one. It differs by one change
(lines 302-308): it normalises scan angles to -pi..pi and rotates the arrays, because the TurtleBot3's
LDS reports angles 0..2pi (index 0 straight ahead) while the original code assumes -pi..pi.
Without that, a beam slightly to the right (about 6.0 rad) reads as a hard left.

Not done yet in this step: nothing builds it. `CMakeLists.txt` has no `add_executable` for it and
`package.xml` doesn't list `rclcpp`, `tf2_ros` or the message packages.

### Mistake: the explorer was never built (`No executable found`)

- Symptom: `colcon build --packages-select tb3_bot` finished in 0.07 s with `1 package finished`, and
  `ros2 run tb3_bot lidar_explorer` printed `No executable found`.
- Cause: a `.cpp` file in `src/` is not compiled just by being there. `CMakeLists.txt` had no
  `add_executable` for it, so `colcon` had nothing to compile, and without an `install(TARGETS ...)`
  the binary wouldn't reach `lib/tb3_bot/`, where `ros2 run` looks. The 0.07 s build time was the clue:
  nothing was being compiled.
- Fix, in `CMakeLists.txt`: `find_package` for `rclcpp`, `geometry_msgs`, `sensor_msgs`,
  `nav_msgs`, `tf2_ros`; `add_executable(lidar_explorer src/lidar_explorer.cpp)`;
  `ament_target_dependencies(...)` with the same packages; `install(TARGETS lidar_explorer
  DESTINATION lib/${PROJECT_NAME})`. In `package.xml`: matching `<depend>` entries, so tools like
  `rosdep` know what the package needs.

## Step 9. SLAM and Nav2 configuration

Symptom that led here: with `lidar_explorer` running, RViz showed only the explorer's looping path
and scan points, no map. Nothing was building one: `slam_toolbox` hadn't been started or configured
in this project, so there was no `/map`, and the explorer was in its no-map fallback (head for the
widest gap), which wanders.

Copied from the earlier `tb3_nav2_demo` project into `src/tb3_bot/config/`:
- `slam_toolbox.yaml`: `async_slam_toolbox_node` in mapping mode. Frames `odom`, `map`,
  `base_footprint`; reads `/scan` and `/odom`; `use_sim_time: true`.
- `nav2_params.yaml`: the full Nav2 parameter set (AMCL, planner, controller, costmaps,
  behaviours), based on the earlier AMR project's config with the TurtleBot3 adaptations:
  `base_footprint` everywhere, `robot_radius: 0.11` and `inflation_radius: 0.25` for the Burger.
  Not used until Nav2 is launched on a saved map.
- Removed `config/.gitkeep`.

One change on the way in: the old `slam_toolbox.yaml` read `scan_topic: /scan_slam` with
`max_laser_range: 3.0`. Those depend on `scan_filler`, a node this project doesn't have yet, so with
them SLAM would wait forever for a topic nobody publishes. For now they are `scan_topic: /scan` and
`max_laser_range: 3.5` (the Burger lidar's real range). When `scan_filler` is added they change
back, with the reason.

The config files are read straight from `src/` by the commands below, so no rebuild is needed for
them (they are also installed by `CMakeLists.txt`, as copies).

## Step 10. Explorer tuning and `scan_filler`

Two additions from the earlier project, added to deal with the map looking bad in this arena. The
map after a few minutes showed only the left and bottom walls as occupied cells, wedges of free
space along the beams that hit them, dark gaps between the wedges (some right next to the robot),
none of the 45 blocks, and the explorer's path scribbling in the middle.

Why it happens here: the Burger's lidar reaches 3.5 m, the arena is 30 × 30 m, and the blocks are
about 3-4 m apart, so most beams hit nothing and return `inf`. That causes two problems:
- With so few features in range, SLAM has little to lock onto.
- `slam_toolbox` (Karto) ignores readings at or beyond the sensor's `range_max`, so a beam that hits
  nothing marks no free space either. Unknown patches stay unknown even beside the robot, and the
  explorer treats them as frontiers and keeps hopping between them.

- `config/lidar_explorer.yaml` (explorer parameters for the Burger; the defaults in the `.cpp` were
  tuned for a faster, longer-range lidar): `obstacle_dist` 0.7, `kp_heading` 1.0, `w_max` 0.6,
  `v_max` 0.18, `waypoint_lookahead` 1.5, `min_frontier_cells` 20, `robot_radius` 0.11. Passed with
  `--params-file`, and read only at startup.
- `src/scan_filler.cpp`: republishes `/scan` as `/scan_slam` with every no-return beam (`inf`, NaN or
  at/above `range_max`) set to `range_max - 0.01`. `slam_toolbox.yaml` now reads `/scan_slam` and
  `max_laser_range` is 3.0, so those filled beams count as "free out to 3.0 m, no wall at the end".
  The Nav2 costmaps, RViz and `lidar_explorer` keep using the raw `/scan`.

### The same mistake again: `scan_filler` had no build rule

`src/scan_filler.cpp` was added, but `CMakeLists.txt` had no `add_executable` for it, which is the
`No executable found` mistake from Step 8. Added `add_executable(scan_filler ...)`,
`ament_target_dependencies(scan_filler rclcpp sensor_msgs)` and `install(TARGETS ...)`.

### Where the lidar range lives (it is not in the world file)

The range is a property of the robot, not the world: it's in the Burger's own model,
`turtlebot3_gazebo/models/turtlebot3_burger/model.sdf` inside the Docker image, in the lidar's ray
sensor. What the running simulation reports on `/scan` matches: 360 samples, `range_max` 3.5 m, 5 Hz.
Raising it would mean editing a copy of that model, which makes the robot something other than the
stock Burger, so it is kept as a later option.
