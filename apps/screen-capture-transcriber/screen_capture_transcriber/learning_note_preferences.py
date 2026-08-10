from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_TEXT_SIZE_POINTS = 10
MIN_TEXT_SIZE_POINTS = 8
MAX_TEXT_SIZE_POINTS = 28
TEXT_SIZE_STEP_POINTS = 2


def learning_note_preferences_path() -> Path:
    root = os.getenv("APPDATA", "").strip()
    base = Path(root) if root else Path.home() / ".config"
    return base / "ScreenCaptureTranscriber" / "learning-note-settings.json"


def normalize_text_size(value: object) -> int:
    try:
        size = int(value)
    except (TypeError, ValueError):
        return DEFAULT_TEXT_SIZE_POINTS
    return min(MAX_TEXT_SIZE_POINTS, max(MIN_TEXT_SIZE_POINTS, size))


@dataclass
class LearningNotePreferences:
    text_size_points: int = DEFAULT_TEXT_SIZE_POINTS


def load_learning_note_preferences(
    path: Path | None = None,
) -> LearningNotePreferences:
    settings_path = path or learning_note_preferences_path()
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return LearningNotePreferences()
    if not isinstance(payload, dict):
        return LearningNotePreferences()
    return LearningNotePreferences(
        normalize_text_size(payload.get("text_size_points"))
    )


def save_learning_note_preferences(
    preferences: LearningNotePreferences,
    path: Path | None = None,
) -> None:
    settings_path = path or learning_note_preferences_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = settings_path.with_suffix(settings_path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(
            {
                "text_size_points": normalize_text_size(
                    preferences.text_size_points
                )
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary_path.replace(settings_path)
