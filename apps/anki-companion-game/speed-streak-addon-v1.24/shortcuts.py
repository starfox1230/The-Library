from __future__ import annotations

from typing import Any


PAUSE_SHORTCUT_MODE_COMBINED = "combined"
PAUSE_SHORTCUT_MODE_SPLIT = "split"
PAUSE_SHORTCUT_MODES = {PAUSE_SHORTCUT_MODE_COMBINED, PAUSE_SHORTCUT_MODE_SPLIT}

SHORTCUT_OPTIONS = (
    {
        "key": "pause",
        "label": "Pause / Unpause",
        "description": "Single-key shortcut used during review to pause or resume the active Speed Streak timer.",
        "default": "P",
    },
    {
        "key": "unpause",
        "label": "Unpause",
        "description": "Shortcut used only to resume the active Speed Streak timer when split pause/unpause shortcuts are enabled.",
        "default": "U",
    },
)


def default_shortcut_bindings() -> dict[str, str]:
    return {str(item["key"]): str(item["default"]) for item in SHORTCUT_OPTIONS}


def normalize_shortcut_value(value: Any, default: str) -> str:
    fallback = str(default or "").strip() or "P"
    text = str(value or "").strip()
    if not text:
        return fallback
    normalized = text[0]
    if normalized.isalpha():
        normalized = normalized.upper()
    return normalized


def normalize_shortcut_bindings(bindings: Any) -> dict[str, str]:
    raw_bindings = bindings if isinstance(bindings, dict) else {}
    defaults = default_shortcut_bindings()
    normalized: dict[str, str] = {}
    for item in SHORTCUT_OPTIONS:
        key = str(item["key"])
        normalized[key] = normalize_shortcut_value(raw_bindings.get(key, defaults[key]), defaults[key])
    return normalized


def normalize_pause_shortcut_mode(value: Any) -> str:
    normalized = str(value or PAUSE_SHORTCUT_MODE_COMBINED).strip().lower()
    if normalized in {"separate", "separated", "split"}:
        return PAUSE_SHORTCUT_MODE_SPLIT
    if normalized in PAUSE_SHORTCUT_MODES:
        return normalized
    return PAUSE_SHORTCUT_MODE_COMBINED
