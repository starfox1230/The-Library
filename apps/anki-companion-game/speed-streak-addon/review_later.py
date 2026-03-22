from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import sqlite3
from typing import Any

from aqt import dialogs, mw
from aqt.webview import AnkiWebView
from aqt.qt import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


ADDON_ROOT = Path(__file__).resolve().parent
USER_FILES_DIR = ADDON_ROOT / "user_files"
DB_PATH = USER_FILES_DIR / "review_later.sqlite3"
REVIEW_LATER_TAG_PREFIX = "speed_streak::review_later"


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


def _ensure_user_files() -> None:
    USER_FILES_DIR.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    _ensure_user_files()
    conn = sqlite3.connect(DB_PATH)
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


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _cohort_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.now()


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
    tags = [tag for tag in _note_tag_list(note) if not tag.startswith(prefix)]
    tags.append(_build_review_later_tag(card_ord, entered_at_iso))
    _set_note_tags(note, tags)


def _remove_review_later_note_tag(note: Any, *, card_ord: int) -> None:
    prefix = _review_later_tag_prefix_for_ord(card_ord)
    tags = [tag for tag in _note_tag_list(note) if not tag.startswith(prefix)]
    _set_note_tags(note, tags)


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
    with _connect() as conn:
        if int(current_flag or 0) == int(review_later_flag):
            entered_at = _active_db_entered_at(conn, card_id=int(card_id), flag=int(review_later_flag)) or _now_iso()
            _ensure_active_cohort(
                conn,
                card_id=int(card_id),
                note_id=int(note_id),
                flag=int(review_later_flag),
                entered_at=entered_at,
            )
        else:
            _close_active_cohort(
                conn,
                card_id=int(card_id),
                flag=int(review_later_flag),
            )
        conn.commit()


def reconcile_review_later_flag(flag: int) -> None:
    if flag <= 0:
        return
    current_card_ids = [int(card_id) for card_id in mw.col.find_cards(_flag_search(flag))]
    current_set = set(current_card_ids)
    now_iso = _now_iso()

    with _connect() as conn:
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
                entered_at = _active_db_entered_at(conn, card_id=card_id, flag=flag) or now_iso
                _ensure_active_cohort(
                    conn,
                    card_id=card_id,
                    note_id=int(getattr(card.note(), "id", 0) or 0),
                    flag=flag,
                    entered_at=entered_at,
                )
            except Exception:
                continue

        stale_ids = active_card_ids - current_set
        for card_id in stale_ids:
            _close_active_cohort(conn, card_id=card_id, flag=flag, removed_at=now_iso)

        conn.commit()


def _active_cohort_map(flag: int) -> dict[int, datetime]:
    cohort_map: dict[int, datetime] = {}
    for card_id in [int(value) for value in mw.col.find_cards(_flag_search(flag))]:
        try:
            card = _col_get_card(card_id)
            note = card.note()
            card_ord = int(getattr(card, "ord", 0) or 0)
            entered_at = _review_later_tag_timestamp_for_ord(note, card_ord)
            if entered_at:
                cohort_map[card_id] = _cohort_datetime(entered_at)
        except Exception:
            continue
    if cohort_map:
        return cohort_map
    with _connect() as conn:
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
        if card_id not in cohort_map:
            cohort_map[card_id] = _cohort_datetime(str(row["entered_at"]))
    return cohort_map


def fetch_review_later_entries(flag: int) -> list[ReviewLaterEntry]:
    if flag <= 0:
        return []

    reconcile_review_later_flag(flag)
    active_map = _active_cohort_map(flag)
    card_ids = [int(card_id) for card_id in mw.col.find_cards(_flag_search(flag))]
    entries: list[ReviewLaterEntry] = []

    for card_id in card_ids:
        try:
            card = _col_get_card(card_id)
            note = card.note()
            fields = _note_fields(note)
            front_html = str(card.question() or "")
            back_html = str(card.answer() or "")
            entries.append(
                ReviewLaterEntry(
                    added_at=active_map.get(card_id, datetime.now()),
                    card_id=int(card.id),
                    note_id=int(note.id),
                    deck_name=_deck_name(card),
                    note_type_name=_note_type_name(note),
                    tags=[str(tag) for tag in getattr(note, "tags", [])],
                    fields=fields,
                    front_html=front_html,
                    back_html=back_html,
                    front_text=html_to_text(front_html),
                    back_text=html_to_text(back_html),
                )
            )
        except Exception:
            continue

    entries.sort(key=lambda entry: entry.added_at, reverse=True)
    return entries


def build_copy_text(entries: list[ReviewLaterEntry]) -> str:
    chunks: list[str] = []
    for entry in entries:
        field_lines = [str(value).strip() for value in entry.fields.values() if str(value).strip()]
        chunks.append("\n".join(field_lines) or "(no fields)")
    return "\n\n".join(chunks).strip()


def preview_html(entries: list[ReviewLaterEntry]) -> str:
    if not entries:
        body = "<div class='empty'>No cards currently match the current Review Later filter.</div>"
    else:
        cards = []
        for entry in entries:
            tags = ", ".join(entry.tags) if entry.tags else "No tags"
            cards.append(
                f"""
                <section class="entry">
                  <div class="meta">
                    <div><strong>{escape(entry.deck_name)}</strong></div>
                    <div>{escape(entry.note_type_name)}</div>
                    <div>Added {entry.added_at.strftime("%Y-%m-%d %H:%M")}</div>
                  </div>
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


def search_query_for_entries(entries: list[ReviewLaterEntry], flag: int, kind: str) -> str:
    if not entries:
        return ""
    if kind == "all" and flag > 0:
        return _flag_search(flag)
    return " or ".join(f"cid:{entry.card_id}" for entry in entries)


class ReviewLaterManagerDialog(QDialog):
    def __init__(self, review_later_flag: int, parent: QWidget | None = None) -> None:
        super().__init__(parent or mw)
        self.review_later_flag = int(review_later_flag)
        self.entries: list[ReviewLaterEntry] = []
        self.visible_entries: list[ReviewLaterEntry] = []
        self.setWindowTitle("Review Later Manager")
        self.resize(920, 700)
        self._build_ui()
        self.refresh_entries()

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
        self.browser_button = QPushButton("Open in Browser")
        self.close_button = QPushButton("Close")
        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.copy_all_button)
        button_row.addWidget(self.filtered_deck_button)
        button_row.addWidget(self.browser_button)
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
        self.close_button.clicked.connect(self.close)

    def refresh_entries(self) -> None:
        if self.review_later_flag <= 0:
            self.entries = []
            self.visible_entries = []
            self.info_label.setText("Choose a Review Later flag in Settings first.")
            self.preview.stdHtml(preview_html([]))
            return

        self.entries = fetch_review_later_entries(self.review_later_flag)
        self._apply_filter()

    def _apply_filter(self) -> None:
        kind = str(self.date_filter.currentData() or "all")
        past_days = int(self.past_days.value())
        self.past_days.setEnabled(kind == "past_x")
        self.visible_entries = filter_entries(self.entries, kind, past_days)
        self.info_label.setText(
            f"Review Later Flag: {self.review_later_flag} | Visible Cards: {len(self.visible_entries)} | Total Cards: {len(self.entries)}"
        )
        self.preview.stdHtml(preview_html(self.visible_entries))

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
        except Exception as exc:
            QMessageBox.warning(self, "Review Later Manager", f"Could not open Browser.\n\n{exc}")

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


def open_review_later_manager(review_later_flag: int) -> None:
    global _dialog
    if _dialog is not None:
        try:
            _dialog.close()
        except Exception:
            pass
    _dialog = ReviewLaterManagerDialog(review_later_flag=review_later_flag, parent=mw)
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()
