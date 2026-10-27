"""Start Gazebo (Classic, via gazebo_ros) and spawn the TurtleBot3 into it.

The robot's URDF is published by robot_state_publisher (for TF) and spawned into Gazebo
from the /robot_description topic. gui:=false runs gzserver only (no gzclient window),
which is much lighter under software rendering; use RViz to watch instead.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    model = os.environ.get('TURTLEBOT3_MODEL', 'burger')
    urdf_path = os.path.join(
        get_package_share_directory('turtlebot3_description'), 'urdf', f'turtlebot3_{model}.urdf')
    with open(urdf_path, 'r') as f:
        robot_description = f.read()

    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true',
                              description='false = gzserver only, no gzclient window'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')),
            launch_arguments={'gui': LaunchConfiguration('gui')}.items(),
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
        ),
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-entity', 'turtlebot3', '-topic', 'robot_description',
                       '-x', '0.0', '-y', '0.0', '-z', '0.01'],
            output='screen',
        ),
    ])
