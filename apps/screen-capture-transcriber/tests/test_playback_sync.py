from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QPointF, QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit

import screen_capture_transcriber.main_window as main_window
from screen_capture_transcriber.hotkeys import GlobalHotkeys
from screen_capture_transcriber.main_window import MainWindow
from screen_capture_transcriber.models import CaptureRegion
from screen_capture_transcriber.playback_point_selector import PlaybackPointSelector


def test_playback_point_maps_logical_selector_click_to_physical_capture() -> None:
    region = CaptureRegion(100, 200, 800, 600)

    point = PlaybackPointSelector.physical_point_for_local(
        region,
        QSize(400, 300),
        QPointF(200, 150),
    )

    assert point == (500, 500)


def test_selector_requires_confirmation_after_blocked_setup_click() -> None:
    app = QApplication.instance() or QApplication([])
    selector = PlaybackPointSelector()
    selector._region = CaptureRegion(100, 200, 800, 600)
    selector.resize(400, 300)
    selector.show()
    app.processEvents()
    selected: list[tuple[int, int]] = []
    selector.selected.connect(selected.append)

    QTest.mouseClick(
        selector,
        Qt.MouseButton.LeftButton,
        pos=QPoint(200, 230),
    )

    assert selector._physical_point is not None
    assert abs(selector._physical_point[0] - 500) <= 2
    assert abs(selector._physical_point[1] - 660) <= 2
    assert selector._confirm_button.isEnabled()
    assert selected == []

    confirmed_point = selector._physical_point
    selector._confirm_button.click()
    app.processEvents()

    assert selected == [confirmed_point]
    assert not selector.isVisible()


def test_period_filter_opens_capture_once_and_suppresses_key_pair() -> None:
    app = QApplication.instance() or QApplication([])
    hotkeys = GlobalHotkeys("<f8>")
    emitted: list[bool] = []
    hotkeys.period_capture.connect(lambda: emitted.append(True))
    period = SimpleNamespace(vkCode=0xBE)

    hotkeys.set_period_capture_enabled(True)

    assert hotkeys._period_win32_event_filter(0x0100, period) is False
    assert hotkeys._period_win32_event_filter(0x0100, period) is False
    assert emitted == [True]

    hotkeys.set_period_capture_enabled(False)
    assert hotkeys._period_win32_event_filter(0x0101, period) is False
    assert hotkeys._suppressing_period is False
    app.processEvents()


def test_period_filter_passes_through_when_capture_is_not_active() -> None:
    hotkeys = GlobalHotkeys("<f8>")
    period = SimpleNamespace(vkCode=0xBE)
    letter = SimpleNamespace(vkCode=0x41)

    assert hotkeys._period_win32_event_filter(0x0100, period) is True
    assert hotkeys._period_win32_event_filter(0x0100, letter) is True


def test_backspace_filter_opens_note_once_without_interfering_with_ctrl_backspace(
    monkeypatch,
) -> None:
    app = QApplication.instance() or QApplication([])
    hotkeys = GlobalHotkeys("<f8>")
    emitted: list[bool] = []
    hotkeys.learning_note.connect(lambda: emitted.append(True))
    backspace = SimpleNamespace(vkCode=0x08)
    import screen_capture_transcriber.hotkeys as hotkeys_module

    hotkeys.set_learning_note_capture_enabled(True)
    monkeypatch.setattr(hotkeys_module, "control_key_is_down", lambda: False)
    monkeypatch.setattr(
        hotkeys_module,
        "foreground_native_text_input_active",
        lambda: False,
    )

    assert hotkeys._period_win32_event_filter(0x0100, backspace) is False
    assert hotkeys._period_win32_event_filter(0x0100, backspace) is False
    assert emitted == [True]
    assert hotkeys._period_win32_event_filter(0x0101, backspace) is False

    monkeypatch.setattr(hotkeys_module, "control_key_is_down", lambda: True)
    assert hotkeys._period_win32_event_filter(0x0100, backspace) is True
    assert emitted == [True]
    app.processEvents()


def test_backspace_filter_passes_through_native_text_fields(monkeypatch) -> None:
    hotkeys = GlobalHotkeys("<f8>")
    hotkeys.set_learning_note_capture_enabled(True)
    backspace = SimpleNamespace(vkCode=0x08)
    import screen_capture_transcriber.hotkeys as hotkeys_module

    monkeypatch.setattr(hotkeys_module, "control_key_is_down", lambda: False)
    monkeypatch.setattr(
        hotkeys_module,
        "foreground_native_text_input_active",
        lambda: True,
    )

    assert hotkeys._period_win32_event_filter(0x0100, backspace) is True


def test_retired_main_window_controls_and_hotkeys_are_absent() -> None:
    ui_source = inspect.getsource(MainWindow._build_ui)

    for retired_label in (
        "Use Primary Screen",
        "Add Chapter",
        "Anatomy Capture (F10)",
        "Anatomy mode",
        "Video link",
        "Extension Folder",
    ):
        assert retired_label not in ui_source
    assert not hasattr(GlobalHotkeys, "add_chapter")
    assert not hasattr(GlobalHotkeys, "anatomy_capture")
    assert not hasattr(GlobalHotkeys, "ctrl_click")


def test_recording_automatically_uses_supported_browser_link() -> None:
    player = {
        "provider": "Medality / Vimeo",
        "top_url": "https://medality.com/course/example/",
    }
    events: list[object] = []
    fake = SimpleNamespace(
        _region=CaptureRegion(0, 0, 1280, 720),
        _ffmpeg_path=object(),
        _ffprobe_path=object(),
        _browser_bridge=SimpleNamespace(current_player=lambda: player),
        _supported_linked_player=MainWindow._supported_linked_player,
        _start_linked_recording=lambda value: events.append(("linked", value)),
        _start_fallback_recording=lambda: events.append("fallback"),
        _fallback_reason="",
    )

    MainWindow._start_recording(fake)

    assert events == [("linked", player)]


def test_recording_automatically_falls_back_without_browser_player() -> None:
    events: list[str] = []
    fake = SimpleNamespace(
        _region=CaptureRegion(0, 0, 1280, 720),
        _ffmpeg_path=object(),
        _ffprobe_path=object(),
        _browser_bridge=SimpleNamespace(current_player=lambda: None),
        _supported_linked_player=MainWindow._supported_linked_player,
        _start_linked_recording=lambda _value: events.append("linked"),
        _start_fallback_recording=lambda: events.append("fallback"),
        _fallback_reason="",
    )

    MainWindow._start_recording(fake)

    assert events == ["fallback"]
    assert "not reporting an active video player" in fake._fallback_reason


def test_learning_note_intent_captures_timestamp_before_requesting_pause() -> None:
    requested: list[str] = []
    fake = SimpleNamespace(
        _is_recording=True,
        _is_busy=False,
        _player_transition_pending=False,
        _session=object(),
        _linked_player={"current_time": 41.0},
        _study_paused=False,
        _active_timeline_seconds=lambda: 18.25,
        _linked_session_active=lambda: True,
        _request_segment_stop=lambda purpose: requested.append(purpose),
    )

    MainWindow._begin_learning_note_capture(
        fake,
        {"current_time": 42.5},
    )

    assert fake._pending_learning_note_timestamp == 18.25
    assert fake._pending_learning_note_source_timestamp == 42.5
    assert fake._study_paused is True
    assert requested == ["note"]

    # The page and iframe can report the same physical shortcut close together.
    # Once the first intent begins the note flow, a duplicate must be harmless.
    MainWindow._begin_learning_note_capture(
        fake,
        {"current_time": 42.5},
    )
    assert requested == ["note"]


def test_extension_backspace_precedes_scrubber_and_ignores_only_text_inputs() -> None:
    extension_root = (
        Path(__file__).resolve().parents[1] / "chrome-extension"
    )
    for filename in ("content-script.js", "medality-transcript.js"):
        source = (extension_root / filename).read_text(encoding="utf-8")

        assert (
            'window.addEventListener("keydown", onLearningNoteKeydown, true)'
            in source
        )
        assert 'target.closest("input")' in source
        assert '"text", "search", "email", "url", "tel", "password", "number"' in source
        assert '"range"' not in source


def test_extension_collects_youtube_transcripts_and_scopes_source_tabs() -> None:
    extension_root = Path(__file__).resolve().parents[1] / "chrome-extension"
    manifest = json.loads(
        (extension_root / "manifest.json").read_text(encoding="utf-8")
    )
    youtube_source = (
        extension_root / "youtube-transcript.js"
    ).read_text(encoding="utf-8")
    content_source = (
        extension_root / "content-script.js"
    ).read_text(encoding="utf-8")

    assert any(
        "youtube-transcript.js" in entry.get("js", [])
        for entry in manifest["content_scripts"]
    )
    assert "ytd-transcript-segment-renderer" in youtube_source
    assert 'buttonWithText("Show transcript")' in youtube_source
    assert "YouTube built-in transcript" in youtube_source
    assert "source_selected === false" in youtube_source
    assert "appState.source_selected !== false" in content_source


def test_player_toggle_moves_then_clicks_before_pause_callback(monkeypatch) -> None:
    events: list[object] = []
    fake = SimpleNamespace(
        _playback_point=(640, 360),
        _player_transition_pending=False,
        _capture_border=SimpleNamespace(
            set_busy=lambda busy: events.append(("busy", busy))
        ),
        _sync_recording_hotkeys=lambda: events.append("sync-shortcuts"),
        _sync_controls=lambda: events.append("sync"),
        _session=None,
        _is_recording=True,
        _is_paused=False,
    )
    fake._click_player_and_continue = lambda x, y, callback: (
        MainWindow._click_player_and_continue(fake, x, y, callback)
    )
    fake._finish_player_toggle = lambda callback: (
        MainWindow._finish_player_toggle(fake, callback)
    )
    monkeypatch.setattr(
        main_window.QTimer,
        "singleShot",
        lambda _delay, callback: callback(),
    )
    monkeypatch.setattr(
        main_window,
        "move_pointer",
        lambda x, y: events.append(("move", x, y)),
    )
    monkeypatch.setattr(
        main_window,
        "replay_left_click",
        lambda x, y: events.append(("click", x, y)),
    )

    MainWindow._schedule_player_toggle(
        fake,
        lambda: events.append("stop-recorder"),
    )

    assert events.index(("move", 640, 360)) < events.index(("click", 640, 360))
    assert events.index(("click", 640, 360)) < events.index("stop-recorder")
    assert fake._player_transition_pending is False


def test_browser_title_autofills_as_soon_as_the_browser_connects() -> None:
    app = QApplication.instance() or QApplication([])
    player = {
        "provider": "Medality / Vimeo",
        "top_url": "https://medality.com/course/example/",
        "top_title": "MRI Elbow Anatomy",
    }
    fake = SimpleNamespace(
        _region=None,
        _title_was_manually_edited=False,
        _auto_title_value="",
        _is_recording=False,
        _is_paused=False,
        _is_busy=False,
        _source_transcript_payload=None,
        _browser_bridge=SimpleNamespace(current_player=lambda: player),
        title_edit=QLineEdit(),
    )
    fake._supported_linked_player = MainWindow._supported_linked_player

    assert MainWindow._maybe_autofill_browser_title(fake) is True
    assert fake.title_edit.text() == "MRI Elbow Anatomy"
    app.processEvents()


def test_browser_title_never_replaces_a_manually_edited_title() -> None:
    app = QApplication.instance() or QApplication([])
    player = {
        "provider": "Medality / Vimeo",
        "top_url": "https://medality.com/course/example/",
        "top_title": "MRI Elbow Anatomy",
    }
    title_edit = QLineEdit()
    title_edit.setText("My custom session name")
    fake = SimpleNamespace(
        _region=CaptureRegion(0, 0, 1280, 720),
        _title_was_manually_edited=True,
        _auto_title_value="",
        _is_recording=False,
        _is_paused=False,
        _is_busy=False,
        _source_transcript_payload=None,
        _browser_bridge=SimpleNamespace(current_player=lambda: player),
        title_edit=title_edit,
    )
    fake._supported_linked_player = MainWindow._supported_linked_player

    assert MainWindow._maybe_autofill_browser_title(fake) is False
    assert title_edit.text() == "My custom session name"
    app.processEvents()


def test_matching_lesson_heading_upgrades_an_automatic_tab_title() -> None:
    app = QApplication.instance() or QApplication([])
    player = {
        "provider": "Medality / Vimeo",
        "top_url": "https://medality.com/course/example/",
        "top_title": "MRI Online | Medality",
    }
    title_edit = QLineEdit()
    title_edit.setText("MRI Online | Medality")
    fake = SimpleNamespace(
        _region=CaptureRegion(0, 0, 1280, 720),
        _title_was_manually_edited=False,
        _auto_title_value="MRI Online | Medality",
        _is_recording=False,
        _is_paused=False,
        _is_busy=False,
        _source_transcript_payload={
            "url": "https://medality.com/course/example/",
            "title": "MRI Anatomy of the Shoulder",
        },
        _browser_bridge=SimpleNamespace(current_player=lambda: player),
        title_edit=title_edit,
    )
    fake._supported_linked_player = MainWindow._supported_linked_player

    assert MainWindow._maybe_autofill_browser_title(fake) is True
    assert title_edit.text() == "MRI Anatomy of the Shoulder"
    app.processEvents()
