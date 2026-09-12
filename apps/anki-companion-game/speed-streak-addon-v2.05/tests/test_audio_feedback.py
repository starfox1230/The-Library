from __future__ import annotations

import ast
import builtins
import gc
import weakref
from unittest.mock import patch
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
    def __init__(self, parent=None) -> None:
        self.parent = parent
        self.volume = 1.0
        self.muted = False

    def setVolume(self, value: float) -> None:
        self.volume = value

    def setMuted(self, value: bool) -> None:
        self.muted = value


class FakeMediaPlayer:
    instances: list["FakeMediaPlayer"] = []

    def __init__(self, parent=None) -> None:
        self.parent = parent
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

    def __init__(self, parent=None) -> None:
        self.parent = parent
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
    fake_qt.QApplication = SimpleNamespace(instance=lambda: FAKE_APP)
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


FAKE_APP = SimpleNamespace()
AUDIO_FEEDBACK = _load_audio_feedback()


class AudioFeedbackPreloadTests(unittest.TestCase):
    def setUp(self) -> None:
        platform_patch = patch.object(AUDIO_FEEDBACK.sys, "platform", "win32")
        platform_patch.start()
        self.addCleanup(platform_patch.stop)
        FAKE_APP.__dict__.clear()
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

    def test_profile_close_quiesces_audio_even_without_an_active_run(self) -> None:
        source = ast.parse((ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8"))
        method = next(node for node in ast.walk(source) if isinstance(node, ast.FunctionDef) and node.name == "on_profile_will_close")
        namespace = {"Any": object}
        exec(compile(ast.Module(body=[method], type_ignores=[]), "profile_close", "exec"), namespace)
        calls = []
        overlay = SimpleNamespace(
            _cancel_countdown_audio=lambda **kw: calls.append(("cancel", kw)),
            audio_feedback=SimpleNamespace(stop_all=lambda: calls.append("stop")),
            run_history=SimpleNamespace(active=None),
        )
        namespace["on_profile_will_close"](overlay)
        self.assertEqual(calls, [("cancel", {"stop_sound": True}), "stop"])

    def test_native_objects_survive_controller_collection_and_setup_failure(self) -> None:
        self.controller.prepare_files(["event.wav", "compressed.mp3"])
        self.controller.prepare_timed("countdown-cues/clock-tick-soft.wav")
        self.controller.prepare_timed("compressed.mp3")
        retained = FAKE_APP._speed_streak_audio_objects
        self.assertEqual(len(retained), 6)
        self.assertTrue(all(obj.parent is FAKE_APP for obj in retained))
        refs = [weakref.ref(obj) for obj in retained]
        self.controller = None
        FakeMediaPlayer.instances.clear()
        FakeSoundEffect.instances.clear()
        gc.collect()
        self.assertTrue(all(ref() is not None for ref in refs))
        controller = AUDIO_FEEDBACK.AudioFeedbackController(self.audio_root)
        with patch.object(FakeMediaPlayer, "setSource", side_effect=RuntimeError("device disappeared")):
            self.assertIsNone(controller._prepare_qt_player(self.audio_root / "compressed.mp3"))
        self.assertEqual(len(retained), 8)  # Failed player AND output remain owned.

    def test_profile_rebinding_reuses_players_and_refreshes_upload_catalog(self) -> None:
        self.controller.prepare_files(["event.wav"])
        self.controller.prepare_timed("compressed.mp3")
        effect = FakeSoundEffect.instances[0]
        player = self.controller._timed_qt_player
        profile = Path(self.temp_dir.name) / "other-profile"
        uploads = profile / AUDIO_FEEDBACK.AUDIO_UPLOADS_DIRECTORY_NAME
        uploads.mkdir(parents=True)
        (uploads / "unique.wav").write_bytes(b"wave")
        self.controller.available_options()
        self.controller.rebind_user_files_root(profile)
        self.assertIn("__uploaded__/unique.wav", self.controller.available_files())
        self.controller.prepare_files(["event.wav"])
        self.assertIs(FakeSoundEffect.instances[0], effect)
        self.assertEqual(len(FakeSoundEffect.instances), 1)
        self.assertIs(self.controller._timed_qt_player, player)
        self.assertGreater(player.stop_count, 0)

    def test_profile_stop_cancels_queued_warmup_without_destroying_objects(self) -> None:
        pending = []
        with patch.object(FakeTimer, "singleShot", side_effect=lambda delay, callback: pending.append(callback)):
            self.controller.warm_up(["event.wav", "compressed.mp3"])
            self.controller.prepare_timed("compressed.mp3")
            self.controller.stop_all()
            counts = [obj.play_count for obj in FakeMediaPlayer.instances + FakeSoundEffect.instances]
            while pending:
                pending.pop(0)()
            self.assertEqual(counts, [obj.play_count for obj in FakeMediaPlayer.instances + FakeSoundEffect.instances])
        self.assertTrue(all(not obj.isPlaying() for obj in FakeSoundEffect.instances))
        self.assertTrue(all(not obj.audio_output.muted for obj in FakeMediaPlayer.instances))
        self.assertTrue(self.controller.play("event.wav"))

    def test_stopping_countdown_cancels_pending_prime_and_stops_compressed_audio(self) -> None:
        pending = []
        with patch.object(FakeTimer, "singleShot", side_effect=lambda delay, callback: pending.append(callback)):
            self.controller.prepare_timed("compressed.mp3")
            self.controller.stop_timed()
            player = self.controller._timed_qt_player
            plays = player.play_count
            while pending:
                pending.pop(0)()
            self.assertEqual(player.play_count, plays)
            self.assertGreater(player.stop_count, 0)
        self.assertTrue(self.controller.play_timed("compressed.mp3"))
        self.assertFalse(player.audio_output.muted)

    def test_mac_never_imports_multimedia_or_shared_av_across_audio_entry_points(self) -> None:
        original_import = builtins.__import__
        attempts = []
        def checked_import(name, globals=None, locals=None, fromlist=(), level=0):
            if "QtMultimedia" in name or name == "aqt.sound" or any(
                part in {"QMediaDevices", "QMediaPlayer", "QAudioOutput", "QSoundEffect"} for part in fromlist
            ):
                attempts.append((name, fromlist))
                raise AssertionError("Forbidden native audio import on macOS")
            return original_import(name, globals, locals, fromlist, level)
        with patch.object(AUDIO_FEEDBACK.sys, "platform", "darwin"), patch.object(builtins, "__import__", checked_import):
            for file in ("event.wav", "compressed.mp3", "countdown-cues/clock-tick-soft.wav"):
                self.assertFalse(self.controller.play(file))
                self.assertFalse(self.controller.play(file, fallback=lambda: False))
                self.assertTrue(self.controller.play(file, fallback=lambda: True))
                self.assertFalse(self.controller.play_native_test(file))
                self.assertFalse(self.controller.play_from_position(file, 100))
                self.assertFalse(self.controller.prepare_timed(file))
                self.assertFalse(self.controller.play_timed(file))
                self.assertFalse(self.controller.timed_ready(file))
                self.assertEqual(self.controller.prepare_files([file]), 0)
                self.controller.warm_up([file])
                self.assertEqual(self.controller.diagnostic_snapshot(file)["nativeStatus"], "disabled-on-macos")
            self.controller.rebind_user_files_root(Path(self.temp_dir.name) / "profile2")
            self.controller.stop_all()
            self.assertRaises(RuntimeError, AUDIO_FEEDBACK._new_audio_object, FakeSoundEffect)
        self.assertEqual(attempts, [])
        self.assertEqual(FakeMediaPlayer.instances, [])
        self.assertEqual(FakeSoundEffect.instances, [])
        self.assertFalse(hasattr(FAKE_APP, "_speed_streak_audio_objects"))

    def test_platform_policy_preserves_windows_and_linux_native_paths(self) -> None:
        for platform_name in ("win32", "linux"):
            with self.subTest(platform=platform_name), patch.object(AUDIO_FEEDBACK.sys, "platform", platform_name):
                self.assertTrue(AUDIO_FEEDBACK.native_audio_enabled())
                self.assertTrue(self.controller.play("event.wav"))
                self.assertTrue(self.controller.play_timed("compressed.mp3"))

    def test_mac_reviewer_routes_wav_and_compressed_previews_and_events_to_browser(self) -> None:
        tree = ast.parse((ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8"))
        names = {"preview_audio_feedback", "preview_audio_feedback_from", "prepare_countdown_audio_preview",
                 "countdown_audio_preview_ready", "preview_countdown_audio", "_play_audio_feedback",
                 "preview_native_audio_diagnostic", "_normalize_feedback_preferences"}
        methods = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name in names]
        namespace = dict(Any=object, Path=Path, DEFAULT_AUDIO_VOLUME_PERCENT=100,
                         native_audio_enabled=AUDIO_FEEDBACK.native_audio_enabled,
                         normalize_audio_volume_percent=lambda v: v, time=SimpleNamespace(monotonic=lambda: 100),
                         SYNC_AUDIO_SUPPRESSION_SECONDS=1, WEBVIEW_AUDIO_EVENT_KEYS={"good"},
                         normalize_audio_event_volumes=lambda v: v, normalize_haptic_event_patterns=lambda v: v,
                         DEFAULT_COUNTDOWN_AUDIO_FILE="countdown-cues/clock-tick-soft.wav")
        exec(compile(ast.Module(body=methods, type_ignores=[]), "reviewer_audio", "exec"), namespace)
        calls = []
        overlay = SimpleNamespace(audio_feedback=self.controller,
            _play_review_web_audio_feedback=lambda file, **kw: calls.append((file, kw)) or True,
            _prepare_web_audio_feedback=lambda file: calls.append((file, {"prepare": True})) or True,
            engine=SimpleNamespace(state=SimpleNamespace(audio_enabled=False, audio_event_volumes={},
                audio_event_files={"good": "event.wav"}, selected_audio_file="event.wav",
                countdown_audio_file="countdown-cues/clock-tick-soft.wav", countdown_audio_enabled=False,
                countdown_audio_volume=100, haptic_event_patterns={})),
            _preferred_audio_file=lambda files: "event.wav",
            _last_audio_feedback_event="", _last_audio_feedback_started_at=0)
        with patch.object(AUDIO_FEEDBACK.sys, "platform", "darwin"):
            # Startup/profile normalization must not initialize native audio even
            # while both audio switches are off (the reported idle crash case).
            namespace["_normalize_feedback_preferences"](overlay)
            self.assertTrue(calls)
            self.assertTrue(all(options == {"prepare": True} for file, options in calls))
            overlay.engine.state.audio_enabled=True
            for file in ("event.wav", "compressed.mp3"):
                overlay._audio_file_for_event=lambda event: file
                self.assertTrue(namespace["preview_audio_feedback"](overlay, file, 150))
                self.assertEqual(calls[-1][1]["volume_percent"], 150)
                self.assertTrue(namespace["preview_audio_feedback_from"](overlay, file, 230, 150))
                self.assertEqual(calls[-1][1]["position_ms"], 230)
                self.assertEqual(calls[-1][1]["channel"], "alignment")
                self.assertTrue(namespace["prepare_countdown_audio_preview"](overlay, file))
                self.assertTrue(namespace["countdown_audio_preview_ready"](overlay, file))
                self.assertTrue(namespace["preview_countdown_audio"](overlay, file, 150))
                self.assertEqual(calls[-1][1]["channel"], "countdown")
                for event in ("good", "reveal", "sync", "timeout"):
                    overlay._last_audio_feedback_event=""
                    before=len(calls)
                    namespace["_play_audio_feedback"](overlay, event)
                    self.assertEqual(len(calls), before+1)
                    self.assertEqual(calls[-1][1]["interrupt"], event != "sync")
                self.assertFalse(namespace["preview_native_audio_diagnostic"](overlay, file))
            overlay._play_review_web_audio_feedback=lambda *args, **kw: False
            self.assertFalse(namespace["preview_countdown_audio"](overlay, "event.wav"))
            self.assertFalse(namespace["preview_audio_feedback"](overlay, "event.wav"))
        self.assertEqual(FakeMediaPlayer.instances, [])
        self.assertEqual(FakeSoundEffect.instances, [])

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
        self.assertIn("if not native_audio_enabled() or event_key in WEBVIEW_AUDIO_EVENT_KEYS", playback_source)
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
