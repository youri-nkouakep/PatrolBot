#!/bin/bash
# Lance toute la simulation PatrolBot (Gazebo, Nav2 et les 5 nœuds).
# Usage : ./start_patrolbot.sh [chemin/vers/carte.yaml]
set -e
source /opt/ros/humble/setup.bash
source "$(dirname "$0")/install/setup.bash"
MAP="${1:-$HOME/maps/patrolbot_map.yaml}"
ros2 launch patrolbot_bringup patrolbot_full.launch.py map:="$MAP"
