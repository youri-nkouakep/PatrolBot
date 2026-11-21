import math

from patrolbot_ai.scoring import best_destination, compute_score, obstacle_cost, sector_index


def test_sector_index():
    assert sector_index(0.0, 36) == 0
    assert sector_index(math.radians(15), 36) == 1
    assert sector_index(math.radians(-5), 36) == 35


def test_obstacle_cost_follows_direction():
    densities = [0.0] * 36
    densities[9] = 0.9              # obstacles à gauche (90°)
    assert obstacle_cost(densities, math.radians(90)) > 0.0
    assert obstacle_cost(densities, 0.0) == 0.0


def test_score_increases_with_distance():
    free = [0.0] * 36
    assert compute_score((0, 0, 0), (1, 0), free) < compute_score((0, 0, 0), (3, 0), free)


def test_blocked_direction_is_avoided():
    densities = [0.0] * 36
    densities[35] = densities[0] = densities[1] = 1.0   # devant bloqué
    best, _ = best_destination((0, 0, 0), [(1.0, 0.0), (0.0, 1.2)], densities)
    assert best == (0.0, 1.2)


def test_uses_robot_pose():
    free = [0.0] * 36
    assert math.isclose(compute_score((1, 1, 0), (1, 1), free), 0.0)
