from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from types import ModuleType, SimpleNamespace


ADDON_ROOT = Path(__file__).resolve().parents[1]


class FakeAudioOutput:
    def __init__(self) -> None:
        self.volume = 1.0
        self.muted = False

    def setVolume(self, value: float) -> None:
        self.volume = value

    def setMuted(self, value: bool) -> None:
        self.muted = value


class FakeMediaPlayer:
    instances: list["FakeMediaPlayer"] = []

    def __init__(self) -> None:
        self.source = ""
        self.source_changes = 0
        self.audio_output = None
        self.positions: list[int] = []
        self.play_count = 0
        self.stop_count = 0
        self.state = SimpleNamespace(name="StoppedState")
        self.__class__.instances.append(self)

    def setAudioOutput(self, output: FakeAudioOutput) -> None:
        self.audio_output = output

    def setSource(self, source: str) -> None:
        self.source = source
        self.source_changes += 1

    def setPosition(self, position: int) -> None:
        self.positions.append(position)

    def play(self) -> None:
        self.play_count += 1
        self.state = SimpleNamespace(name="PlayingState")

    def stop(self) -> None:
        self.stop_count += 1
        self.state = SimpleNamespace(name="StoppedState")

    def playbackState(self):
        return self.state


class FakeSoundEffect:
    instances: list["FakeSoundEffect"] = []
    default_loaded = True

    def __init__(self) -> None:
        self.source = ""
        self.play_count = 0
        self.stop_count = 0
        self.loop_count = 0
        self.volume = 0.0
        self.muted = False
        self.playing = False
        self.loaded = self.__class__.default_loaded
        self.__class__.instances.append(self)

    def setSource(self, source: str) -> None:
        self.source = source

    def setLoopCount(self, count: int) -> None:
        self.loop_count = count

    def setVolume(self, volume: float) -> None:
        self.volume = volume

    def setMuted(self, muted: bool) -> None:
        self.muted = muted

    def isLoaded(self) -> bool:
        return self.loaded

    def play(self) -> None:
        self.play_count += 1
        self.playing = True

    def stop(self) -> None:
        self.stop_count += 1
        self.playing = False

    def isPlaying(self) -> bool:
        return self.playing


class FakeUrl:
    @staticmethod
    def fromLocalFile(path: str) -> str:
        return path


class FakeTimer:
    @staticmethod
    def singleShot(_delay: int, callback) -> None:
        callback()


def _load_audio_feedback() -> ModuleType:
    package_name = "speed_streak_v2_04_audio_feedback_test"
    package = ModuleType(package_name)
    package.__path__ = [str(ADDON_ROOT)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package

    fake_aqt = ModuleType("aqt")
    fake_qt = ModuleType("aqt.qt")
    fake_qt.QAudioOutput = FakeAudioOutput
    fake_qt.QMediaPlayer = FakeMediaPlayer
    fake_qt.QSoundEffect = FakeSoundEffect
    fake_qt.QTimer = FakeTimer
    fake_qt.QUrl = FakeUrl
    fake_aqt.qt = fake_qt
    sys.modules["aqt"] = fake_aqt
    sys.modules["aqt.qt"] = fake_qt

    for module_name in ("feedback_catalog", "audio_feedback"):
        qualified = f"{package_name}.{module_name}"
        spec = importlib.util.spec_from_file_location(qualified, ADDON_ROOT / f"{module_name}.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.audio_feedback"]


AUDIO_FEEDBACK = _load_audio_feedback()


class AudioFeedbackPreloadTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeMediaPlayer.instances.clear()
        FakeSoundEffect.instances.clear()
        FakeSoundEffect.default_loaded = True
        self.temp_dir = tempfile.TemporaryDirectory()
        self.audio_root = Path(self.temp_dir.name) / "Audio_trimmed"
        (self.audio_root / "countdown-cues").mkdir(parents=True)
        (self.audio_root / "compressed.mp3").write_bytes(b"compressed")
        (self.audio_root / "event.mp3").write_bytes(b"legacy")
        (self.audio_root / "event.wav").write_bytes(b"wave")
        (self.audio_root / "second.wav").write_bytes(b"wave")
        (self.audio_root / "countdown-cues" / "clock-tick-soft.wav").write_bytes(b"wave")
        self.controller = AUDIO_FEEDBACK.AudioFeedbackController(self.audio_root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_selected_sound_keeps_one_sourced_player(self) -> None:
        self.assertEqual(self.controller.prepare_files(["compressed.mp3", "compressed.mp3"]), 1)
        self.assertTrue(self.controller.play("compressed.mp3"))
        self.assertTrue(self.controller.play("compressed.mp3"))
        self.assertEqual(len(FakeMediaPlayer.instances), 1)
        self.assertEqual(FakeMediaPlayer.instances[0].source_changes, 1)
        self.assertEqual(FakeMediaPlayer.instances[0].positions, [0, 0])
        self.assertEqual(FakeMediaPlayer.instances[0].stop_count, 0)

    def test_warm_up_is_silent_and_only_runs_once(self) -> None:
        self.controller.warm_up(["compressed.mp3", "compressed.mp3"])
        player = FakeMediaPlayer.instances[0]
        self.assertEqual(player.play_count, 1)
        self.assertFalse(player.audio_output.muted)
        self.controller.warm_up(["compressed.mp3"])
        self.assertEqual(player.play_count, 1)

    def test_wav_event_is_predecoded_and_reuses_one_low_latency_effect(self) -> None:
        self.assertEqual(self.controller.prepare_files(["event.wav", "event.wav"]), 1)
        self.controller.warm_up(["event.wav"])
        self.assertTrue(self.controller.play("event.wav"))
        self.assertTrue(self.controller.play("event.wav"))
        self.assertEqual(len(FakeSoundEffect.instances), 1)
        # One silent prime followed by two audible plays.
        self.assertEqual(FakeSoundEffect.instances[0].play_count, 3)

    def test_new_event_does_not_cut_off_effect_already_playing(self) -> None:
        self.controller.warm_up(["event.wav", "second.wav"])
        first, second = FakeSoundEffect.instances
        self.assertTrue(self.controller.play("event.wav"))
        first_stop_count = first.stop_count
        self.assertTrue(self.controller.play("second.wav", interrupt=True))
        self.assertEqual(first.stop_count, first_stop_count)
        self.assertTrue(first.isPlaying())
        self.assertTrue(second.isPlaying())

    def test_unloaded_wav_effect_falls_back_instead_of_reporting_silent_success(self) -> None:
        FakeSoundEffect.default_loaded = False
        fallback_calls: list[str] = []
        self.assertTrue(
            self.controller.play(
                "event.wav",
                fallback=lambda: fallback_calls.append("browser") is None,
            )
        )
        self.assertEqual(FakeSoundEffect.instances[0].play_count, 0)
        self.assertEqual(fallback_calls, ["browser"])
        self.assertEqual(len(FakeMediaPlayer.instances), 0)

    def test_unloaded_wav_without_independent_fallback_keeps_prior_fast_path(self) -> None:
        FakeSoundEffect.default_loaded = False
        self.assertTrue(self.controller.play("event.wav"))
        self.assertEqual(FakeSoundEffect.instances[0].play_count, 1)
        self.assertEqual(len(FakeMediaPlayer.instances), 0)

    def test_noninterrupt_sync_is_suppressed_while_another_effect_plays(self) -> None:
        self.controller.warm_up(["event.wav", "second.wav"])
        self.assertTrue(self.controller.play("event.wav"))
        self.assertFalse(self.controller.play("second.wav", interrupt=False))

    def test_wav_countdown_uses_low_latency_sound_effect(self) -> None:
        cue = "countdown-cues/clock-tick-soft.wav"
        self.assertTrue(self.controller.prepare_timed(cue))
        self.assertTrue(self.controller.play_timed(cue))
        self.assertEqual(len(FakeSoundEffect.instances), 1)
        # One muted prime plus the audible cue; later cues reuse this decoder.
        self.assertEqual(FakeSoundEffect.instances[0].play_count, 2)
        self.assertEqual(FakeSoundEffect.instances[0].loop_count, 1)

    def test_volume_midpoint_and_double_use_real_linear_output(self) -> None:
        self.assertTrue(self.controller.play("compressed.mp3", volume_percent=100))
        player = FakeMediaPlayer.instances[0]
        self.assertEqual(player.audio_output.volume, 0.5)
        self.assertTrue(self.controller.play("compressed.mp3", volume_percent=200))
        self.assertEqual(player.audio_output.volume, 1.0)

    def test_mp3_volume_zero_is_a_real_mute_after_warm_up(self) -> None:
        self.controller.warm_up(["compressed.mp3"])
        self.assertTrue(self.controller.play("compressed.mp3", volume_percent=0))
        output = FakeMediaPlayer.instances[0].audio_output
        self.assertEqual(output.volume, 0.0)
        self.assertTrue(output.muted)
        self.assertTrue(self.controller.play("compressed.mp3", volume_percent=200))
        self.assertEqual(output.volume, 1.0)
        self.assertFalse(output.muted)

    def test_mp3_player_supports_anki_versions_that_do_not_reexport_qt_multimedia(self) -> None:
        source = (ADDON_ROOT / "audio_feedback.py").read_text(encoding="utf-8")
        self.assertIn("from PyQt6.QtMultimedia import QMediaPlayer", source)
        self.assertIn("from PyQt6.QtMultimedia import QAudioOutput", source)
        self.assertIn("set_muted(linear_volume <= 0.0)", source)

    def test_mp3_sampler_uses_fresh_preloaded_volume_controlled_players(self) -> None:
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        start = reviewer.index("def preview_audio_feedback(")
        end = reviewer.index("def preview_native_audio_diagnostic", start)
        source = reviewer[start:end]
        self.assertIn('path.suffix.lower() != ".wav"', source)
        self.assertIn("self._play_review_web_audio_feedback(", source)
        self.assertIn("volume_percent=volume_percent", source)

        browser_audio = (ADDON_ROOT / "web" / "audio_feedback.js").read_text(encoding="utf-8")
        self.assertIn("standbyByUrl: new Map()", browser_audio)
        self.assertIn("state.standbyByUrl.get(url)", browser_audio)
        self.assertIn("state.standbyByUrl.set(url, createAudio(url))", browser_audio)
        self.assertIn("silence(previous)", browser_audio)
        self.assertNotIn("currentTime = 0", browser_audio)

    def test_timed_volume_is_applied_after_silent_prime(self) -> None:
        cue = "countdown-cues/clock-tick-soft.wav"
        self.assertTrue(self.controller.prepare_timed(cue, 160))
        self.assertTrue(self.controller.timed_ready(cue))
        self.assertAlmostEqual(FakeSoundEffect.instances[0].volume, 0.8)

    def test_alignment_preview_seeks_to_selected_point(self) -> None:
        self.assertTrue(self.controller.play_from_position("compressed.mp3", 135))
        self.assertEqual(FakeMediaPlayer.instances[0].positions, [135])

    def test_existing_mp3_event_selection_migrates_to_low_latency_wav(self) -> None:
        self.assertEqual(self.controller.normalize_file("event.mp3"), "event.wav")

    def test_temporarily_missing_uploaded_selection_is_never_replaced_by_default(self) -> None:
        uploaded = "__uploaded__/converted-rating.wav"
        self.assertEqual(self.controller.normalize_file(uploaded), uploaded)
        normalized = self.controller.normalize_event_files({"good": uploaded})
        self.assertEqual(normalized["good"], uploaded)
        self.assertIsNone(self.controller.resolve_path(uploaded))

    def test_profile_upload_becomes_available_without_changing_its_saved_key(self) -> None:
        uploaded = "__uploaded__/converted-rating.wav"
        profile_root = Path(self.temp_dir.name) / "profile-data"
        upload_root = profile_root / "audio_uploads"
        upload_root.mkdir(parents=True)
        (upload_root / "converted-rating.wav").write_bytes(b"profile wave")
        profile_controller = AUDIO_FEEDBACK.AudioFeedbackController(self.audio_root, profile_root)
        self.assertEqual(profile_controller.normalize_file(uploaded), uploaded)
        self.assertEqual(profile_controller.resolve_path(uploaded), upload_root / "converted-rating.wav")

    def test_uploaded_mp3_is_not_replaced_when_same_stem_wav_also_exists(self) -> None:
        profile_root = Path(self.temp_dir.name) / "profile-data"
        upload_root = profile_root / "audio_uploads"
        upload_root.mkdir(parents=True)
        (upload_root / "rating.mp3").write_bytes(b"custom mp3")
        (upload_root / "rating.wav").write_bytes(b"custom wav")
        profile_controller = AUDIO_FEEDBACK.AudioFeedbackController(self.audio_root, profile_root)
        selected = "__uploaded__/rating.mp3"
        self.assertEqual(profile_controller.normalize_file(selected), selected)
        self.assertEqual(profile_controller.resolve_path(selected), upload_root / "rating.mp3")

    def test_profile_mp3_gets_content_addressed_browser_export_without_moving_original(self) -> None:
        uploaded = "__uploaded__/custom-rating.mp3"
        profile_root = Path(self.temp_dir.name) / "profile-data"
        upload_root = profile_root / "audio_uploads"
        upload_root.mkdir(parents=True)
        original = upload_root / "custom-rating.mp3"
        original.write_bytes(b"custom compressed audio")
        profile_controller = AUDIO_FEEDBACK.AudioFeedbackController(self.audio_root, profile_root)
        relative_path = profile_controller.export_relative_path(uploaded)
        self.assertTrue(relative_path.startswith("user_files/audio_uploads/web_cache/"))
        mirrored = self.audio_root.parent / Path(relative_path)
        self.assertEqual(mirrored.read_bytes(), original.read_bytes())
        self.assertTrue(original.exists())

    def test_old_mp3_countdown_selection_migrates_to_wav(self) -> None:
        normalized = self.controller.normalize_file("countdown-cues/clock-tick-soft.mp3")
        self.assertEqual(normalized, "countdown-cues/clock-tick-soft.wav")

    def test_reported_retro_laser_one_selection_uses_packaged_wav(self) -> None:
        packaged_audio_root = ADDON_ROOT / "Audio_trimmed"
        controller = AUDIO_FEEDBACK.AudioFeedbackController(packaged_audio_root)
        mp3_selection = "kenney_sci-fi-sounds/Audio/laserRetro_000.mp3"
        wav_selection = "kenney_sci-fi-sounds/Audio/laserRetro_000.wav"
        self.assertTrue((packaged_audio_root / wav_selection).is_file())
        self.assertEqual(controller.normalize_file(mp3_selection), wav_selection)

    def test_card_phase_reset_does_not_stop_an_already_started_countdown_cue(self) -> None:
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        start = reviewer.index("def _reset_countdown_audio_phase")
        end = reviewer.index("def _sync_countdown_audio", start)
        reset_source = reviewer[start:end]
        self.assertIn("self._cancel_countdown_audio(stop_sound=False)", reset_source)
        self.assertNotIn("self._cancel_countdown_audio(stop_sound=True)", reset_source)

    def test_wavs_keep_fast_native_playback_and_all_compressed_events_prefer_review_web(self) -> None:
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        start = reviewer.index("def _play_audio_feedback")
        end = reviewer.index("def _play_haptic_feedback", start)
        playback_source = reviewer[start:end]
        self.assertIn('"sync",', reviewer)
        self.assertIn('"timeout",', reviewer)
        self.assertIn("if event_key in WEBVIEW_AUDIO_EVENT_KEYS", playback_source)
        self.assertIn('interrupt=(event_key != "sync")', playback_source)
        self.assertIn('Path(selected).suffix.lower() != ".wav"', playback_source)
        self.assertIn("played = web_fallback() if prefer_review_web else False", playback_source)
        self.assertIn("fallback=None if prefer_review_web else web_fallback", playback_source)

        browser_audio = (ADDON_ROOT / "web" / "audio_feedback.js").read_text(encoding="utf-8")
        self.assertIn("volumePercent / 200", browser_audio)
        self.assertNotIn("Number(volumePercent || 100)", browser_audio)

    def test_compressed_audio_uses_one_browser_player_across_every_route(self) -> None:
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        self.assertIn('self._audio_feedback_bootstrap = _read_web_asset("web", "audio_feedback.js")', reviewer)
        self.assertIn('return main_web or self._review_web or reviewer_web', reviewer)
        self.assertIn('channel="alignment"', reviewer)
        self.assertIn('channel="countdown"', reviewer)
        self.assertIn('self._stop_web_audio_feedback("countdown")', reviewer)
        self.assertIn('for part in ("card_timer.css", "card_timer.js", "audio_feedback.js")', reviewer)

        due_start = reviewer.index("def _on_countdown_cue_due")
        due_end = reviewer.index("def _on_pause_shortcut", due_start)
        due_source = reviewer[due_start:due_end]
        self.assertIn("self.preview_countdown_audio(", due_source)
        self.assertNotIn("self.audio_feedback.play_timed(", due_source)

        browser_audio = (ADDON_ROOT / "web" / "audio_feedback.js").read_text(encoding="utf-8")
        self.assertIn("activeByChannel: new Map()", browser_audio)
        self.assertIn("positionMs / 1000", browser_audio)
        self.assertIn('String(settings.channel || "feedback")', browser_audio)

    def test_standalone_browser_player_is_packaged_and_installed(self) -> None:
        generator = (ADDON_ROOT / "generate_web_assets.py").read_text(encoding="utf-8")
        build = (ADDON_ROOT / "build_ankiaddon.ps1").read_text(encoding="utf-8")
        installer = (ADDON_ROOT / "install_to_anki.ps1").read_text(encoding="utf-8")
        posix_build = (ADDON_ROOT / "build_ankiaddon.sh").read_text(encoding="utf-8")
        posix_installer = (ADDON_ROOT / "install_to_anki.sh").read_text(encoding="utf-8")
        self.assertIn('"audio_feedback.js"', generator)
        self.assertIn('"web\\\\audio_feedback.js"', build)
        self.assertIn('"web\\\\audio_feedback.js"', installer)
        self.assertIn("web/audio_feedback.js", posix_build)
        self.assertIn("web/audio_feedback.js", posix_installer)

    def test_wav_volume_reaches_true_mute_and_full_output(self) -> None:
        self.assertTrue(self.controller.play("event.wav", volume_percent=0))
        effect = FakeSoundEffect.instances[0]
        self.assertEqual(effect.volume, 0.0)
        self.assertTrue(effect.muted)
        self.assertTrue(self.controller.play("event.wav", volume_percent=200))
        self.assertEqual(effect.volume, 1.0)
        self.assertFalse(effect.muted)

    def test_packaged_event_defaults_use_low_latency_wav_files(self) -> None:
        config = json.loads((ADDON_ROOT / "config.json").read_text(encoding="utf-8"))
        event_files = config["audio_event_files"]
        self.assertTrue(event_files)
        self.assertTrue(all(Path(file_name).suffix.lower() == ".wav" for file_name in event_files.values()))

    def test_packaged_event_wavs_start_at_zero_to_prevent_replay_clicks(self) -> None:
        config = json.loads((ADDON_ROOT / "config.json").read_text(encoding="utf-8"))
        for file_name in config["audio_event_files"].values():
            path = ADDON_ROOT / "Audio_trimmed" / file_name
            with self.subTest(file=file_name), wave.open(str(path), "rb") as audio:
                first_frame = audio.readframes(1)
                self.assertTrue(first_frame)
                self.assertTrue(all(byte == 0 for byte in first_frame))

        trim_script = (ADDON_ROOT / "trim_audio_to_trimmed.ps1").read_text(encoding="utf-8")
        self.assertIn("afade=t=in:st=0:d=$($FadeInSeconds)", trim_script)

    def test_startup_persists_audio_file_migrations(self) -> None:
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        start = reviewer.index("def _load_persisted_settings")
        end = reviewer.index("def _build_persisted_settings_config", start)
        load_source = reviewer[start:end]
        self.assertIn("feedback_preferences_migrated = (", load_source)
        self.assertIn("self.engine.state.audio_event_files != persisted_audio_event_files", load_source)
        self.assertIn("if feedback_preferences_migrated:", load_source)
        self.assertIn("self._save_persisted_settings()", load_source)

    def test_selected_audio_is_prepared_without_waiting_for_first_review_card(self) -> None:
        audio_source = (ADDON_ROOT / "audio_feedback.py").read_text(encoding="utf-8")
        warm_start = audio_source.index("def warm_up")
        warm_end = audio_source.index("def play_from_position", warm_start)
        warm_source = audio_source[warm_start:warm_end]
        self.assertIn("self._schedule_qt_sound_effect_warm_up(normalized_path)", warm_source)
        self.assertIn("self._start_warm_up(queued)", warm_source)
        self.assertNotIn("self._warm_up_queue", warm_source)

        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        load_start = reviewer.index("def _load_persisted_settings")
        load_end = reviewer.index("def _build_persisted_settings_config", load_start)
        self.assertIn("self._normalize_feedback_preferences()", reviewer[load_start:load_end])
        question_start = reviewer.index("def on_reviewer_did_show_question")
        question_end = reviewer.index("def on_reviewer_did_show_answer", question_start)
        self.assertNotIn("_ensure_audio_feedback_prepared", reviewer[question_start:question_end])

    def test_audio_diagnostic_is_copyable_and_privacy_safe(self) -> None:
        settings = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
        self.assertIn("class AudioDiagnosticsDialog", settings)
        self.assertIn('ModernButton("Play Native"', settings)
        self.assertIn('ModernButton("Play Browser"', settings)
        self.assertIn('ModernButton("Copy Report"', settings)
        context_start = settings.index("def _context", settings.index("class AudioDiagnosticsDialog"))
        context_end = settings.index("def _refresh_report", context_start)
        self.assertNotIn('endswith(".wav")', settings[context_start:context_end])
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        report_start = reviewer.index("def audio_diagnostic_report")
        report_end = reviewer.index("def preview_audio_feedback_from", report_start)
        report_source = reviewer[report_start:report_end]
        self.assertIn("Selected file:", report_source)
        self.assertNotIn("resolve()", report_source)

    def test_preview_uses_live_volume_without_blocking_on_full_settings_save(self) -> None:
        settings = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
        preview_start = settings.index("def _preview_audio_feedback")
        preview_end = settings.index("def _open_audio_diagnostics", preview_start)
        preview_source = settings[preview_start:preview_end]
        self.assertNotIn("self._flush_audio_volume_persist()", preview_source)
        self.assertIn("self._current_audio_volume_for_event(event_key)", preview_source)
        close_start = settings.index("class SettingsDialog")
        close_start = settings.index("def closeEvent", close_start)
        close_end = settings.index("def _install_developer_hold_filters", close_start)
        self.assertIn("self._flush_audio_volume_persist()", settings[close_start:close_end])

    def test_sound_volume_sliders_ignore_incidental_mouse_wheel_scrolling(self) -> None:
        settings = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
        row_start = settings.index("def _build_audio_controls")
        row_end = settings.index("def _build_developer_testing_section", row_start)
        row_source = settings[row_start:row_end]
        self.assertIn("ScrollSafeSlider(Qt.Orientation.Horizontal, container)", row_source)
        self.assertNotIn("slider = QSlider(", row_source)

    def test_answer_shown_hook_defers_addon_work_until_after_card_paint(self) -> None:
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        start = reviewer.index("def on_reviewer_did_show_answer")
        end = reviewer.index("def on_reviewer_will_answer_card", start)
        hook_source = reviewer[start:end]
        self.assertIn("QTimer.singleShot", hook_source)
        self.assertIn("ANSWER_SHOWN_POST_PAINT_DELAY_MS", hook_source)
        self.assertIn("_handle_answer_shown_after_paint", hook_source)
        before_deferred_handler = hook_source[:hook_source.index("def _handle_answer_shown_after_paint")]
        self.assertNotIn("self._handle_answer_shown(reviewer)", before_deferred_handler)

        handler_start = reviewer.index("def _handle_answer_shown(self, reviewer")
        handler_end = reviewer.index("def _finalize_rate", handler_start)
        handler_source = reviewer[handler_start:handler_end]
        self.assertIn("ANSWER_SHOWN_PANEL_UPDATE_DELAY_MS", handler_source)
        self.assertIn("QTimer.singleShot", handler_source)

    def test_external_surface_and_no_undo_updates_are_idempotent(self) -> None:
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")

        no_undo_start = reviewer.index("def _sync_no_undo_guard")
        no_undo_end = reviewer.index("def _schedule_time_boost_shortcut_health_check", no_undo_start)
        no_undo_source = reviewer[no_undo_start:no_undo_end]
        self.assertIn("if active and not self._undo_action_guarded", no_undo_source)
        self.assertIn("elif not active and self._undo_action_guarded", no_undo_source)

        floating_start = reviewer.index("def _ensure_floating_sidebar")
        floating_end = reviewer.index("def _set_sidebar_hidden", floating_start)
        floating_source = reviewer[floating_start:floating_end]
        self.assertIn("surface_changed = False", floating_source)
        self.assertIn("if surface_changed:", floating_source)


if __name__ == "__main__":
    unittest.main()
