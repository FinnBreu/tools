# tools

Run, logging, replay, CSV export, plotting, and RViz helpers for Hippocampus.

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

## Foxglove

Start the Foxglove bridge:

```bash
ros2 launch tools foxglove.launch.py
```

Then connect Foxglove to `ws://localhost:8765`, or use the robot IP address
when connecting from another machine.

## Export and Plot

```bash
ros2 run tools export_csv --run data/runs/<run_id>
ros2 run tools plot_depth --run data/runs/<run_id>
ros2 run tools plot_navigation --run data/runs/<run_id>
```

## RViz and Simulation

Open RViz against an already running real robot:

```bash
ros2 launch tools rviz.launch.py \
  vehicle_name:=uuv02 \
  use_sim_time:=false
```

Open RViz against an already running simulation:

```bash
ros2 launch tools rviz.launch.py \
  vehicle_name:=uuv00 \
  use_sim_time:=true
```

Start the simulation environment and RViz:

```bash
ros2 launch tools rviz.launch.py launch_sim:=true
```

Open the richer environment RViz view without starting Gazebo:

```bash
ros2 launch tools rviz.launch.py \
  vehicle_name:=uuv02 \
  use_sim_time:=false
```

Replay a bag and open RViz with one command:

```bash
ros2 launch tools rviz.launch.py \
  bag:=data/runs/<run_id>/bag \
  vehicle_name:=uuv02 \
  use_sim_time:=true
```
