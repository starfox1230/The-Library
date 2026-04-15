from __future__ import annotations

import json

from .common import user_files_dir


SETTINGS_PATH = user_files_dir() / "settings.json"
DEFAULT_SETTINGS = {
    "scroll_to_top_on_answer": True,
    "review_image_overlay_shortcuts": True,
    "review_image_overlay_remember_position": False,
    "recent_leech_banner": True,
    "tts_enabled_card_audio": False,
    "disable_default_f3_shortcut": True,
    "visual_card_multitude_add_button": True,
    "add_cards_diagnosis_button": True,
    "add_cards_cloze_auto_deck": True,
    "add_cards_multi_image_counter": True,
    "add_cards_tab_cycles_clozes": True,
    "visual_card_multitude_auto_visual_deck": True,
}


def load_settings() -> dict[str, bool]:
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
        settings[key] = bool(raw_value)
    return settings


def save_settings(settings: dict[str, bool]) -> None:
    normalized = dict(DEFAULT_SETTINGS)
    for key in normalized:
        normalized[key] = bool(settings.get(key, normalized[key]))
    SETTINGS_PATH.write_text(json.dumps(normalized, indent=2, sort_keys=True), encoding="utf-8")


def get_setting(name: str) -> bool:
    return bool(load_settings().get(name, DEFAULT_SETTINGS.get(name, False)))


def set_setting(name: str, value: bool) -> bool:
    settings = load_settings()
    settings[str(name)] = bool(value)
    save_settings(settings)
    return bool(settings[str(name)])


def toggle_setting(name: str) -> bool:
    return set_setting(name, not get_setting(name))
