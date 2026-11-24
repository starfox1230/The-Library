from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import time
from typing import Any, Dict

from .stats_store import StatsStore


SCOREBOARD_LAYOUT_OFF = "off"
SCOREBOARD_LAYOUT_COMPACT = "compact"
SCOREBOARD_LAYOUT_LADDER = "ladder"
SCOREBOARD_LAYOUT_BEST_ONLY = "best_only"
SCOREBOARD_LAYOUTS = {
    SCOREBOARD_LAYOUT_OFF,
    SCOREBOARD_LAYOUT_COMPACT,
    SCOREBOARD_LAYOUT_LADDER,
    SCOREBOARD_LAYOUT_BEST_ONLY,
}
SCOREBOARD_LIST_RECENT = "recent"
SCOREBOARD_LIST_BEST = "best"
SCOREBOARD_LIST_TODAY = "today"
SCOREBOARD_LIST_MODES = {SCOREBOARD_LIST_RECENT, SCOREBOARD_LIST_BEST, SCOREBOARD_LIST_TODAY}
SCOREBOARD_ORDER_RANKED = "ranked"
SCOREBOARD_ORDER_CHRONOLOGICAL = "chronological"
SCOREBOARD_ORDERS = {SCOREBOARD_ORDER_RANKED, SCOREBOARD_ORDER_CHRONOLOGICAL}
SCOREBOARD_PURITY_ALL = "all"
SCOREBOARD_PURITY_PURE = "pure"
SCOREBOARD_PURITY_MODES = {SCOREBOARD_PURITY_ALL, SCOREBOARD_PURITY_PURE}


def normalize_scoreboard_layout(value: object) -> str:
    normalized = str(value or SCOREBOARD_LAYOUT_BEST_ONLY).strip().lower()
    return normalized if normalized in SCOREBOARD_LAYOUTS else SCOREBOARD_LAYOUT_BEST_ONLY


def normalize_scoreboard_list_mode(value: object) -> str:
    normalized = str(value or SCOREBOARD_LIST_BEST).strip().lower()
    return normalized if normalized in SCOREBOARD_LIST_MODES else SCOREBOARD_LIST_BEST


def scoreboard_list_mode_for_layout(layout: object, list_mode: object) -> str:
    """Recent 5 only has meaning when the five-row record list is visible."""

    normalized_layout = normalize_scoreboard_layout(layout)
    normalized_mode = normalize_scoreboard_list_mode(list_mode)
    if normalized_mode == SCOREBOARD_LIST_RECENT and normalized_layout != SCOREBOARD_LAYOUT_LADDER:
        return SCOREBOARD_LIST_BEST
    return normalized_mode


def normalize_scoreboard_order(value: object) -> str:
    normalized = str(value or SCOREBOARD_ORDER_RANKED).strip().lower()
    return normalized if normalized in SCOREBOARD_ORDERS else SCOREBOARD_ORDER_RANKED


def normalize_scoreboard_purity(value: object) -> str:
    normalized = str(value or SCOREBOARD_PURITY_ALL).strip().lower()
    return normalized if normalized in SCOREBOARD_PURITY_MODES else SCOREBOARD_PURITY_ALL


def _now_epoch_ms() -> int:
    return int(time.time() * 1000)


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class RunHistoryTracker:
    """Tracks gameplay streak runs independently from review correctness stats."""

    def __init__(self, store: StatsStore) -> None:
        self.store = store
        self.active: Dict[str, Any] | None = None

    def restore_active(self, raw: object, *, resume_enabled: bool, state: Any) -> None:
        active = self._normalize_active(raw)
        if active is None:
            if resume_enabled and int(getattr(state, "streak", 0) or 0) > 0:
                # A user upgrading from v2.03 may have a restorable gameplay
                # streak but no v2.04 run-history payload yet. Adopt that live
                # streak without inventing pre-upgrade timing details.
                self.observe_answer(state, active_ms=0)
                if self.active is not None:
                    self.active["resumedAfterRestart"] = True
                    self._begin_review_exit(at_epoch_ms=_now_epoch_ms())
            return
        if resume_enabled and int(getattr(state, "streak", 0) or 0) > 0:
            self.active = active
            self.active["resumedAfterRestart"] = True
            if int(self.active.get("reviewExitStartedEpochMs", 0) or 0) <= 0:
                last_saved = max(
                    int(self.active.get("lastSavedEpochMs", 0) or 0),
                    int(self.active.get("lastProgressEpochMs", 0) or 0),
                )
                self._begin_review_exit(at_epoch_ms=last_saved or _now_epoch_ms())
            return
        cutoff_ms = max(
            int(active.get("lastSavedEpochMs", 0) or 0),
            int(active.get("lastProgressEpochMs", 0) or 0),
        )
        pause_started = int(active.get("manualPauseStartedEpochMs", 0) or 0)
        if pause_started > 0:
            active["pausedMs"] = max(0, int(active.get("pausedMs", 0) or 0)) + max(
                0, cutoff_ms - pause_started
            )
            active["manualPauseStartedEpochMs"] = 0
        exit_started = int(active.get("reviewExitStartedEpochMs", 0) or 0)
        if exit_started > 0:
            active["reviewExitMs"] = max(0, int(active.get("reviewExitMs", 0) or 0)) + max(
                0, cutoff_ms - exit_started
            )
            active["reviewExitStartedEpochMs"] = 0
        self._record_active(active, end_reason="restart-without-resume")

    def observe_answer(self, state: Any, *, active_ms: int) -> None:
        streak = max(0, int(getattr(state, "streak", 0) or 0))
        if streak <= 0:
            return
        now_ms = _now_epoch_ms()
        now_iso = _now_iso()
        if self.active is None:
            self.active = {
                "startedAt": now_iso,
                "startedEpochMs": now_ms,
                "lastProgressAt": now_iso,
                "lastProgressEpochMs": now_ms,
                "peakStreak": streak,
                "cardsAnswered": streak,
                "gameplayMode": str(getattr(state, "gameplay_mode", "time_boost") or "time_boost"),
                "legacyScore": max(0, int(getattr(state, "score", 0) or 0)),
                "activeMs": max(0, int(active_ms or 0)),
                "pausedMs": 0,
                "pauseCount": 0,
                "manualPauseStartedEpochMs": 0,
                "reviewExitMs": 0,
                "reviewExitCount": 0,
                "reviewExitStartedEpochMs": 0,
                "resumedAfterRestart": False,
                "undoCount": 0,
                "usedUndo": False,
                "boostsUsed": max(0, int(getattr(state, "boosts_used", 0) or 0)),
                "progress": [],
                "lastSavedEpochMs": now_ms,
            }
        else:
            self.active["activeMs"] = max(0, int(self.active.get("activeMs", 0) or 0)) + max(
                0, int(active_ms or 0)
            )
        self.active["peakStreak"] = streak
        self.active["cardsAnswered"] = streak
        self.active["legacyScore"] = max(0, int(getattr(state, "score", 0) or 0))
        self.active["boostsUsed"] = max(0, int(getattr(state, "boosts_used", 0) or 0))
        self.active["lastProgressAt"] = now_iso
        self.active["lastProgressEpochMs"] = now_ms
        progress = self.active.setdefault("progress", [])
        if isinstance(progress, list):
            progress.append(
                {
                    "streak": streak,
                    "at": now_iso,
                    "atEpochMs": now_ms,
                    "activeMs": int(self.active.get("activeMs", 0) or 0),
                    "legacyScore": int(self.active.get("legacyScore", 0) or 0),
                    "boostsUsed": int(self.active.get("boostsUsed", 0) or 0),
                }
            )
            if len(progress) > 5000:
                del progress[:-5000]

    def observe_undo(self, state: Any) -> None:
        if self.active is None:
            return
        streak = max(0, int(getattr(state, "streak", 0) or 0))
        progress = self.active.get("progress", [])
        if isinstance(progress, list):
            while progress and int(progress[-1].get("streak", 0) or 0) > streak:
                progress.pop()
        self.active["undoCount"] = max(0, int(self.active.get("undoCount", 0) or 0)) + 1
        self.active["usedUndo"] = True
        if streak <= 0:
            self.active = None
            return
        self.active["peakStreak"] = streak
        self.active["cardsAnswered"] = streak
        if isinstance(progress, list) and progress:
            checkpoint = progress[-1]
            self.active["lastProgressAt"] = str(checkpoint.get("at", self.active.get("startedAt", "")) or "")
            self.active["lastProgressEpochMs"] = max(
                int(self.active.get("startedEpochMs", 0) or 0),
                int(checkpoint.get("atEpochMs", 0) or 0),
            )
            self.active["activeMs"] = max(0, int(checkpoint.get("activeMs", 0) or 0))
            self.active["legacyScore"] = max(0, int(checkpoint.get("legacyScore", 0) or 0))
            self.active["boostsUsed"] = max(0, int(checkpoint.get("boostsUsed", 0) or 0))
        else:
            self.active["lastProgressAt"] = str(self.active.get("startedAt", "") or "")
            self.active["lastProgressEpochMs"] = int(self.active.get("startedEpochMs", 0) or 0)
            self.active["legacyScore"] = max(0, int(getattr(state, "score", 0) or 0))
            self.active["boostsUsed"] = max(0, int(getattr(state, "boosts_used", 0) or 0))

    def begin_manual_pause(self) -> None:
        if self.active is None or int(self.active.get("manualPauseStartedEpochMs", 0) or 0) > 0:
            return
        self.active["pauseCount"] = max(0, int(self.active.get("pauseCount", 0) or 0)) + 1
        self.active["manualPauseStartedEpochMs"] = _now_epoch_ms()

    def end_manual_pause(self) -> None:
        if self.active is None:
            return
        started = int(self.active.get("manualPauseStartedEpochMs", 0) or 0)
        if started <= 0:
            return
        self.active["pausedMs"] = max(0, int(self.active.get("pausedMs", 0) or 0)) + max(
            0, _now_epoch_ms() - started
        )
        self.active["manualPauseStartedEpochMs"] = 0

    def begin_review_exit(self) -> None:
        self._begin_review_exit(at_epoch_ms=_now_epoch_ms())

    def _begin_review_exit(self, *, at_epoch_ms: int) -> None:
        if self.active is None or int(self.active.get("reviewExitStartedEpochMs", 0) or 0) > 0:
            return
        self.active["reviewExitCount"] = max(0, int(self.active.get("reviewExitCount", 0) or 0)) + 1
        self.active["reviewExitStartedEpochMs"] = max(1, int(at_epoch_ms or _now_epoch_ms()))

    def end_review_exit(self) -> None:
        if self.active is None:
            return
        started = int(self.active.get("reviewExitStartedEpochMs", 0) or 0)
        if started <= 0:
            return
        self.active["reviewExitMs"] = max(0, int(self.active.get("reviewExitMs", 0) or 0)) + max(
            0, _now_epoch_ms() - started
        )
        self.active["reviewExitStartedEpochMs"] = 0

    def complete(self, *, end_reason: str, state: Any) -> int:
        if self.active is None:
            return 0
        self.active["peakStreak"] = max(
            0,
            int(getattr(state, "streak", 0) or self.active.get("peakStreak", 0) or 0),
        )
        self.active["legacyScore"] = max(0, int(getattr(state, "score", 0) or 0))
        self.active["boostsUsed"] = max(0, int(getattr(state, "boosts_used", 0) or 0))
        active = self.active
        self.active = None
        return self._record_active(active, end_reason=end_reason)

    def discard_active(self) -> None:
        self.active = None

    def export_active(self) -> Dict[str, Any]:
        if self.active is None:
            return {}
        self.active["lastSavedEpochMs"] = _now_epoch_ms()
        return deepcopy(self.active)

    def display_payload(self, *, list_mode: str, purity_mode: str = SCOREBOARD_PURITY_ALL) -> Dict[str, Any]:
        mode = normalize_scoreboard_list_mode(list_mode)
        purity = normalize_scoreboard_purity(purity_mode)
        saved_best = (
            self.store.best_speed_streak_today(purity=purity)
            if mode == SCOREBOARD_LIST_TODAY
            else self.store.best_speed_streak(purity=purity)
        )
        active = self._active_display_payload()
        live_streak = max(0, int((active or {}).get("streak", 0) or 0))
        active_is_eligible = bool(active) and (
            purity != SCOREBOARD_PURITY_PURE
            or (
                max(0, int(active.get("pauseCount", 0) or 0)) == 0
                and max(0, int(active.get("reviewExitCount", 0) or 0)) == 0
                and not bool(active.get("resumedAfterRestart", False))
                and max(
                    0,
                    int(
                        active.get(
                            "undoCount",
                            1 if active.get("usedUndo", False) else 0,
                        )
                        or 0
                    ),
                )
                == 0
            )
        )
        eligible_live_streak = live_streak if active_is_eligible else 0
        return {
            # The review-window target should react immediately. A live run is
            # provisional until it ends, but hiding it behind a dash makes the
            # feature look broken precisely when the user sets their first
            # streak record or passes an old record.
            "bestStreak": max(saved_best, eligible_live_streak),
            "savedBestStreak": saved_best,
            "liveIsNewBest": bool(active_is_eligible and live_streak > saved_best),
            "benchmarkMode": "today" if mode == SCOREBOARD_LIST_TODAY else "all_time",
            "runs": self.store.speed_streak_runs(list_mode=mode, limit=5, purity=purity),
            "purityMode": purity,
            "active": active,
        }

    def _active_display_payload(self) -> Dict[str, Any] | None:
        if self.active is None:
            return None
        active = deepcopy(self.active)
        now_ms = _now_epoch_ms()
        pause_started = int(active.get("manualPauseStartedEpochMs", 0) or 0)
        exit_started = int(active.get("reviewExitStartedEpochMs", 0) or 0)
        if pause_started > 0:
            active["pausedMs"] = int(active.get("pausedMs", 0) or 0) + max(0, now_ms - pause_started)
        if exit_started > 0:
            active["reviewExitMs"] = int(active.get("reviewExitMs", 0) or 0) + max(0, now_ms - exit_started)
        active["runSpanMs"] = max(
            0,
            int(active.get("lastProgressEpochMs", 0) or 0) - int(active.get("startedEpochMs", 0) or 0),
        )
        active["streak"] = max(0, int(active.get("peakStreak", 0) or 0))
        active.pop("progress", None)
        active.pop("manualPauseStartedEpochMs", None)
        active.pop("reviewExitStartedEpochMs", None)
        active.pop("lastSavedEpochMs", None)
        return active

    def _record_active(self, active: Dict[str, Any], *, end_reason: str) -> int:
        now_ms = _now_epoch_ms()
        pause_started = int(active.get("manualPauseStartedEpochMs", 0) or 0)
        exit_started = int(active.get("reviewExitStartedEpochMs", 0) or 0)
        paused_ms = max(0, int(active.get("pausedMs", 0) or 0))
        review_exit_ms = max(0, int(active.get("reviewExitMs", 0) or 0))
        if pause_started > 0:
            paused_ms += max(0, now_ms - pause_started)
        if exit_started > 0:
            review_exit_ms += max(0, now_ms - exit_started)
        started_ms = max(0, int(active.get("startedEpochMs", 0) or 0))
        last_progress_ms = max(started_ms, int(active.get("lastProgressEpochMs", started_ms) or started_ms))
        return self.store.record_speed_streak_run(
            started_at=str(active.get("startedAt", "") or _now_iso()),
            ended_at=_now_iso(),
            end_reason=end_reason,
            peak_streak=max(0, int(active.get("peakStreak", 0) or 0)),
            gameplay_mode=str(active.get("gameplayMode", "time_boost") or "time_boost"),
            legacy_score=max(0, int(active.get("legacyScore", 0) or 0)),
            cards_answered=max(0, int(active.get("cardsAnswered", 0) or 0)),
            run_span_ms=max(0, last_progress_ms - started_ms),
            active_ms=max(0, int(active.get("activeMs", 0) or 0)),
            paused_ms=paused_ms,
            pause_count=max(0, int(active.get("pauseCount", 0) or 0)),
            review_exit_ms=review_exit_ms,
            review_exit_count=max(0, int(active.get("reviewExitCount", 0) or 0)),
            resumed_after_restart=bool(active.get("resumedAfterRestart", False)),
            undo_count=max(
                0,
                int(active.get("undoCount", 1 if active.get("usedUndo", False) else 0) or 0),
            ),
            used_undo=bool(active.get("usedUndo", False)),
            boosts_used=max(0, int(active.get("boostsUsed", 0) or 0)),
        )

    def _normalize_active(self, raw: object) -> Dict[str, Any] | None:
        if not isinstance(raw, dict):
            return None
        active = deepcopy(raw)
        if max(0, int(active.get("peakStreak", 0) or 0)) <= 0:
            return None
        active.setdefault("progress", [])
        active.setdefault("pausedMs", 0)
        active.setdefault("pauseCount", 0)
        active.setdefault("manualPauseStartedEpochMs", 0)
        active.setdefault("reviewExitMs", 0)
        active.setdefault("reviewExitCount", 0)
        active.setdefault("reviewExitStartedEpochMs", 0)
        active.setdefault("resumedAfterRestart", False)
        active["undoCount"] = max(
            0,
            int(active.get("undoCount", 1 if active.get("usedUndo", False) else 0) or 0),
        )
        active.setdefault("usedUndo", False)
        active["usedUndo"] = bool(active.get("usedUndo", False) or active["undoCount"] > 0)
        active.setdefault("lastSavedEpochMs", 0)
        return active
