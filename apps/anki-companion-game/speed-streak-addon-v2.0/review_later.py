from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Callable, Iterator

from aqt import dialogs, gui_hooks, mw
from aqt.webview import AnkiWebView
from aqt.qt import (
    QApplication,
    QComboBox,
    QDialog,
    QEvent,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .data_paths import speed_streak_data_root


ADDON_ROOT = Path(__file__).resolve().parent
REVIEW_LATER_TAG_PREFIX = "speed_streak::review_later"
REVIEW_LATER_TODAY_OPEN_MESSAGE = "speed-streak:open-review-later-manager-today"
SHARED_DECK_ACTIONS_STYLE_ID = "anki-shared-deck-actions-style"
SHARED_DECK_ACTIONS_CONTAINER_START = "<!--anki-shared-deck-actions:start-->"
SHARED_DECK_ACTIONS_CONTAINER_END = "<!--anki-shared-deck-actions:end-->"
SHARED_DECK_ACTIONS_CONTAINER_OPEN = '<div id="anki-shared-deck-actions-row" class="anki-shared-deck-actions-row">'
SHARED_DECK_ACTIONS_CONTAINER_CLOSE = "</div>"
SHARED_DECK_ACTIONS_STYLE = f"""
<style id="{SHARED_DECK_ACTIONS_STYLE_ID}">
  #anki-shared-deck-actions-row {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 10px;
    margin: 0 0 14px 0;
  }}

  .anki-shared-deck-action-slot {{
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  .anki-shared-deck-action-button {{
    appearance: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    min-height: 38px;
    padding: 8px 14px;
    border-radius: 999px;
    border: 1px solid rgba(0, 0, 0, 0.14);
    background: var(--canvas, #ffffff);
    color: inherit;
    font: 600 13px/1.2 "Segoe UI", system-ui, sans-serif;
    text-align: center;
    white-space: nowrap;
    cursor: pointer;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }}

  .anki-shared-deck-action-button:hover {{
    background: rgba(127, 127, 127, 0.08);
  }}
</style>
""".strip()
_SHARED_DECK_ACTION_BLOCK_RE = re.compile(
    r"<!--anki-shared-deck-action:(?P<key>.+?):start-->(?P<block>.*?)<!--anki-shared-deck-action:(?P=key):end-->",
    re.DOTALL,
)
_SHARED_DECK_ACTION_CONTAINER_RE = re.compile(
    re.escape(SHARED_DECK_ACTIONS_CONTAINER_START)
    + r"(?P<body>.*?)"
    + re.escape(SHARED_DECK_ACTIONS_CONTAINER_END),
    re.DOTALL,
)
_SHARED_DECK_ACTION_ORDER_RE = re.compile(r'data-anki-deck-action-order="(?P<order>-?\d+)"')


class _HtmlToTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"br", "p", "div", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def get_text(self) -> str:
        text = "".join(self.parts)
        lines = [line.rstrip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line).strip()


def html_to_text(html: str) -> str:
    parser = _HtmlToTextParser()
    parser.feed(html or "")
    return parser.get_text()


def build_shared_deck_action_item(*, key: str, order: int, message: str, label: str) -> str:
    safe_message = str(message).replace("\\", "\\\\").replace("'", "\\'")
    return (
        f"<!--anki-shared-deck-action:{key}:start-->"
        f'<div class="anki-shared-deck-action-slot" data-anki-deck-action-order="{int(order)}" '
        f'data-anki-deck-action-key="{escape(str(key), quote=True)}">'
        f'<button type="button" class="anki-shared-deck-action-button" '
        f'onclick="pycmd(\'{safe_message}\'); return false;">{escape(str(label))}</button>'
        f"</div>"
        f"<!--anki-shared-deck-action:{key}:end-->"
    )


def _shared_deck_action_order(item_html: str) -> int:
    match = _SHARED_DECK_ACTION_ORDER_RE.search(str(item_html))
    if match is None:
        return 0
    try:
        return int(match.group("order"))
    except Exception:
        return 0


def inject_shared_deck_action_html(content_html: str, item_html: str) -> str:
    html = str(content_html or "")
    prefix = "" if SHARED_DECK_ACTIONS_STYLE_ID in html else f"{SHARED_DECK_ACTIONS_STYLE}\n"
    match = _SHARED_DECK_ACTION_CONTAINER_RE.search(html)
    if match is None:
        container_html = (
            f"{SHARED_DECK_ACTIONS_CONTAINER_START}"
            f"{SHARED_DECK_ACTIONS_CONTAINER_OPEN}{item_html}{SHARED_DECK_ACTIONS_CONTAINER_CLOSE}"
            f"{SHARED_DECK_ACTIONS_CONTAINER_END}"
        )
        return f"{prefix}{container_html}{html}"

    existing_items = [entry.group(0) for entry in _SHARED_DECK_ACTION_BLOCK_RE.finditer(match.group("body"))]
    existing_items.append(str(item_html))
    existing_items.sort(key=_shared_deck_action_order)
    container_html = (
        f"{SHARED_DECK_ACTIONS_CONTAINER_START}"
        f"{SHARED_DECK_ACTIONS_CONTAINER_OPEN}{''.join(existing_items)}{SHARED_DECK_ACTIONS_CONTAINER_CLOSE}"
        f"{SHARED_DECK_ACTIONS_CONTAINER_END}"
    )
    return f"{prefix}{html[:match.start()]}{container_html}{html[match.end():]}"


@dataclass
class ReviewLaterEntry:
    added_at: datetime
    card_id: int
    note_id: int
    deck_name: str
    note_type_name: str
    tags: list[str]
    fields: dict[str, str]
    front_html: str
    back_html: str
    front_text: str
    back_text: str


def _data_root() -> Path:
    root = speed_streak_data_root(ADDON_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _db_path() -> Path:
    return _data_root() / "review_later.sqlite3"


def _state_path() -> Path:
    return _data_root() / "review_later_state.json"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS review_later_cohorts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            note_id INTEGER NOT NULL,
            flag INTEGER NOT NULL,
            entered_at TEXT NOT NULL,
            removed_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_review_later_active
        ON review_later_cohorts(flag, removed_at, card_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_review_later_card_flag
        ON review_later_cohorts(card_id, flag, removed_at)
        """
    )
    return conn


@contextmanager
def _open_connection() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def _load_state() -> dict[str, dict[str, str]]:
    state_path = _state_path()
    if not state_path.exists():
        return {}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    normalized: dict[str, dict[str, str]] = {}
    for flag_key, entries in data.items():
        if not isinstance(entries, dict):
            continue
        normalized[str(flag_key)] = {
            str(card_id): str(entered_at)
            for card_id, entered_at in entries.items()
            if str(card_id).strip() and str(entered_at).strip()
        }
    return normalized


def _save_state(state: dict[str, dict[str, str]]) -> None:
    state_path = _state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _state_entered_at(flag: int, card_id: int) -> str | None:
    state = _load_state()
    return state.get(str(int(flag)), {}).get(str(int(card_id)))


def _set_state_entered_at(flag: int, card_id: int, entered_at: str) -> None:
    state = _load_state()
    flag_key = str(int(flag))
    card_key = str(int(card_id))
    if state.get(flag_key, {}).get(card_key) == str(entered_at):
        return
    state.setdefault(flag_key, {})[card_key] = str(entered_at)
    _save_state(state)


def _remove_state_entered_at(flag: int, card_id: int) -> None:
    state = _load_state()
    flag_key = str(int(flag))
    entries = state.get(flag_key)
    if not entries or str(int(card_id)) not in entries:
        return
    entries.pop(str(int(card_id)), None)
    if not entries:
        state.pop(flag_key, None)
    _save_state(state)


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _cohort_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.now()


def _is_before_today(value: str) -> bool:
    try:
        return datetime.fromisoformat(value).date() < datetime.now().date()
    except Exception:
        return False


def _col_get_card(card_id: int) -> Any:
    getter = getattr(mw.col, "get_card", None)
    if callable(getter):
        return getter(card_id)
    getter = getattr(mw.col, "getCard", None)
    if callable(getter):
        return getter(card_id)
    raise RuntimeError("Unable to load card from collection.")


def _deck_name(card: Any) -> str:
    did = getattr(card, "odid", 0) or getattr(card, "did", 0)
    try:
        return mw.col.decks.name(did)
    except Exception:
        return "Unknown Deck"


def _note_type_name(note: Any) -> str:
    for attr in ("note_type", "notetype", "model"):
        fn = getattr(note, attr, None)
        if callable(fn):
            try:
                info = fn()
                if isinstance(info, dict):
                    return str(info.get("name", "Unknown Note Type"))
            except Exception:
                continue
    return "Unknown Note Type"


def _note_fields(note: Any) -> dict[str, str]:
    try:
        items = note.items()
        return {str(name): str(value) for name, value in items}
    except Exception:
        fields = getattr(note, "fields", [])
        return {f"Field {idx + 1}": str(value) for idx, value in enumerate(fields)}


def _note_tag_list(note: Any) -> list[str]:
    return [str(tag) for tag in getattr(note, "tags", [])]


def _display_note_tags(note: Any) -> list[str]:
    return [tag for tag in _note_tag_list(note) if not tag.startswith(f"{REVIEW_LATER_TAG_PREFIX}::")]


def _sanitize_timestamp_tag_value(iso_value: str) -> str:
    return str(iso_value).replace(":", "-")


def _restore_timestamp_tag_value(tag_value: str) -> str:
    text = str(tag_value)
    if "T" not in text:
        return text
    date_part, time_part = text.split("T", 1)
    if time_part.count("-") >= 2:
        parts = time_part.split("-")
        time_part = ":".join(parts[:3]) + (f".{parts[3]}" if len(parts) > 3 else "")
    return f"{date_part}T{time_part}"


def _review_later_tag_prefix_for_ord(card_ord: int) -> str:
    return f"{REVIEW_LATER_TAG_PREFIX}::{int(card_ord)}::"


def _build_review_later_tag(card_ord: int, entered_at_iso: str) -> str:
    return f"{_review_later_tag_prefix_for_ord(card_ord)}{_sanitize_timestamp_tag_value(entered_at_iso)}"


def _parse_review_later_tag(tag: str) -> tuple[int, str] | None:
    prefix = f"{REVIEW_LATER_TAG_PREFIX}::"
    if not str(tag).startswith(prefix):
        return None
    parts = str(tag).split("::", 3)
    if len(parts) != 4:
        return None
    try:
        card_ord = int(parts[2])
    except Exception:
        return None
    return (card_ord, _restore_timestamp_tag_value(parts[3]))


def _review_later_tag_timestamp_for_ord(note: Any, card_ord: int) -> str | None:
    prefix = _review_later_tag_prefix_for_ord(card_ord)
    for tag in _note_tag_list(note):
        if tag.startswith(prefix):
            parsed = _parse_review_later_tag(tag)
            if parsed is not None:
                return parsed[1]
    return None


def _set_note_tags(note: Any, tags: list[str]) -> None:
    setattr(note, "tags", list(dict.fromkeys(str(tag) for tag in tags if str(tag).strip())))
    for method_name in ("flush", "save"):
        method = getattr(note, method_name, None)
        if callable(method):
            try:
                method()
                return
            except Exception:
                continue
    update_note = getattr(mw.col, "update_note", None)
    if callable(update_note):
        update_note(note)
        return
    update_note = getattr(mw.col, "updateNote", None)
    if callable(update_note):
        update_note(note)


def _ensure_review_later_note_tag(note: Any, *, card_ord: int, entered_at_iso: str) -> None:
    prefix = _review_later_tag_prefix_for_ord(card_ord)
    current_tags = _note_tag_list(note)
    next_tags = [tag for tag in current_tags if not tag.startswith(prefix)]
    next_tags.append(_build_review_later_tag(card_ord, entered_at_iso))
    if next_tags != current_tags:
        _set_note_tags(note, next_tags)


def _remove_review_later_note_tag(note: Any, *, card_ord: int) -> None:
    prefix = _review_later_tag_prefix_for_ord(card_ord)
    current_tags = _note_tag_list(note)
    next_tags = [tag for tag in current_tags if not tag.startswith(prefix)]
    if next_tags != current_tags:
        _set_note_tags(note, next_tags)


def _flag_search(flag: int) -> str:
    return f"flag:{flag}"


def _ensure_active_cohort(
    conn: sqlite3.Connection,
    *,
    card_id: int,
    note_id: int,
    flag: int,
    entered_at: str | None = None,
) -> None:
    row = conn.execute(
        """
        SELECT id
        FROM review_later_cohorts
        WHERE card_id = ? AND flag = ? AND removed_at IS NULL
        ORDER BY id DESC
        LIMIT 1
        """,
        (card_id, flag),
    ).fetchone()
    if row is not None:
        return
    conn.execute(
        """
        INSERT INTO review_later_cohorts(card_id, note_id, flag, entered_at, removed_at)
        VALUES (?, ?, ?, ?, NULL)
        """,
        (card_id, note_id, flag, entered_at or _now_iso()),
    )


def _close_active_cohort(conn: sqlite3.Connection, *, card_id: int, flag: int, removed_at: str | None = None) -> None:
    conn.execute(
        """
        UPDATE review_later_cohorts
        SET removed_at = COALESCE(removed_at, ?)
        WHERE card_id = ? AND flag = ? AND removed_at IS NULL
        """,
        (removed_at or _now_iso(), card_id, flag),
    )


def _active_db_entered_at(conn: sqlite3.Connection, *, card_id: int, flag: int) -> str | None:
    row = conn.execute(
        """
        SELECT entered_at
        FROM review_later_cohorts
        WHERE card_id = ? AND flag = ? AND removed_at IS NULL
        ORDER BY id DESC
        LIMIT 1
        """,
        (card_id, flag),
    ).fetchone()
    if row is None:
        return None
    return str(row["entered_at"])


def sync_review_later_membership(*, card_id: int, note_id: int, card_ord: int, current_flag: int, review_later_flag: int) -> None:
    if review_later_flag <= 0 or card_id <= 0:
        return
    with _open_connection() as conn:
        if int(current_flag or 0) == int(review_later_flag):
            stored_entered_at = (
                _state_entered_at(int(review_later_flag), int(card_id))
                or _active_db_entered_at(conn, card_id=int(card_id), flag=int(review_later_flag))
            )
            entered_at = (
                _now_iso()
                if stored_entered_at and _is_before_today(stored_entered_at)
                else (stored_entered_at or _now_iso())
            )
            if stored_entered_at and entered_at != stored_entered_at:
                _close_active_cohort(
                    conn,
                    card_id=int(card_id),
                    flag=int(review_later_flag),
                    removed_at=entered_at,
                )
            _ensure_active_cohort(
                conn,
                card_id=int(card_id),
                note_id=int(note_id),
                flag=int(review_later_flag),
                entered_at=entered_at,
            )
            _set_state_entered_at(int(review_later_flag), int(card_id), entered_at)
        else:
            _close_active_cohort(
                conn,
                card_id=int(card_id),
                flag=int(review_later_flag),
            )
            _remove_state_entered_at(int(review_later_flag), int(card_id))
        conn.commit()


def reconcile_review_later_flag(flag: int) -> None:
    if flag <= 0:
        return
    current_card_ids = [int(card_id) for card_id in mw.col.find_cards(_flag_search(flag))]
    current_set = set(current_card_ids)
    now_iso = _now_iso()

    with _open_connection() as conn:
        active_rows = conn.execute(
            """
            SELECT id, card_id
            FROM review_later_cohorts
            WHERE flag = ? AND removed_at IS NULL
            """,
            (flag,),
        ).fetchall()
        active_card_ids = {int(row["card_id"]) for row in active_rows}

        for card_id in current_set:
            try:
                card = _col_get_card(card_id)
                note = card.note()
                card_ord = int(getattr(card, "ord", 0) or 0)
                entered_at = (
                    _state_entered_at(flag, card_id)
                    or _active_db_entered_at(conn, card_id=card_id, flag=flag)
                    or _review_later_tag_timestamp_for_ord(note, card_ord)
                )
                if not entered_at:
                    # Do not silently adopt every card that happens to share the Review Later
                    # flag color. Only cards already tracked by Speed Streak (or carrying a
                    # legacy Review Later tag) belong in the manager.
                    continue
                _ensure_active_cohort(
                    conn,
                    card_id=card_id,
                    note_id=int(getattr(note, "id", 0) or 0),
                    flag=flag,
                    entered_at=entered_at,
                )
                _set_state_entered_at(flag, card_id, entered_at)
            except Exception:
                continue

        stale_ids = active_card_ids - current_set
        for card_id in stale_ids:
            _close_active_cohort(conn, card_id=card_id, flag=flag, removed_at=now_iso)
            _remove_state_entered_at(flag, card_id)

        conn.commit()


def _active_cohort_map(flag: int) -> dict[int, datetime]:
    cohort_map: dict[int, datetime] = {}
    current_card_ids = [int(value) for value in mw.col.find_cards(_flag_search(flag))]
    state = _load_state().get(str(int(flag)), {})
    for card_id in current_card_ids:
        entered_at = state.get(str(card_id))
        if entered_at:
            cohort_map[card_id] = _cohort_datetime(entered_at)
    with _open_connection() as conn:
        rows = conn.execute(
            """
            SELECT card_id, entered_at
            FROM review_later_cohorts
            WHERE flag = ? AND removed_at IS NULL
            ORDER BY id DESC
            """,
            (flag,),
        ).fetchall()
    for row in rows:
        card_id = int(row["card_id"])
        if card_id in current_card_ids and card_id not in cohort_map:
            cohort_map[card_id] = _cohort_datetime(str(row["entered_at"]))
    for card_id in current_card_ids:
        try:
            if card_id in cohort_map:
                continue
            card = _col_get_card(card_id)
            note = card.note()
            card_ord = int(getattr(card, "ord", 0) or 0)
            entered_at = _review_later_tag_timestamp_for_ord(note, card_ord)
            if entered_at:
                cohort_map[card_id] = _cohort_datetime(entered_at)
        except Exception:
            continue
    return cohort_map


def fetch_review_later_entries(flag: int) -> list[ReviewLaterEntry]:
    if flag <= 0:
        return []

    reconcile_review_later_flag(flag)
    active_map = _active_cohort_map(flag)
    card_ids = [int(card_id) for card_id in mw.col.find_cards(_flag_search(flag)) if int(card_id) in active_map]
    entries: list[ReviewLaterEntry] = []
    with _open_connection() as conn:
        for card_id in card_ids:
            try:
                card = _col_get_card(card_id)
                note = card.note()
                card_ord = int(getattr(card, "ord", 0) or 0)
                entered_at = (
                    active_map.get(card_id)
                    or (
                        _cohort_datetime(db_entered_at)
                        if (db_entered_at := _active_db_entered_at(conn, card_id=card_id, flag=flag))
                        else None
                    )
                    or (
                        _cohort_datetime(tag_entered_at)
                        if (tag_entered_at := _review_later_tag_timestamp_for_ord(note, card_ord))
                        else None
                    )
                    or datetime.min
                )
                fields = _note_fields(note)
                front_html = str(card.question() or "")
                back_html = str(card.answer() or "")
                entries.append(
                    ReviewLaterEntry(
                        added_at=entered_at,
                        card_id=int(card.id),
                        note_id=int(note.id),
                        deck_name=_deck_name(card),
                        note_type_name=_note_type_name(note),
                        tags=_display_note_tags(note),
                        fields=fields,
                        front_html=front_html,
                        back_html=back_html,
                        front_text=html_to_text(front_html),
                        back_text=html_to_text(back_html),
                    )
                )
            except Exception:
                continue

    entries.sort(key=lambda entry: (entry.added_at, entry.card_id), reverse=True)
    return entries


def build_copy_text(entries: list[ReviewLaterEntry]) -> str:
    chunks: list[str] = []
    for entry in entries:
        field_lines = [str(value).strip() for value in entry.fields.values() if str(value).strip()]
        chunks.append("\n".join(field_lines) or "(no fields)")
    return "\n\n".join(chunks).strip()


def preview_html(entries: list[ReviewLaterEntry], pending_card_removals: set[int] | None = None) -> str:
    pending_card_removals = set(pending_card_removals or set())
    if not entries:
        body = "<div class='empty'>No cards currently match the current Review Later filter.</div>"
    else:
        cards = []
        for entry in entries:
            tags = ", ".join(entry.tags) if entry.tags else "No tags"
            pending_remove = entry.card_id in pending_card_removals
            toggle_label = "Review Later Off" if pending_remove else "Review Later On"
            toggle_class = "toggle pending" if pending_remove else "toggle active"
            pending_copy = (
                "<div class='pending-copy'>This card will be removed from Review Later when you save and close.</div>"
                if pending_remove
                else "<div class='pending-copy stable'>This card will stay in Review Later unless you toggle it off.</div>"
            )
            cards.append(
                f"""
                <section class="entry{' pending-remove' if pending_remove else ''}">
                  <div class="entry-head">
                    <div class="meta">
                      <div><strong>{escape(entry.deck_name)}</strong></div>
                      <div>{escape(entry.note_type_name)}</div>
                      <div>Added {entry.added_at.strftime("%Y-%m-%d %H:%M:%S")}</div>
                    </div>
                    <div class="entry-actions">
                      <button class="entry-action secondary" type="button" onclick="return speedStreakReviewLaterAction('open-card', {int(entry.card_id)})">Open in Browser</button>
                      <button class="entry-action {toggle_class}" type="button" onclick="return speedStreakReviewLaterAction('toggle-card', {int(entry.card_id)})">{toggle_label}</button>
                    </div>
                  </div>
                  {pending_copy}
                  <div class="tags">{escape(tags)}</div>
                  <div class="card-face">
                    <div class="face-label">Front</div>
                    <div class="card-preview">{entry.front_html}</div>
                  </div>
                  <div class="card-face">
                    <div class="face-label">Back</div>
                    <div class="card-preview">{entry.back_html}</div>
                  </div>
                </section>
                """
            )
        body = "".join(cards)

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script>
    function speedStreakReviewLaterAction(action, cardId) {{
      if (typeof pycmd === "function") {{
        pycmd(`speed-streak:review-later-manager:${{action}}:${{cardId}}`);
      }}
      return false;
    }}
  </script>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      background: #141822;
      color: #eef2ff;
      font-family: "Segoe UI", system-ui, sans-serif;
    }}
    .wrap {{
      padding: 16px;
      display: grid;
      gap: 16px;
    }}
    .entry {{
      border: 1px solid rgba(136, 169, 255, 0.18);
      border-radius: 20px;
      background:
        radial-gradient(circle at top, rgba(71, 117, 255, 0.13), transparent 48%),
        linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
      padding: 16px;
      display: grid;
      gap: 12px;
      box-shadow: 0 14px 32px rgba(0, 0, 0, 0.26);
    }}
    .entry.pending-remove {{
      border-color: rgba(255, 170, 105, 0.28);
      background:
        radial-gradient(circle at top, rgba(255, 166, 82, 0.12), transparent 48%),
        linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
    }}
    .entry-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      flex-wrap: wrap;
    }}
    .meta {{
      color: #a8b7dc;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .entry-actions {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .entry-action {{
      appearance: none;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.14);
      padding: 8px 12px;
      background: rgba(255,255,255,0.06);
      color: #eef3ff;
      font: 700 12px/1 "Segoe UI", system-ui, sans-serif;
      letter-spacing: 0.02em;
      cursor: pointer;
    }}
    .entry-action.secondary {{
      border-color: rgba(136, 169, 255, 0.2);
    }}
    .entry-action.active {{
      border-color: rgba(101, 240, 194, 0.34);
      background: rgba(41, 118, 88, 0.36);
      color: #ddfff4;
    }}
    .entry-action.pending {{
      border-color: rgba(255, 188, 122, 0.34);
      background: rgba(122, 71, 28, 0.36);
      color: #fff0db;
    }}
    .entry-action:hover {{
      background: rgba(255,255,255,0.12);
    }}
    .pending-copy {{
      color: #ffc98a;
      font-size: 12px;
      line-height: 1.45;
    }}
    .pending-copy.stable {{
      color: #8ea0cc;
    }}
    .tags {{
      color: #d8e2ff;
      font-size: 13px;
      line-height: 1.5;
    }}
    .card-face {{
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(8,12,22,0.9), rgba(24,28,40,0.92));
      padding: 14px;
      border: 1px solid rgba(255,255,255,0.08);
      display: grid;
      gap: 10px;
    }}
    .face-label {{
      color: #8ea0cc;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
    .card-preview {{
      border-radius: 14px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.06);
      min-height: 72px;
      padding: 16px;
      color: #f6f8ff;
      line-height: 1.6;
      overflow-wrap: anywhere;
    }}
    .card-preview .card {{
      color: inherit;
      background: transparent;
      box-shadow: none;
    }}
    .empty {{
      color: #9fb0d8;
      padding: 16px;
    }}
  </style>
</head>
<body>
  <div class="wrap">{body}</div>
</body>
</html>
"""


def _date_filter_predicate(kind: str, past_days: int):
    now = datetime.now()
    today = now.date()

    if kind == "today":
        return lambda dt: dt.date() == today
    if kind == "yesterday":
        return lambda dt: dt.date() == (today - timedelta(days=1))
    if kind == "past_x":
        cutoff = now - timedelta(days=max(1, int(past_days)))
        return lambda dt: dt >= cutoff
    return lambda dt: True


def filter_entries(entries: list[ReviewLaterEntry], kind: str, past_days: int) -> list[ReviewLaterEntry]:
    pred = _date_filter_predicate(kind, past_days)
    return [entry for entry in entries if pred(entry.added_at)]


def review_later_today_count(flag: int) -> int:
    if flag <= 0:
        return 0
    reconcile_review_later_flag(flag)
    today = datetime.now().date()
    return sum(1 for added_at in _active_cohort_map(flag).values() if added_at.date() == today)


def build_review_later_today_button_html(count: int) -> str:
    safe_count = max(0, int(count or 0))
    if safe_count <= 0:
        return ""
    return build_shared_deck_action_item(
        key="speed-streak:review-later",
        order=30,
        message=REVIEW_LATER_TODAY_OPEN_MESSAGE,
        label=f"{safe_count} review later",
    )


def search_query_for_entries(entries: list[ReviewLaterEntry], flag: int, kind: str) -> str:
    if not entries:
        return ""
    return " or ".join(f"cid:{entry.card_id}" for entry in entries)


def _open_browser_for_query(query: str) -> None:
    browser = dialogs.open("Browser", mw)
    search_for = getattr(browser, "search_for", None)
    if callable(search_for):
        search_for(query)
        return
    search = getattr(browser, "search", None)
    if callable(search):
        search(query)
        return
    form = getattr(browser, "form", None)
    if form and hasattr(form, "searchEdit"):
        form.searchEdit.lineEdit().setText(query)
        browser.onSearchActivated()
        return
    raise RuntimeError("Browser search API not available.")


def _update_card(card: Any) -> None:
    for method_name in ("flush", "save"):
        method = getattr(card, method_name, None)
        if callable(method):
            try:
                method()
                return
            except Exception:
                continue
    update_card = getattr(mw.col, "update_card", None)
    if callable(update_card):
        update_card(card)
        return
    update_card = getattr(mw.col, "updateCard", None)
    if callable(update_card):
        update_card(card)


def _set_card_user_flag(card: Any, flag: int) -> None:
    for method_name in ("set_user_flag", "setUserFlag"):
        method = getattr(card, method_name, None)
        if callable(method):
            try:
                method(int(flag))
                return
            except Exception:
                continue
    current_flags = int(getattr(card, "flags", 0) or 0)
    setattr(card, "flags", (current_flags & ~0b111) | (int(flag) & 0b111))
    _update_card(card)


def _set_user_flag_for_cards(card_ids: list[int], flag: int) -> None:
    unique_ids = [int(card_id) for card_id in dict.fromkeys(int(card_id) for card_id in card_ids if int(card_id) > 0)]
    if not unique_ids:
        return

    collection_methods = [
        ("set_user_flag_for_cards", ((int(flag), unique_ids), {})),
        ("set_user_flag_for_cards", ((), {"flag": int(flag), "card_ids": unique_ids})),
        ("set_user_flag_for_cards", ((), {"flag": int(flag), "cids": unique_ids})),
        ("setUserFlag", ((int(flag), unique_ids), {})),
        ("setUserFlag", ((unique_ids, int(flag)), {})),
        ("set_user_flag", ((int(flag), unique_ids), {})),
        ("set_user_flag", ((), {"flag": int(flag), "card_ids": unique_ids})),
        ("set_user_flag", ((), {"flag": int(flag), "cids": unique_ids})),
    ]
    for method_name, (args, kwargs) in collection_methods:
        method = getattr(mw.col, method_name, None)
        if not callable(method):
            continue
        try:
            method(*args, **kwargs)
            return
        except TypeError:
            continue
        except Exception:
            continue

    for card_id in unique_ids:
        _set_card_user_flag(_col_get_card(card_id), int(flag))


class ReviewLaterManagerDialog(QDialog):
    def __init__(
        self,
        review_later_flag: int,
        *,
        review_later_today_button_enabled: bool = False,
        on_review_later_today_button_changed: Callable[[bool], bool | None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent or mw)
        self.review_later_flag = int(review_later_flag)
        self.review_later_today_button_enabled = bool(review_later_today_button_enabled)
        self.on_review_later_today_button_changed = on_review_later_today_button_changed
        self.entries: list[ReviewLaterEntry] = []
        self.visible_entries: list[ReviewLaterEntry] = []
        self.pending_card_removals: set[int] = set()
        self._bridge_hook_installed = False
        self.setWindowTitle("Review Later Manager")
        self.resize(920, 700)
        self._build_ui()
        self._attach_bridge_hook()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        controls_row = QHBoxLayout()
        controls_row.addWidget(QLabel("Added to Review Later:"))
        self.date_filter = QComboBox()
        self.date_filter.addItem("Today", "today")
        self.date_filter.addItem("Yesterday", "yesterday")
        self.date_filter.addItem("Past X days", "past_x")
        self.date_filter.addItem("All", "all")
        controls_row.addWidget(self.date_filter)
        controls_row.addWidget(QLabel("X:"))
        self.past_days = QSpinBox()
        self.past_days.setRange(1, 365)
        self.past_days.setValue(3)
        controls_row.addWidget(self.past_days)
        controls_row.addStretch(1)
        layout.addLayout(controls_row)

        button_row = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.copy_all_button = QPushButton("Copy All")
        self.filtered_deck_button = QPushButton("Make Filtered Deck")
        self.browser_button = QPushButton("Open All in Browser")
        self.deck_page_button_toggle = QPushButton()
        self.deck_page_button_toggle.setCheckable(True)
        self.deck_page_button_toggle.setToolTip("Show today's Review Later count above the main deck list.")
        self._sync_deck_page_button_toggle()
        self.close_button = QPushButton("Close")
        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.copy_all_button)
        button_row.addWidget(self.filtered_deck_button)
        button_row.addWidget(self.browser_button)
        button_row.addWidget(self.deck_page_button_toggle)
        button_row.addStretch(1)
        button_row.addWidget(self.close_button)
        layout.addLayout(button_row)

        self.preview = AnkiWebView(self)
        layout.addWidget(self.preview, 1)

        self.refresh_button.clicked.connect(self.refresh_entries)
        self.date_filter.currentIndexChanged.connect(self._apply_filter)
        self.past_days.valueChanged.connect(self._apply_filter)
        self.copy_all_button.clicked.connect(self.copy_all)
        self.filtered_deck_button.clicked.connect(self.make_filtered_deck)
        self.browser_button.clicked.connect(self.open_in_browser)
        self.deck_page_button_toggle.clicked.connect(self._on_deck_page_button_toggle_clicked)
        self.close_button.clicked.connect(self.close)

    def _sync_deck_page_button_toggle(self) -> None:
        enabled = bool(self.review_later_today_button_enabled)
        if self.deck_page_button_toggle.isChecked() != enabled:
            self.deck_page_button_toggle.setChecked(enabled)
        self.deck_page_button_toggle.setText("Deck Page Button On" if enabled else "Deck Page Button Off")

    def _on_deck_page_button_toggle_clicked(self, checked: bool) -> None:
        next_enabled = bool(checked)
        callback = self.on_review_later_today_button_changed
        if callable(callback):
            try:
                callback_result = callback(next_enabled)
                if callback_result is not None:
                    next_enabled = bool(callback_result)
            except Exception:
                next_enabled = bool(self.review_later_today_button_enabled)
        self.review_later_today_button_enabled = next_enabled
        self._sync_deck_page_button_toggle()

    def _attach_bridge_hook(self) -> None:
        if self._bridge_hook_installed:
            return
        gui_hooks.webview_did_receive_js_message.append(self._on_preview_js_message)
        self._bridge_hook_installed = True

    def _detach_bridge_hook(self) -> None:
        if not self._bridge_hook_installed:
            return
        try:
            gui_hooks.webview_did_receive_js_message.remove(self._on_preview_js_message)
        except Exception:
            pass
        self._bridge_hook_installed = False

    def _on_preview_js_message(self, handled: tuple[bool, Any], message: str, context: Any) -> tuple[bool, Any]:
        prefix = "speed-streak:review-later-manager:"
        if not str(message or "").startswith(prefix):
            return handled
        payload = str(message)[len(prefix) :]
        action, _, raw_card_id = payload.partition(":")
        try:
            card_id = int(raw_card_id or 0)
        except Exception:
            card_id = 0
        if action == "open-card" and card_id > 0:
            self.open_single_in_browser(card_id)
            return (True, None)
        if action == "toggle-card" and card_id > 0:
            self.toggle_pending_removal(card_id)
            return (True, None)
        return (True, None)

    def _render_preview(self) -> None:
        self.preview.stdHtml(preview_html(self.visible_entries, self.pending_card_removals))

    def _update_info_label(self) -> None:
        pending_count = len(self.pending_card_removals)
        suffix = f" | Pending removals: {pending_count}" if pending_count else ""
        self.info_label.setText(
            f"Review Later Flag: {self.review_later_flag} | Visible Cards: {len(self.visible_entries)} | Total Cards: {len(self.entries)}{suffix}"
        )

    def refresh_entries(self) -> None:
        if self.review_later_flag <= 0:
            self.entries = []
            self.visible_entries = []
            self.pending_card_removals.clear()
            self.info_label.setText("Choose a Review Later flag in Settings first.")
            self._render_preview()
            return

        self.entries = fetch_review_later_entries(self.review_later_flag)
        self.pending_card_removals.intersection_update({entry.card_id for entry in self.entries})
        self._apply_filter()

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
        self.refresh_entries()

    def event(self, event: Any) -> bool:
        if event is not None and getattr(event, "type", None) is not None:
            try:
                if event.type() == QEvent.Type.WindowActivate:
                    self.refresh_entries()
            except Exception:
                pass
        return super().event(event)

    def _apply_filter(self) -> None:
        kind = str(self.date_filter.currentData() or "all")
        past_days = int(self.past_days.value())
        self.past_days.setEnabled(kind == "past_x")
        self.visible_entries = filter_entries(self.entries, kind, past_days)
        self._update_info_label()
        self._render_preview()

    def copy_all(self) -> None:
        if not self.visible_entries:
            QMessageBox.information(self, "Review Later Manager", "No Review Later cards to copy.")
            return
        QApplication.clipboard().setText(build_copy_text(self.visible_entries))
        QMessageBox.information(
            self,
            "Review Later Manager",
            f"Copied the field text from {len(self.visible_entries)} cards.",
        )

    def open_in_browser(self) -> None:
        if not self.visible_entries:
            QMessageBox.information(self, "Review Later Manager", "No visible Review Later cards to open.")
            return
        query = search_query_for_entries(
            self.visible_entries,
            self.review_later_flag,
            str(self.date_filter.currentData() or "all"),
        )
        try:
            _open_browser_for_query(query)
        except Exception as exc:
            QMessageBox.warning(self, "Review Later Manager", f"Could not open Browser.\n\n{exc}")

    def open_single_in_browser(self, card_id: int) -> None:
        entry = next((entry for entry in self.entries if int(entry.card_id) == int(card_id)), None)
        if entry is None:
            QMessageBox.information(self, "Review Later Manager", "That card is no longer available.")
            return
        try:
            _open_browser_for_query(f"cid:{int(entry.card_id)}")
        except Exception as exc:
            QMessageBox.warning(self, "Review Later Manager", f"Could not open Browser.\n\n{exc}")

    def toggle_pending_removal(self, card_id: int) -> None:
        if int(card_id) in self.pending_card_removals:
            self.pending_card_removals.remove(int(card_id))
        else:
            self.pending_card_removals.add(int(card_id))
        self._update_info_label()
        self._render_preview()

    def _apply_pending_removals(self) -> None:
        card_ids = sorted(int(card_id) for card_id in self.pending_card_removals if int(card_id) > 0)
        if not card_ids:
            return
        _set_user_flag_for_cards(card_ids, 0)
        reconcile_review_later_flag(self.review_later_flag)
        self.pending_card_removals.clear()
        mw.reset()

    def _confirm_close(self) -> bool:
        pending_count = len(self.pending_card_removals)
        if pending_count <= 0:
            return True
        noun = "card" if pending_count == 1 else "cards"
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Review Later Manager")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setText(f"Save your changes to {pending_count} {noun}?")
        dialog.setInformativeText(
            "Choose Save to remove the Review Later flag from those cards now, "
            "Close Without Saving to keep all flags as they are, or Cancel to stay in the manager."
        )
        save_button = dialog.addButton(f"Save {pending_count} {noun}", QMessageBox.ButtonRole.AcceptRole)
        discard_button = dialog.addButton("Close Without Saving", QMessageBox.ButtonRole.DestructiveRole)
        cancel_button = dialog.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        dialog.setDefaultButton(save_button)
        dialog.exec()
        clicked = dialog.clickedButton()
        if clicked is save_button:
            try:
                self._apply_pending_removals()
                return True
            except Exception as exc:
                QMessageBox.warning(self, "Review Later Manager", f"Could not save changes.\n\n{exc}")
                return False
        if clicked is discard_button:
            self.pending_card_removals.clear()
            return True
        if clicked is cancel_button:
            return False
        return False

    def closeEvent(self, event: Any) -> None:
        if not self._confirm_close():
            event.ignore()
            return
        self._detach_bridge_hook()
        super().closeEvent(event)

    def make_filtered_deck(self) -> None:
        if not self.visible_entries:
            QMessageBox.information(self, "Review Later Manager", "No visible Review Later cards to include.")
            return
        name = datetime.now().strftime("Review Later %Y-%m-%d %H-%M-%S")
        search = search_query_for_entries(
            self.visible_entries,
            self.review_later_flag,
            str(self.date_filter.currentData() or "all"),
        )
        limit = len(self.visible_entries)
        try:
            deck_id = mw.col.decks.id(name)
            deck = mw.col.decks.get(deck_id)
            deck["dyn"] = 1
            deck["resched"] = False
            deck["delays"] = None
            deck["terms"] = [[search, limit, 0]]
            mw.col.decks.save(deck)
            rebuild = getattr(mw.col.sched, "rebuild_filtered_deck", None)
            if callable(rebuild):
                rebuild(deck_id)
            else:
                rebuild = getattr(mw.col.sched, "rebuildDyn", None)
                if callable(rebuild):
                    rebuild(deck_id)
            mw.reset()
            QMessageBox.information(
                self,
                "Review Later Manager",
                f"Created filtered deck:\n{name}",
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Review Later Manager",
                f"Could not create filtered deck.\n\n{exc}",
            )


_dialog: ReviewLaterManagerDialog | None = None


def open_review_later_manager(
    review_later_flag: int,
    *,
    review_later_today_button_enabled: bool = False,
    on_review_later_today_button_changed: Callable[[bool], bool | None] | None = None,
) -> None:
    global _dialog
    if _dialog is not None:
        try:
            _dialog.close()
            if _dialog.isVisible():
                _dialog.raise_()
                _dialog.activateWindow()
                return
        except Exception:
            pass
    _dialog = ReviewLaterManagerDialog(
        review_later_flag=review_later_flag,
        review_later_today_button_enabled=review_later_today_button_enabled,
        on_review_later_today_button_changed=on_review_later_today_button_changed,
        parent=mw,
    )
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()
