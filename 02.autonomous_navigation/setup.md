# Autonomous Navigation — ROS2 Humble Demo

A self-contained ROS2 (Humble) workspace that drives the simple wheel car
**autonomously**: it generates random waypoints, navigates to them with a PID
heading controller, and uses wall-following to avoid obstacles — all visible in
Gazebo Classic and RViz2.

```
02.autonomous_navigation/
└── src/
    ├── ros_car_description/   # Robot model + Gazebo spawn (URDF, launch, world)
    ├── ros_car_msgs/          # Custom messages/services (ament_cmake)
    │   ├── msg/MoveControls.msg  msg/SpeedControls.msg
    │   └── srv/ResetPose.srv     srv/WaypointService.srv
    └── ros_car_cmd/           # Autonomous behaviour (rclpy)
        ├── config/            # car_params.yaml, world_bounds.yaml, secret_key.yaml
        ├── launch/ros_car_autonomous.launch.py
        ├── rviz/custom_autonomous.rviz
        └── scripts/           # waypoint_manager, waypoint_navigator, waypoint_visualizer
```

## Prerequisites

- Ubuntu 22.04 with **ROS2 Humble** installed
- Packages: `gazebo_ros`, `gazebo_plugins`, `robot_state_publisher`, `xacro`,
  `rviz2` (and `python3-yaml`, bundled with rclpy)

```bash
sudo apt install ros-humble-gazebo-ros ros-humble-gazebo-plugins
```

## Build

```bash
cd 02.autonomous_navigation
source /opt/ros/humble/setup.bash
colcon build --packages-select ros_car_msgs ros_car_description ros_car_cmd
source install/setup.bash
```

> Source `install/setup.bash` in every new terminal.

## Run

```bash
ros2 launch ros_car_cmd ros_car_autonomous.launch.py
```

This starts: Gazebo Classic (car + 3 cube obstacles) → `robot_state_publisher`
→ spawn the car → `waypoint_manager` / `waypoint_navigator` /
`waypoint_visualizer` → RViz2 with the waypoint view.

In RViz2 (fixed frame `odom`), the waypoint markers are:
blue = current, red = next, yellow = last.

## How it works

| Node | Role |
|---|---|
| `waypoint_manager` | Serves `/waypoint_request`; returns and rotates random waypoints inside `world_bounds` |
| `waypoint_navigator` | Subscribes `/odom`+`/scan`, PID-heading toward the current waypoint, wall-following on obstacle, publishes `/cmd_vel` at 10 Hz |
| `waypoint_visualizer` | Polls the manager and publishes `/visualization_marker` spheres |

## Verify

In a second terminal (after sourcing `install/setup.bash`):

```bash
ros2 node list                       # waypoint_manager, waypoint_navigator, waypoint_visualizer
ros2 service list | grep waypoint_request
ros2 topic hz /scan                  # one topic at a time
ros2 topic hz /odom
ros2 topic echo /cmd_vel             # non-zero once the car starts moving
```

The car should rotate toward the blue current waypoint, then drive around the
world while avoiding the red/blue/green cubes.

## Config

Tune behaviour in `src/ros_car_cmd/config/`:

- `car_params.yaml` — linear/angular speed, PID gains, obstacle threshold, wall-follow distance, `front_angle_width` (degrees).
- `world_bounds.yaml` — initial waypoints, arrival threshold, world x/y limits.
- `secret_key.yaml` — shared key required by the `/waypoint_request` service.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `package 'ros_car_cmd' not found` | `source install/setup.bash` in this terminal |
| `/scan` shows `does not appear to be published yet` | Rebuild (`colcon build`) — the xacro remaps `~/out:=scan` |
| Car not moving, only rotating | Normal early on — it aligns to the heading before driving |
| RViz shows no laser/markers | Set Fixed Frame to `odom` |
