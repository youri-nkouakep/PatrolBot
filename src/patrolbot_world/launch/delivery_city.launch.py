"""Monde urbain de livraison avec un TurtleBot3 Waffle Pi.

Le plugin gazebo_map_creator (sous-module) permet d'exporter une carte du monde.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

def generate_launch_description():
    world_file = os.path.join(
        get_package_share_directory('patrolbot_world'),
        'worlds', 'delivery_city.world')
    tb3 = get_package_share_directory('turtlebot3_gazebo')
    with open(os.path.join(tb3, 'urdf', 'turtlebot3_waffle_pi.urdf')) as f:
        robot_description = f.read()

    return LaunchDescription([
        ExecuteProcess(
            cmd=['gazebo', '--verbose', world_file,
                 '-s', 'libgazebo_ros_factory.so',
                 '-s', 'libgazebo_ros_init.so',
                 '-s', 'libgazebo_map_creator.so'],
            output='screen'
        ),
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-entity', 'waffle_pi',
                '-file', os.path.join(tb3, 'models', 'turtlebot3_waffle_pi', 'model.sdf'),
                '-x', '0', '-y', '0', '-z', '0.01'
            ],
            output='screen'
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
            output='screen'
        ),
    ])
