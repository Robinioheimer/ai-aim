import math


def exclusion_rect(config, width, height):
    return (width * config.exclude_left / 100, height * config.exclude_top / 100,
            width * config.exclude_right / 100, height * config.exclude_bottom / 100)


def select_target(boxes, config, width, height):
    left, top, right, bottom = exclusion_rect(config, width, height)
    accepted, candidates = [], []
    for box in boxes:
        x1, y1, x2, y2, *_ = box
        x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        if config.exclude_self and left <= x <= right and top <= mid_y <= bottom:
            continue
        accepted.append(box)
        y = y1 + (y2 - y1) * config.vertical
        distance = math.hypot(x - width / 2, y - height / 2)
        if getattr(config, "full_screen", False) or distance <= config.fov:
            candidates.append((distance, x, y))
    return accepted, min(candidates, default=None)


def input_status(config, target, foreground, aim_held, foreground_title=None):
    if not config.aim_enabled:
        return "Mauseingabe deaktiviert"
    if not foreground:
        if foreground_title:
            return (f"Eingabe gesperrt: '{config.window_title}' kommt nicht in "
                    f"aktuellem Titel vor ({foreground_title!r})")
        return "Eingabe gesperrt: Spielfenster nicht im Vordergrund"
    if not target:
        return "Kein auswählbares Ziel · Erkennung, Eigenzone und Auswahlradius prüfen"
    if not config.automatic and not aim_held:
        return "Warte auf Ziel-Hotkey"
    return "Zielbewegung aktiv"


def can_move(config, target, foreground, aim_held):
    return bool(config.aim_enabled and target and foreground and (config.automatic or aim_held))
