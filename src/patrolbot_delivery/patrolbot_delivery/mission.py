"""Fonctions de mission sans dépendance ROS (testables avec pytest)."""
import hmac


def parse_mission(text):
    """'x,y,code' -> (x, y, code). Lève ValueError si le format est invalide."""
    parts = [p.strip() for p in text.split(',')]
    if len(parts) != 3 or not parts[2]:
        raise ValueError('format attendu : "x,y,code"')
    return float(parts[0]), float(parts[1]), parts[2]


def code_is_valid(submitted, expected):
    """Comparaison en temps constant, pour ne rien révéler du code attendu."""
    return hmac.compare_digest(submitted.encode(), expected.encode())
