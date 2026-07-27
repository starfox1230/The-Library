from __future__ import annotations

import ctypes
from ctypes import wintypes

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .capture_border import _disable_rounded_corners
from .models import CaptureRegion


class PlaybackPointSelector(QWidget):
    """Blocks the capture area while the user chooses a stable player toggle point."""

    selected = Signal(object)
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__(None)
        self._region: CaptureRegion | None = None
        self._local_point: QPointF | None = None
        self._physical_point: tuple[int, int] | None = None
        self.setWindowTitle("Choose video play/pause point")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        self._panel = QFrame()
        self._panel.setObjectName("PlaybackPointPanel")
        self._panel.setMaximumWidth(650)
        self._panel.setMinimumHeight(138)
        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(16, 13, 16, 13)
        panel_layout.setSpacing(9)
        self._instruction = QLabel(
            "Click a stable spot on the video surface. This setup click is blocked "
            "and will not play or pause the webpage."
        )
        self._instruction.setMinimumHeight(54)
        self._instruction.setWordWrap(True)
        self._instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(self._instruction)
        actions = QHBoxLayout()
        actions.addStretch()
        self._cancel_button = QPushButton("Cancel")
        self._confirm_button = QPushButton("Use This Point")
        self._confirm_button.setObjectName("PrimaryButton")
        self._confirm_button.setEnabled(False)
        self._cancel_button.clicked.connect(self._cancel)
        self._confirm_button.clicked.connect(self._confirm)
        actions.addWidget(self._cancel_button)
        actions.addWidget(self._confirm_button)
        actions.addStretch()
        panel_layout.addLayout(actions)
        layout.addWidget(
            self._panel,
            0,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
        )
        layout.addStretch()

        self.setStyleSheet(
            """
            QFrame#PlaybackPointPanel {
                background: rgba(9, 16, 28, 245);
                border: 2px solid #58D7FF;
                border-radius: 8px;
            }
            QLabel { color:#F2F7FD; font:11pt "Segoe UI"; }
            QPushButton {
                color:#EEF4FC; background:#17273A; border:1px solid #405A77;
                border-radius:6px; padding:8px 14px; font:10pt "Segoe UI";
            }
            QPushButton:hover { background:#24415F; }
            QPushButton:disabled { color:#65758B; background:#111A27; }
            QPushButton#PrimaryButton {
                background:#1A7390; border-color:#58D7FF; font-weight:700;
            }
            """
        )

    def begin(self, region: CaptureRegion) -> None:
        self._region = region
        self._local_point = None
        self._physical_point = None
        self._confirm_button.setEnabled(False)
        self._instruction.setText(
            "Click a stable spot on the video surface. This setup click is blocked "
            "and will not play or pause the webpage."
        )
        self._set_physical_geometry(region.x, region.y, region.width, region.height)
        self._fit_instruction_panel()
        _disable_rounded_corners(self)
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    @staticmethod
    def physical_point_for_local(
        region: CaptureRegion,
        widget_size: QSize,
        local_point: QPointF,
    ) -> tuple[int, int]:
        x_scale = region.width / max(1, widget_size.width())
        y_scale = region.height / max(1, widget_size.height())
        x = region.x + round(local_point.x() * x_scale)
        y = region.y + round(local_point.y() * y_scale)
        return (
            min(region.x + region.width - 1, max(region.x, x)),
            min(region.y + region.height - 1, max(region.y, y)),
        )

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(4, 10, 20, 72))
        outline = QPen(QColor("#58D7FF"))
        outline.setWidth(3)
        outline.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(outline)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5))
        if self._local_point is None:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        marker = QPen(QColor("#FFCC4D"))
        marker.setWidth(3)
        painter.setPen(marker)
        point = self._local_point
        painter.drawEllipse(point, 12, 12)
        painter.drawLine(
            QPointF(point.x() - 18, point.y()),
            QPointF(point.x() + 18, point.y()),
        )
        painter.drawLine(
            QPointF(point.x(), point.y() - 18),
            QPointF(point.x(), point.y() + 18),
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._region is None:
            return
        if self._panel.geometry().contains(event.position().toPoint()):
            return
        self._local_point = event.position()
        self._physical_point = self.physical_point_for_local(
            self._region,
            self.size(),
            self._local_point,
        )
        self._confirm_button.setEnabled(True)
        self._instruction.setText(
            "Point marked. Click elsewhere to move it, or choose "
            "Use This Point to start recording."
        )
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm()
            return
        if event.key() == Qt.Key.Key_Escape:
            self._cancel()
            return
        super().keyPressEvent(event)

    def _confirm(self) -> None:
        if self._physical_point is None:
            return
        point = self._physical_point
        self.hide()
        self.selected.emit(point)

    def _cancel(self) -> None:
        self.hide()
        self.cancelled.emit()

    def _fit_instruction_panel(self) -> None:
        available_width = max(280, self.width() - 36)
        self._panel.setFixedWidth(min(650, available_width))

    def _set_physical_geometry(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        self.setGeometry(x, y, width, height)
        self.show()
        if not hasattr(ctypes, "windll"):
            return
        try:
            user32 = ctypes.windll.user32
            set_window_pos = user32.SetWindowPos
            set_window_pos.argtypes = [
                wintypes.HWND,
                wintypes.HWND,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                wintypes.UINT,
            ]
            set_window_pos.restype = wintypes.BOOL
            HWND_TOPMOST = wintypes.HWND(-1)
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040
            set_window_pos(
                wintypes.HWND(int(self.winId())),
                HWND_TOPMOST,
                x,
                y,
                width,
                height,
                SWP_NOACTIVATE | SWP_SHOWWINDOW,
            )
        except (AttributeError, OSError, TypeError, ValueError):
            pass
