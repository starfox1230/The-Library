from __future__ import annotations

import json
from typing import Any

from .common import user_files_dir


SETTINGS_PATH = user_files_dir() / "settings.json"
DEFAULT_SETTINGS = {
    "scroll_to_top_on_answer": True,
    "review_image_overlay_shortcuts": True,
    "review_image_overlay_remember_position": False,
    "recent_leech_banner": True,
    "tts_enabled_card_audio": False,
    "disable_default_f3_shortcut": True,
    "underline_trailing_spaces_fix": True,
    "visual_card_multitude_add_button": True,
    "add_cards_sticky_fields_default_on": True,
    "add_cards_diagnosis_button": True,
    "add_cards_cloze_auto_deck": True,
    "add_cards_multi_image_counter": True,
    "add_cards_tab_cycles_clozes": True,
    "visual_card_multitude_auto_visual_deck": True,
    "ai_tools_enabled": True,
    "ai_tools_model": "gpt-4.1",
    "ai_tools_api_key": "",
    "ai_spellcheck_auto_on_add": False,
    "ai_spellcheck_preview": True,
    "ai_preview_show_html": False,
    "lightning_mode_card_limit": 100,
    "lightning_mode_question_seconds": 10,
    "lightning_mode_answer_seconds": 5,
}


def _coerce_setting_value(raw_value: Any, default_value: Any) -> Any:
    if isinstance(default_value, bool):
        return bool(raw_value)

    if isinstance(default_value, int):
        try:
            return int(raw_value)
        except Exception:
            return int(default_value)

    if isinstance(default_value, float):
        try:
            return float(raw_value)
        except Exception:
            return float(default_value)

    if isinstance(default_value, str):
        return str(raw_value)

    return raw_value


def load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return dict(DEFAULT_SETTINGS)

    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULT_SETTINGS)

    if not isinstance(data, dict):
        return dict(DEFAULT_SETTINGS)

    settings = dict(DEFAULT_SETTINGS)
    for key, default_value in DEFAULT_SETTINGS.items():
        raw_value = data.get(key, default_value)
        settings[key] = _coerce_setting_value(raw_value, default_value)
    return settings


def save_settings(settings: dict[str, Any]) -> None:
    normalized = dict(DEFAULT_SETTINGS)
    for key, default_value in normalized.items():
        normalized[key] = _coerce_setting_value(settings.get(key, default_value), default_value)
    SETTINGS_PATH.write_text(json.dumps(normalized, indent=2, sort_keys=True), encoding="utf-8")


def get_setting(name: str) -> Any:
    default_value = DEFAULT_SETTINGS.get(name, False)
    return load_settings().get(name, default_value)


def set_setting(name: str, value: Any) -> Any:
    settings = load_settings()
    key = str(name)
    default_value = DEFAULT_SETTINGS.get(key)
    settings[key] = _coerce_setting_value(value, default_value) if default_value is not None else value
    save_settings(settings)
    return settings[key]


def toggle_setting(name: str) -> bool:
    return bool(set_setting(name, not bool(get_setting(name))))
