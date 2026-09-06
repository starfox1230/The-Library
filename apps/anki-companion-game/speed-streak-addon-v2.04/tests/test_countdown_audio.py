from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType


ADDON_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("speed_streak_countdown_audio_test", ADDON_ROOT / "countdown_audio.py")
assert SPEC and SPEC.loader
COUNTDOWN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = COUNTDOWN
SPEC.loader.exec_module(COUNTDOWN)


def _load_game_state() -> ModuleType:
    package_name = "speed_streak_v2_04_countdown_state_test"
    package = ModuleType(package_name)
    package.__path__ = [str(ADDON_ROOT)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package
    for module_name in ("countdown_audio", "feedback_catalog", "game_state"):
        qualified = f"{package_name}.{module_name}"
        spec = importlib.util.spec_from_file_location(qualified, ADDON_ROOT / f"{module_name}.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.game_state"]


class CountdownAudioScheduleTests(unittest.TestCase):
    def test_preview_recreates_early_launch_and_omits_zero(self) -> None:
        cues = COUNTDOWN.countdown_preview_cues(
            warning_seconds=3,
            alignment_ms=125,
        )
        self.assertEqual(
            [(cue.second, cue.delay_ms) for cue in cues],
            [(3, 875), (2, 1875), (1, 2875)],
        )

    def test_first_cue_targets_warning_boundary(self) -> None:
        schedule = COUNTDOWN.next_countdown_cue(
            remaining_ms=12_000,
            warning_seconds=3,
            alignment_ms=0,
        )
        self.assertEqual((schedule.second, schedule.delay_ms), (3, 9_000))

    def test_alignment_launches_clip_early(self) -> None:
        schedule = COUNTDOWN.next_countdown_cue(
            remaining_ms=12_000,
            warning_seconds=3,
            alignment_ms=125,
        )
        self.assertEqual((schedule.second, schedule.delay_ms), (3, 8_875))

    def test_zero_mark_is_never_scheduled(self) -> None:
        schedule = COUNTDOWN.next_countdown_cue(
            remaining_ms=900,
            warning_seconds=3,
            alignment_ms=0,
        )
        self.assertIsNone(schedule)

    def test_fired_second_advances_to_next_boundary(self) -> None:
        schedule = COUNTDOWN.next_countdown_cue(
            remaining_ms=3_000,
            warning_seconds=3,
            alignment_ms=0,
            fired_seconds={3},
        )
        self.assertEqual((schedule.second, schedule.delay_ms), (2, 1_000))

    def test_small_timer_drift_fires_now_instead_of_skipping(self) -> None:
        schedule = COUNTDOWN.next_countdown_cue(
            remaining_ms=2_955,
            warning_seconds=3,
            alignment_ms=0,
        )
        self.assertEqual((schedule.second, schedule.delay_ms), (3, 0))

    def test_large_lateness_skips_stale_second(self) -> None:
        schedule = COUNTDOWN.next_countdown_cue(
            remaining_ms=2_700,
            warning_seconds=3,
            alignment_ms=0,
        )
        self.assertEqual((schedule.second, schedule.delay_ms), (2, 700))


class CountdownAudioStateTests(unittest.TestCase):
    def test_settings_export_and_reset(self) -> None:
        game_state = _load_game_state()
        engine = game_state.CompanionGameEngine()
        engine.update_time_limits(
            question_seconds=12,
            answer_seconds=8,
            countdown_audio_enabled=True,
            countdown_audio_file="countdown-cues/clock-tick-crisp.mp3",
            countdown_audio_volume=175,
            audio_event_volumes={"sync": 200, "timeout": -20},
            countdown_warning_seconds=6,
            countdown_audio_alignment_ms=135,
        )
        payload = engine.export()
        self.assertEqual(payload["countdownAudioEnabled"], 1)
        self.assertEqual(payload["countdownAudioVolume"], 175)
        self.assertEqual(payload["audioEventVolumes"]["sync"], 200)
        self.assertEqual(payload["audioEventVolumes"]["timeout"], 0)
        self.assertEqual(payload["countdownWarningSeconds"], 6)
        self.assertEqual(payload["countdownAudioAlignmentMs"], 135)

        engine.reset_settings_to_defaults()
        self.assertFalse(engine.state.countdown_audio_enabled)
        self.assertEqual(engine.state.countdown_audio_volume, 100)
        self.assertTrue(all(value == 100 for value in engine.state.audio_event_volumes.values()))
        self.assertEqual(engine.state.countdown_warning_seconds, 3)
        self.assertEqual(engine.state.countdown_audio_alignment_ms, 0)

    def test_alignment_and_threshold_are_clamped(self) -> None:
        game_state = _load_game_state()
        engine = game_state.CompanionGameEngine()
        engine.update_time_limits(
            question_seconds=12,
            answer_seconds=8,
            countdown_warning_seconds=999,
            countdown_audio_alignment_ms=9999,
        )
        self.assertEqual(engine.state.countdown_warning_seconds, 120)
        self.assertEqual(engine.state.countdown_audio_alignment_ms, 950)

    def test_settings_uses_waveform_sync_editor_instead_of_seek_preview(self) -> None:
        source = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
        self.assertIn("CountdownSyncPointDialog", source)
        self.assertIn("Adjust Sync Point…", source)
        self.assertIn("The complete clip starts early; it is not trimmed.", source)
        self.assertIn("prepare_countdown_audio_preview", source)
        self.assertNotIn('ModernButton("Play Point"', source)
        self.assertNotIn("That point could not be played from the settings screen.", source)


if __name__ == "__main__":
    unittest.main()
