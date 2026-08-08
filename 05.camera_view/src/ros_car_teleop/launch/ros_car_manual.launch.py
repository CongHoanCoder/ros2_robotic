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

        # RViz with the manual-control view
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),

        # Live camera feed (small window; drag it into a screen corner)
        Node(
            package='rqt_image_view',
            executable='rqt_image_view',
            name='camera_view',
            arguments=['/camera/image_raw'],
            output='screen'
        ),
    ])