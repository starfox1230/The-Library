from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


@dataclass(frozen=True)
class TrayVisualState:
    tooltip: str
    label: str
    fill: str
    ring: str


class CursorTray(QObject):
    toggle_requested = Signal()
    show_requested = Signal()
    exit_requested = Signal()

    def __init__(self, *, toggle_hotkey_label: str, exit_hotkey_label: str) -> None:
        super().__init__()
        self._toggle_hotkey_label = toggle_hotkey_label
        self._exit_hotkey_label = exit_hotkey_label
        self._tray = QSystemTrayIcon(self)
        self._menu = QMenu()
        self._status_action = QAction("Status: Starting", self)
        self._status_action.setEnabled(False)
        self._toggle_action = QAction(f"Start Recording ({self._toggle_hotkey_label})", self)
        self._show_action = QAction("Show Shortcuts", self)
        self._exit_action = QAction(f"Quit ({self._exit_hotkey_label})", self)

        self._menu.addAction(self._status_action)
        self._menu.addSeparator()
        self._menu.addAction(self._toggle_action)
        self._menu.addAction(self._show_action)
        self._menu.addSeparator()
        self._menu.addAction(self._exit_action)

        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._handle_activated)
        self._toggle_action.triggered.connect(self.toggle_requested.emit)
        self._show_action.triggered.connect(self.show_requested.emit)
        self._exit_action.triggered.connect(self.exit_requested.emit)
        self._set_visual_state(
            TrayVisualState(
                tooltip="Cursor Transcriber: Starting",
                label="Starting",
                fill="#38bdf8",
                ring="#e0f2fe",
            ),
            can_toggle=False,
            toggle_text=f"Start Recording ({self._toggle_hotkey_label})",
        )

    @staticmethod
    def is_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def set_ready(self) -> None:
        self._set_visual_state(
            TrayVisualState(
                tooltip="Cursor Transcriber: Ready",
                label="Ready",
                fill="#14b8a6",
                ring="#99f6e4",
            ),
            can_toggle=True,
            toggle_text=f"Start Recording ({self._toggle_hotkey_label})",
        )

    def set_arming(self) -> None:
        self._set_visual_state(
            TrayVisualState(
                tooltip="Cursor Transcriber: Preparing microphone",
                label="Preparing microphone",
                fill="#f59e0b",
                ring="#fde68a",
            ),
            can_toggle=True,
            toggle_text=f"Stop Recording ({self._toggle_hotkey_label})",
        )

    def set_recording(self) -> None:
        self._set_visual_state(
            TrayVisualState(
                tooltip="Cursor Transcriber: Recording",
                label="Recording",
                fill="#ef4444",
                ring="#fecaca",
            ),
            can_toggle=True,
            toggle_text=f"Stop Recording ({self._toggle_hotkey_label})",
        )

    def set_transcribing(self) -> None:
        self._set_visual_state(
            TrayVisualState(
                tooltip="Cursor Transcriber: Transcribing",
                label="Transcribing",
                fill="#fbbf24",
                ring="#fef3c7",
            ),
            can_toggle=False,
            toggle_text="Transcribing...",
        )

    def set_transcript_ready(self) -> None:
        self._set_visual_state(
            TrayVisualState(
                tooltip="Cursor Transcriber: Transcript copied to clipboard",
                label="Transcript copied",
                fill="#22c55e",
                ring="#bbf7d0",
            ),
            can_toggle=True,
            toggle_text=f"Start Recording ({self._toggle_hotkey_label})",
        )

    def set_error(self) -> None:
        self._set_visual_state(
            TrayVisualState(
                tooltip="Cursor Transcriber: Last action had an error",
                label="Error",
                fill="#f97316",
                ring="#fdba74",
            ),
            can_toggle=True,
            toggle_text=f"Start Recording ({self._toggle_hotkey_label})",
        )

    def _set_visual_state(self, state: TrayVisualState, *, can_toggle: bool, toggle_text: str) -> None:
        self._tray.setToolTip(state.tooltip)
        self._status_action.setText(f"Status: {state.label}")
        self._toggle_action.setEnabled(can_toggle)
        self._toggle_action.setText(toggle_text)
        self._tray.setIcon(self._build_icon(fill=QColor(state.fill), ring=QColor(state.ring)))

    def _handle_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_requested.emit()

    def _build_icon(self, *, fill: QColor, ring: QColor) -> QIcon:
        size = 32
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outer_rect = pixmap.rect().adjusted(4, 4, -4, -4)
        inner_rect = pixmap.rect().adjusted(9, 9, -9, -9)

        painter.setPen(QPen(ring, 4))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(outer_rect)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawEllipse(inner_rect)

        painter.end()
        return QIcon(pixmap)
