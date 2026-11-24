from __future__ import annotations

from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
import time
from typing import Any


class SprintTimeTracker:
    """Tracks strict, uninterrupted focus sprints independently of card streaks."""

    def __init__(self, data_root: Path, *, undo_allowed: bool = True) -> None:
        self.data_root = Path(data_root)
        self.db_path = self.data_root / "speed_streak_sprints.sqlite3"
        self.undo_allowed = bool(undo_allowed)
        self.started_at = 0.0
        self.ended_at = 0.0
        self.ended_at_epoch = 0.0
        self.frozen_elapsed_ms = 0
        self.cards_answered = 0
        self.time_drain_cards = 0
        self.time_drain_ms = 0
        self.time_drain_started_at = 0.0
        self.time_drain_card_id = ""
        self.time_drain_card_ids: set[str] = set()
        self.time_drain_flagged = False
        self.time_drain_tamper = False
        self._initialized = False

    def _connect(self) -> sqlite3.Connection:
        self.data_root.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        if self._initialized:
            return
        self.data_root.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.execute("""create table if not exists sprint_records (
                id integer primary key autoincrement,
                started_at text not null, ended_at text not null,
                duration_ms integer not null, cards_answered integer not null,
                undo_allowed integer not null, time_drain_cards integer not null,
                time_drain_ms integer not null, time_drain_tamper integer not null
            )""")
        self._initialized = True

    def set_undo_allowed(self, allowed: bool) -> None:
        self.undo_allowed = bool(allowed)

    def start(self) -> None:
        if self.started_at <= 0 and self.ended_at <= 0:
            self.started_at = time.monotonic()

    def elapsed_ms(self) -> int:
        if self.started_at <= 0:
            return 0
        if self.ended_at > 0:
            return self.frozen_elapsed_ms
        drain_ms = self.time_drain_ms
        if self.time_drain_started_at > 0:
            drain_ms += int((time.monotonic() - self.time_drain_started_at) * 1000)
        return max(0, int((time.monotonic() - self.started_at) * 1000) - drain_ms)

    def answer(self) -> None:
        if self.started_at > 0:
            self.cards_answered += 1

    def finish_for_time_drain_review(self) -> None:
        """End timed reviewing while retaining later Time Drain audit details."""
        if self.started_at > 0 and self.ended_at <= 0:
            self.frozen_elapsed_ms = self.elapsed_ms()
            self.ended_at = time.monotonic()
            self.ended_at_epoch = time.time()

    def reset(self) -> None:
        if self.started_at > 0 and self.cards_answered > 0:
            self._init_db()
            ended_monotonic = self.ended_at or time.monotonic()
            ended_epoch = self.ended_at_epoch or time.time()
            started = datetime.fromtimestamp(ended_epoch - (ended_monotonic - self.started_at))
            ended = datetime.fromtimestamp(ended_epoch)
            drain_total_ms = self.time_drain_ms
            if self.time_drain_started_at > 0:
                drain_total_ms += max(0, int((time.monotonic() - self.time_drain_started_at) * 1000))
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "insert into sprint_records (started_at, ended_at, duration_ms, cards_answered, undo_allowed, time_drain_cards, time_drain_ms, time_drain_tamper) values (?, ?, ?, ?, ?, ?, ?, ?)",
                    (started.isoformat(timespec="seconds"), ended.isoformat(timespec="seconds"), self.elapsed_ms(),
                     self.cards_answered, int(self.undo_allowed), self.time_drain_cards, drain_total_ms,
                     int(self.time_drain_tamper)),
                )
        self.started_at = 0.0
        self.ended_at = 0.0
        self.ended_at_epoch = 0.0
        self.frozen_elapsed_ms = 0
        self.cards_answered = 0
        self.time_drain_cards = 0
        self.time_drain_ms = 0
        self.time_drain_started_at = 0.0
        self.time_drain_card_id = ""
        self.time_drain_card_ids.clear()
        self.time_drain_flagged = False
        self.time_drain_tamper = False

    def undo(self) -> None:
        if not self.undo_allowed:
            self.reset()

    def set_time_drain(self, flagged: bool, card_id: str) -> None:
        flagged = bool(flagged)
        card_id = str(card_id or "")
        if flagged:
            if card_id and card_id not in self.time_drain_card_ids:
                self.time_drain_card_ids.add(card_id)
                self.time_drain_cards += 1
            self.time_drain_card_id = card_id
        elif self.time_drain_flagged and card_id == self.time_drain_card_id and self.time_drain_started_at > 0:
            self.time_drain_tamper = True
        self.time_drain_flagged = flagged

    def set_time_drain_paused(self, paused: bool) -> None:
        if paused and self.started_at > 0 and self.time_drain_flagged and self.time_drain_started_at <= 0:
            self.time_drain_started_at = time.monotonic()
        elif not paused and self.time_drain_started_at > 0:
            self.time_drain_ms += max(0, int((time.monotonic() - self.time_drain_started_at) * 1000))
            self.time_drain_started_at = 0.0

    def payload(self) -> dict[str, Any]:
        self._init_db()
        with closing(self._connect()) as conn, conn:
            today = datetime.now().date().isoformat()
            today_row = conn.execute(
                "select max(duration_ms) as value from sprint_records where substr(ended_at, 1, 10) = ? and undo_allowed = ?",
                (today, int(self.undo_allowed)),
            ).fetchone()
            all_row = conn.execute(
                "select max(duration_ms) as value from sprint_records where undo_allowed = ?",
                (int(self.undo_allowed),),
            ).fetchone()
            prior_row = conn.execute(
                "select duration_ms from sprint_records order by id desc limit 1"
            ).fetchone()
        return {
            "priorMs": self.frozen_elapsed_ms if self.ended_at > 0 else int((prior_row["duration_ms"] if prior_row else 0) or 0),
            "enabled": True,
            "active": self.started_at > 0 and self.ended_at <= 0,
            "elapsedMs": self.elapsed_ms() if self.ended_at <= 0 else 0,
            "todayBestMs": max(self.elapsed_ms(), int((today_row["value"] if today_row else 0) or 0)),
            "allTimeBestMs": max(self.elapsed_ms(), int((all_row["value"] if all_row else 0) or 0)),
            "undoAllowed": self.undo_allowed,
            "timeDrainCards": self.time_drain_cards,
            "timeDrainMs": self.time_drain_ms + (max(0, int((time.monotonic() - self.time_drain_started_at) * 1000)) if self.time_drain_started_at > 0 else 0),
            "timeDrainTamper": self.time_drain_tamper,
            "timeDrainPaused": self.time_drain_started_at > 0,
        }

    def records(self, limit: int | None = 100) -> list[dict[str, Any]]:
        self._init_db()
        with closing(self._connect()) as conn, conn:
            if limit is None:
                rows = conn.execute(
                    "select * from sprint_records order by ended_at desc, id desc"
                ).fetchall()
            else:
                rows = conn.execute(
                    "select * from sprint_records order by ended_at desc, id desc limit ?",
                    (max(1, min(500, int(limit))),),
                ).fetchall()
        return [dict(row) for row in rows]

    def best_today(self, limit: int = 5) -> list[dict[str, Any]]:
        self._init_db()
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                "select * from sprint_records where substr(ended_at, 1, 10) = ? "
                "order by duration_ms desc, ended_at desc, id desc limit ?",
                (datetime.now().date().isoformat(), max(1, min(100, int(limit)))),
            ).fetchall()
        return [dict(row) for row in rows]
