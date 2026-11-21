"""Détection de blocage (sans dépendance ROS, testable avec pytest).

Le robot est considéré bloqué s'il est censé se déplacer (mission en cours)
mais a parcouru moins de `min_progress` mètres pendant `window` secondes.
"""
import math

# États de la mission pendant lesquels le robot doit avancer
MOVING_STATES = ('NAVIGATING', 'RETURNING')


class StuckDetector:

    def __init__(self, window=5.0, min_progress=0.05):
        self.window = window
        self.min_progress = min_progress
        self.reset()

    def reset(self):
        self.ref_time = None
        self.ref_pos = None

    def update(self, t, x, y, mission_state):
        """Renvoie True si le robot est bloqué à l'instant t."""
        if mission_state not in MOVING_STATES:
            self.reset()
            return False
        if self.ref_time is None:
            self.ref_time, self.ref_pos = t, (x, y)
            return False
        if math.hypot(x - self.ref_pos[0], y - self.ref_pos[1]) >= self.min_progress:
            # Le robot avance : on repart de la position actuelle
            self.ref_time, self.ref_pos = t, (x, y)
            return False
        return (t - self.ref_time) >= self.window


# Manœuvres successives : (nom, vitesse linéaire m/s, vitesse angulaire rad/s, durée s)
RECOVERY_SEQUENCE = (
    ('backup', -0.10, 0.0, 3.0),          # recul de 0,3 m (3,0 s)
    ('spin', 0.0, 1.0, math.pi),          # demi-tour sur place (3,1 s)
)
