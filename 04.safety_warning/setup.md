# Safety Warning — ROS2 Humble Demo

A self-contained ROS2 (Humble) workspace that extends the **Manual Control** demo
with an automatic **safety watchdog**: while you drive with the keyboard, the
car stops itself if an obstacle gets too close, and a glowing **red beacon**
appears above the car in the Gazebo GUI (plus an RViz marker). Control returns
automatically a moment after the obstacle clears.

```
04.safety_warning/
└── src/
    ├── ros_car_description/   # Robot model + Gazebo spawn (URDF, launch, world)
    ├── ros_car_msgs/          # Custom messages/services (ament_cmake)
    └── ros_car_teleop/        # Manual control + safety (rclpy)
        ├── launch/ros_car_manual.launch.py      # also starts safety_watchdog
        ├── rviz/custom_manual.rviz               # + WarningMarker display
        ├── models/beacon.sdf                     # warning beacon model
        └── scripts/
            ├── teleop_node.py           # MoveControls/SpeedControls -> /cmd_vel
            ├── keyboard_controls.py     # keyboard -> /teleop_cmd + /set_speed
            └── safety_watchdog.py       # laser watchdog -> stop + beacon
```

## Prerequisites

- Ubuntu 22.04 with **ROS2 Humble** installed
- Packages: `gazebo_ros`, `gazebo_plugins`, `robot_state_publisher`, `xacro`, `rviz2`

```bash
sudo apt install ros-humble-gazebo-ros ros-humble-gazebo-plugins
```

## Build

```bash
cd 04.safety_warning
source /opt/ros/humble/setup.bash
colcon build --packages-select ros_car_msgs ros_car_description ros_car_teleop
source install/setup.bash
```

> Source `install/setup.bash` in every new terminal.

## Run

In **terminal 1** — start the simulation, the teleop node, and the watchdog:

```bash
ros2 launch ros_car_teleop ros_car_manual.launch.py
```

This opens Gazebo Classic (car + 3 cube obstacles) and RViz2. The
`safety_watchdog` starts with the beacon model and these defaults:
`stop_distance=0.5`, `warning_distance=1.0`, `hold_time=1.0`.

In **terminal 2** — start the keyboard driver (after sourcing `install/setup.bash`):

```bash
ros2 run ros_car_teleop keyboard_controls.py
```

Click on the **keyboard_controls terminal** and press keys to drive:

| Key | Action |
|---|---|
| `i` | move forward |
| `,` | move backward |
| `j` | turn left |
| `l` | turn right |
| `k` | stop |
| `w` / `s` | increase / decrease linear speed |
| `a` / `d` | increase / decrease angular speed |
| `q` | quit |

## How it works

```
keyboard_controls -> /teleop_cmd + /set_speed -> teleop_node -> /cmd_vel -> wheels
                                                        ^
                                                        | brake (Twist 0) while close
safety_watchdog <- /scan (+ /odom)  ->  /warning_marker  |   /warning_beacon (Gazebo)
```

| Zone | Dist. | Beacon | Car |
|---|---|---|---|
| Safe | > 1.0 m | none | free |
| Warning | 0.5 – 1.0 m | orange | free |
| Danger | < 0.5 m | red | hard stop |

The beacon is spawned once (a dynamic, gravity-free model so it can be moved),
then kept glued to the car with `/set_entity_state` (from `/odom`) while an
obstacle is within `warning_distance`, and hidden below the ground when clear —
instead of being deleted and respawned, it never "forgets" to come back. After
the obstacle leaves the `stop_distance` zone the watchdog keeps braking for
another `hold_time` (1 s), then control is handed back to the keyboard.

## Verify

In terminal 3 (after sourcing `install/setup.bash`):

```bash
ros2 node list                       # includes safety_watchdog
ros2 topic echo /cmd_vel             # zeros out right before you hit an obstacle
ros2 service list | grep entity      # /spawn_entity /set_entity_state /get_entity_state
```

Drive the car toward a cube: as you get within ~1 m,* the beacon appears
(orange) over the car in Gazebo; under ~0.5 m it turns red and the car stops.
Back away and the beacon disappears and movement resumes.

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| `package 'ros_car_teleop' not found` | `source install/setup.bash` in this terminal |
| Pressing keys does nothing | Focus the `keyboard_controls` terminal, then press a key |
| Beacon never appears | Rebuild the description package (the `gazebo_ros_state` world plugin must be loaded so `/set_entity_state` exists) |
| Stop too late / too early | Change `stop_distance` / `warning_distance` in `ros_car_manual.launch.py` |