from __future__ import annotations

import ctypes

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from .models import CaptureRegion


class _BorderStrip(QWidget):
    def __init__(self, color: str) -> None:
        super().__init__(None)
        self._color = QColor(color)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._color)


class CaptureBorderOverlay:
    """Four click-through strips immediately outside the recorded pixels."""

    def __init__(self, color: str = "#FF3B4F", thickness: int = 4) -> None:
        self._thickness = max(2, thickness)
        self._strips = [_BorderStrip(color) for _ in range(4)]
        self._visible = False

    def show(self, region: CaptureRegion) -> None:
        geometries = self.geometries_for(region, self._thickness)
        for strip, geometry in zip(self._strips, geometries):
            strip.show()
            self._set_physical_geometry(strip, *geometry)
            strip.raise_()
        self._visible = True

    def hide(self) -> None:
        for strip in self._strips:
            strip.hide()
        self._visible = False

    @property
    def is_visible(self) -> bool:
        return self._visible

    @staticmethod
    def geometries_for(
        region: CaptureRegion,
        thickness: int,
    ) -> tuple[tuple[int, int, int, int], ...]:
        t = max(2, thickness)
        return (
            (region.x - t, region.y - t, region.width + 2 * t, t),
            (region.x - t, region.y + region.height, region.width + 2 * t, t),
            (region.x - t, region.y, t, region.height),
            (region.x + region.width, region.y, t, region.height),
        )

    @staticmethod
    def _set_physical_geometry(
        widget: QWidget,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        if hasattr(ctypes, "windll"):
            hwnd = int(widget.winId())
            HWND_TOPMOST = -1
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040
            ctypes.windll.user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                x,
                y,
                width,
                height,
                SWP_NOACTIVATE | SWP_SHOWWINDOW,
            )
        else:
            widget.setGeometry(x, y, width, height)
