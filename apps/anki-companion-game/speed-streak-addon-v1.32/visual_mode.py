from __future__ import annotations


VISUAL_MODE_SPHERE = "sphere"
VISUAL_MODE_CRYSTAL_REACTOR = "crystal_reactor"
VISUAL_MODE_LIGHTWEIGHT_ROWS = "lightweight_rows"

VISUAL_MODE_OPTIONS = [
    (VISUAL_MODE_SPHERE, "Sphere/Satellites"),
    (VISUAL_MODE_CRYSTAL_REACTOR, "Crystal Reactor"),
    (VISUAL_MODE_LIGHTWEIGHT_ROWS, "Brick Layout"),
]


def normalize_visual_mode(value: object) -> str:
    normalized = str(value or VISUAL_MODE_SPHERE).strip().lower() or VISUAL_MODE_SPHERE
    if normalized in {VISUAL_MODE_LIGHTWEIGHT_ROWS, "rows"}:
        return VISUAL_MODE_LIGHTWEIGHT_ROWS
    if normalized in {VISUAL_MODE_CRYSTAL_REACTOR, "crystal", "reactor"}:
        return VISUAL_MODE_CRYSTAL_REACTOR
    return VISUAL_MODE_SPHERE


def visual_mode_label(value: object) -> str:
    normalized = normalize_visual_mode(value)
    for option_value, label in VISUAL_MODE_OPTIONS:
        if option_value == normalized:
            return label
    return "Sphere/Satellites"
