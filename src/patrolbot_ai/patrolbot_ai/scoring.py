"""Score multicritère d'une destination (sans dépendance ROS, testable avec pytest).

Plus le score est bas, meilleure est la destination. Chaque critère est normalisé
entre 0 et 1 environ avant d'être pondéré.
"""
import math

ROBOT_SPEED = 0.22    # [m/s] vitesse max du TurtleBot3 Waffle Pi
MAX_DISTANCE = 10.0   # [m] distance de normalisation
ENERGY_PER_M = 0.1    # coût énergétique par mètre (unité arbitraire)

DEFAULT_WEIGHTS = {
    'distance': 0.25,
    'time': 0.20,
    'obstacles': 0.35,
    'risk': 0.15,
    'energy': 0.05,
}


def wrap(angle):
    """Ramène un angle dans ]-pi, pi]."""
    return math.atan2(math.sin(angle), math.cos(angle))


def sector_index(bearing, num_sectors, angle_min=0.0):
    """Indice du secteur LiDAR qui couvre la direction `bearing` (repère robot)."""
    width = 2.0 * math.pi / num_sectors
    return int(((bearing - angle_min) % (2.0 * math.pi)) // width) % num_sectors


def obstacle_cost(densities, bearing, angle_min=0.0, spread=1):
    """Densité d'obstacles dans la direction de la destination.

    On prend la moyenne du secteur visé et de ses `spread` voisins de chaque côté,
    pour tenir compte de la largeur du robot.
    """
    n = len(densities)
    if n == 0:
        return 0.0
    i = sector_index(bearing, n, angle_min)
    window = [densities[(i + k) % n] for k in range(-spread, spread + 1)]
    return float(sum(window) / len(window))


def compute_score(robot_pose, destination, densities, weights=None,
                  risk=0.0, angle_min=0.0):
    """Score d'une destination.

    robot_pose  : (x, y, yaw) du robot dans le repère map
    destination : (x, y) dans le repère map
    densities   : densités d'obstacles par secteur (sortie de obstacle_detector)
    """
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    rx, ry, ryaw = robot_pose
    dx, dy = destination[0] - rx, destination[1] - ry
    distance = math.hypot(dx, dy)
    bearing = wrap(math.atan2(dy, dx) - ryaw)
    duration = distance / ROBOT_SPEED

    return (w['distance'] * distance / MAX_DISTANCE
            + w['time'] * duration / (MAX_DISTANCE / ROBOT_SPEED)
            + w['obstacles'] * obstacle_cost(densities, bearing, angle_min)
            + w['risk'] * risk
            + w['energy'] * distance * ENERGY_PER_M)


def best_destination(robot_pose, destinations, densities, weights=None, angle_min=0.0):
    """Renvoie (destination, score) de la destination au plus petit score."""
    scored = [(d, compute_score(robot_pose, d, densities, weights, angle_min=angle_min))
              for d in destinations]
    return min(scored, key=lambda item: item[1])
