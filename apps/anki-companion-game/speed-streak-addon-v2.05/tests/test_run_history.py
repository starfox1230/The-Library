from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


ADDON_ROOT = Path(__file__).resolve().parents[1]


def _load_modules() -> tuple[ModuleType, ModuleType]:
    package_name = "speed_streak_v2_04_run_history_test"
    package = ModuleType(package_name)
    package.__path__ = [str(ADDON_ROOT)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package
    for module_name in ("stats_store", "run_history"):
        qualified = f"{package_name}.{module_name}"
        spec = importlib.util.spec_from_file_location(qualified, ADDON_ROOT / f"{module_name}.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
    return (
        sys.modules[f"{package_name}.stats_store"],
        sys.modules[f"{package_name}.run_history"],
    )


class RunHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stats_module, self.history_module = _load_modules()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.store = self.stats_module.StatsStore(Path(self.temporary_directory.name))
        self.tracker = self.history_module.RunHistoryTracker(self.store)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def state(self, streak: int, *, score: int = 0, boosts_used: int = 0) -> SimpleNamespace:
        return SimpleNamespace(
            streak=streak,
            score=score,
            boosts_used=boosts_used,
            gameplay_mode="time_boost",
        )

    def test_records_comparable_time_and_interruption_fields(self) -> None:
        with (
            patch.object(
                self.history_module,
                "_now_epoch_ms",
                side_effect=[1000, 1100, 2100, 2200, 5200, 6000, 7000],
            ),
            patch.object(
                self.history_module,
                "_now_iso",
                side_effect=["start", "second", "ended"],
            ),
        ):
            self.tracker.observe_answer(self.state(1), active_ms=200)
            self.tracker.begin_manual_pause()
            self.tracker.end_manual_pause()
            self.tracker.begin_review_exit()
            self.tracker.end_review_exit()
            self.tracker.observe_answer(self.state(2), active_ms=500)
            self.tracker.complete(end_reason="timeout", state=self.state(0))

        rows = self.store.speed_streak_runs(list_mode="recent")
        self.assertEqual(len(rows), 1)
        run = rows[0]
        self.assertEqual(run["streak"], 2)
        self.assertEqual(run["runSpanMs"], 5000)
        self.assertEqual(run["activeMs"], 700)
        self.assertEqual(run["pauseCount"], 1)
        self.assertEqual(run["pausedMs"], 1000)
        self.assertEqual(run["reviewExitCount"], 1)
        self.assertEqual(run["reviewExitMs"], 3000)

    def test_undo_rolls_back_score_and_answering_time(self) -> None:
        with (
            patch.object(self.history_module, "_now_epoch_ms", side_effect=[1000, 2000, 2500, 3000]),
            patch.object(
                self.history_module,
                "_now_iso",
                side_effect=["first", "second", "second-again", "ended"],
            ),
        ):
            self.tracker.observe_answer(self.state(1), active_ms=100)
            self.tracker.observe_answer(self.state(2), active_ms=250)
            self.tracker.observe_undo(self.state(1))
            self.tracker.observe_answer(self.state(2), active_ms=200)
            self.tracker.observe_undo(self.state(1))
            self.tracker.complete(end_reason="manual-reset", state=self.state(1))

        run = self.store.speed_streak_runs()[0]
        self.assertEqual(run["streak"], 1)
        self.assertEqual(run["activeMs"], 100)
        self.assertEqual(run["runSpanMs"], 0)
        self.assertTrue(run["usedUndo"])
        self.assertEqual(run["undoCount"], 2)

    def test_legacy_boolean_undo_restores_as_a_count_of_one(self) -> None:
        raw = {
            "startedAt": "start",
            "startedEpochMs": 1000,
            "lastProgressAt": "last",
            "lastProgressEpochMs": 2000,
            "peakStreak": 2,
            "usedUndo": True,
        }

        self.tracker.restore_active(raw, resume_enabled=True, state=self.state(2))

        self.assertEqual(self.tracker.active["undoCount"], 1)
        self.assertTrue(self.tracker.active["usedUndo"])

    def test_best_is_derived_and_recalculated_after_deletion(self) -> None:
        for index, streak in enumerate((4, 9, 6), start=1):
            self.store.record_speed_streak_run(
                started_at=f"start-{index}",
                ended_at=f"end-{index}",
                end_reason="timeout",
                peak_streak=streak,
                gameplay_mode="time_boost",
                legacy_score=0,
                cards_answered=streak,
                run_span_ms=1000,
                active_ms=500,
                paused_ms=0,
                pause_count=0,
                review_exit_ms=0,
                review_exit_count=0,
                resumed_after_restart=False,
                used_undo=False,
                boosts_used=0,
            )
        self.assertEqual(self.store.best_speed_streak(), 9)
        self.assertTrue(self.store.delete_best_speed_streak_run())
        self.assertEqual(self.store.best_speed_streak(), 6)

    def test_record_lookup_reports_exact_all_time_rank(self) -> None:
        run_ids = []
        for index, streak in enumerate((4, 9, 6), start=1):
            run_ids.append(
                self.store.record_speed_streak_run(
                    started_at=f"start-{index}",
                    ended_at=f"2026-08-0{index}T12:00:00",
                    end_reason="timeout",
                    peak_streak=streak,
                    gameplay_mode="time_boost",
                    legacy_score=0,
                    cards_answered=streak,
                    run_span_ms=1000,
                    active_ms=500,
                    paused_ms=0,
                    pause_count=0,
                    review_exit_ms=0,
                    review_exit_count=0,
                    resumed_after_restart=False,
                    used_undo=False,
                    boosts_used=0,
                )
            )

        middle = self.store.speed_streak_run_with_rank(run_ids[2])
        self.assertIsNotNone(middle)
        self.assertEqual(middle["streak"], 6)
        self.assertEqual(middle["allTimeRank"], 2)

    def test_live_run_immediately_becomes_the_displayed_best(self) -> None:
        self.tracker.observe_answer(self.state(6), active_ms=1200)

        payload = self.tracker.display_payload(list_mode="recent")

        self.assertEqual(payload["savedBestStreak"], 0)
        self.assertEqual(payload["bestStreak"], 6)
        self.assertTrue(payload["liveIsNewBest"])
        self.assertEqual(payload["active"]["streak"], 6)

    def test_saved_best_remains_distinct_from_live_target(self) -> None:
        self.store.record_speed_streak_run(
            started_at="old-start",
            ended_at="old-end",
            end_reason="timeout",
            peak_streak=8,
            gameplay_mode="time_boost",
            legacy_score=0,
            cards_answered=8,
            run_span_ms=1000,
            active_ms=500,
            paused_ms=0,
            pause_count=0,
            review_exit_ms=0,
            review_exit_count=0,
            resumed_after_restart=False,
            used_undo=False,
            boosts_used=0,
        )
        self.tracker.observe_answer(self.state(9), active_ms=300)

        payload = self.tracker.display_payload(list_mode="best")

        self.assertEqual(payload["savedBestStreak"], 8)
        self.assertEqual(payload["bestStreak"], 9)
        self.assertTrue(payload["liveIsNewBest"])

    def test_run_with_breaks_does_not_claim_a_pure_record(self) -> None:
        self.store.record_speed_streak_run(
            started_at="pure-start",
            ended_at="pure-end",
            end_reason="timeout",
            peak_streak=5,
            gameplay_mode="time_boost",
            legacy_score=0,
            cards_answered=5,
            run_span_ms=1000,
            active_ms=500,
            paused_ms=0,
            pause_count=0,
            review_exit_ms=0,
            review_exit_count=0,
            resumed_after_restart=False,
            used_undo=False,
            boosts_used=0,
        )
        self.tracker.observe_answer(self.state(6), active_ms=300)
        self.tracker.begin_manual_pause()

        payload = self.tracker.display_payload(list_mode="best", purity_mode="pure")

        self.assertEqual(payload["savedBestStreak"], 5)
        self.assertEqual(payload["bestStreak"], 5)
        self.assertFalse(payload["liveIsNewBest"])

    def test_today_mode_uses_only_todays_finished_runs_as_the_target(self) -> None:
        yesterday = (datetime.now() - timedelta(days=1)).isoformat(timespec="seconds")
        today = datetime.now().isoformat(timespec="seconds")
        for ended_at, streak in ((yesterday, 50), (today, 7)):
            self.store.record_speed_streak_run(
                started_at=ended_at,
                ended_at=ended_at,
                end_reason="timeout",
                peak_streak=streak,
                gameplay_mode="time_boost",
                legacy_score=0,
                cards_answered=streak,
                run_span_ms=1000,
                active_ms=500,
                paused_ms=0,
                pause_count=0,
                review_exit_ms=0,
                review_exit_count=0,
                resumed_after_restart=False,
                used_undo=False,
                boosts_used=0,
            )
        self.tracker.observe_answer(self.state(6), active_ms=300)

        payload = self.tracker.display_payload(list_mode="today")

        self.assertEqual(payload["benchmarkMode"], "today")
        self.assertEqual(payload["savedBestStreak"], 7)
        self.assertEqual(payload["bestStreak"], 7)
        self.assertFalse(payload["liveIsNewBest"])
        self.assertEqual([run["streak"] for run in payload["runs"]], [7])

    def test_existing_resume_preference_controls_restart_continuation(self) -> None:
        raw = {
            "startedAt": "start",
            "startedEpochMs": 1000,
            "lastProgressAt": "last",
            "lastProgressEpochMs": 3000,
            "lastSavedEpochMs": 3500,
            "peakStreak": 3,
            "cardsAnswered": 3,
            "gameplayMode": "time_boost",
            "legacyScore": 0,
            "activeMs": 900,
            "pausedMs": 0,
            "pauseCount": 0,
            "manualPauseStartedEpochMs": 0,
            "reviewExitMs": 0,
            "reviewExitCount": 0,
            "reviewExitStartedEpochMs": 0,
            "resumedAfterRestart": False,
            "usedUndo": False,
            "boostsUsed": 0,
            "progress": [],
        }

        continuing = self.history_module.RunHistoryTracker(self.store)
        continuing.restore_active(raw, resume_enabled=True, state=self.state(3))
        self.assertIsNotNone(continuing.active)
        self.assertTrue(continuing.active["resumedAfterRestart"])
        self.assertEqual(self.store.speed_streak_runs(), [])

        ending = self.history_module.RunHistoryTracker(self.store)
        ending.restore_active(raw, resume_enabled=False, state=self.state(0))
        rows = self.store.speed_streak_runs()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["streak"], 3)
        self.assertEqual(rows[0]["endReason"], "restart-without-resume")


if __name__ == "__main__":
    unittest.main()
