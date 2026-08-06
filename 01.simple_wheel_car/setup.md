# Simple Wheel Car — Gazebo Demo (ROS2 Humble)

A self-contained ROS2 (Humble) package that spawns a simple 4-wheel robot car
into Gazebo Classic, publishes its laser scan and odometry, and shows it in
RViz2.

```
01.simple_wheel_car/
└── src/
    └── ros_car_description/      # ROS2 package (ament_cmake)
        ├── CMakeLists.txt
        ├── package.xml
        ├── urdf/ros_car.xacro    # Robot model + Gazebo plugins
        ├── launch/gazebo.launch.py
        └── worlds/custom_world.sdf
```

## Prerequisites

- Ubuntu 22.04 with **ROS2 Humble** installed
- ROS2 packages: `gazebo_ros`, `gazebo_plugins`, `robot_state_publisher`,
  `xacro`, `rviz2`, `teleop_twist_keyboard` (optional, for driving)

Install missing packages if needed:

```bash
sudo apt install ros-humble-gazebo-ros ros-humble-gazebo-plugins \
                 ros-humble-xacro ros-humble-teleop-twist-keyboard
```

## Setup

```bash
source /opt/ros/humble/setup.bash
```

## Build

```bash
cd 01.simple_wheel_car
colcon build --packages-select ros_car_description
source install/setup.bash
```

> The first `colcon build` creates `build/`, `install/` and `log/` folders.
> Re-run `source install/setup.bash` in every new terminal after building.

## Run

```bash
ros2 launch ros_car_description gazebo.launch.py
```

This opens:

1. **Gazebo Classic** — the car spawns at the origin; red/blue/green cube
   obstacles are placed in the world.
2. **RViz2** — an empty view opens. To see the car:
   - Set **Fixed Frame** to `base_link` (or `odom`).
   - *Add → RobotModel* (uses `/robot_description`) to show the car.
   - *Add → LaserScan* with topic `/scan` to see the 360° laser.

## Verify & Drive

In another terminal (after `source /opt/ros/humble/setup.bash && source install/setup.bash`):

```bash
# Active topics
ros2 topic list

# Should show: /cmd_vel, /odom, /scan, /robot_description, ...
ros2 topic hz /scan

# Drive the car (select the terminal, then use arrow keys / i, j, k, l, ,)
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Pressing the arrow keys sends `geometry_msgs/Twist` to `/cmd_vel`, which the
`gazebo_ros_diff_drive` plugin converts into wheel motion. Odometry is
published on `/odom` and TF on `odom → base_link`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `package 'ros_car_description' not found` | Run `source install/setup.bash` in this terminal |
| Gazebo plugin `libgazebo_ros_*.so` not found | Install `ros-humble-gazebo-ros` and `ros-humble-gazebo-plugins` |
| RViz2 shows nothing / "no transform" | Set Fixed Frame to `base_link` or `odom` and check TF |
| Car falls through the ground | Re-launch; the car is spawned at `z = 0.1` above the ground plane |

## Model Summary

| Link | Description |
|---|---|
| `base_link` | Grey chassis box (0.4 × 0.2 × 0.05 m) |
| `laser_link` | 360° ray sensor (LaserScan, 20 Hz, 2 m range) |
| `wheel_left` / `wheel_right` | Driven wheels (`continuous` joints) |
| `caster_wheel` | Passive sphere at the rear |

- **cmd_vel → wheels:** `gazebo_ros_diff_drive` plugin
- **Laser:** `gazebo_ros_ray_sensor` plugin publishing `sensor_msgs/LaserScan`
- **TF:** `robot_state_publisher` (static) + diff-drive odom TF
