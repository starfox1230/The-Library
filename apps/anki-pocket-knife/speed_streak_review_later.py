from __future__ import annotations

import importlib
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any

from aqt import mw


class SpeedStreakIntegrationError(RuntimeError):
    pass


def _loaded_speed_streak() -> tuple[str, Any, Any]:
    """Return (package, controller, review_later module) without a versioned import."""
    for module_name, module in list(sys.modules.items()):
        if not module_name or not module_name.endswith(".reviewer_overlay") or module is None:
            continue
        package_name = str(getattr(module, "ADDON_PACKAGE", "") or module_name.split(".", 1)[0])
        display_name = str(getattr(module, "ADDON_DISPLAY_NAME", "") or "")
        haystack = f"{module_name} {package_name} {display_name}".casefold()
        if "speed_streak" not in haystack and "speed streak" not in haystack:
            continue
        controller = getattr(module, "controller", None)
        if controller is None or not hasattr(controller, "engine"):
            continue
        review_module_name = f"{module_name.rsplit('.', 1)[0]}.review_later"
        review_module = sys.modules.get(review_module_name)
        if review_module is None:
            review_module = importlib.import_module(review_module_name)
        fetch = getattr(review_module, "fetch_review_later_entries", None)
        if callable(fetch):
            return package_name, controller, review_module
    raise SpeedStreakIntegrationError(
        "Speed Streak is not loaded. Make sure it is enabled, then restart Anki."
    )


def _review_later_flag(package_name: str, controller: Any) -> int:
    state = getattr(getattr(controller, "engine", None), "state", None)
    try:
        flag = int(getattr(state, "review_later_flag", 0) or 0)
    except Exception:
        flag = 0
    if flag <= 0:
        try:
            config = mw.addonManager.getConfig(package_name) or {}
            flag = int(config.get("review_later_flag", 0) or 0)
        except Exception:
            flag = 0
    if flag <= 0:
        raise SpeedStreakIntegrationError(
            "Speed Streak does not currently have a Review Later flag configured."
        )
    return flag


def _entry_value(entry: Any, name: str, default: Any = None) -> Any:
    if isinstance(entry, dict):
        return entry.get(name, default)
    return getattr(entry, name, default)


def _local_iso(value: Any) -> str:
    if isinstance(value, datetime):
        try:
            return value.astimezone().isoformat(timespec="seconds")
        except Exception:
            return value.isoformat(timespec="seconds")
    return str(value or "")


def fetch_current_review_later() -> dict[str, Any]:
    """Fetch the complete active Speed Streak queue on Anki's main thread."""
    package_name, controller, review_module = _loaded_speed_streak()
    flag = _review_later_flag(package_name, controller)
    raw_entries = review_module.fetch_review_later_entries(flag)
    cards: list[dict[str, Any]] = []
    for entry in raw_entries:
        raw = asdict(entry) if is_dataclass(entry) else entry
        fields = dict(_entry_value(raw, "fields", {}) or {})
        cards.append(
            {
                "card_id": int(_entry_value(raw, "card_id", 0) or 0),
                "note_id": int(_entry_value(raw, "note_id", 0) or 0),
                "flagged_at": _local_iso(_entry_value(raw, "added_at", "")),
                "deck": str(_entry_value(raw, "deck_name", "") or ""),
                "note_type": str(_entry_value(raw, "note_type_name", "") or ""),
                "tags": [str(tag) for tag in (_entry_value(raw, "tags", []) or [])],
                "fields": {str(name): str(value or "") for name, value in fields.items()},
                "front_html": str(_entry_value(raw, "front_html", "") or ""),
                "back_html": str(_entry_value(raw, "back_html", "") or ""),
                "front_text": str(_entry_value(raw, "front_text", "") or ""),
                "back_text": str(_entry_value(raw, "back_text", "") or ""),
                "media": [],
            }
        )
    return {
        "source_addon": package_name,
        "review_later_flag": flag,
        "cards": cards,
    }
