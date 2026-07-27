from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QPushButton

from screen_capture_transcriber import capture_border
from screen_capture_transcriber.capture_border import CaptureBorderOverlay
from screen_capture_transcriber.models import CaptureRegion


def test_boundary_is_one_full_square_region_instead_of_four_strips() -> None:
    region = CaptureRegion(100, 200, 800, 600)

    assert CaptureBorderOverlay.boundary_geometry_for(region) == (
        100,
        200,
        800,
        600,
    )


def test_recording_controls_stay_at_the_bottom_right_perimeter() -> None:
    region = CaptureRegion(100, 200, 800, 600)

    controls = CaptureBorderOverlay.control_geometry_for(
        region,
        QSize(190, 38),
        (0, 0, 1920, 1080),
        2,
    )

    assert controls == (702, 754, 190, 38)
    assert controls[0] + controls[2] < region.x + region.width
    assert controls[1] + controls[3] < region.y + region.height


def test_full_screen_controls_fall_back_inside_desktop_bounds() -> None:
    region = CaptureRegion(0, 0, 1920, 1080)

    controls = CaptureBorderOverlay.control_geometry_for(
        region,
        QSize(190, 38),
        (0, 0, 1920, 1080),
        2,
    )

    assert controls == (1722, 1034, 190, 38)


def test_controls_shrink_to_fit_a_small_recording_region() -> None:
    region = CaptureRegion(20, 30, 90, 60)

    x, y, width, height = CaptureBorderOverlay.control_geometry_for(
        region,
        QSize(180, 66),
        (0, 0, 1920, 1080),
        3,
    )

    assert (width, height) == (90, 60)
    assert x >= region.x
    assert y >= region.y
    assert x + width <= region.x + region.width
    assert y + height <= region.y + region.height


def test_safe_geometry_is_applied_before_native_window_position(
    monkeypatch,
) -> None:
    events = []

    class FakeNativeCall:
        argtypes = None
        restype = None

        def __call__(self, *_args):
            events.append("native")
            return 0

    class FakeWidget:
        def setGeometry(self, *geometry):
            events.append(("geometry", geometry))

        def show(self):
            events.append("show")

        def winId(self):
            return 123

    monkeypatch.setattr(
        capture_border.ctypes,
        "windll",
        SimpleNamespace(
            user32=SimpleNamespace(SetWindowPos=FakeNativeCall()),
        ),
    )

    CaptureBorderOverlay._set_physical_geometry(
        FakeWidget(),
        100,
        200,
        804,
        2,
    )

    assert events[:2] == [
        ("geometry", (100, 200, 804, 2)),
        "show",
    ]
    assert events[2] == "native"


def test_overlay_controls_are_vector_icons_and_pause_becomes_resume() -> None:
    app = QApplication.instance() or QApplication([])
    overlay = CaptureBorderOverlay()
    buttons = overlay._controls.findChildren(QPushButton)
    overlay._controls.show()
    app.processEvents()

    assert overlay._recording_color == "#58D7FF"
    assert overlay._thickness == 3
    assert overlay._controls.size() == QSize(120, 44)
    assert [button.accessibleName() for button in buttons] == [
        "Screenshot",
        "Pause recording",
        "Stop recording",
    ]
    assert all(button.text() == "" for button in buttons)
    assert all(
        overlay._controls.rect().contains(button.geometry())
        for button in buttons
    )

    overlay.set_paused(True)

    assert overlay._controls._pause._symbol == "play"
    assert buttons[1].accessibleName() == "Resume recording"
