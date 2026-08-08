import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    tel_share = get_package_share_directory('ros_car_teleop')
    desc_share = get_package_share_directory('ros_car_description')

    xacro_file = os.path.join(desc_share, 'urdf', 'ros_car.xacro')
    robot_description = {'robot_description': xacro.process_file(xacro_file).toxml()}

    rviz_config = os.path.join(tel_share, 'rviz', 'custom_manual.rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),

        # Static transform so the odom fixed frame exists (no Gazebo here)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_tf_odom_base_link',
            arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link'],
            output='screen'
        ),

        # Publish the URDF + joint TF tree
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[
                robot_description,
                {'use_sim_time': LaunchConfiguration('use_sim_time')}
            ],
            output='screen'
        ),

        # RViz view of the model
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            output='screen'
        ),
    ])