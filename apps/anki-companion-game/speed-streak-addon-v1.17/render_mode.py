from __future__ import annotations


RENDER_MODE_CLASSIC = "classic"
RENDER_MODE_LOW_RESOURCE = "low_resource"
RENDER_MODE_ULTRA_LOW_RESOURCE = "ultra_low_resource"

RENDER_MODE_OPTIONS = [
    (RENDER_MODE_CLASSIC, "Classic"),
    (RENDER_MODE_LOW_RESOURCE, "Low Resource"),
    (RENDER_MODE_ULTRA_LOW_RESOURCE, "Ultra Low Resource"),
]


def normalize_render_mode(value: object) -> str:
    normalized = str(value or RENDER_MODE_CLASSIC).strip().lower() or RENDER_MODE_CLASSIC
    if normalized in {RENDER_MODE_CLASSIC, RENDER_MODE_LOW_RESOURCE, RENDER_MODE_ULTRA_LOW_RESOURCE}:
        return normalized
    return RENDER_MODE_CLASSIC


def render_mode_label(value: object) -> str:
    normalized = normalize_render_mode(value)
    for option_value, label in RENDER_MODE_OPTIONS:
        if option_value == normalized:
            return label
    return "Classic"
