from __future__ import annotations


DISPLAY_MODE_INLINE = "inline"
DISPLAY_MODE_COMPATIBILITY = "compatibility"

DISPLAY_MODE_OPTIONS = (
    (DISPLAY_MODE_INLINE, "Inline Left Pane"),
    (DISPLAY_MODE_COMPATIBILITY, "Compatibility Window"),
)


def normalize_display_mode(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == DISPLAY_MODE_COMPATIBILITY:
        return DISPLAY_MODE_COMPATIBILITY
    return DISPLAY_MODE_INLINE


def display_mode_label(value: object) -> str:
    mode = normalize_display_mode(value)
    for key, label in DISPLAY_MODE_OPTIONS:
        if key == mode:
            return label
    return "Inline Left Pane"
