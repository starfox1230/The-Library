from __future__ import annotations


SPHERE_MODE_CLASSIC = "classic"
SPHERE_MODE_CONSOLIDATE = "consolidate"
SPHERE_MODE_MILESTONE = "milestone"
SPHERE_MODE_FUSION = "fusion"
SPHERE_MODE_DEFAULT = SPHERE_MODE_FUSION

SPHERE_MODE_OPTIONS = [
    (SPHERE_MODE_CLASSIC, "Classic Orbit"),
    (SPHERE_MODE_FUSION, "Fusion Rings"),
]


def normalize_sphere_mode(value: object) -> str:
    normalized = str(value or SPHERE_MODE_DEFAULT).strip().lower() or SPHERE_MODE_DEFAULT
    if normalized == SPHERE_MODE_CLASSIC:
        return SPHERE_MODE_CLASSIC
    # Consolidate and Milestone were experimental predecessors to Fusion.
    # Keep accepting their saved values, but migrate them to the supported mode.
    if normalized in {SPHERE_MODE_CONSOLIDATE, SPHERE_MODE_MILESTONE, SPHERE_MODE_FUSION}:
        return SPHERE_MODE_FUSION
    return SPHERE_MODE_DEFAULT


def sphere_mode_label(value: object) -> str:
    normalized = normalize_sphere_mode(value)
    for option_value, label in SPHERE_MODE_OPTIONS:
        if option_value == normalized:
            return label
    return "Fusion Rings"
