from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QPointF, QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

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


def test_ctrl_click_filter_suppresses_only_inside_selected_capture(
    monkeypatch,
) -> None:
    app = QApplication.instance() or QApplication([])
    hotkeys = GlobalHotkeys("<f8>", "<f9>", "<f10>")
    hotkeys.set_ctrl_click_capture_region((100, 200, 800, 600))
    emitted: list[tuple[int, int]] = []
    hotkeys.ctrl_click.connect(lambda x, y: emitted.append((x, y)))
    import screen_capture_transcriber.hotkeys as hotkeys_module

    monkeypatch.setattr(
        hotkeys_module.ctypes,
        "windll",
        SimpleNamespace(
            user32=SimpleNamespace(GetAsyncKeyState=lambda _key: 0x8000)
        ),
    )
    inside = SimpleNamespace(pt=SimpleNamespace(x=300, y=400))
    outside = SimpleNamespace(pt=SimpleNamespace(x=50, y=50))

    assert hotkeys._win32_event_filter(0x0201, inside) is False
    assert emitted == [(300, 400)]
    assert hotkeys._win32_event_filter(0x0202, inside) is False
    assert hotkeys._win32_event_filter(0x0201, outside) is True
    app.processEvents()


def test_period_filter_opens_capture_once_and_suppresses_key_pair() -> None:
    app = QApplication.instance() or QApplication([])
    hotkeys = GlobalHotkeys("<f8>", "<f9>", "<f10>")
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
    hotkeys = GlobalHotkeys("<f8>", "<f9>", "<f10>")
    period = SimpleNamespace(vkCode=0xBE)
    letter = SimpleNamespace(vkCode=0x41)

    assert hotkeys._period_win32_event_filter(0x0100, period) is True
    assert hotkeys._period_win32_event_filter(0x0100, letter) is True


def test_player_toggle_moves_then_clicks_before_pause_callback(monkeypatch) -> None:
    events: list[object] = []
    fake = SimpleNamespace(
        _playback_point=(640, 360),
        _player_transition_pending=False,
        _capture_border=SimpleNamespace(
            set_busy=lambda busy: events.append(("busy", busy))
        ),
        _sync_ctrl_click_capture=lambda: events.append("sync-shortcuts"),
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
