from __future__ import annotations


CRYSTAL_COLOR_MODE_ICE = "ice"
CRYSTAL_COLOR_MODE_ANSWER = "answer"
CRYSTAL_COLOR_MODE_CORE = "core"

CRYSTAL_COLOR_MODE_OPTIONS = (
    (CRYSTAL_COLOR_MODE_CORE, "Single Crystal Color"),
    (CRYSTAL_COLOR_MODE_ANSWER, "Rating Colors"),
)


def normalize_crystal_color_mode(value: object) -> str:
    normalized = str(value or CRYSTAL_COLOR_MODE_CORE).strip().lower() or CRYSTAL_COLOR_MODE_CORE
    if normalized in {CRYSTAL_COLOR_MODE_ANSWER, "answers", "rating", "ratings"}:
        return CRYSTAL_COLOR_MODE_ANSWER
    if normalized in {CRYSTAL_COLOR_MODE_CORE, "orb", "single", "monochrome"}:
        return CRYSTAL_COLOR_MODE_CORE
    # "ice" is the legacy name for the built-in single-color appearance.
    return CRYSTAL_COLOR_MODE_CORE


def crystal_color_mode_label(value: object) -> str:
    normalized = normalize_crystal_color_mode(value)
    for option_value, label in CRYSTAL_COLOR_MODE_OPTIONS:
        if option_value == normalized:
            return label
    return "Single Crystal Color"
