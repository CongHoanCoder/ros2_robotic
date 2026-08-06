import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_share = get_package_share_directory('ros_car_description')

    xacro_file = os.path.join(pkg_share, 'urdf', 'ros_car.xacro')
    robot_description_content = xacro.process_file(xacro_file).toxml()
    robot_description = {'robot_description': robot_description_content}

    world_file = os.path.join(pkg_share, 'worlds', 'custom_world.sdf')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use simulation (Gazebo) clock if true'
        ),
        DeclareLaunchArgument(
            'use_rviz', default_value='true',
            description='Open RViz2 automatically if true'
        ),

        # Start Gazebo classic with the ROS2 factory plugin
        ExecuteProcess(
            cmd=['gazebo', '--verbose', '-s', 'libgazebo_ros_factory.so',
                 world_file],
            output='screen'
        ),

        # Publish robot state / TF from the URDF
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[
                robot_description,
                {'use_sim_time': LaunchConfiguration('use_sim_time')}
            ],
            output='screen'
        ),

        # Spawn the robot into Gazebo
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-topic', 'robot_description',
                '-entity', 'ros_car',
                '-x', '0', '-y', '0', '-z', '0.1'
            ],
            output='screen'
        ),

        # RViz2 visualisation
        Node(
            package='rviz2',
            executable='rviz2',
            condition=IfCondition(LaunchConfiguration('use_rviz')),
            output='screen'
        ),
    ])