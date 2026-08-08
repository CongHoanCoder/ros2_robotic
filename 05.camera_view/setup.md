# Camera View — ROS2 Humble Demo

A self-contained ROS2 (Humble) workspace that adds an **onboard camera** to the
car and shows the **live camera feed** in a small window while you drive with
the keyboard. Based on `03.manual_control`.

```
05.camera_view/
└── src/
    ├── ros_car_description/   # Car model + camera (URDF/xacro, launch, world)
    ├── ros_car_msgs/          # Custom messages/services (ament_cmake)
    └── ros_car_teleop/        # Manual control + camera viewer (rclpy + rqt)
        ├── launch/ros_car_manual.launch.py   # also opens the camera view
        ├── rviz/custom_manual.rviz
        └── scripts/
            ├── teleop_node.py        # MoveControls/SpeedControls -> /cmd_vel
            └── keyboard_controls.py  # keyboard -> /teleop_cmd + /set_speed
```

The camera is added in `ros_car_description/urdf/ros_car.xacro`:
- a `camera_link` fixed to the front of `base_link`,
- a `<sensor type="camera" name="camera">` running `libgazebo_ros_camera.so`,
  publishing on `/camera/image_raw` + `/camera/camera_info` (640x480, 10 Hz).

## Prerequisites

- Ubuntu 22.04 with **ROS2 Humble** installed
- Packages: `gazebo_ros`, `gazebo_plugins`, `robot_state_publisher`, `xacro`,
  `rviz2`, `rqt_image_view`

```bash
sudo apt install ros-humble-gazebo-ros ros-humble-gazebo-plugins \
                 ros-humble-rqt-image-view
```

## Build

```bash
cd 05.camera_view
source /opt/ros/humble/setup.bash
colcon build --packages-select ros_car_msgs ros_car_description ros_car_teleop
source install/setup.bash
```

> Source `install/setup.bash` in every new terminal.

## Run

In **terminal 1** — start the simulation, the teleop node, and the camera view:

```bash
ros2 launch ros_car_teleop ros_car_manual.launch.py
```

This opens Gazebo Classic (car + 3 cubes), RViz2, and a small **rqt_image_view**
window showing the live camera feed. Drag that window into a corner of your
screen next to Gazebo.

In **terminal 2** — start the keyboard driver (after sourcing `install/setup.bash`):

```bash
ros2 run ros_car_teleop keyboard_controls.py
```

Click the **keyboard_controls terminal** and press keys to drive; watch the
live image change as the car moves toward/away from the coloured obstacles:

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
camera sensor (on camera_link)
   --libgazebo_ros_camera.so-->  /camera/image_raw   -->  rqt_image_view (live window)

keyboard_controls -> /teleop_cmd + /set_speed -> teleop_node -> /cmd_vel -> wheels
```

| Topic | Message | Content |
|---|---|---|
| `/camera/image_raw` | `sensor_msgs/Image` | 640x480 RGB, ~10 Hz |
| `/camera/camera_info` | `sensor_msgs/CameraInfo` | intrinsic camera calibration |

`rqt_image_view` is launched by `ros_car_manual.launch.py` with `/camera/image_raw`
as its topic argument.

> **Note on "corner of Gazebo":** Gazebo Classic does not draw ROS image topics
> inside its own window. The camera feed shows in the small **`rqt_image_view`**
> window, which you can position at the corner of the screen beside Gazebo.

## Verify

In terminal 3 (after sourcing `install/setup.bash`):

```bash
ros2 topic list                     # shows /camera/image_raw and /camera/camera_info
ros2 topic hz /camera/image_raw     # ~10 Hz while driving
ros2 topic echo /camera/camera_info --once
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `package 'ros_car_teleop' not found` | `source install/setup.bash` in this terminal |
| Pressing keys does nothing | Focus the `keyboard_controls` terminal, then press a key |
| No image in the view | Set the topic to `/camera/image_raw` in the `rqt_image_view` dropdown |
| Camera image is black/stalled | Confirm `/camera/image_raw` is publishing (`ros2 topic hz`); the sensor needs rendering (software OGRE works headless) |
| `/camera/image_raw` topic missing | The `libgazebo_ros_camera.so` plugin must be loadable — reinstall `gazebo_plugins` if it's absent |