from __future__ import annotations

from datetime import datetime
import csv
import json
import sqlite3
from typing import Any

from aqt import mw

try:
    from aqt.qt import (
        QDialog,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
    )
except Exception:
    QDialog = object
    QHBoxLayout = QLabel = QPushButton = QTableWidget = QTableWidgetItem = QVBoxLayout = None

try:
    from aqt.utils import openLink, showInfo, showWarning
except Exception:
    openLink = None
    showInfo = lambda message: None
    showWarning = lambda message: None

try:
    from .common import user_files_dir
except Exception:
    from pathlib import Path

    def user_files_dir() -> Path:
        path = Path(__file__).resolve().parent / "user_files"
        path.mkdir(parents=True, exist_ok=True)
        return path
CARD_SAFETY_DB_PATH = user_files_dir() / "card_safety_log.sqlite3"
CARD_SAFETY_CSV_PATH = user_files_dir() / "card_safety_log.csv"
_HOOK_REGISTERED = False
_dialog: "CardSafetyLogDialog | None" = None


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(CARD_SAFETY_DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS card_safety_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            operation TEXT NOT NULL,
            card_count INTEGER NOT NULL DEFAULT 0,
            note_count INTEGER NOT NULL DEFAULT 0,
            deck_id INTEGER,
            deck_name TEXT,
            details_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_card_safety_events_created ON card_safety_events(created_at)"
    )
    return conn


def _clean_ints(values: Any) -> list[int]:
    if values is None:
        return []
    if isinstance(values, int):
        values = [values]
    if not isinstance(values, (list, tuple, set)):
        return []
    cleaned: list[int] = []
    seen: set[int] = set()
    for raw_value in values:
        try:
            value = int(raw_value)
        except Exception:
            continue
        if value <= 0 or value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    return cleaned


def _placeholders(count: int) -> str:
    return ", ".join("?" for _ in range(max(0, int(count))))


def _db_rows(sql: str, *args: Any) -> list[tuple[Any, ...]]:
    try:
        rows = mw.col.db.all(sql, *args)
    except Exception:
        return []
    return [tuple(row) for row in rows or []]


def _deck_name_for_id(deck_id: int | None) -> str:
    if not deck_id:
        return ""
    try:
        return str(mw.col.decks.name(int(deck_id)))
    except Exception:
        return f"Deck {int(deck_id)}"


def snapshot_card_rows(card_ids: list[int]) -> list[dict[str, Any]]:
    cleaned = _clean_ints(card_ids)
    if not cleaned:
        return []
    snapshots: list[dict[str, Any]] = []
    for start in range(0, len(cleaned), 250):
        chunk = cleaned[start : start + 250]
        rows = _db_rows(
            f"""
            SELECT c.id, c.nid, c.did, c.odid, c.type, c.queue, c.due, c.odue
            FROM cards AS c
            WHERE c.id IN ({_placeholders(len(chunk))})
            ORDER BY c.id
            """,
            *chunk,
        )
        for row in rows:
            did = int(row[2] or 0)
            odid = int(row[3] or 0)
            snapshots.append(
                {
                    "card_id": int(row[0] or 0),
                    "note_id": int(row[1] or 0),
                    "deck_id": did,
                    "deck_name": _deck_name_for_id(did),
                    "original_deck_id": odid,
                    "original_deck_name": _deck_name_for_id(odid) if odid else "",
                    "type": int(row[4] or 0),
                    "queue": int(row[5] or 0),
                    "due": int(row[6] or 0),
                    "odue": int(row[7] or 0),
                }
            )
    return snapshots


def card_ids_for_note_ids(note_ids: list[int]) -> list[int]:
    cleaned = _clean_ints(note_ids)
    if not cleaned:
        return []
    card_ids: list[int] = []
    for start in range(0, len(cleaned), 250):
        chunk = cleaned[start : start + 250]
        rows = _db_rows(
            f"SELECT id FROM cards WHERE nid IN ({_placeholders(len(chunk))}) ORDER BY id",
            *chunk,
        )
        card_ids.extend(int(row[0]) for row in rows if row)
    return _clean_ints(card_ids)


def log_card_safety_event(
    operation: str,
    *,
    card_ids: list[int] | None = None,
    note_ids: list[int] | None = None,
    deck_id: int | None = None,
    deck_name: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    cleaned_card_ids = _clean_ints(card_ids)
    cleaned_note_ids = _clean_ints(note_ids)
    event_details = dict(details or {})
    event_details.setdefault("card_ids", cleaned_card_ids)
    event_details.setdefault("note_ids", cleaned_note_ids)
    if cleaned_card_ids and "card_snapshots" not in event_details:
        event_details["card_snapshots"] = snapshot_card_rows(cleaned_card_ids)

    safe_deck_id = int(deck_id) if deck_id else None
    safe_deck_name = str(deck_name or (_deck_name_for_id(safe_deck_id) if safe_deck_id else ""))
    created_at = _now_iso()
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO card_safety_events(
                    created_at, operation, card_count, note_count, deck_id, deck_name, details_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    str(operation),
                    len(cleaned_card_ids),
                    len(cleaned_note_ids),
                    safe_deck_id,
                    safe_deck_name,
                    json.dumps(event_details, sort_keys=True),
                ),
            )
    except Exception:
        return


def _recent_events(limit: int = 250) -> list[dict[str, Any]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT id, created_at, operation, card_count, note_count, deck_id, deck_name, details_json
                FROM card_safety_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
    except Exception:
        return []
    events: list[dict[str, Any]] = []
    for row in rows:
        try:
            details = json.loads(row[7] or "{}")
        except Exception:
            details = {}
        events.append(
            {
                "id": int(row[0]),
                "created_at": str(row[1]),
                "operation": str(row[2]),
                "card_count": int(row[3] or 0),
                "note_count": int(row[4] or 0),
                "deck_id": int(row[5]) if row[5] is not None else None,
                "deck_name": str(row[6] or ""),
                "details": details,
            }
        )
    return events


def export_card_safety_csv() -> str:
    events = _recent_events(limit=100000)
    with CARD_SAFETY_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "created_at", "operation", "card_count", "note_count", "deck_id", "deck_name", "card_ids", "note_ids"])
        for event in reversed(events):
            details = event.get("details") or {}
            writer.writerow(
                [
                    event.get("id"),
                    event.get("created_at"),
                    event.get("operation"),
                    event.get("card_count"),
                    event.get("note_count"),
                    event.get("deck_id") or "",
                    event.get("deck_name") or "",
                    " ".join(str(value) for value in details.get("card_ids", []) or []),
                    " ".join(str(value) for value in details.get("note_ids", []) or []),
                ]
            )
    return str(CARD_SAFETY_CSV_PATH)


class CardSafetyLogDialog(QDialog):
    def __init__(self) -> None:
        super().__init__(mw)
        self.setWindowTitle("Pocket Knife Card Safety Log")
        self.resize(980, 560)
        self._events: list[dict[str, Any]] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        intro = QLabel(
            "Recent Pocket Knife card movement, restore, and deletion-safety events. Export opens a CSV copy."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.table = QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels(["Time", "Operation", "Cards", "Notes", "Deck", "Card IDs"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)

        button_row = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.export_button = QPushButton("Export CSV")
        self.close_button = QPushButton("Close")
        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.export_button)
        button_row.addStretch(1)
        button_row.addWidget(self.close_button)
        layout.addLayout(button_row)

        self.refresh_button.clicked.connect(self.refresh)
        self.export_button.clicked.connect(self.export_csv)
        self.close_button.clicked.connect(self.close)

    def refresh(self) -> None:
        self._events = _recent_events()
        self.table.setRowCount(len(self._events))
        for row, event in enumerate(self._events):
            details = event.get("details") or {}
            card_ids = details.get("card_ids", []) or []
            values = [
                event.get("created_at", ""),
                event.get("operation", ""),
                str(event.get("card_count", 0)),
                str(event.get("note_count", 0)),
                event.get("deck_name", "") or "",
                " ".join(str(value) for value in card_ids[:40]),
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

    def export_csv(self) -> None:
        path = export_card_safety_csv()
        if callable(openLink):
            try:
                openLink(path)
                return
            except Exception:
                pass
        showInfo(f"Exported card safety log:\n{path}")


def open_card_safety_log_dialog() -> None:
    global _dialog
    if _dialog is not None:
        try:
            _dialog.close()
        except Exception:
            pass
    _dialog = CardSafetyLogDialog()
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    try:
        _connect().close()
    except Exception as exc:
        showWarning(f"Pocket Knife could not prepare the card safety log.\n\n{exc}")
    _HOOK_REGISTERED = True
