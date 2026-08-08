# Manual Control — ROS2 Humble Demo

A self-contained ROS2 (Humble) workspace where you **drive the car yourself**.
The car model spawns in Gazebo Classic and you control it with the keyboard via
a two-node teleoperation pipeline that uses the project's custom messages
(`MoveControls` / `SpeedControls`).

```
03.manual_control/
└── src/
    ├── ros_car_description/   # Robot model + Gazebo spawn (URDF, launch, world)
    ├── ros_car_msgs/          # Custom messages/services (ament_cmake)
    │   ├── msg/MoveControls.msg   msg/SpeedControls.msg
    │   └── srv/ResetPose.srv      srv/WaypointService.srv
    └── ros_car_teleop/        # Manual control (rclpy)
        ├── launch/ros_car_manual.launch.py
        ├── rviz/custom_manual.rviz
        └── scripts/
            ├── teleop_node.py        # MoveControls/SpeedControls -> /cmd_vel
            └── keyboard_controls.py  # keyboard -> /teleop_cmd + /set_speed
```

## Prerequisites

- Ubuntu 22.04 with **ROS2 Humble** installed
- Packages: `gazebo_ros`, `gazebo_plugins`, `robot_state_publisher`, `xacro`, `rviz2`

```bash
sudo apt install ros-humble-gazebo-ros ros-humble-gazebo-plugins
```

## Build

```bash
cd 03.manual_control
source /opt/ros/humble/setup.bash
colcon build --packages-select ros_car_msgs ros_car_description ros_car_teleop
source install/setup.bash
```

> Source `install/setup.bash` in every new terminal.

## Run

In **terminal 1** — start the simulation and the teleop node:

```bash
ros2 launch ros_car_teleop ros_car_manual.launch.py
```

This opens Gazebo Classic (car + 3 cube obstacles) and RViz2 (fixed frame
`odom`, Grid, LaserScan, RobotModel). The `teleop_node` is running and ready to
convert your commands into wheel motion.

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

> `keyboard_controls.py` reads raw terminal input, so the terminal must be
> focused. The car only moves while you hold/invoke a movement key — release
> or press `k` to stop (a final STOP is sent automatically when you quit).

## How it works

```
keyboard_controls  --MoveControls-->  /teleop_cmd \
                                              \-->  teleop_node  --Twist-->  /cmd_vel --> wheels
keyboard_controls  --SpeedControls--> /set_speed /
```

| Component | Role |
|---|---|
| `keyboard_controls` | Reads keys, publishes `MoveControls` on `/teleop_cmd` and speed changes on `/set_speed` |
| `teleop_node` | Converts movement/speed commands into `Twist` and publishes `/cmd_vel` |
| diff_drive plugin | Applies `/cmd_vel` to the wheels; publishes `/odom` and TF |

## Verify

In a third terminal (after sourcing `install/setup.bash`):

```bash
ros2 node list                       # teleop_node, keyboard_controls, robot_state_publisher,...             
ros2 topic list                      # /teleop_cmd, /set_speed, /cmd_vel, /scan, /odom
ros2 topic echo /cmd_vel             # shows Twist while you press i/j/k/l/, 
```

Press `i`: you should see `/cmd_vel` with a positive `linear.x` and the car
drive forward in Gazebo. The laser scan appears in RViz2.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `package 'ros_car_teleop' not found` | `source install/setup.bash` in this terminal |
| Pressing keys does nothing | Focus the `keyboard_controls` terminal (not the launch terminal), then press a key |
| Car drives only when key held | Expected — press `i` again to move, `k` to stop |
| No laser in RViz | Set Fixed Frame to `odom`, or rebuild (xacro remaps `~/out:=scan`) |