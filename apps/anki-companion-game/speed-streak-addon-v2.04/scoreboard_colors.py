from __future__ import annotations

from typing import Any


DEFAULT_SCOREBOARD_COLORS = {
    "label": "#8ea0cc",
    "value": "#65f0c2",
    # Matches the warm orange Anki uses for its second flag by default. It
    # reads as gold against the dark review panel without sacrificing contrast.
    "new_record": "#f5aa41",
}
SCOREBOARD_COLOR_KEYS = tuple(DEFAULT_SCOREBOARD_COLORS)


def normalize_scoreboard_colors(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, str] = {}
    for key in SCOREBOARD_COLOR_KEYS:
        color = str(value.get(key, "") or "").strip().lower()
        if not color:
            continue
        if not color.startswith("#"):
            color = f"#{color}"
        if len(color) == 4 and all(character in "#0123456789abcdef" for character in color):
            color = "#" + "".join(character * 2 for character in color[1:])
        if len(color) == 7 and all(character in "#0123456789abcdef" for character in color):
            normalized[key] = color
    return normalized


def resolved_scoreboard_colors(value: Any) -> dict[str, str]:
    return {**DEFAULT_SCOREBOARD_COLORS, **normalize_scoreboard_colors(value)}
