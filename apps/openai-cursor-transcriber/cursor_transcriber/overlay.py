from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPoint, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QFontMetrics, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .helpers import format_duration, preview_text


@dataclass
class OverlayState:
    title: str
    body: str
    hint: str
    accent: QColor
    timer_ratio: float | None = None
    timer_label: str = ""


class CursorOverlay(QWidget):
    def __init__(
        self,
        *,
        max_width: int,
        offset_x: int,
        offset_y: int,
        toggle_hotkey_label: str,
        exit_hotkey_label: str,
    ) -> None:
        super().__init__(None)
        self._max_width = max_width
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._toggle_hotkey_label = toggle_hotkey_label
        self._exit_hotkey_label = exit_hotkey_label
        self._state = OverlayState(
            title="",
            body="",
            hint="",
            accent=QColor("#22c55e"),
        )

        self._title_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self._body_font = QFont("Segoe UI", 10)
        self._hint_font = QFont("Segoe UI", 8)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

        self._follow_timer = QTimer(self)
        self._follow_timer.setInterval(33)
        self._follow_timer.timeout.connect(self._follow_cursor)

        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()

    def show_ready(self) -> None:
        self._set_state(
            title="Cursor transcriber is running",
            body=f"{self._toggle_hotkey_label} to record, {self._exit_hotkey_label} to quit",
            hint="",
            accent="#22c55e",
        )

    def show_recording(self, *, seconds_remaining: float, max_seconds: int) -> None:
        ratio = max(0.0, min(1.0, seconds_remaining / max_seconds if max_seconds else 0.0))
        self._set_state(
            title="Recording",
            body=f"{format_duration(seconds_remaining)} left",
            hint=f"Press {self._toggle_hotkey_label} again to stop",
            accent="#ef4444",
            timer_ratio=ratio,
            timer_label="Mic live",
        )

    def show_transcribing(self) -> None:
        self._set_state(
            title="Transcribing",
            body="Sending the recording to OpenAI...",
            hint="",
            accent="#38bdf8",
        )

    def show_transcript(self, text: str) -> None:
        self._set_state(
            title="Copied to clipboard",
            body=preview_text(text),
            hint="Paste with your keyboard shortcut to dismiss",
            accent="#14b8a6",
        )

    def show_error(self, message: str) -> None:
        self._set_state(
            title="Something went wrong",
            body=message,
            hint=f"Press {self._toggle_hotkey_label} to try again",
            accent="#f97316",
        )

    def schedule_hide(self, delay_ms: int) -> None:
        self._hide_timer.start(delay_ms)

    def hide(self) -> None:  # type: ignore[override]
        self._hide_timer.stop()
        self._follow_timer.stop()
        super().hide()

    def sizeHint(self) -> QSize:  # type: ignore[override]
        padding = 16
        icon_size = 14
        content_width = self._max_width - (padding * 2)
        title_width = content_width - icon_size - 10

        title_height = self._measure_text_height(self._state.title, self._title_font, title_width)
        body_height = self._measure_text_height(self._state.body, self._body_font, content_width)
        hint_height = self._measure_text_height(self._state.hint, self._hint_font, content_width) if self._state.hint else 0
        timer_height = 18 if self._state.timer_ratio is not None else 0

        height = padding + title_height + 8 + body_height + (10 if self._state.hint else 0) + hint_height + timer_height + padding
        return QSize(self._max_width, max(height, 92))

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outer_rect = QRectF(0, 0, self.width() - 12, self.height() - 12)
        shadow_rect = outer_rect.translated(8, 8)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#0f172a"))
        painter.drawRoundedRect(shadow_rect, 20, 20)

        painter.setBrush(QColor("#111827"))
        painter.drawRoundedRect(outer_rect, 20, 20)

        painter.setPen(QPen(QColor("#1f2937"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(outer_rect.adjusted(1, 1, -1, -1), 19, 19)

        padding = 16
        icon_size = 14
        content_width = self._max_width - (padding * 2)
        title_width = content_width - icon_size - 10
        y = padding

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._state.accent)
        painter.drawEllipse(QRectF(padding, y + 2, icon_size, icon_size))

        painter.setPen(QColor("#f9fafb"))
        painter.setFont(self._title_font)
        title_rect = QRect(padding + icon_size + 10, y, title_width, 40)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self._state.title)

        title_height = self._measure_text_height(self._state.title, self._title_font, title_width)
        y += title_height + 12

        painter.setPen(QColor("#d1d5db"))
        painter.setFont(self._body_font)
        body_height = self._measure_text_height(self._state.body, self._body_font, content_width)
        body_rect = QRect(padding, y, content_width, body_height)
        painter.drawText(body_rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self._state.body)
        y += body_height + 10

        if self._state.hint:
            painter.setPen(QColor("#94a3b8"))
            painter.setFont(self._hint_font)
            hint_height = self._measure_text_height(self._state.hint, self._hint_font, content_width)
            hint_rect = QRect(padding, y, content_width, hint_height)
            painter.drawText(hint_rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self._state.hint)
            y += hint_height + 10

        if self._state.timer_ratio is not None:
            painter.setPen(QColor("#94a3b8"))
            painter.setFont(self._hint_font)
            painter.drawText(QPoint(padding, y + 10), self._state.timer_label)

            bar_x1 = padding + 54
            bar_y1 = y + 4
            bar_width = self.width() - padding - 24 - bar_x1
            bar_rect = QRectF(bar_x1, bar_y1, bar_width, 8)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#1f2937"))
            painter.drawRoundedRect(bar_rect, 4, 4)

            fill_width = max(0.0, bar_width * self._state.timer_ratio)
            if fill_width > 0:
                painter.setBrush(self._state.accent)
                painter.drawRoundedRect(QRectF(bar_x1, bar_y1, fill_width, 8), 4, 4)

    def _set_state(
        self,
        *,
        title: str,
        body: str,
        hint: str,
        accent: str,
        timer_ratio: float | None = None,
        timer_label: str = "",
    ) -> None:
        self._state = OverlayState(
            title=title,
            body=body,
            hint=hint,
            accent=QColor(accent),
            timer_ratio=timer_ratio,
            timer_label=timer_label,
        )
        size = self.sizeHint()
        self.resize(size)
        self._hide_timer.stop()
        self.show()
        self.raise_()
        self._follow_cursor()
        self._follow_timer.start()
        self.update()

    def _follow_cursor(self) -> None:
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        x = min(cursor_pos.x() + self._offset_x, available.right() - self.width() - 12)
        y = min(cursor_pos.y() + self._offset_y, available.bottom() - self.height() - 12)
        x = max(available.left() + 12, x)
        y = max(available.top() + 12, y)
        self.move(x, y)

    @staticmethod
    def _measure_text_height(text: str, font: QFont, width: int) -> int:
        if not text:
            return 0
        metrics = QFontMetrics(font)
        rect = metrics.boundingRect(QRect(0, 0, width, 1000), Qt.TextFlag.TextWordWrap, text)
        return rect.height()
