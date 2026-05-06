from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ADDON_ROOT = Path(__file__).resolve().parent
USER_FILES = ADDON_ROOT / "user_files"
SETTINGS_PATH = USER_FILES / "settings.json"

DEFAULT_SETTINGS = {
    "enabled": True,
    "goal_window_visible": True,
    "pet_visible": True,
    "goal_count": 100,
    "goal_mode": "total",
    "paused": False,
    "elapsed_seconds": 0.0,
    "pet_x": 90,
    "pet_y": 130,
    "goal_x": 360,
    "goal_y": 130,
    "goal_width": 360,
    "goal_height": 300,
    "character": "moth",
}


def _coerce(value: Any, default: Any) -> Any:
    if isinstance(default, bool):
        return bool(value)
    if isinstance(default, int):
        try:
            return int(value)
        except Exception:
            return int(default)
    if isinstance(default, float):
        try:
            return float(value)
        except Exception:
            return float(default)
    if isinstance(default, str):
        return str(value)
    return value


def load_settings() -> dict[str, Any]:
    USER_FILES.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_PATH.exists():
        return dict(DEFAULT_SETTINGS)
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULT_SETTINGS)
    if not isinstance(data, dict):
        return dict(DEFAULT_SETTINGS)
    settings = dict(DEFAULT_SETTINGS)
    for key, default in DEFAULT_SETTINGS.items():
        settings[key] = _coerce(data.get(key, default), default)
    return settings


def save_settings(settings: dict[str, Any]) -> None:
    USER_FILES.mkdir(parents=True, exist_ok=True)
    normalized = dict(DEFAULT_SETTINGS)
    for key, default in DEFAULT_SETTINGS.items():
        normalized[key] = _coerce(settings.get(key, default), default)
    SETTINGS_PATH.write_text(json.dumps(normalized, indent=2, sort_keys=True), encoding="utf-8")


def get_setting(name: str) -> Any:
    return load_settings().get(str(name), DEFAULT_SETTINGS.get(str(name)))


def set_setting(name: str, value: Any) -> Any:
    settings = load_settings()
    key = str(name)
    settings[key] = _coerce(value, DEFAULT_SETTINGS.get(key, value))
    save_settings(settings)
    return settings[key]
