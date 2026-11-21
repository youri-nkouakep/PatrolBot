"""Lancement complet : Gazebo + Nav2 + les 5 nœuds PatrolBot.

Exemple :
    ros2 launch patrolbot_bringup patrolbot_full.launch.py map:=$HOME/maps/patrolbot_map.yaml
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            SetEnvironmentVariable, TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

NODES = [
    ('patrolbot_perception', 'obstacle_detector'),
    ('patrolbot_ai', 'ai_planner'),
    ('patrolbot_recovery', 'recovery_node'),
    ('patrolbot_delivery', 'delivery_manager'),
    ('patrolbot_api', 'api_server'),
]


def generate_launch_description():
    tb3_gazebo = get_package_share_directory('turtlebot3_gazebo')
    tb3_nav = get_package_share_directory('turtlebot3_navigation2')
    map_file = LaunchConfiguration('map')

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=os.path.join(os.path.expanduser('~'), 'maps', 'patrolbot_map.yaml'),
            description='Carte (.yaml) générée avec SLAM Toolbox'),
        SetEnvironmentVariable('TURTLEBOT3_MODEL', 'waffle_pi'),

        # 1. Simulation Gazebo
        IncludeLaunchDescription(PythonLaunchDescriptionSource(
            os.path.join(tb3_gazebo, 'launch', 'turtlebot3_world.launch.py'))),

        # 2. Nav2 (AMCL + planificateur + contrôleur) et RViz, après le démarrage de Gazebo
        TimerAction(period=5.0, actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(tb3_nav, 'launch', 'navigation2.launch.py')),
                launch_arguments={'map': map_file, 'use_sim_time': 'True'}.items()),
        ]),

        # 3. Nœuds PatrolBot, une fois Nav2 lancé
        TimerAction(period=15.0, actions=[
            Node(package=pkg, executable=exe, name=exe, output='screen',
                 parameters=[{'use_sim_time': True}])
            for pkg, exe in NODES
        ]),
    ])
