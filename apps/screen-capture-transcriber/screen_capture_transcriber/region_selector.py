from __future__ import annotations

import ctypes
from dataclasses import dataclass

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen, QScreen
from PySide6.QtWidgets import QApplication, QWidget

from .models import CaptureRegion


@dataclass(frozen=True)
class NativeMonitor:
    device_name: str
    friendly_name: str
    x: int
    y: int
    width: int
    height: int


def _native_monitors() -> list[NativeMonitor]:
    if not hasattr(ctypes, "windll"):
        return []

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", ctypes.c_ulong),
            ("szDevice", ctypes.c_wchar * 32),
        ]

    class DISPLAY_DEVICEW(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("DeviceName", ctypes.c_wchar * 32),
            ("DeviceString", ctypes.c_wchar * 128),
            ("StateFlags", ctypes.c_ulong),
            ("DeviceID", ctypes.c_wchar * 128),
            ("DeviceKey", ctypes.c_wchar * 128),
        ]

    friendly_names: dict[str, str] = {}
    display_index = 0
    while True:
        adapter = DISPLAY_DEVICEW()
        adapter.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        if not ctypes.windll.user32.EnumDisplayDevicesW(
            None, display_index, ctypes.byref(adapter), 0
        ):
            break
        monitor = DISPLAY_DEVICEW()
        monitor.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        if ctypes.windll.user32.EnumDisplayDevicesW(
            adapter.DeviceName, 0, ctypes.byref(monitor), 0
        ):
            friendly_names[adapter.DeviceName.casefold()] = monitor.DeviceString
        display_index += 1

    monitors: list[NativeMonitor] = []
    callback_type = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(RECT),
        ctypes.c_longlong,
    )

    def callback(
        monitor_handle: int,
        _device_context: int,
        _rect: ctypes.POINTER(RECT),
        _data: int,
    ) -> int:
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if ctypes.windll.user32.GetMonitorInfoW(monitor_handle, ctypes.byref(info)):
            rect = info.rcMonitor
            monitors.append(
                NativeMonitor(
                    device_name=info.szDevice,
                    friendly_name=friendly_names.get(info.szDevice.casefold(), ""),
                    x=rect.left,
                    y=rect.top,
                    width=rect.right - rect.left,
                    height=rect.bottom - rect.top,
                )
            )
        return 1

    callback_ref = callback_type(callback)
    ctypes.windll.user32.EnumDisplayMonitors(0, 0, callback_ref, 0)
    return monitors


def _physical_region(screen: QScreen, logical_rect: QRect) -> CaptureRegion:
    logical_screen = screen.geometry()
    monitors = _native_monitors()
    native = next(
        (
            monitor
            for monitor in monitors
            if monitor.device_name.casefold() == screen.name().casefold()
            or monitor.friendly_name.casefold() == screen.name().casefold()
        ),
        None,
    )
    if native is None:
        expected_width = logical_screen.width() * float(screen.devicePixelRatio())
        expected_height = logical_screen.height() * float(screen.devicePixelRatio())
        size_matches = [
            monitor
            for monitor in monitors
            if abs(monitor.width - expected_width) <= 2
            and abs(monitor.height - expected_height) <= 2
        ]
        if len(size_matches) == 1:
            native = size_matches[0]
        elif len(monitors) == len(QApplication.screens()):
            try:
                native = monitors[QApplication.screens().index(screen)]
            except ValueError:
                native = None
    if native is None:
        ratio = max(1.0, float(screen.devicePixelRatio()))
        x = round(logical_rect.x() * ratio)
        y = round(logical_rect.y() * ratio)
        width = round(logical_rect.width() * ratio)
        height = round(logical_rect.height() * ratio)
    else:
        x_scale = native.width / max(1, logical_screen.width())
        y_scale = native.height / max(1, logical_screen.height())
        x = native.x + round((logical_rect.x() - logical_screen.x()) * x_scale)
        y = native.y + round((logical_rect.y() - logical_screen.y()) * y_scale)
        width = round(logical_rect.width() * x_scale)
        height = round(logical_rect.height() * y_scale)

    width = max(2, width - (width % 2))
    height = max(2, height - (height % 2))
    return CaptureRegion(
        x=x,
        y=y,
        width=width,
        height=height,
        screen_name=screen.name(),
    )


class RegionSelector(QWidget):
    selected = Signal(object)
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)
        self._origin: QPoint | None = None
        self._selection = QRect()
        self._active_screen: QScreen | None = None

        virtual = QRect()
        for screen in QApplication.screens():
            virtual = virtual.united(screen.geometry())
        self.setGeometry(virtual)

    def begin(self) -> None:
        self._origin = None
        self._selection = QRect()
        self._active_screen = None
        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(5, 10, 20, 155))
        if not self._selection.isNull():
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self._selection, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor("#58D7FF"), 3))
            painter.drawRect(self._selection.adjusted(1, 1, -1, -1))

            size_text = f"{self._selection.width()} × {self._selection.height()}"
            badge = QRect(
                self._selection.left(),
                max(8, self._selection.top() - 34),
                160,
                28,
            )
            painter.fillRect(badge, QColor(9, 18, 32, 235))
            painter.setPen(QColor("#F5F8FC"))
            painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, size_text)

        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(
            self.rect().adjusted(0, 24, 0, 0),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            "Drag to select one screen area  •  Esc to cancel",
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        global_point = event.globalPosition().toPoint()
        self._active_screen = QApplication.screenAt(global_point)
        self._origin = global_point
        self._selection = QRect(self.mapFromGlobal(global_point), self.mapFromGlobal(global_point))
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._origin is None or self._active_screen is None:
            return
        screen_rect = self._active_screen.geometry()
        global_point = event.globalPosition().toPoint()
        global_point.setX(min(screen_rect.right(), max(screen_rect.left(), global_point.x())))
        global_point.setY(min(screen_rect.bottom(), max(screen_rect.top(), global_point.y())))
        self._selection = QRect(
            self.mapFromGlobal(self._origin),
            self.mapFromGlobal(global_point),
        ).normalized()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if (
            event.button() != Qt.MouseButton.LeftButton
            or self._active_screen is None
            or self._selection.width() < 16
            or self._selection.height() < 16
        ):
            return
        logical_rect = QRect(
            self.mapToGlobal(self._selection.topLeft()),
            self._selection.size(),
        )
        region = _physical_region(self._active_screen, logical_rect)
        self.hide()
        self.selected.emit(region)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()
            return
        super().keyPressEvent(event)
