import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    cmd_share = get_package_share_directory('ros_car_cmd')
    desc_share = get_package_share_directory('ros_car_description')

    config_dir = os.path.join(cmd_share, 'config')
    rviz_config = os.path.join(cmd_share, 'rviz', 'custom_autonomous.rviz')

    return LaunchDescription([
        # Gazebo + spawn + robot_state_publisher (no RViz here, we launch our own)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(desc_share, 'launch', 'gazebo.launch.py')
            ),
            launch_arguments={'use_rviz': 'false'}.items()
        ),

        # Startup Waypoint Manager
        Node(
            package='ros_car_cmd',
            executable='waypoint_manager.py',
            name='waypoint_manager',
            parameters=[{'config_dir': config_dir}],
            output='screen'
        ),

        # Startup Waypoint Navigator
        Node(
            package='ros_car_cmd',
            executable='waypoint_navigator.py',
            name='waypoint_navigator',
            parameters=[{'config_dir': config_dir}],
            output='screen'
        ),

        # Startup Waypoint Visualizer
        Node(
            package='ros_car_cmd',
            executable='waypoint_visualizer.py',
            name='waypoint_visualizer',
            parameters=[{'config_dir': config_dir}],
            output='screen'
        ),

        # Startup RViz with the custom waypoint view
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            output='screen'
        ),
    ])