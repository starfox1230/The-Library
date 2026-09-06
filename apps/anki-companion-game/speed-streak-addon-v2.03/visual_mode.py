from __future__ import annotations


VISUAL_MODE_SPHERE = "sphere"
VISUAL_MODE_SINGULARITY = "singularity"
VISUAL_MODE_CRYSTAL_REACTOR = "crystal_reactor"
VISUAL_MODE_LIGHTWEIGHT_ROWS = "lightweight_rows"
VISUAL_MODE_NUMBER_ONLY = "number_only"

VISUAL_MODE_OPTIONS = [
    (VISUAL_MODE_SPHERE, "Sphere/Satellites"),
    (VISUAL_MODE_SINGULARITY, "Singularity"),
    (VISUAL_MODE_CRYSTAL_REACTOR, "Crystal Reactor"),
    (VISUAL_MODE_LIGHTWEIGHT_ROWS, "Brick Layout"),
    (VISUAL_MODE_NUMBER_ONLY, "# Only"),
]


def normalize_visual_mode(value: object) -> str:
    normalized = str(value or VISUAL_MODE_SPHERE).strip().lower() or VISUAL_MODE_SPHERE
    if normalized in {VISUAL_MODE_LIGHTWEIGHT_ROWS, "rows"}:
        return VISUAL_MODE_LIGHTWEIGHT_ROWS
    if normalized in {VISUAL_MODE_NUMBER_ONLY, "number", "number-only", "streak_number"}:
        return VISUAL_MODE_NUMBER_ONLY
    if normalized in {VISUAL_MODE_CRYSTAL_REACTOR, "crystal", "reactor"}:
        return VISUAL_MODE_CRYSTAL_REACTOR
    if normalized in {VISUAL_MODE_SINGULARITY, "gravity", "gravity_core", "black_hole"}:
        return VISUAL_MODE_SINGULARITY
    return VISUAL_MODE_SPHERE


def visual_mode_label(value: object) -> str:
    normalized = normalize_visual_mode(value)
    for option_value, label in VISUAL_MODE_OPTIONS:
        if option_value == normalized:
            return label
    return "Sphere/Satellites"
