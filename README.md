# tools

Simulation, logging, replay, CSV export, plotting, and visualization for Hippocampus.

The source folder, ROS package, and Python module are all named `tools`. This
keeps the repo naming consistent with role-based packages such as `hardware`.

## Vehicle Names

- `uuv02`: real Hippocampus robot
- `uuv00`: simulated Hippocampus robot

## Record

```bash
ros2 launch tools record.launch.py \
  vehicle_name:=uuv02 \
  scenario:=tank_depth_step \
  profile:=control \
  use_sim_time:=false
```

```bash
ros2 launch tools record.launch.py \
  vehicle_name:=uuv00 \
  scenario:=path_following \
  profile:=sim \
  use_sim_time:=true
```

Runs are written below `data/runs` by default:

```text
data/runs/<timestamp>_<vehicle>_<source>_<scenario>/
  manifest.yaml
  bag/
  csv/
  plots/
  notes.md
```

## Replay

```bash
ros2 launch tools replay.launch.py bag:=data/runs/<run_id>/bag
```

## Export and Plot

```bash
ros2 run tools export_csv --run data/runs/<run_id>
ros2 run tools plot_depth --run data/runs/<run_id>
ros2 run tools plot_navigation --run data/runs/<run_id>
```

Topic profiles may also define a `fields` map. The rosbag always keeps complete
messages; the field selection is applied only during CSV export. The
`thruster_loadcell` profile uses this to export ESC 1 command, battery voltage,
and calibrated wrench values.

## Simulation

`sim.launch.py` starts Gazebo, spawns `uuv00`, and publishes the model and TF
helpers. Simulation time is always enabled. Select a viewer:

```bash
ros2 launch tools sim.launch.py visualization:=rviz
ros2 launch tools sim.launch.py visualization:=foxglove
ros2 launch tools sim.launch.py visualization:=none
```

Run only one of these commands. Gazebo's GUI is disabled by default; add
`start_gazebo_gui:=true` to enable it. Use `visualization:=none` if your Foxglove
bridge or RViz is already running. `visualization:=foxglove` starts the bridge,
not the Foxglove desktop app.

Viewer arguments can be passed through, for example `port:=8766` for Foxglove
or `rviz_config:=simple` for RViz. Camera, modem, AprilTag, and world options
remain available through `--show-args`.

## Standalone Visualization

Neither viewer launcher starts a simulation or robot hardware. Both accept
`vehicle_name:=uuv00` (default, simulation time) or `vehicle_name:=uuv02`
(wall time). `use_sim_time` can be overridden for playback.

Connect to an experiment on the real Hippo:

```bash
ros2 launch tools rviz.launch.py vehicle_name:=uuv02
ros2 launch tools foxglove.launch.py vehicle_name:=uuv02
```

Connect to a simulation started with `sim.launch.py`:

```bash
ros2 launch tools rviz.launch.py vehicle_name:=uuv00 publish_models:=false
ros2 launch tools foxglove.launch.py vehicle_name:=uuv00 publish_models:=false
```

The standalone launchers publish model descriptions and TF helpers by default.
Set `publish_models:=false` when these are already provided by the simulation,
another viewer launcher, or the robot. With model publishing enabled,
`publish_joint_states:=false` disables the zero-position thruster joint helper,
and `publish_pool_model:=false` disables the pool model and its static TF.

Connect the Foxglove app to `ws://localhost:8765`, or use the robot IP address
when connecting from another machine. The bridge accepts `port` and `address`
arguments and filters vehicle topics using `vehicle_name`. Shared `/tf`,
`/tf_static`, `/clock`, `/rosout`, and `/pool/*` topics remain available. Topic
names are not aliased, so select the matching `uuv00` or `uuv02` Foxglove layout
when switching between simulation and the real robot.

### Occupancy grid

The Foxglove launcher also starts `hippo_maps`' `occupancy_grid_bridge`. It
converts the bytewise `/occupancy_grid_3d` message into Foxglove's native
`foxglove_msgs/msg/VoxelGrid` on `/pool/voxel_grid`, with transparent free and
unknown cells. Occupied voxels are red by default; edit
`hippo_maps/config/voxel_colors.yaml` to change the display colors.
Publish a saved map in another terminal:

```bash
ros2 launch tools foxglove.launch.py vehicle_name:=uuv02 publish_models:=false
ros2 run hippo_maps generate_occupancy_grid \
  --load data/maps/pool_01.npz --publish
```

In Foxglove, enable `/pool/voxel_grid` in the 3D panel and select
**RGBA (separate fields)**. The map publisher and bridge use transient-local QoS, so late subscribers can
receive the latest map.

For a movable local 3D view without ROS or Foxglove, run:

```bash
ros2 run hippo_maps view_occupancy_grid data/maps/pool_01.npz
```

Drag with the mouse to rotate and use the toolbar to zoom. The viewer shows
occupied cells by default; `--show-unknown` adds unknown cells.
`--max-points` limits dense maps for responsive rotation.

Replay a bag and open RViz with one command (also supported by `foxglove.launch.py`):

```bash
ros2 launch tools rviz.launch.py \
  bag:=data/runs/<run_id>/bag \
  vehicle_name:=uuv02 \
  use_sim_time:=true
```

Simulation startup has moved from `rviz.launch.py launch_sim:=true` to
`sim.launch.py`. The old `launch_rviz` and `launch_foxglove` switches are replaced
by `visualization` on the simulation launcher.
