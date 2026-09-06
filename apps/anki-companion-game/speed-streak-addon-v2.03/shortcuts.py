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
    {
        "key": "boost",
        "label": "Use Time Boost",
        "description": "Uses one Boost to add time to the active question or answer timer in Time Boost mode.",
        "default": "C",
    },
)


# Vanilla Anki review shortcuts that can collide with Speed Streak's
# single-key controls. This mirrors Reviewer._shortcutKeys() in current Anki.
# Modifier-only shortcuts such as Ctrl+1 cannot be entered in Speed Streak's
# one-character fields, so only their unmodified equivalents belong here.
ANKI_REVIEW_SHORTCUT_ACTIONS = {
    " ": "Show Answer or answer Good",
    "1": "Answer Again",
    "2": "Answer Hard or Good, depending on the available answer buttons",
    "3": "Answer Good or Easy, depending on the available answer buttons",
    "4": "Answer Easy",
    "5": "Pause or resume audio",
    "6": "Seek audio backward",
    "7": "Seek audio forward",
    "e": "Edit the current card",
    "i": "Show Card Info",
    "m": "Open the More menu",
    "o": "Open Deck Options",
    "r": "Replay Audio",
    "u": "Undo",
    "v": "Replay Recorded Voice",
    "*": "Mark or unmark the current note",
    "=": "Bury the current note",
    "-": "Bury the current card",
    "!": "Suspend the current note",
    "@": "Suspend the current card",
    # Anki also supplies localized single-key equivalents for Korean layouts.
    "ㄷ": "Edit the current card",
    "ㅡ": "Open the More menu",
    "ㄱ": "Replay Audio",
    "ㅍ": "Replay Recorded Voice",
    "ㅐ": "Open Deck Options",
    "ㅑ": "Show Card Info",
    "ㅕ": "Undo",
}


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


def anki_review_shortcut_action(value: Any, answer_key_actions: Any = None) -> str:
    """Return the vanilla Anki review action assigned to a single key."""
    text = str(value or "")
    if not text:
        return ""
    key = text[0]
    lookup_key = key.casefold() if key.isalpha() else key
    runtime_actions = answer_key_actions if isinstance(answer_key_actions, dict) else {}
    runtime_action = runtime_actions.get(lookup_key)
    if runtime_action:
        return str(runtime_action)
    return ANKI_REVIEW_SHORTCUT_ACTIONS.get(lookup_key, "")


def normalize_pause_shortcut_mode(value: Any) -> str:
    normalized = str(value or PAUSE_SHORTCUT_MODE_COMBINED).strip().lower()
    if normalized in {"separate", "separated", "split"}:
        return PAUSE_SHORTCUT_MODE_SPLIT
    if normalized in PAUSE_SHORTCUT_MODES:
        return normalized
    return PAUSE_SHORTCUT_MODE_COMBINED
