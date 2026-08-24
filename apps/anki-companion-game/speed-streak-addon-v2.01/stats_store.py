from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Any, Dict, Iterator, List


@dataclass
class StatsStore:
    data_root: Path

    def __post_init__(self) -> None:
        self.data_root = Path(self.data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_root / "speed_streak_stats.sqlite3"
        self._init_db()

    def record_review(self, *, card_id: int, deck_name: str, active_ms: int, ease: int, correct: int) -> int:
        now = datetime.now()
        with self._open_connection() as conn:
            cur = conn.execute(
                """
                insert into review_events (
                    answered_at,
                    day,
                    card_id,
                    deck_name,
                    active_ms,
                    ease,
                    correct
                ) values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now.isoformat(timespec="seconds"),
                    now.date().isoformat(),
                    int(card_id or 0),
                    str(deck_name or ""),
                    int(max(0, active_ms)),
                    int(ease or 0),
                    int(1 if correct else 0),
                ),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def delete_review_event(self, event_id: int) -> None:
        if event_id <= 0:
            return
        with self._open_connection() as conn:
            conn.execute("delete from review_events where id = ?", (int(event_id),))
            conn.commit()

    def today_summary(self) -> Dict[str, Any]:
        return self.summary_for_day(datetime.now().date().isoformat())

    def summary_for_day(self, day: str) -> Dict[str, Any]:
        with self._open_connection() as conn:
            row = conn.execute(
                """
                select
                    count(*) as cards,
                    coalesce(avg(active_ms), 0) as avg_active_ms,
                    coalesce(sum(correct), 0) as correct_cards
                from review_events
                where day = ?
                """,
                (str(day),),
            ).fetchone()
        cards = int(row["cards"] or 0) if row else 0
        correct_cards = int(row["correct_cards"] or 0) if row else 0
        incorrect_cards = max(0, cards - correct_cards)
        correct_pct = (correct_cards / cards * 100) if cards else 0.0
        return {
            "day": str(day),
            "cards": cards,
            "avgActiveMs": float(row["avg_active_ms"] or 0.0) if row else 0.0,
            "correctCards": correct_cards,
            "incorrectCards": incorrect_cards,
            "correctPct": correct_pct,
            "incorrectPct": 100.0 - correct_pct if cards else 0.0,
            "longestStreak": self._longest_streak(day=str(day)),
        }

    def historical_daily_stats(self) -> List[Dict[str, Any]]:
        with self._open_connection() as conn:
            rows = conn.execute(
                """
                select
                    day,
                    count(*) as cards,
                    coalesce(avg(active_ms), 0) as avg_active_ms,
                    coalesce(sum(correct), 0) as correct_cards
                from review_events
                group by day
                order by day asc
                """
            ).fetchall()
        series: List[Dict[str, Any]] = []
        for row in rows:
            cards = int(row["cards"] or 0)
            correct_cards = int(row["correct_cards"] or 0)
            incorrect_cards = max(0, cards - correct_cards)
            correct_pct = (correct_cards / cards * 100) if cards else 0.0
            series.append(
                {
                    "day": str(row["day"]),
                    "cards": cards,
                    "avgActiveMs": float(row["avg_active_ms"] or 0.0),
                    "correctCards": correct_cards,
                    "incorrectCards": incorrect_cards,
                    "correctPct": correct_pct,
                    "incorrectPct": 100.0 - correct_pct if cards else 0.0,
                }
            )
        return series

    def overall_summary(self) -> Dict[str, Any]:
        with self._open_connection() as conn:
            row = conn.execute(
                """
                select
                    count(*) as cards,
                    coalesce(avg(active_ms), 0) as avg_active_ms,
                    coalesce(sum(correct), 0) as correct_cards
                from review_events
                """
            ).fetchone()
        cards = int(row["cards"] or 0) if row else 0
        correct_cards = int(row["correct_cards"] or 0) if row else 0
        correct_pct = (correct_cards / cards * 100) if cards else 0.0
        return {
            "cards": cards,
            "avgActiveMs": float(row["avg_active_ms"] or 0.0) if row else 0.0,
            "correctCards": correct_cards,
            "incorrectCards": max(0, cards - correct_cards),
            "correctPct": correct_pct,
            "incorrectPct": 100.0 - correct_pct if cards else 0.0,
            "longestStreak": self._longest_streak(),
        }

    def _longest_streak(self, day: str | None = None) -> int:
        query = "select correct from review_events"
        params: tuple[Any, ...] = ()
        if day is not None:
            query += " where day = ?"
            params = (str(day),)
        query += " order by answered_at asc, id asc"
        with self._open_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        best = 0
        current = 0
        for row in rows:
            if int(row["correct"] or 0):
                current += 1
                best = max(best, current)
            else:
                current = 0
        return best

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _open_connection(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._open_connection() as conn:
            conn.executescript(
                """
                create table if not exists review_events (
                    id integer primary key autoincrement,
                    answered_at text not null,
                    day text not null,
                    card_id integer not null,
                    deck_name text not null,
                    active_ms integer not null,
                    ease integer not null,
                    correct integer not null
                );

                create index if not exists idx_review_events_day on review_events(day);
                create index if not exists idx_review_events_answered_at on review_events(answered_at);
                """
            )
            conn.commit()
