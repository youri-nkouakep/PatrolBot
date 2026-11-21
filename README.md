# PatrolBot: Autonomous Delivery Robot

[![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)](https://docs.ros.org/en/humble/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Classic%2011-orange)](https://classic.gazebosim.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

PatrolBot is an autonomous delivery robot built on **ROS 2 Humble** and **Nav2**, simulated in Gazebo with a TurtleBot3 Waffle Pi. Customers send a mission through a **REST API**. The robot drives to the address, waits for a **delivery code**, then returns to its base. If it gets stuck along the way, it **recovers on its own**.

> Mission flow in one request: `POST /api/mission` → Nav2 navigation → code check at the door → return to base. An 8-state FSM drives the whole flow and recovers from every failure.

---

## Features

| Module | What it does |
| --- | --- |
| Perception | Converts the 360° LiDAR scan into obstacle density over 36 sectors of 10° each |
| AI planner | Ranks candidate destinations with a weighted multi-criteria score (distance, time, obstacles in that direction, risk, energy) |
| Delivery manager | Runs an 8-state FSM on top of Nav2: code timeout, constant-time code check, error recovery |
| Self-recovery | Detects a stuck robot from odometry during a mission, then backs up and spins in place |
| API | Exposes REST endpoints with input validation, plus a WebSocket for live tracking |
| World | Provides a custom urban Gazebo world (roads, houses, vehicles, pedestrians) |

## Architecture

```mermaid
flowchart LR
    U[Client] -- REST / WebSocket --> API[api_server]
    API -- /delivery/new_mission<br/>/delivery/code_submitted --> DM[delivery_manager<br/>8-state FSM]
    DM -- goToPose --> NAV[Nav2<br/>AMCL + planner + DWB]
    NAV -- /cmd_vel --> ROBOT[TurtleBot3<br/>Gazebo]
    ROBOT -- /scan --> PER[obstacle_detector]
    PER -- /obstacle_density --> AI[ai_planner]
    ROBOT -- /odom --> REC[recovery_node]
    DM -- /delivery/status --> REC
    DM -- /delivery/status --> API
    REC -- /cmd_vel --> ROBOT
```

### Delivery state machine

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> NAVIGATING: new mission
    NAVIGATING --> ARRIVED: goal reached
    NAVIGATING --> ERROR: navigation failed
    ARRIVED --> WAITING_CODE
    WAITING_CODE --> VERIFYING: code received
    WAITING_CODE --> RETURNING: timeout (120 s)
    VERIFYING --> DELIVERING: correct code
    VERIFYING --> RETURNING: wrong code
    DELIVERING --> RETURNING
    ERROR --> RETURNING
    RETURNING --> IDLE: back at base
```

---

## Project structure

```text
patrolbot/
├── src/
│   ├── patrolbot_perception/   # LiDAR → obstacle density per sector
│   ├── patrolbot_ai/           # multi-criteria scoring (scoring.py, no ROS dependency)
│   ├── patrolbot_delivery/     # delivery FSM on top of Nav2
│   ├── patrolbot_recovery/     # stuck detection (stuck_detector.py) and maneuvers
│   ├── patrolbot_api/          # FastAPI server (REST + WebSocket)
│   ├── patrolbot_world/        # custom Gazebo worlds
│   ├── patrolbot_bringup/      # full launch file
│   └── gazebo_map_creator/     # submodule: map export from a Gazebo world
└── start_patrolbot.sh          # one-command launch
```

## Installation

```bash
sudo apt install ros-humble-desktop ros-humble-turtlebot3 ros-humble-turtlebot3-simulations \
  ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-slam-toolbox
pip install fastapi uvicorn

git clone --recurse-submodules https://github.com/youri-nkouakep/patrolbot.git
cd patrolbot
colcon build --symlink-install
source install/setup.bash
```

## Launch

First build a map of the world with SLAM Toolbox, then save it to `~/maps/patrolbot_map.yaml`.

```bash
./start_patrolbot.sh                     # or: ./start_patrolbot.sh path/to/map.yaml
```

To launch the custom urban world on its own:

```bash
ros2 launch patrolbot_world delivery_city.launch.py
```

## Send a delivery mission

```bash
curl -X POST http://localhost:5000/api/mission \
  -H "Content-Type: application/json" \
  -d '{"destination_x": 0.5, "destination_y": 0.3, "delivery_code": "1234"}'

curl -X POST http://localhost:5000/api/code \
  -H "Content-Type: application/json" -d '{"code": "1234"}'
```

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/status` | Robot position and FSM state |
| POST | `/api/mission` | Send a mission (`409` if the robot is busy) |
| POST | `/api/code` | Submit the delivery code (`409` if no code is expected) |
| WS | `/ws/tracking` | Live position and state stream at 2 Hz |

Swagger UI: http://localhost:5000/docs

## Tests

The scoring, stuck-detection and mission-parsing logic is kept free of ROS dependencies and covered by unit tests:

```bash
colcon test --packages-select patrolbot_ai patrolbot_recovery patrolbot_delivery
colcon test-result --verbose
```

## Performance

Values measured in simulation:

| Metric | Measured | Requirement |
| --- | --- | --- |
| Perception latency | 0.8 ms | < 100 ms |
| API latency | 15 ms | < 500 ms |
| WebSocket rate | 2 Hz | > 1 Hz |
| Code verification | 8 ms | < 100 ms |

Recovery maneuvers are configured in `stuck_detector.py`: a 0.3 m backup (3.0 s), then a half turn in place (3.1 s).

## Limitations and next steps

- The recovery node publishes on `/cmd_vel` alongside the Nav2 controller. A cleaner design would move these maneuvers into Nav2's behavior tree.
- The AI planner ranks candidate destinations but does not feed Nav2 yet. Next step: plug it into multi-stop missions.
- The robot has only been tested in simulation. Next step: run it on a real TurtleBot3.

---

## Authors

- **Youri Nkouakep** ([@youri-nkouakep](https://github.com/youri-nkouakep))
- **N'faly Sangare**
- **Zakaria Nasr-Allah**

Master IA et Objets Connectés, Université Ibn Tofail (Kénitra). Module: Real-Time Systems, 2025-2026.

## License

MIT, see [LICENSE](LICENSE).
