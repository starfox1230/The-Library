from __future__ import annotations

from screen_capture_transcriber.capture_border import CaptureBorderOverlay
from screen_capture_transcriber.models import CaptureRegion


def test_border_strips_stay_outside_recorded_pixels() -> None:
    region = CaptureRegion(100, 200, 800, 600)

    top, bottom, left, right = CaptureBorderOverlay.geometries_for(region, 4)

    assert top == (96, 196, 808, 4)
    assert bottom == (96, 800, 808, 4)
    assert left == (96, 200, 4, 600)
    assert right == (900, 200, 4, 600)
