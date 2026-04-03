from __future__ import annotations

import json
from typing import Any

import aqt
from aqt import gui_hooks, mw
from aqt.qt import QAction, QTimer
from aqt.utils import showInfo

from .common import user_files_dir


SUSPENDED_SEARCH_TAG = "anki-pocket-knife:suspended-recent"
SUSPENDED_SEARCH_PROMPT = "is:suspended"
SUSPENDED_TIMES_PATH = user_files_dir() / "suspended_card_times.json"
_HOOK_REGISTERED = False
_sync_timer: QTimer | None = None


def _load_suspended_times() -> dict[int, int]:
    if not SUSPENDED_TIMES_PATH.exists():
        return {}
    try:
        data = json.loads(SUSPENDED_TIMES_PATH.read_text(encoding="utf-8"))
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
        if card_id <= 0:
            continue
        cleaned[card_id] = timestamp
    return cleaned


def _save_suspended_times(values: dict[int, int]) -> None:
    payload = {str(card_id): int(timestamp) for card_id, timestamp in sorted(values.items())}
    SUSPENDED_TIMES_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _current_suspended_rows() -> list[tuple[int, int]]:
    rows = mw.col.db.all(
        """
        SELECT c.id, c.mod
        FROM cards AS c
        WHERE c.queue = -1
        ORDER BY c.mod DESC, c.id DESC
        """
    )
    return [(int(card_id), int(mod_value or 0)) for card_id, mod_value in rows]


def sync_suspended_card_times() -> dict[int, int]:
    current_rows = _current_suspended_rows()
    current_map = {card_id: mod_value for card_id, mod_value in current_rows}

    stored_times = _load_suspended_times()
    changed = False

    for card_id, mod_value in current_map.items():
        if card_id not in stored_times:
            stored_times[card_id] = int(mod_value)
            changed = True

    for card_id in list(stored_times.keys()):
        if card_id not in current_map:
            del stored_times[card_id]
            changed = True

    if changed:
        _save_suspended_times(stored_times)

    return stored_times


def ordered_suspended_card_ids() -> list[int]:
    current_rows = _current_suspended_rows()
    if not current_rows:
        stored_times = _load_suspended_times()
        if stored_times:
            _save_suspended_times({})
        return []

    suspended_times = sync_suspended_card_times()
    sorted_rows = sorted(
        current_rows,
        key=lambda row: (
            int(suspended_times.get(int(row[0]), int(row[1]))),
            int(row[1]),
            int(row[0]),
        ),
        reverse=True,
    )
    return [int(card_id) for card_id, _mod_value in sorted_rows]


def _apply_suspended_browser_search(search_context: Any) -> None:
    if getattr(search_context, "search", "") != SUSPENDED_SEARCH_TAG:
        return

    card_ids = ordered_suspended_card_ids()
    search_context.search = SUSPENDED_SEARCH_PROMPT
    search_context.ids = card_ids


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


def open_suspended_cards_browser() -> None:
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
    browser.search_for(SUSPENDED_SEARCH_TAG, SUSPENDED_SEARCH_PROMPT)

    if not ordered_suspended_card_ids():
        showInfo("No suspended cards are available right now.")


def _schedule_sync(*_args: Any) -> None:
    global _sync_timer
    if _sync_timer is None:
        return
    _sync_timer.start(750)


def _on_operation_did_execute(changes: Any, handler: object | None) -> None:
    del handler
    if not getattr(changes, "card", False) and not getattr(changes, "browser_table", False):
        return
    _schedule_sync()


def _on_main_window_init() -> None:
    global _sync_timer
    if _sync_timer is None:
        _sync_timer = QTimer(mw)
        _sync_timer.setSingleShot(True)
        _sync_timer.setInterval(750)
        _sync_timer.timeout.connect(sync_suspended_card_times)
    sync_suspended_card_times()


def build_open_suspended_cards_action(parent) -> QAction:
    action = QAction("Open Suspended Cards In Browser", parent)
    action.triggered.connect(lambda *_args: open_suspended_cards_browser())
    return action


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    browser_will_search = getattr(gui_hooks, "browser_will_search", None)
    if browser_will_search is not None:
        browser_will_search.append(_apply_suspended_browser_search)

    operation_did_execute = getattr(gui_hooks, "operation_did_execute", None)
    if operation_did_execute is not None:
        operation_did_execute.append(_on_operation_did_execute)

    gui_hooks.main_window_did_init.append(_on_main_window_init)
    _HOOK_REGISTERED = True
