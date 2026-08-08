# 🤖 ros2_robotic

> A hands-on ROS2 (Humble) learning repo to build a **manual & autonomous control car**, step by step.

Learn how to spawn a 2-wheel robot car in **Gazebo Classic** and control it — first with the keyboard, then autonomously with a PID heading controller, while adding safety and vision along the way. Every example is **self-contained** and comes with its own `setup.md` guide.

![img](https://img.shields.io/badge/ROS2-Humble-red)

## 📚 What you will learn

| Demo | Topic |
|---|---|
| 🚗 [01. simple_wheel_car](01.simple_wheel_car/setup.md) | Spawn a car in Gazebo, laser scan, odometry, RViz2, manual drive |
| 🧠 [02. autonomous_navigation](02.autonomous_navigation/setup.md) | Random waypoints, PID heading controller, obstacle avoidance |
| ⌨️ [03. manual_control](03.manual_control/setup.md) | Drive the car yourself with a custom keyboard teleop pipeline |
| ⚠️ [04. safety_warning](04.safety_warning/setup.md) | Automatic obstacle watchdog + warning beacon on the car |
| 📷 [05. camera_view](05.camera_view/setup.md) | Onboard camera with a live image feed while driving |

## 🚀 Quick start

### 1. Prerequisites

- **Ubuntu 22.04** with **ROS2 Humble** installed
- Basic ROS2 packages (install missing ones if needed):

```bash
sudo apt install ros-humble-gazebo-ros ros-humble-gazebo-plugins \
                 ros-humble-robot-state-publisher ros-humble-xacro \
                 ros-humble-rviz2 ros-humble-rqt-image-view
```

### 2. Build a module

Each demo is its own workspace. For example, to try **Manual Control**:

```bash
cd 03.manual_control
source /opt/ros/humble/setup.bash
colcon build --packages-select ros_car_msgs ros_car_description ros_car_teleop
source install/setup.bash
```

> ℹ️ The first `colcon build` creates `build/`, `install/` and `log/`. Re-run `source install/setup.bash` in **every new terminal**.

### 3. Run it

```bash
# Terminal 1 — launch sim + teleop node
ros2 launch ros_car_teleop ros_car_manual.launch.py

# Terminal 2 — start the keyboard driver
ros2 run ros_car_teleop keyboard_controls.py
```

Click the **keyboard terminal** and drive with `i` (forward), `j`/`l` (turn), `k` (stop), `q` (quit).

## 🗺️ Suggested learning path

Each folder builds on the previous one. We recommended to follow them in order:

1. **01.simple_wheel_car** → get the car on wheels, and learn topics + TF + RViz.
2. **02.autonomous_navigation** → let the car decide its own path (waypoints + PID + wall-following).
3. **03.manual_control** → take back control with your own keyboard teleop nodes.
4. **04.safety_warning** → teach the car to protect itself (watchdog + beacon).
5. **05.camera_view** → give the car "eyes" and watch the live feed.

## 💡 Commands cheat-sheet

```bash
ros2 launch <pkg> <launch_file>   # start demo (see each setup.md)
ros2 topic list                   # active topics (/cmd_vel, /odom, /scan, ...)
ros2 topic hz /scan               # publishing rate check
ros2 topic echo /cmd_vel          # inspect a message as you drive
ros2 node list                    # running nodes
ros2 run teleop_twist_keyboard teleop_twist_keyboard   # alternative generic driver (module 01)
```

## 🔧 Common pitfalls

| Symptom | Fix |
|---|---|
| `package '...' not found` | Run `source install/setup.bash` in this terminal |
| RViz shows nothing / no laser | Set **Fixed Frame** to `odom` (or `base_link`) |
| Keys do nothing while driving | Focus the `keyboard_controls` terminal before pressing a key |
| `/scan` not published yet | Rebuild `colcon build` — the xacro remaps `~/out:=scan` |

## 📚 Docs

Every folder has its own **`setup.md`** with full prerequisites, build/run commands, verification steps and troubleshooting — start there for the deep dive.

---

*Built with ROS2 Humble • Gazebo Classic • RViz2*