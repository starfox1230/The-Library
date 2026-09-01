from __future__ import annotations

import importlib
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
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


def _revlog_last_seen(card_ids: list[int]) -> dict[int, str]:
    seen: dict[int, str] = {}
    for start in range(0, len(card_ids), 800):
        batch = card_ids[start : start + 800]
        if not batch:
            continue
        placeholders = ",".join("?" for _ in batch)
        rows = mw.col.db.all(
            f"SELECT cid, MAX(id) FROM revlog WHERE cid IN ({placeholders}) GROUP BY cid",
            *batch,
        )
        for card_id, review_id in rows:
            if not review_id:
                continue
            value = datetime.fromtimestamp(int(review_id) / 1000, tz=timezone.utc).astimezone()
            seen[int(card_id)] = value.isoformat(timespec="seconds")
    return seen


def _newest_iso(*values: str) -> str:
    parsed: list[tuple[datetime, str]] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        try:
            date_value = datetime.fromisoformat(text)
            if date_value.tzinfo is None:
                date_value = date_value.astimezone()
            parsed.append((date_value, text))
        except Exception:
            continue
    return max(parsed, key=lambda item: item[0])[1] if parsed else ""


def fetch_current_review_later() -> dict[str, Any]:
    """Fetch the complete active Speed Streak queue on Anki's main thread."""
    package_name, controller, review_module = _loaded_speed_streak()
    flag = _review_later_flag(package_name, controller)
    raw_entries = review_module.fetch_review_later_entries(flag)
    tracked_ids = [int(_entry_value(entry, "card_id", 0) or 0) for entry in raw_entries]
    tracked_ids = [card_id for card_id in tracked_ids if card_id > 0]
    flagged_ids = [int(card_id) for card_id in mw.col.find_cards(f"flag:{flag}")]
    first_flagged: dict[int, Any] = {}
    first_flagged_api = getattr(review_module, "review_later_first_flagged_at", None)
    if callable(first_flagged_api):
        try:
            first_flagged = dict(first_flagged_api(flag, tracked_ids) or {})
        except Exception:
            first_flagged = {}
    last_reviewed = _revlog_last_seen(flagged_ids)
    cards: list[dict[str, Any]] = []
    for entry in raw_entries:
        raw = asdict(entry) if is_dataclass(entry) else entry
        fields = dict(_entry_value(raw, "fields", {}) or {})
        card_id = int(_entry_value(raw, "card_id", 0) or 0)
        active_entry_at = _local_iso(_entry_value(raw, "added_at", ""))
        first_flagged_at = _local_iso(first_flagged.get(card_id, "")) or active_entry_at
        cards.append(
            {
                "card_id": card_id,
                "note_id": int(_entry_value(raw, "note_id", 0) or 0),
                "flagged_at": first_flagged_at,
                "last_seen_at": _newest_iso(active_entry_at, last_reviewed.get(card_id, "")),
                "deck": str(_entry_value(raw, "deck_name", "") or ""),
                "note_type": str(_entry_value(raw, "note_type_name", "") or ""),
                "tags": [str(tag) for tag in (_entry_value(raw, "tags", []) or [])],
                "fields": {str(name): str(value or "") for name, value in fields.items()},
                "front_html": str(_entry_value(raw, "front_html", "") or ""),
                "back_html": str(_entry_value(raw, "back_html", "") or ""),
                "front_text": str(_entry_value(raw, "front_text", "") or ""),
                "back_text": str(_entry_value(raw, "back_text", "") or ""),
                "media": [],
                "tracked_by_speed_streak": True,
            }
        )

    tracked_set = set(tracked_ids)
    for card_id in flagged_ids:
        if card_id in tracked_set:
            continue
        # A recently reviewed blue card belongs in the personal daily view even
        # if an older Speed Streak session failed to create its cohort record.
        # This is intentionally scoped to Pocket Knife's read-only export; the
        # public add-on still owns its normal queue state.
        try:
            card = mw.col.get_card(card_id)
            note = card.note()
            note_type = note.note_type() if hasattr(note, "note_type") else None
            if not isinstance(note_type, dict):
                note_type = {}
            seen_at = last_reviewed.get(card_id, "")
            cards.append(
                {
                    "card_id": card_id,
                    "note_id": int(getattr(note, "id", 0) or 0),
                    "flagged_at": seen_at,
                    "last_seen_at": seen_at,
                    "deck": str(mw.col.decks.name(int(getattr(card, "did", 0) or 0)) or ""),
                    "note_type": str(note_type.get("name", "") or ""),
                    "tags": [str(tag) for tag in (getattr(note, "tags", []) or [])],
                    "fields": {str(name): str(value or "") for name, value in note.items()},
                    "front_html": str(card.question() or ""),
                    "back_html": str(card.answer() or ""),
                    "front_text": "",
                    "back_text": "",
                    "media": [],
                    "tracked_by_speed_streak": False,
                }
            )
        except Exception:
            continue
    return {
        "source_addon": package_name,
        "review_later_flag": flag,
        "cards": cards,
    }
