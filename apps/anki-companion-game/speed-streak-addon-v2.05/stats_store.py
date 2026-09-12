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

    def record_speed_streak_run(
        self,
        *,
        started_at: str,
        ended_at: str,
        end_reason: str,
        peak_streak: int,
        gameplay_mode: str,
        legacy_score: int,
        cards_answered: int,
        run_span_ms: int,
        active_ms: int,
        paused_ms: int,
        pause_count: int,
        review_exit_ms: int,
        review_exit_count: int,
        resumed_after_restart: bool,
        used_undo: bool,
        boosts_used: int,
        undo_count: int | None = None,
    ) -> int:
        """Store one completed gameplay run.

        A run is meaningful only after at least one card has been completed.
        The all-time best is intentionally derived from these rows rather than
        copied into a separate setting, so deleting a run also repairs the best.
        """
        peak = max(0, int(peak_streak or 0))
        if peak <= 0:
            return 0
        normalized_undo_count = max(
            0,
            int(undo_count if undo_count is not None else int(bool(used_undo))),
        )
        with self._open_connection() as conn:
            cur = conn.execute(
                """
                insert into speed_streak_runs (
                    started_at,
                    ended_at,
                    end_reason,
                    peak_streak,
                    gameplay_mode,
                    legacy_score,
                    cards_answered,
                    run_span_ms,
                    active_ms,
                    paused_ms,
                    pause_count,
                    review_exit_ms,
                    review_exit_count,
                    resumed_after_restart,
                    used_undo,
                    undo_count,
                    boosts_used,
                    deleted_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, null)
                """,
                (
                    str(started_at or ended_at),
                    str(ended_at),
                    str(end_reason or "ended")[:80],
                    peak,
                    str(gameplay_mode or "time_boost")[:40],
                    max(0, int(legacy_score or 0)),
                    max(1, int(cards_answered or peak)),
                    max(0, int(run_span_ms or 0)),
                    max(0, int(active_ms or 0)),
                    max(0, int(paused_ms or 0)),
                    max(0, int(pause_count or 0)),
                    max(0, int(review_exit_ms or 0)),
                    max(0, int(review_exit_count or 0)),
                    int(bool(resumed_after_restart)),
                    int(bool(used_undo) or normalized_undo_count > 0),
                    normalized_undo_count,
                    max(0, int(boosts_used or 0)),
                ),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def speed_streak_runs(
        self,
        *,
        list_mode: str = "recent",
        limit: int = 5,
        purity: str = "all",
    ) -> List[Dict[str, Any]]:
        requested_mode = str(list_mode or "").strip().lower()
        normalized_mode = requested_mode if requested_mode in {"best", "today"} else "recent"
        normalized_purity = str(purity or "all").strip().lower()
        safe_limit = max(1, min(100, int(limit or 5)))
        ordering = (
            "peak_streak desc, ended_at desc, id desc"
            if normalized_mode in {"best", "today"}
            else "ended_at desc, id desc"
        )
        today_clause = "and substr(ended_at, 1, 10) = ?" if normalized_mode == "today" else ""
        purity_clause = (
            "and pause_count = 0 and review_exit_count = 0 and resumed_after_restart = 0 and used_undo = 0"
            if normalized_purity == "pure"
            else ""
        )
        query_parameters: tuple[Any, ...] = (
            (datetime.now().date().isoformat(), safe_limit)
            if normalized_mode == "today"
            else (safe_limit,)
        )
        with self._open_connection() as conn:
            rows = conn.execute(
                f"""
                select
                    id,
                    started_at,
                    ended_at,
                    end_reason,
                    peak_streak,
                    gameplay_mode,
                    legacy_score,
                    cards_answered,
                    run_span_ms,
                    active_ms,
                    paused_ms,
                    pause_count,
                    review_exit_ms,
                    review_exit_count,
                    resumed_after_restart,
                    used_undo,
                    undo_count,
                    boosts_used
                from speed_streak_runs
                where deleted_at is null
                {today_clause}
                {purity_clause}
                order by {ordering}
                limit ?
                """,
                query_parameters,
            ).fetchall()
        return [self._speed_streak_run_payload(row) for row in rows]

    def speed_streak_run_with_rank(self, run_id: int) -> Dict[str, Any] | None:
        safe_run_id = int(run_id or 0)
        if safe_run_id <= 0:
            return None
        with self._open_connection() as conn:
            row = conn.execute(
                """
                select
                    id,
                    started_at,
                    ended_at,
                    end_reason,
                    peak_streak,
                    gameplay_mode,
                    legacy_score,
                    cards_answered,
                    run_span_ms,
                    active_ms,
                    paused_ms,
                    pause_count,
                    review_exit_ms,
                    review_exit_count,
                    resumed_after_restart,
                    used_undo,
                    undo_count,
                    boosts_used
                from speed_streak_runs
                where id = ? and deleted_at is null
                """,
                (safe_run_id,),
            ).fetchone()
            if row is None:
                return None
            rank_row = conn.execute(
                """
                select count(*) + 1 as ranking
                from speed_streak_runs
                where deleted_at is null
                  and (
                    peak_streak > ?
                    or (peak_streak = ? and ended_at > ?)
                    or (peak_streak = ? and ended_at = ? and id > ?)
                  )
                """,
                (
                    int(row["peak_streak"] or 0),
                    int(row["peak_streak"] or 0),
                    str(row["ended_at"] or ""),
                    int(row["peak_streak"] or 0),
                    str(row["ended_at"] or ""),
                    safe_run_id,
                ),
            ).fetchone()
        payload = self._speed_streak_run_payload(row)
        payload["allTimeRank"] = max(1, int(rank_row["ranking"] or 1)) if rank_row else 1
        return payload

    def _speed_streak_run_payload(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": int(row["id"] or 0),
            "startedAt": str(row["started_at"] or ""),
            "endedAt": str(row["ended_at"] or ""),
            "endReason": str(row["end_reason"] or ""),
            "streak": int(row["peak_streak"] or 0),
            "gameplayMode": str(row["gameplay_mode"] or ""),
            "legacyScore": int(row["legacy_score"] or 0),
            "cardsAnswered": int(row["cards_answered"] or 0),
            "runSpanMs": int(row["run_span_ms"] or 0),
            "activeMs": int(row["active_ms"] or 0),
            "pausedMs": int(row["paused_ms"] or 0),
            "pauseCount": int(row["pause_count"] or 0),
            "reviewExitMs": int(row["review_exit_ms"] or 0),
            "reviewExitCount": int(row["review_exit_count"] or 0),
            "resumedAfterRestart": bool(row["resumed_after_restart"]),
            "usedUndo": bool(row["used_undo"]),
            "undoCount": max(0, int(row["undo_count"] or 0)),
            "boostsUsed": int(row["boosts_used"] or 0),
        }

    def best_speed_streak(self, *, purity: str = "all") -> int:
        purity_clause = (
            "and pause_count = 0 and review_exit_count = 0 and resumed_after_restart = 0 and used_undo = 0"
            if str(purity or "all").strip().lower() == "pure"
            else ""
        )
        with self._open_connection() as conn:
            row = conn.execute(
                f"""
                select coalesce(max(peak_streak), 0) as best
                from speed_streak_runs
                where deleted_at is null
                  {purity_clause}
                """
            ).fetchone()
        return int(row["best"] or 0) if row else 0

    def best_speed_streak_today(self, *, purity: str = "all") -> int:
        today = datetime.now().date().isoformat()
        purity_clause = (
            "and pause_count = 0 and review_exit_count = 0 and resumed_after_restart = 0 and used_undo = 0"
            if str(purity or "all").strip().lower() == "pure"
            else ""
        )
        with self._open_connection() as conn:
            row = conn.execute(
                f"""
                select coalesce(max(peak_streak), 0) as best
                from speed_streak_runs
                where deleted_at is null
                  and substr(ended_at, 1, 10) = ?
                  {purity_clause}
                """,
                (today,),
            ).fetchone()
        return int(row["best"] or 0) if row else 0

    def delete_speed_streak_run(self, run_id: int) -> bool:
        if int(run_id or 0) <= 0:
            return False
        deleted_at = datetime.now().isoformat(timespec="seconds")
        with self._open_connection() as conn:
            cur = conn.execute(
                """
                update speed_streak_runs
                set deleted_at = ?
                where id = ? and deleted_at is null
                """,
                (deleted_at, int(run_id)),
            )
            conn.commit()
            return int(cur.rowcount or 0) > 0

    def delete_best_speed_streak_run(self) -> bool:
        with self._open_connection() as conn:
            row = conn.execute(
                """
                select id
                from speed_streak_runs
                where deleted_at is null
                order by peak_streak desc, ended_at desc, id desc
                limit 1
                """
            ).fetchone()
        return self.delete_speed_streak_run(int(row["id"] or 0)) if row else False

    def reset_speed_streak_runs(self) -> int:
        deleted_at = datetime.now().isoformat(timespec="seconds")
        with self._open_connection() as conn:
            cur = conn.execute(
                """
                update speed_streak_runs
                set deleted_at = ?
                where deleted_at is null
                """,
                (deleted_at,),
            )
            conn.commit()
            return max(0, int(cur.rowcount or 0))

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

                create table if not exists speed_streak_runs (
                    id integer primary key autoincrement,
                    started_at text not null,
                    ended_at text not null,
                    end_reason text not null,
                    peak_streak integer not null,
                    gameplay_mode text not null,
                    legacy_score integer not null,
                    cards_answered integer not null,
                    run_span_ms integer not null default 0,
                    active_ms integer not null,
                    paused_ms integer not null,
                    pause_count integer not null,
                    review_exit_ms integer not null default 0,
                    review_exit_count integer not null default 0,
                    resumed_after_restart integer not null,
                    used_undo integer not null,
                    undo_count integer not null default 0,
                    boosts_used integer not null,
                    deleted_at text
                );

                create index if not exists idx_speed_streak_runs_ended_at
                    on speed_streak_runs(ended_at);
                create index if not exists idx_speed_streak_runs_peak
                    on speed_streak_runs(peak_streak);
                """
            )
            self._ensure_speed_streak_run_columns(conn)
            conn.commit()

    def _ensure_speed_streak_run_columns(self, conn: sqlite3.Connection) -> None:
        """Add v2.04 detail fields if an early preview database already exists."""
        existing = {
            str(row["name"])
            for row in conn.execute("pragma table_info(speed_streak_runs)").fetchall()
        }
        additions = {
            "run_span_ms": "integer not null default 0",
            "review_exit_ms": "integer not null default 0",
            "review_exit_count": "integer not null default 0",
            "undo_count": "integer not null default 0",
        }
        for column_name, declaration in additions.items():
            if column_name not in existing:
                conn.execute(
                    f"alter table speed_streak_runs add column {column_name} {declaration}"
                )
        # Early v2.04 previews only kept a boolean. Preserve that information
        # as the smallest truthful count when upgrading their existing rows.
        conn.execute(
            """
            update speed_streak_runs
            set undo_count = 1
            where used_undo != 0 and undo_count = 0
            """
        )
