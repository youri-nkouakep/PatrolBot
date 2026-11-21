#!/usr/bin/env python3
"""Gestionnaire de mission de livraison : machine à 8 états au-dessus de Nav2.

IDLE -> NAVIGATING -> ARRIVED -> WAITING_CODE -> VERIFYING -> DELIVERING -> RETURNING -> IDLE
Toute erreur (mission invalide, navigation échouée) passe par ERROR puis
ramène le robot à la base, pour qu'il puisse accepter une nouvelle mission.
"""
from enum import auto, Enum
import threading
import time

from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import String

from patrolbot_delivery.mission import code_is_valid, parse_mission


class DeliveryState(Enum):
    IDLE = auto()
    NAVIGATING = auto()
    ARRIVED = auto()
    WAITING_CODE = auto()
    VERIFYING = auto()
    DELIVERING = auto()
    RETURNING = auto()
    ERROR = auto()


class DeliveryManager(Node):

    def __init__(self):
        super().__init__('delivery_manager')
        self.declare_parameter('code_timeout', 120.0)
        self.declare_parameter('base_x', 0.0)
        self.declare_parameter('base_y', 0.0)
        self.code_timeout = self.get_parameter('code_timeout').value

        self.state = DeliveryState.IDLE
        self.lock = threading.Lock()
        self.navigator = BasicNavigator()
        self.nav_ready = False
        self.expected_code = None
        self.code_timer = None

        self.status_pub = self.create_publisher(String, '/delivery/status', 10)
        self.create_subscription(String, '/delivery/new_mission', self.mission_cb, 10)
        self.create_subscription(String, '/delivery/code_submitted', self.code_cb, 10)
        self.create_timer(1.0, self.publish_status)   # état republié pour les nouveaux abonnés

        self.get_logger().info('Delivery Manager démarré')

    # ── Machine à états ──────────────────────────────────────────────────────
    def transition(self, new_state, reason=''):
        self.get_logger().info(f'FSM: {self.state.name} -> {new_state.name} [{reason}]')
        self.state = new_state
        self.publish_status()

    def publish_status(self):
        msg = String()
        msg.data = f'STATE:{self.state.name}'
        self.status_pub.publish(msg)

    # ── Navigation ───────────────────────────────────────────────────────────
    def make_pose(self, x, y):
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.navigator.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.w = 1.0
        return pose

    def go_to(self, x, y):
        if not self.nav_ready:
            self.navigator.waitUntilNav2Active()
            self.nav_ready = True
        self.navigator.goToPose(self.make_pose(x, y))
        while not self.navigator.isTaskComplete():
            time.sleep(0.1)
        return self.navigator.getResult() == TaskResult.SUCCEEDED

    # ── Callbacks ────────────────────────────────────────────────────────────
    def mission_cb(self, msg):
        with self.lock:
            if self.state != DeliveryState.IDLE:
                self.get_logger().warn('Mission refusée : une mission est déjà en cours')
                return
            try:
                x, y, code = parse_mission(msg.data)
            except ValueError as e:
                self.get_logger().error(f'Mission invalide : {e}')
                return
            self.expected_code = code
            self.transition(DeliveryState.NAVIGATING, f'vers ({x:.2f}, {y:.2f})')
        threading.Thread(target=self.run_mission, args=(x, y), daemon=True).start()

    def code_cb(self, msg):
        with self.lock:
            if self.state != DeliveryState.WAITING_CODE:
                return
            if self.code_timer:
                self.code_timer.cancel()
            self.transition(DeliveryState.VERIFYING, 'code reçu')
            ok = code_is_valid(msg.data, self.expected_code)
            self.expected_code = None
            if ok:
                self.transition(DeliveryState.DELIVERING, 'code correct')
            else:
                self.transition(DeliveryState.RETURNING, 'code incorrect')
        threading.Thread(target=self.finish_delivery, args=(ok,), daemon=True).start()

    def code_timeout_cb(self):
        with self.lock:
            if self.state != DeliveryState.WAITING_CODE:
                return
            self.expected_code = None
            self.transition(DeliveryState.RETURNING, f'aucun code après {self.code_timeout:.0f} s')
        self.return_to_base()

    # ── Séquences (exécutées dans un thread) ────────────────────────────────
    def run_mission(self, x, y):
        if not self.go_to(x, y):
            with self.lock:
                self.transition(DeliveryState.ERROR, 'navigation échouée')
                self.transition(DeliveryState.RETURNING, 'abandon de la mission')
            self.return_to_base()
            return
        with self.lock:
            self.transition(DeliveryState.ARRIVED, 'destination atteinte')
            self.transition(DeliveryState.WAITING_CODE, 'attente du code')
            self.code_timer = threading.Timer(self.code_timeout, self.code_timeout_cb)
            self.code_timer.start()

    def finish_delivery(self, delivered):
        if delivered:
            self.get_logger().info('Livraison confirmée')
            time.sleep(2.0)   # temps de retrait du colis
            with self.lock:
                self.transition(DeliveryState.RETURNING, 'livraison terminée')
        self.return_to_base()

    def return_to_base(self):
        ok = self.go_to(self.get_parameter('base_x').value, self.get_parameter('base_y').value)
        with self.lock:
            if not ok:
                self.transition(DeliveryState.ERROR, 'retour à la base échoué')
            self.transition(DeliveryState.IDLE, 'prêt pour une nouvelle mission')


def main(args=None):
    rclpy.init(args=args)
    node = DeliveryManager()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
