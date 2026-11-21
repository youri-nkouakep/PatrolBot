from patrolbot_recovery.stuck_detector import StuckDetector


def test_not_stuck_when_idle():
    d = StuckDetector(window=5.0)
    assert not any(d.update(t, 0.0, 0.0, 'WAITING_CODE') for t in range(20))


def test_stuck_when_no_progress_during_mission():
    d = StuckDetector(window=5.0)
    results = [d.update(t, 0.0, 0.0, 'NAVIGATING') for t in range(7)]
    assert results[-1] and not results[3]


def test_not_stuck_when_moving():
    d = StuckDetector(window=5.0, min_progress=0.05)
    assert not any(d.update(t, 0.1 * t, 0.0, 'NAVIGATING') for t in range(20))
