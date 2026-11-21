#!/usr/bin/env python3
"""Sélection de destination multicritère : choisit la meilleure destination candidate.

Le score combine distance, temps, densité d'obstacles dans la direction de la
destination, risque et énergie (voir scoring.py).
"""
import math

from geometry_msgs.msg import PoseWithCovarianceStamped
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String

from patrolbot_ai.scoring import best_destination


def yaw_from_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class AIPlanner(Node):

    def __init__(self):
        super().__init__('ai_planner')
        self.declare_parameter('w_distance', 0.25)
        self.declare_parameter('w_time', 0.20)
        self.declare_parameter('w_obstacles', 0.35)
        self.declare_parameter('w_risk', 0.15)
        self.declare_parameter('w_energy', 0.05)
        # Angle (repère robot) du premier rayon LiDAR : 0 rad pour le LDS du TurtleBot3
        self.declare_parameter('scan_angle_min', 0.0)
        # Destinations candidates [x1, y1, x2, y2, ...] dans le repère map
        self.declare_parameter('candidates', [0.5, 0.3, 1.0, 0.5, -0.5, 0.8, 1.5, -0.5])

        self.obstacle_density = []
        self.robot_pose = (0.0, 0.0, 0.0)

        self.create_subscription(Float32MultiArray, '/obstacle_density', self.density_cb, 10)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.pose_cb, 10)
        self.score_pub = self.create_publisher(String, '/ai_planner/score', 10)
        self.create_timer(1.0, self.publish_best)

        self.get_logger().info('AI Planner démarré')

    def density_cb(self, msg):
        self.obstacle_density = list(msg.data)

    def pose_cb(self, msg):
        p = msg.pose.pose
        self.robot_pose = (p.position.x, p.position.y, yaw_from_quaternion(p.orientation))

    def weights(self):
        return {k: self.get_parameter('w_' + k).value
                for k in ('distance', 'time', 'obstacles', 'risk', 'energy')}

    def candidates(self):
        flat = list(self.get_parameter('candidates').value)
        return [(flat[i], flat[i + 1]) for i in range(0, len(flat) - 1, 2)]

    def publish_best(self):
        candidates = self.candidates()
        if not candidates:
            return
        dest, score = best_destination(
            self.robot_pose, candidates, self.obstacle_density,
            self.weights(), self.get_parameter('scan_angle_min').value)
        msg = String()
        msg.data = f'best={dest[0]:.2f},{dest[1]:.2f} score={score:.4f}'
        self.score_pub.publish(msg)
        self.get_logger().debug(msg.data)


def main(args=None):
    rclpy.init(args=args)
    node = AIPlanner()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
