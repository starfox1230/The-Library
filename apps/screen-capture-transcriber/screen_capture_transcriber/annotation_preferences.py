from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_ANNOTATION_COLOR = "#FFAA00"
MAX_RECENT_COLORS = 8
_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def annotation_preferences_path() -> Path:
    root = os.getenv("APPDATA", "").strip()
    base = Path(root) if root else Path.home() / ".config"
    return base / "ScreenCaptureTranscriber" / "annotation-settings.json"


def normalize_color(value: object) -> str | None:
    color = str(value or "").strip().upper()
    return color if _COLOR_PATTERN.fullmatch(color) else None


@dataclass
class AnnotationColorPreferences:
    selected_color: str = DEFAULT_ANNOTATION_COLOR
    recent_colors: list[str] = field(default_factory=list)


def load_annotation_preferences(
    path: Path | None = None,
) -> AnnotationColorPreferences:
    settings_path = path or annotation_preferences_path()
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return AnnotationColorPreferences()
    if not isinstance(payload, dict):
        return AnnotationColorPreferences()

    selected = (
        normalize_color(payload.get("selected_color"))
        or DEFAULT_ANNOTATION_COLOR
    )
    recent: list[str] = []
    raw_recent = payload.get("recent_colors", [])
    if isinstance(raw_recent, list):
        for value in raw_recent:
            color = normalize_color(value)
            if color and color not in recent:
                recent.append(color)
            if len(recent) >= MAX_RECENT_COLORS:
                break
    return AnnotationColorPreferences(selected, recent)


def save_annotation_preferences(
    preferences: AnnotationColorPreferences,
    path: Path | None = None,
) -> None:
    settings_path = path or annotation_preferences_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "selected_color": (
            normalize_color(preferences.selected_color)
            or DEFAULT_ANNOTATION_COLOR
        ),
        "recent_colors": [
            color
            for color in (
                normalize_color(value) for value in preferences.recent_colors
            )
            if color
        ][:MAX_RECENT_COLORS],
    }
    temporary_path = settings_path.with_suffix(settings_path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(settings_path)


def remember_used_colors(
    preferences: AnnotationColorPreferences,
    used_colors: list[str],
) -> AnnotationColorPreferences:
    recent = list(preferences.recent_colors)
    for value in used_colors:
        color = normalize_color(value)
        if not color:
            continue
        recent = [existing for existing in recent if existing != color]
        recent.insert(0, color)
    preferences.recent_colors = recent[:MAX_RECENT_COLORS]
    return preferences
