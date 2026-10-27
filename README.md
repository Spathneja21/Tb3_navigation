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
  -v ~/projects/tb3_assignment:/ros2_ws \
  tb3assign:humble
```
- `--net=host`: ROS 2 discovery is multicast-based, and bridged networks break it. Stop any
  other ROS container first, since both would share one ROS domain.
- `-v ~/projects/tb3_assignment:/ros2_ws`: the project is the colcon workspace, mounted at
  `/ros2_ws` (the path the build commands below use). Mounts can't be changed on an
  existing container; remove it with `docker rm -f tb3assign` and run again.
- `LIBGL_ALWAYS_SOFTWARE=1`: there is no GPU passthrough, so Gazebo and RViz render on the CPU.
- `xhost +local:docker` lets the container draw on your display. It doesn't survive a new
  login, so run it again if a window fails with `No protocol specified`.

Later sessions:
```bash
docker start -ai tb3assign       # to start the container
docker exec -it tb3assign bash   # extra shell in the running container
```

### 3. Build the package

```bash
cd /ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select tb3_bot
```
(`--packages-select`, not `--package-select`.) Launch files and configs are installed
copies, so rebuild after editing them.

### Every shell

Every new shell (each `docker exec`, and any shell open during a build) needs both lines,
ROS first and then the workspace, before any `ros2` command:
```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
```
Without the second line ROS doesn't know about `tb3_bot`: `ros2 pkg prefix tb3_bot` prints
`Package 'tb3_bot' not found`. After a rebuild, shells that are already open pick up the
changes only if they source it again.

## World: SC7a clutter field

The robot runs in `src/tb3_bot/models/SC7a_clutter_field_low.sdf`. It is an SDF **world**
(the arena, with no robot in it), not a URDF. The robot's own description comes from the
TurtleBot3 packages.

![Overview render of the SC7a clutter field: a walled 30 × 30 m arena with 45 scattered blocks](src/tb3_bot/models/render_overview.png)

*Overview render of the world (`src/tb3_bot/models/render_overview.png`): the walled arena
with the 45 blocks.*

### Source

- Collection: [`mertgulerx/world-collection`](https://github.com/mertgulerx/world-collection),
  42 Gazebo worlds for testing robot exploration, navigation and SLAM, built for the
  exploration benchmark of the author's `frontier_exploration_ros2`.
- Announcement:
  [42 Gazebo Harmonic simulation worlds for navigation, exploration and SLAM workflows](https://discourse.openrobotics.org/t/42-gazebo-harmonic-simulation-worlds-for-navigation-exploration-and-slam-workflows/58934)
  (Open Robotics Discourse).
- Licence: Apache-2.0, as stated in the collection's README. The collection also has a
  `CITATION.cff` file with citation details.
- In the collection's naming, **SC** worlds are the single-challenge ones, each targeting one
  difficulty. SC7a is the "clutter field": blocks that hide each other, with SC7b the denser
  version of the same field.

### What the world contains

| Property | Value |
|---|---|
| World name | `sc7a_clutter_field_low` |
| Arena | 30 × 30 m floor, four 2 m tall outer walls |
| Obstacles | 45 static blocks, 1.2 m tall, 0.5–2.0 m wide |
| Minimum gap | 1.0 m between blocks, and 1.0 m between a block and a wall |
| Spawn area | nothing within 1.5 m of the origin, so the robot can start at (0, 0) |
| Geometry | plain boxes only (50 collision elements: ground, 4 walls, 45 blocks), no meshes |
| Generation | `worldgen` 1.0.1, seed 7100, from the file's own header |
| Physics | ODE, 0.01 s step, 200 Hz |

World and map coordinates coincide, because the spawn point is the world's origin.

### Gazebo version

The file targets **Gazebo Harmonic** (SDF 1.9, `gz-sim-*-system` plugins). This project uses
**Gazebo Classic** (ROS 2 Humble with `gazebo_ros`), which is a different simulator. The file
is therefore kept unchanged here as the original, and a Classic-compatible copy is made
when the world is first launched (see `PROCESS.md`). Any modified copy will say so, as the
Apache-2.0 licence requires.

## Robot model: TurtleBot3 Burger

![The TurtleBot3 Burger URDF shown in RViz's RobotModel display](src/tb3_bot/models/robot_model.png)

*The Burger in RViz: two drive wheels, the stacked plates and the lidar on top
(`src/tb3_bot/models/robot_model.png`).*

The robot description is the stock one from the `turtlebot3_description` package (installed
in the image), read at launch time rather than copied into this repository. The
`TURTLEBOT3_MODEL` environment variable picks the model, and the Dockerfile sets it to `burger`.

`launch/rsp.launch.py` publishes the robot's TF tree from that URDF with no simulator running, so
the model can be checked in RViz first.

### View it in RViz

Rebuild first if you edited a launch file (launch files are installed copies):
```bash
cd /ros2_ws
colcon build --packages-select tb3_bot
```

Shell 1, publish the robot description and TF:
```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
ros2 launch tb3_bot rsp.launch.py
```

Shell 2 (`docker exec -it tb3assign bash`), open RViz:
```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
rviz2
```
In RViz: **Add → RobotModel** and set its **Description Topic** to `/robot_description`;
**Add → TF** to see the frames; set the **Fixed Frame** to `base_footprint`, the robot's root frame.

The launch files remove a `${namespace}` placeholder that the stock Humble URDF has in every
link name (ROBOTIS's launch files substitute it). Without that, the frames are literally
named `${namespace}base_scan` and so on, and nothing that uses the plain names (the scan,
RViz) can find them.

## Gazebo: spawn the robot

`launch/gazebo.launch.py` starts Gazebo Classic with the SC7a world, publishes the robot's TF
(from the URDF) and spawns the TurtleBot3 at the origin from `turtlebot3_gazebo`'s `model.sdf`.
The SDF is what carries the plugins that publish `/odom` and `/scan` and drive the wheels; the
URDF has none of them. Stop the `rsp.launch.py` shell first: it publishes
the same robot, and only one of the two should run.

```bash
cd /ros2_ws
colcon build --packages-select tb3_bot
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
ros2 launch tb3_bot gazebo.launch.py gui:=false     # or gui:=true for the Gazebo window
```
By default it loads the SC7a clutter field (see "World" above) and spawns the robot at the
origin. `world:=<file>` loads another world.
`gui:=false` runs the simulation without its window, which is much lighter under software
rendering. Check what the simulation publishes from a second shell (both setup files sourced):
```bash
ros2 topic list
ros2 node list
```

### Watch it in the Gazebo window

With the window on (`gui:=true`, the default) you see the arena and the robot at its origin:
```bash
ros2 launch tb3_bot gazebo.launch.py gui:=true
```
`LIBGL_ALWAYS_SOFTWARE=1` means Gazebo renders on the CPU, so the window can take a minute
to appear and then runs slowly. Give it time before concluding it is stuck. The robot is driven
by `lidar_explorer` (below), not by hand.

## Mapping the arena

The robot explores the arena on its own while `slam_toolbox` builds the map. Four terminals
(`docker exec -it tb3assign bash` for each extra one), each starting with:
```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
```
After building once (`cd /ros2_ws && colcon build --packages-select tb3_bot`):

| Terminal | Command |
|---|---|
| 1. Simulation | `ros2 launch tb3_bot gazebo.launch.py gui:=false` |
| 2. Fill the scan | `ros2 run tb3_bot scan_filler` |
| 3. SLAM | `ros2 run slam_toolbox async_slam_toolbox_node --ros-args --params-file /ros2_ws/src/tb3_bot/config/slam_toolbox_odomonly.yaml` |
| 4. Explorer | `ros2 run tb3_bot lidar_explorer --ros-args --params-file /ros2_ws/src/tb3_bot/config/lidar_explorer.yaml` |
| 5. RViz (optional) | `rviz2` |

Start them in that order, and restart Gazebo (terminal 1) first if the robot isn't at the origin.
In RViz: Fixed Frame `map`; a **Map** display on `/map` with Durability Policy **Transient Local**;
a **Path** display on `/explorer_path` for where the robot has been.

What each piece is for:
- **`scan_filler`** republishes `/scan` as `/scan_slam`, with the beams that hit nothing (`inf`)
  set just under the lidar's 3.5 m range. `slam_toolbox` ignores readings at or beyond the range
  limit, so without this, open space is never marked free and the explorer chases unknown patches
  beside itself.
- **`slam_toolbox_odomonly.yaml`** is the SLAM configuration (frames `odom`, `map`, `base_footprint`,
  scan topic `/scan_slam`, range 3.0 m) with scan matching and loop closure **off**, so the map is
  built from the wheel odometry. In this arena (30 × 30 m, a 3.5 m lidar, blocks 3–4 m apart) there
  are few features in range, and with matching on the map shifted and bent. Gazebo's odometry has
  no noise, so the odometry-only map stays consistent, though it can drift slowly over a long run.
  `slam_toolbox.yaml` is the same file with matching and loop closure on.
- **`lidar_explorer`** drives to the nearest unexplored frontier on the live map. Its parameters
  for the Burger (slower, gentler turns, larger minimum frontier size) are in
  `lidar_explorer.yaml`.

### Why the odometry-only config gives a better map

`slam_toolbox_odomonly.yaml` differs from `slam_toolbox.yaml` in two lines:

| Parameter | `slam_toolbox.yaml` | `slam_toolbox_odomonly.yaml` |
|---|---|---|
| `use_scan_matching` | `true` | `false` |
| `do_loop_closing` | `true` | `false` |

With scan matching on, `slam_toolbox` aligns each new scan with the previous ones and corrects the
robot's pose from the match. In this arena most beams hit nothing within the lidar's range, so a
scan has few features and the best match can be wrong. The pose then jumps, and the map shifts and
bends. With matching off, each scan is placed at the pose the odometry reports. Gazebo's odometry
has no noise, so the placements agree with each other and the map stays consistent. Loop closing
detects revisits by matching scans, so it is turned off with matching. The cost is that nothing
corrects drift during mapping. That isn't measured here, and AMCL corrects the pose during
navigation.

### Result

![The occupancy map built by the explorer: the 45 blocks as dark rectangles on grey, with the robot's path in pink](src/tb3_bot/models/autonomous_map_formation.png)

*Map after one autonomous run (`src/tb3_bot/models/autonomous_map_formation.png`, RViz): the
robot's path (pink, from `/explorer_path`) covers the whole arena, and the blocks show up as filled
rectangles.*

Save it while `slam_toolbox` is still running (the command reads the live `/map` topic):
```bash
ros2 run nav2_map_server map_saver_cli -f /ros2_ws/src/tb3_bot/maps/sc7a_map --ros-args -p save_map_timeout:=10000.0
```
This writes `maps/sc7a_map.pgm` (the image) and `maps/sc7a_map.yaml` (resolution and origin).

Navigation later uses AMCL on the saved map, which corrects the robot's pose from the lidar, so
the navigation pose doesn't inherit any odometry drift from mapping. `config/nav2_params.yaml`
holds the Nav2 and AMCL settings, used in the Nav2 step.
