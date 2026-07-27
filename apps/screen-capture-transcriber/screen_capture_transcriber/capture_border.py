from __future__ import annotations

import ctypes
from ctypes import wintypes

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QStyle,
    QStyleOptionButton,
    QWidget,
)

from .models import CaptureRegion


def _exclude_from_capture(widget: QWidget) -> None:
    """Ask Windows to omit an overlay window from screen-capture output."""
    if not hasattr(ctypes, "windll"):
        return
    try:
        user32 = ctypes.windll.user32
        set_affinity = user32.SetWindowDisplayAffinity
        set_affinity.argtypes = [wintypes.HWND, wintypes.DWORD]
        set_affinity.restype = wintypes.BOOL
        WDA_EXCLUDEFROMCAPTURE = 0x00000011
        set_affinity(
            wintypes.HWND(int(widget.winId())),
            WDA_EXCLUDEFROMCAPTURE,
        )
    except (AttributeError, OSError, TypeError, ValueError):
        pass


def _disable_rounded_corners(widget: QWidget) -> None:
    """Prevent Windows 11 from rounding a frameless boundary window."""
    if not hasattr(ctypes, "windll"):
        return
    try:
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_DONOTROUND = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(int(widget.winId())),
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(DWMWCP_DONOTROUND),
            ctypes.sizeof(DWMWCP_DONOTROUND),
        )
    except (AttributeError, OSError, TypeError, ValueError):
        pass


class _RecordingBoundary(QWidget):
    """One transparent window that paints a single square recording outline."""

    def __init__(self, color: str, thickness: int) -> None:
        super().__init__(None)
        self.setWindowTitle("Recording boundary")
        self._color = QColor(color)
        self._thickness = max(2, thickness)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        _exclude_from_capture(self)
        _disable_rounded_corners(self)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        pen = QPen(self._color)
        pen.setWidth(self._thickness)
        pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        inset = self._thickness / 2
        painter.drawRect(QRectF(self.rect()).adjusted(inset, inset, -inset, -inset))

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()


class _OverlayIconButton(QPushButton):
    """DPI-independent vector icon button for the compact recording tray."""

    def __init__(self, symbol: str) -> None:
        super().__init__("")
        self._symbol = symbol
        self.setFixedSize(34, 34)

    def set_symbol(self, symbol: str) -> None:
        self._symbol = symbol
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        self.style().drawControl(
            QStyle.ControlElement.CE_PushButton,
            option,
            painter,
            self,
        )
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = QColor("#6F8198") if not self.isEnabled() else QColor("#F7FAFF")
        if self._symbol == "stop" and self.isEnabled():
            color = QColor("#FF8F9C")
        pen = QPen(color)
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        center = self.rect().center()
        if self._symbol == "camera":
            body = QRectF(center.x() - 8, center.y() - 5.5, 16, 11)
            painter.drawRoundedRect(body, 1.5, 1.5)
            painter.drawEllipse(QPointF(center), 3.2, 3.2)
            painter.drawLine(
                QPointF(center.x() - 5.5, center.y() - 6),
                QPointF(center.x() - 2.5, center.y() - 8),
            )
            painter.drawLine(
                QPointF(center.x() - 2.5, center.y() - 8),
                QPointF(center.x() + 1, center.y() - 8),
            )
        elif self._symbol == "play":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawPolygon(
                QPolygonF(
                    [
                        QPointF(center.x() - 4.5, center.y() - 7),
                        QPointF(center.x() + 7, center.y()),
                        QPointF(center.x() - 4.5, center.y() + 7),
                    ]
                )
            )
        elif self._symbol == "pause":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRect(QRectF(center.x() - 6, center.y() - 7, 4, 14))
            painter.drawRect(QRectF(center.x() + 2, center.y() - 7, 4, 14))
        elif self._symbol == "stop":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRect(QRectF(center.x() - 6, center.y() - 6, 12, 12))


class _RecordingControls(QWidget):
    screenshot_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()

    def __init__(self) -> None:
        super().__init__(None)
        self.setObjectName("RecordingControls")
        self.setWindowTitle("Recording controls")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedSize(120, 44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)
        screenshot = _OverlayIconButton("camera")
        screenshot.setAccessibleName("Screenshot")
        screenshot.setToolTip("Pause recording and capture an anatomy screenshot")
        self._pause = _OverlayIconButton("pause")
        self._pause.setAccessibleName("Pause recording")
        self._pause.setToolTip("Pause recording")
        stop = _OverlayIconButton("stop")
        stop.setAccessibleName("Stop recording")
        stop.setToolTip("Stop and save the recording")
        stop.setObjectName("StopButton")
        screenshot.clicked.connect(self.screenshot_requested.emit)
        self._pause.clicked.connect(self.pause_requested.emit)
        stop.clicked.connect(self.stop_requested.emit)
        layout.addWidget(screenshot)
        layout.addWidget(self._pause)
        layout.addWidget(stop)
        self.setStyleSheet(
            """
            QWidget#RecordingControls {
                background: rgba(10, 17, 28, 242);
                border: 1px solid #58D7FF;
                border-radius: 5px;
            }
            QPushButton {
                background: #17273A;
                border: 1px solid #405A77;
                border-radius: 4px;
                padding: 0;
            }
            QPushButton:hover { background: #24415F; border-color: #6F9BC4; }
            QPushButton:pressed { background: #0E1B2A; }
            QPushButton:disabled { background: #111A27; border-color: #29394D; }
            QWidget#RecordingControls[paused="true"] { border-color: #FFB020; }
            """
        )
        _exclude_from_capture(self)

    def set_paused(self, paused: bool) -> None:
        self.setProperty("paused", paused)
        self._pause.set_symbol("play" if paused else "pause")
        self._pause.setAccessibleName(
            "Resume recording" if paused else "Pause recording"
        )
        self._pause.setToolTip("Resume recording" if paused else "Pause recording")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def set_busy(self, busy: bool) -> None:
        for button in self.findChildren(QPushButton):
            button.setEnabled(not busy)


class CaptureBorderOverlay:
    """Capture-excluded square boundary with a compact peripheral control tray."""

    def __init__(
        self,
        color: str = "#58D7FF",
        paused_color: str = "#FFB020",
        thickness: int = 3,
    ) -> None:
        self._thickness = max(2, thickness)
        self._recording_color = color
        self._paused_color = paused_color
        self._boundary = _RecordingBoundary(color, self._thickness)
        self._controls = _RecordingControls()
        self.screenshot_requested = self._controls.screenshot_requested
        self.pause_requested = self._controls.pause_requested
        self.stop_requested = self._controls.stop_requested
        self._visible = False

    def show(self, region: CaptureRegion) -> None:
        self.set_paused(False)
        self.set_busy(False)
        self._set_physical_geometry(
            self._boundary,
            *self.boundary_geometry_for(region),
        )
        _exclude_from_capture(self._boundary)
        _disable_rounded_corners(self._boundary)
        self._boundary.raise_()

        scale = self._dpi_scale_for_region(region)
        logical_size = self._controls.size()
        physical_size = QSize(
            max(1, round(logical_size.width() * scale)),
            max(1, round(logical_size.height() * scale)),
        )
        controls_geometry = self.control_geometry_for(
            region,
            physical_size,
            self._virtual_desktop_geometry(),
            self._thickness,
        )
        self._set_physical_geometry(self._controls, *controls_geometry)
        _exclude_from_capture(self._controls)
        self._controls.raise_()
        self._visible = True

    def hide(self) -> None:
        self._boundary.hide()
        self._controls.hide()
        self._visible = False

    def set_paused(self, paused: bool) -> None:
        color = self._paused_color if paused else self._recording_color
        self._boundary.set_color(color)
        self._controls.set_paused(paused)

    def set_busy(self, busy: bool) -> None:
        self._controls.set_busy(busy)

    @property
    def is_visible(self) -> bool:
        return self._visible

    @staticmethod
    def boundary_geometry_for(region: CaptureRegion) -> tuple[int, int, int, int]:
        return region.x, region.y, region.width, region.height

    @staticmethod
    def control_geometry_for(
        region: CaptureRegion,
        panel_size: QSize,
        desktop: tuple[int, int, int, int],
        thickness: int,
    ) -> tuple[int, int, int, int]:
        """Place the full control tray inside the selection's lower-right corner."""
        desktop_x, desktop_y, desktop_width, desktop_height = desktop
        desktop_right = desktop_x + desktop_width
        desktop_bottom = desktop_y + desktop_height
        panel_width = min(panel_size.width(), max(1, region.width))
        panel_height = min(panel_size.height(), max(1, region.height))
        region_right = region.x + region.width
        region_bottom = region.y + region.height
        inset = max(8, thickness + 5)
        min_x = max(region.x, desktop_x)
        min_y = max(region.y, desktop_y)
        max_x = min(region_right - panel_width, desktop_right - panel_width)
        max_y = min(region_bottom - panel_height, desktop_bottom - panel_height)
        desired_x = region_right - inset - panel_width
        desired_y = region_bottom - inset - panel_height
        x = min(max_x, max(min_x, desired_x))
        y = min(max_y, max(min_y, desired_y))
        return x, y, panel_width, panel_height

    @staticmethod
    def _dpi_scale_for_region(region: CaptureRegion) -> float:
        if not hasattr(ctypes, "windll"):
            return 1.0
        try:
            point = wintypes.POINT(
                region.x + max(0, region.width // 2),
                region.y + max(0, region.height // 2),
            )
            user32 = ctypes.windll.user32
            monitor_from_point = user32.MonitorFromPoint
            monitor_from_point.argtypes = [wintypes.POINT, wintypes.DWORD]
            monitor_from_point.restype = wintypes.HANDLE
            MONITOR_DEFAULTTONEAREST = 2
            monitor = monitor_from_point(point, MONITOR_DEFAULTTONEAREST)
            dpi_x = wintypes.UINT()
            dpi_y = wintypes.UINT()
            get_dpi = ctypes.windll.shcore.GetDpiForMonitor
            get_dpi.argtypes = [
                wintypes.HANDLE,
                ctypes.c_int,
                ctypes.POINTER(wintypes.UINT),
                ctypes.POINTER(wintypes.UINT),
            ]
            get_dpi.restype = ctypes.HRESULT
            MDT_EFFECTIVE_DPI = 0
            if get_dpi(
                monitor,
                MDT_EFFECTIVE_DPI,
                ctypes.byref(dpi_x),
                ctypes.byref(dpi_y),
            ) == 0:
                return max(1.0, dpi_x.value / 96.0)
        except (AttributeError, OSError, TypeError, ValueError):
            pass
        return 1.0

    @staticmethod
    def _virtual_desktop_geometry() -> tuple[int, int, int, int]:
        if not hasattr(ctypes, "windll"):
            return 0, 0, 1920, 1080
        user32 = ctypes.windll.user32
        return (
            user32.GetSystemMetrics(76),  # SM_XVIRTUALSCREEN
            user32.GetSystemMetrics(77),  # SM_YVIRTUALSCREEN
            user32.GetSystemMetrics(78),  # SM_CXVIRTUALSCREEN
            user32.GetSystemMetrics(79),  # SM_CYVIRTUALSCREEN
        )

    @staticmethod
    def _set_physical_geometry(
        widget: QWidget,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        # Establish a bounded fallback before making the native tool window visible.
        widget.setGeometry(x, y, width, height)
        widget.show()
        if hasattr(ctypes, "windll"):
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
                    wintypes.HWND(int(widget.winId())),
                    HWND_TOPMOST,
                    x,
                    y,
                    width,
                    height,
                    SWP_NOACTIVATE | SWP_SHOWWINDOW,
                )
            except (AttributeError, OSError, TypeError, ValueError):
                pass
