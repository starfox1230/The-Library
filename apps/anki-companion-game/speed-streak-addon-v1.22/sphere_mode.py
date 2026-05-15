from __future__ import annotations


SPHERE_MODE_CLASSIC = "classic"
SPHERE_MODE_CONSOLIDATE = "consolidate"

SPHERE_MODE_OPTIONS = [
    (SPHERE_MODE_CLASSIC, "Classic Orbit"),
    (SPHERE_MODE_CONSOLIDATE, "Consolidate"),
]


def normalize_sphere_mode(value: object) -> str:
    normalized = str(value or SPHERE_MODE_CLASSIC).strip().lower() or SPHERE_MODE_CLASSIC
    if normalized == SPHERE_MODE_CONSOLIDATE:
        return SPHERE_MODE_CONSOLIDATE
    return SPHERE_MODE_CLASSIC


def sphere_mode_label(value: object) -> str:
    normalized = normalize_sphere_mode(value)
    for option_value, label in SPHERE_MODE_OPTIONS:
        if option_value == normalized:
            return label
    return "Classic Orbit"
