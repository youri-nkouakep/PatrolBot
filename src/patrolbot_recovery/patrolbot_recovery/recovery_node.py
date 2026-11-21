#!/usr/bin/env python3
"""Auto-récupération : détecte un blocage pendant une mission et lance une manœuvre.

Le blocage est mesuré sur l'odométrie (le robot n'avance plus alors qu'une
mission est en cours), et non sur /cmd_vel. Les manœuvres sont exécutées pas à
pas par un timer, sans bloquer l'exécuteur ROS.
"""
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from patrolbot_recovery.stuck_detector import RECOVERY_SEQUENCE, StuckDetector


class RecoveryNode(Node):

    def __init__(self):
        super().__init__('recovery_node')
        self.declare_parameter('stuck_window', 5.0)
        self.declare_parameter('min_progress', 0.05)
        self.detector = StuckDetector(
            self.get_parameter('stuck_window').value,
            self.get_parameter('min_progress').value)

        self.mission_state = 'IDLE'
        self.attempt = 0          # indice de la prochaine manœuvre
        self.maneuver = None      # (nom, v, w, fin) de la manœuvre en cours

        self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.create_subscription(String, '/delivery/status', self.delivery_status_cb, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/recovery/status', 10)
        self.create_timer(0.1, self.step)

        self.get_logger().info('Recovery Node démarré')

    def now(self):
        return self.get_clock().now().nanoseconds / 1e9

    def delivery_status_cb(self, msg):
        self.mission_state = msg.data.replace('STATE:', '')
        if self.mission_state == 'IDLE':
            self.attempt = 0

    def odom_cb(self, msg):
        if self.maneuver is not None:
            return
        p = msg.pose.pose.position
        if self.detector.update(self.now(), p.x, p.y, self.mission_state):
            self.start_recovery()

    def start_recovery(self):
        if self.attempt >= len(RECOVERY_SEQUENCE):
            self.get_logger().error('Récupération impossible : intervention requise')
            self.publish_status('RECOVERY_FAILED')
            self.attempt = 0
            self.detector.reset()
            return
        name, v, w, duration = RECOVERY_SEQUENCE[self.attempt]
        self.attempt += 1
        self.maneuver = (name, v, w, self.now() + duration)
        self.get_logger().warn(f'Blocage détecté : manœuvre {self.attempt} ({name})')
        self.publish_status(f'RECOVERING {name}')

    def step(self):
        if self.maneuver is None:
            return
        name, v, w, end = self.maneuver
        cmd = Twist()
        if self.now() < end:
            cmd.linear.x = v
            cmd.angular.z = w
            self.cmd_pub.publish(cmd)
            return
        self.cmd_pub.publish(cmd)   # arrêt
        self.maneuver = None
        self.detector.reset()
        self.publish_status(f'RECOVERED {name}')

    def publish_status(self, text):
        msg = String()
        msg.data = text
        self.status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = RecoveryNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
