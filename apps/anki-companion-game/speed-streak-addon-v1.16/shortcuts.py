from __future__ import annotations

from typing import Any


SHORTCUT_OPTIONS = (
    {
        "key": "pause",
        "label": "Pause / Unpause",
        "description": "Single-key shortcut used during review to pause or resume the active Speed Streak timer.",
        "default": "P",
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
