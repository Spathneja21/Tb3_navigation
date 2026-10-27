"""Import the stock TurtleBot3 URDF and publish TF from it, with no Gazebo yet.
Use with RViz (RobotModel + TF displays) to check the model imports correctly before
anything simulates it. joint_state_publisher fakes zero joint states so RobotModel has
something to render without Gazebo driving the wheels.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    model = os.environ.get('TURTLEBOT3_MODEL', 'burger')
    urdf_path = os.path.join(
        get_package_share_directory('turtlebot3_description'), 'urdf', f'turtlebot3_{model}.urdf')
    with open(urdf_path, 'r') as f:
        robot_description = f.read()

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description, 'use_sim_time': False}],
        ),
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            parameters=[{'robot_description': robot_description, 'use_sim_time': False}],
        ),
    ])
