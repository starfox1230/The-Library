from __future__ import annotations

import json
import time
from typing import Any

import aqt
from aqt import gui_hooks, mw
from aqt.qt import QAction
from aqt.utils import showInfo

from .common import user_files_dir
from .settings import get_setting, set_setting


SETTING_NAME = "recent_leech_banner"
RECENT_LEECH_WINDOW_HOURS = 48
RECENT_LEECH_WINDOW_SECONDS = RECENT_LEECH_WINDOW_HOURS * 60 * 60
RECENT_LEECH_SEARCH_TAG = "anki-pocket-knife:recent-leeches"
RECENT_LEECH_SEARCH_PROMPT = "tag:leech"
RECENT_LEECH_OPEN_MESSAGE = "anki-pocket-knife:open-recent-leeches"
RECENT_LEECH_EVENTS_PATH = user_files_dir() / "recent_leech_events.json"
_HOOK_REGISTERED = False
_pre_answer_leech_state: dict[int, bool] = {}


def is_recent_leech_banner_enabled() -> bool:
    return bool(get_setting(SETTING_NAME))


def _refresh_deck_browser() -> None:
    deck_browser = getattr(mw, "deckBrowser", None)
    if deck_browser is None:
        return

    refresh = getattr(deck_browser, "refresh", None)
    if callable(refresh):
        try:
            refresh()
            return
        except Exception:
            pass

    show = getattr(deck_browser, "show", None)
    if callable(show):
        try:
            show()
        except Exception:
            pass


def set_recent_leech_banner_enabled(enabled: bool) -> bool:
    value = bool(set_setting(SETTING_NAME, bool(enabled)))
    try:
        from .menu import sync_settings_ui
    except Exception:
        sync_settings_ui = None
    if callable(sync_settings_ui):
        try:
            sync_settings_ui()
        except Exception:
            pass
    _refresh_deck_browser()
    return value


def _now_seconds() -> int:
    return int(time.time())


def _cutoff_seconds() -> int:
    return _now_seconds() - RECENT_LEECH_WINDOW_SECONDS


def _cutoff_millis() -> int:
    return _cutoff_seconds() * 1000


def _load_event_times() -> dict[int, int]:
    if not RECENT_LEECH_EVENTS_PATH.exists():
        return {}
    try:
        data = json.loads(RECENT_LEECH_EVENTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}

    cleaned: dict[int, int] = {}
    for raw_card_id, raw_timestamp in data.items():
        try:
            card_id = int(raw_card_id)
            timestamp = int(raw_timestamp)
        except Exception:
            continue
        if card_id <= 0 or timestamp <= 0:
            continue
        cleaned[card_id] = timestamp
    return cleaned


def _save_event_times(values: dict[int, int]) -> None:
    payload = {str(card_id): int(timestamp) for card_id, timestamp in sorted(values.items())}
    RECENT_LEECH_EVENTS_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _prune_event_times(values: dict[int, int]) -> dict[int, int]:
    keep_after = _now_seconds() - (30 * 24 * 60 * 60)
    return {
        int(card_id): int(timestamp)
        for card_id, timestamp in values.items()
        if int(card_id) > 0 and int(timestamp) >= keep_after
    }


def _record_recent_leech(card_id: int, timestamp: int | None = None) -> None:
    safe_card_id = int(card_id)
    if safe_card_id <= 0:
        return

    event_times = _prune_event_times(_load_event_times())
    if safe_card_id in event_times:
        return

    safe_timestamp = int(timestamp or _now_seconds())
    if safe_timestamp <= 0:
        safe_timestamp = _now_seconds()
    event_times[safe_card_id] = safe_timestamp
    _save_event_times(event_times)


def _card_id(card: Any) -> int:
    try:
        return int(getattr(card, "id", 0) or 0)
    except Exception:
        return 0


def _card_note_has_leech_tag(card: Any) -> bool:
    try:
        note = card.note()
    except Exception:
        note = None
    if note is None:
        return False

    raw_tags = getattr(note, "tags", [])
    if isinstance(raw_tags, str):
        tags = [part for part in raw_tags.split() if part]
    else:
        tags = [str(tag) for tag in raw_tags or []]
    return any(str(tag).casefold() == "leech" for tag in tags)


def _recent_backfill_rows() -> list[tuple[int, int]]:
    rows = mw.col.db.all(
        """
        SELECT c.id, c.mod, MAX(CAST(r.id / 1000 AS INTEGER))
        FROM cards AS c
        JOIN notes AS n ON n.id = c.nid
        LEFT JOIN revlog AS r ON r.cid = c.id AND r.id >= ?
        WHERE c.mod >= ?
          AND LOWER(' ' || REPLACE(COALESCE(n.tags, ''), '　', ' ') || ' ') LIKE '% leech %'
          AND (c.queue = -1 OR r.id IS NOT NULL)
        GROUP BY c.id, c.mod
        ORDER BY c.mod DESC, c.id DESC
        """,
        int(_cutoff_millis()),
        int(_cutoff_seconds()),
    )

    merged: list[tuple[int, int]] = []
    for raw_card_id, raw_mod, raw_review in rows:
        try:
            card_id = int(raw_card_id)
            mod_value = int(raw_mod or 0)
            review_value = int(raw_review or 0)
        except Exception:
            continue
        if card_id <= 0:
            continue
        merged.append((card_id, max(mod_value, review_value)))
    return merged


def sync_recent_leech_events() -> dict[int, int]:
    stored = _prune_event_times(_load_event_times())
    changed = False

    for card_id, timestamp in _recent_backfill_rows():
        if timestamp <= 0:
            continue
        if int(stored.get(card_id, 0)) >= int(timestamp):
            continue
        stored[int(card_id)] = int(timestamp)
        changed = True

    if changed or stored != _load_event_times():
        _save_event_times(stored)
    return stored


def _existing_card_ids(card_ids: list[int]) -> set[int]:
    safe_ids = [int(card_id) for card_id in card_ids if int(card_id) > 0]
    if not safe_ids:
        return set()
    placeholders = ", ".join("?" for _ in safe_ids)
    rows = mw.col.db.all(
        f"SELECT id FROM cards WHERE id IN ({placeholders})",
        *safe_ids,
    )
    return {int(row[0]) for row in rows}


def recent_leech_rows() -> list[tuple[int, int]]:
    event_times = sync_recent_leech_events()
    cutoff = _cutoff_seconds()
    rows = [
        (int(card_id), int(timestamp))
        for card_id, timestamp in event_times.items()
        if int(card_id) > 0 and int(timestamp) >= cutoff
    ]
    if not rows:
        return []

    existing = _existing_card_ids([card_id for card_id, _timestamp in rows])
    filtered = [(card_id, timestamp) for card_id, timestamp in rows if card_id in existing]
    return sorted(filtered, key=lambda row: (int(row[1]), int(row[0])), reverse=True)


def recent_leech_count() -> int:
    return len(recent_leech_rows())


def recent_leeches_summary() -> str:
    count = recent_leech_count()
    if count == 1:
        return "1 leech has been recorded in the last 48 hours."
    return f"{count} leeches have been recorded in the last 48 hours."


def _browser_cards_mode(browser: Any) -> None:
    table = getattr(browser, "table", None)
    if table is None:
        return
    is_notes_mode = getattr(table, "is_notes_mode", None)
    if not callable(is_notes_mode):
        return
    try:
        currently_notes_mode = bool(is_notes_mode())
    except Exception:
        return
    if not currently_notes_mode:
        return

    toggle = getattr(browser, "on_table_state_changed", None)
    if callable(toggle):
        try:
            toggle(False)
            return
        except Exception:
            pass


def open_recent_leeches_browser() -> None:
    rows = recent_leech_rows()
    if not rows:
        showInfo("No leeches were found in the last 48 hours.")
        return

    browser = None
    dialogs = getattr(aqt, "dialogs", None)
    opener = getattr(dialogs, "open", None) if dialogs is not None else None
    if callable(opener):
        browser = opener("Browser", mw)

    if browser is None:
        showInfo("Could not open Anki's Browser window.")
        return

    _browser_cards_mode(browser)
    browser.activateWindow()
    browser.raise_()
    browser.search_for(RECENT_LEECH_SEARCH_TAG, RECENT_LEECH_SEARCH_PROMPT)


def _recent_leech_button_label(count: int) -> str:
    if count == 1:
        return "1 leech in the last 48 hours, click to view."
    return f"{count} leeches in the last 48 hours, click to view."


def _deck_browser_banner_html(count: int) -> str:
    label = _recent_leech_button_label(int(count))
    return f"""
<div class="anki-pocket-knife-recent-leeches" style="margin: 0 0 14px 0;">
  <button
    type="button"
    onclick="pycmd('{RECENT_LEECH_OPEN_MESSAGE}'); return false;"
    style="display: inline-block; box-sizing: border-box; padding: 10px 12px; text-align: left; cursor: pointer; max-width: min(100%, 44rem); white-space: normal;"
  >
    {label}
  </button>
</div>
"""


def _on_deck_browser_will_render_content(deck_browser: Any, content: Any) -> None:
    del deck_browser
    if not is_recent_leech_banner_enabled():
        return

    count = recent_leech_count()
    if count <= 0:
        return

    banner_html = _deck_browser_banner_html(count)
    current_tree = getattr(content, "tree", None)
    if isinstance(current_tree, str):
        content.tree = f"{banner_html}{current_tree}"
        return

    current_stats = getattr(content, "stats", None)
    if isinstance(current_stats, str):
        content.stats = f"{banner_html}{current_stats}"


def _is_deck_browser_context(context: Any) -> bool:
    if context is getattr(mw, "deckBrowser", None):
        return True
    return getattr(getattr(context, "__class__", None), "__name__", "") == "DeckBrowser"


def _on_webview_did_receive_js_message(
    handled: tuple[bool, Any],
    message: str,
    context: Any,
) -> tuple[bool, Any]:
    if handled[0]:
        return handled
    if message != RECENT_LEECH_OPEN_MESSAGE:
        return handled
    if not _is_deck_browser_context(context):
        return handled

    open_recent_leeches_browser()
    return (True, None)


def _apply_recent_leech_browser_search(search_context: Any) -> None:
    if getattr(search_context, "search", "") != RECENT_LEECH_SEARCH_TAG:
        return

    rows = recent_leech_rows()
    search_context.search = RECENT_LEECH_SEARCH_PROMPT
    search_context.ids = [int(card_id) for card_id, _timestamp in rows]


def _on_reviewer_did_show_question(card: Any) -> None:
    card_id = _card_id(card)
    if card_id <= 0:
        return
    _pre_answer_leech_state[card_id] = _card_note_has_leech_tag(card)


def _on_reviewer_did_answer_card(reviewer: Any, card: Any, ease: int) -> None:
    del reviewer
    del ease

    card_id = _card_id(card)
    if card_id <= 0:
        return

    had_leech_tag = bool(_pre_answer_leech_state.pop(card_id, False))
    has_leech_tag = _card_note_has_leech_tag(card)
    if had_leech_tag or not has_leech_tag:
        return

    try:
        timestamp = int(getattr(card, "mod", 0) or 0)
    except Exception:
        timestamp = 0
    _record_recent_leech(card_id, timestamp if timestamp > 0 else None)


def build_open_recent_leeches_action(parent) -> QAction:
    action = QAction("Open Recent Leeches In Browser", parent)
    action.triggered.connect(lambda *_args: open_recent_leeches_browser())
    return action


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    deck_browser_hook = getattr(gui_hooks, "deck_browser_will_render_content", None)
    if deck_browser_hook is not None:
        deck_browser_hook.append(_on_deck_browser_will_render_content)

    browser_will_search = getattr(gui_hooks, "browser_will_search", None)
    if browser_will_search is not None:
        browser_will_search.append(_apply_recent_leech_browser_search)

    webview_hook = getattr(gui_hooks, "webview_did_receive_js_message", None)
    if webview_hook is not None:
        webview_hook.append(_on_webview_did_receive_js_message)

    reviewer_show_question = getattr(gui_hooks, "reviewer_did_show_question", None)
    if reviewer_show_question is not None:
        reviewer_show_question.append(_on_reviewer_did_show_question)

    reviewer_answer = getattr(gui_hooks, "reviewer_did_answer_card", None)
    if reviewer_answer is not None:
        reviewer_answer.append(_on_reviewer_did_answer_card)

    main_window_did_init = getattr(gui_hooks, "main_window_did_init", None)
    if main_window_did_init is not None:
        main_window_did_init.append(lambda: sync_recent_leech_events())

    _HOOK_REGISTERED = True
