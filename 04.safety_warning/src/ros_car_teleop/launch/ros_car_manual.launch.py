import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    tel_share = get_package_share_directory('ros_car_teleop')
    desc_share = get_package_share_directory('ros_car_description')

    rviz_config = os.path.join(tel_share, 'rviz', 'custom_manual.rviz')
    beacon_model = os.path.join(tel_share, 'models', 'beacon.sdf')

    return LaunchDescription([
        # Gazebo + spawn + robot_state_publisher (RViz handled below)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(desc_share, 'launch', 'gazebo.launch.py')
            ),
            launch_arguments={'use_rviz': 'false'}.items()
        ),

        # Manual control: converts MoveControls/SpeedControls into /cmd_vel
        Node(
            package='ros_car_teleop',
            executable='teleop_node.py',
            name='teleop_node',
            output='screen'
        ),

        # Safety watchdog: hard-stops near obstacles and shows a warning beacon
        Node(
            package='ros_car_teleop',
            executable='safety_watchdog.py',
            name='safety_watchdog',
            output='screen',
            parameters=[{
                'beacon_model_file': beacon_model,
                'stop_distance': 0.5,
                'warning_distance': 1.0,
                'hold_time': 1.0,
            }]
        ),

        # RViz with the manual-control view
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            output='screen'
        ),
    ])