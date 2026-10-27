"""Start Gazebo (Classic, via gazebo_ros) with a world and spawn the TurtleBot3 into it.

The robot's URDF is published by robot_state_publisher (for TF); the robot itself is spawned
into Gazebo from turtlebot3_gazebo's model.sdf, which has the sensor and drive plugins.
The world defaults to the SC7a clutter field (world:=<file> to use another).
gui:=false runs gzserver only (no gzclient window), which is much lighter under software
rendering; use RViz to watch instead.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    model = os.environ.get('TURTLEBOT3_MODEL', 'burger')
    tb3_gazebo_share = get_package_share_directory('turtlebot3_gazebo')
    urdf_path = os.path.join(
        get_package_share_directory('turtlebot3_description'), 'urdf', f'turtlebot3_{model}.urdf')
    with open(urdf_path, 'r') as f:
        robot_description = f.read().replace('${namespace}', '')  # stock URDF placeholder, no namespace here

    world = os.path.join(get_package_share_directory('tb3_bot'), 'models', 'SC7a_clutter_field_low.sdf')

    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true',
                              description='false = gzserver only, no gzclient window'),
        DeclareLaunchArgument('world', default_value=world,
                              description='world file to load (default: the SC7a clutter field)'),
        SetEnvironmentVariable('GAZEBO_MODEL_PATH', os.path.join(tb3_gazebo_share, 'models')),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')),
            launch_arguments={'gui': LaunchConfiguration('gui'),
                              'world': LaunchConfiguration('world')}.items(),
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
        ),
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-entity', 'turtlebot3', '-file',
                       os.path.join(tb3_gazebo_share, 'models', f'turtlebot3_{model}', 'model.sdf'),
                       '-x', '0.0', '-y', '0.0', '-z', '0.01'],
            output='screen',
        ),
    ])
