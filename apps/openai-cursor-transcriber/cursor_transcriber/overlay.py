from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QFontMetrics, QGuiApplication, QLinearGradient, QPainter, QPainterPath, QPen
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


@dataclass(frozen=True)
class LayoutMetrics:
    bubble_width: int
    bubble_height: int
    content_width: int
    title_width: int
    title_height: int
    header_height: int
    body_height: int
    hint_height: int
    timer_label_height: int


class CursorOverlay(QWidget):
    _shadow_margin = 18
    _corner_radius = 18
    _padding_x = 16
    _padding_y = 14
    _header_gap = 12
    _section_gap = 12
    _icon_size = 24
    _icon_dot_size = 10
    _timer_gap = 6
    _timer_track_height = 10
    _min_bubble_height = 96

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

        self._title_font = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
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
        layout = self._measure_layout()
        return QSize(
            layout.bubble_width + (self._shadow_margin * 2),
            layout.bubble_height + (self._shadow_margin * 2),
        )

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        layout = self._measure_layout()
        bubble_rect = QRectF(
            self._shadow_margin,
            self._shadow_margin,
            layout.bubble_width,
            layout.bubble_height,
        )
        bubble_path = QPainterPath()
        bubble_path.addRoundedRect(bubble_rect, self._corner_radius, self._corner_radius)

        self._draw_shadow(painter, bubble_path)
        self._draw_bubble_shell(painter, bubble_rect, bubble_path)
        self._draw_content(painter, bubble_rect, layout)

    def _draw_shadow(self, painter: QPainter, bubble_path: QPainterPath) -> None:
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        shadow_color = QColor(2, 6, 23)

        for offset, alpha in ((10, 16), (7, 22), (4, 32), (2, 48)):
            painter.setBrush(QColor(shadow_color.red(), shadow_color.green(), shadow_color.blue(), alpha))
            painter.drawPath(bubble_path.translated(0, offset))

        painter.restore()

    def _draw_bubble_shell(self, painter: QPainter, bubble_rect: QRectF, bubble_path: QPainterPath) -> None:
        painter.save()

        fill_gradient = QLinearGradient(bubble_rect.topLeft(), bubble_rect.bottomLeft())
        fill_gradient.setColorAt(0.0, QColor("#17263a"))
        fill_gradient.setColorAt(0.45, QColor("#122033"))
        fill_gradient.setColorAt(1.0, QColor("#0d1727"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill_gradient)
        painter.drawPath(bubble_path)

        glow_rect = QRectF(bubble_rect.left(), bubble_rect.top(), bubble_rect.width(), bubble_rect.height() * 0.55)
        glow_gradient = QLinearGradient(glow_rect.topLeft(), glow_rect.bottomLeft())
        glow_gradient.setColorAt(0.0, QColor(255, 255, 255, 24))
        glow_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setClipPath(bubble_path)
        painter.setBrush(glow_gradient)
        painter.drawRect(glow_rect)
        painter.setClipping(False)

        painter.setPen(QPen(QColor(255, 255, 255, 34), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(bubble_path)

        inner_rect = bubble_rect.adjusted(1.5, 1.5, -1.5, -1.5)
        inner_path = QPainterPath()
        inner_path.addRoundedRect(inner_rect, self._corner_radius - 1, self._corner_radius - 1)
        painter.setPen(QPen(QColor(255, 255, 255, 10), 1))
        painter.drawPath(inner_path)

        painter.restore()

    def _draw_content(self, painter: QPainter, bubble_rect: QRectF, layout: LayoutMetrics) -> None:
        content_left = bubble_rect.left() + self._padding_x
        content_top = bubble_rect.top() + self._padding_y
        content_width = layout.content_width

        badge_rect = QRectF(content_left, content_top, self._icon_size, self._icon_size)
        title_left = badge_rect.right() + self._header_gap
        title_y = content_top + max(0, (layout.header_height - layout.title_height) // 2)
        title_rect = QRect(
            round(title_left),
            round(title_y),
            layout.title_width,
            layout.title_height,
        )

        self._draw_badge(painter, badge_rect)

        painter.setPen(QColor("#f8fafc"))
        painter.setFont(self._title_font)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self._state.title)

        y = content_top + layout.header_height + self._section_gap

        painter.setPen(QColor("#d7e0ec"))
        painter.setFont(self._body_font)
        body_rect = QRect(round(content_left), round(y), content_width, layout.body_height)
        painter.drawText(body_rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self._state.body)
        y += layout.body_height

        if self._state.hint:
            y += 10
            painter.setPen(QColor("#98a9bf"))
            painter.setFont(self._hint_font)
            hint_rect = QRect(round(content_left), round(y), content_width, layout.hint_height)
            painter.drawText(hint_rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self._state.hint)
            y += layout.hint_height

        if self._state.timer_ratio is not None:
            y += 12
            self._draw_timer(
                painter,
                x=content_left,
                y=y,
                width=content_width,
                label_height=layout.timer_label_height,
            )

    def _draw_badge(self, painter: QPainter, badge_rect: QRectF) -> None:
        painter.save()
        halo_color = QColor(self._state.accent)
        halo_color.setAlpha(52)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(halo_color)
        painter.drawEllipse(badge_rect)

        inner_rect = badge_rect.adjusted(3, 3, -3, -3)
        inner_gradient = QLinearGradient(inner_rect.topLeft(), inner_rect.bottomLeft())
        top_color = QColor(self._state.accent)
        top_color.setAlpha(230)
        bottom_color = QColor(self._state.accent)
        bottom_color.setAlpha(165)
        inner_gradient.setColorAt(0.0, top_color)
        inner_gradient.setColorAt(1.0, bottom_color)
        painter.setBrush(inner_gradient)
        painter.drawEllipse(inner_rect)

        dot_rect = QRectF(
            inner_rect.center().x() - (self._icon_dot_size / 2),
            inner_rect.center().y() - (self._icon_dot_size / 2),
            self._icon_dot_size,
            self._icon_dot_size,
        )
        painter.setBrush(QColor("#f8fafc"))
        painter.drawEllipse(dot_rect)
        painter.restore()

    def _draw_timer(self, painter: QPainter, *, x: float, y: float, width: int, label_height: int) -> None:
        painter.save()

        label_rect = QRect(round(x), round(y), width, label_height)
        painter.setPen(QColor("#8fa4bc"))
        painter.setFont(self._hint_font)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._state.timer_label)

        track_y = y + label_height + self._timer_gap
        track_rect = QRectF(x, track_y, width, self._timer_track_height)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 22))
        painter.drawRoundedRect(track_rect, self._timer_track_height / 2, self._timer_track_height / 2)

        fill_width = max(0.0, min(track_rect.width(), track_rect.width() * (self._state.timer_ratio or 0.0)))
        if fill_width > 0:
            fill_gradient = QLinearGradient(track_rect.topLeft(), track_rect.topRight())
            fill_gradient.setColorAt(0.0, self._state.accent.lighter(110))
            fill_gradient.setColorAt(1.0, self._state.accent)
            painter.setBrush(fill_gradient)
            fill_rect = QRectF(track_rect.left(), track_rect.top(), fill_width, track_rect.height())
            painter.drawRoundedRect(fill_rect, self._timer_track_height / 2, self._timer_track_height / 2)

        painter.restore()

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
        self.resize(self.sizeHint())
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

    def _measure_layout(self) -> LayoutMetrics:
        content_width = self._max_width - (self._padding_x * 2)
        title_width = content_width - self._icon_size - self._header_gap

        title_height = self._measure_text_height(self._state.title, self._title_font, title_width)
        header_height = max(self._icon_size, title_height)
        body_height = self._measure_text_height(self._state.body, self._body_font, content_width)
        hint_height = self._measure_text_height(self._state.hint, self._hint_font, content_width) if self._state.hint else 0
        timer_label_height = self._measure_text_height(self._state.timer_label, self._hint_font, content_width)

        bubble_height = self._padding_y + header_height + self._section_gap + body_height + self._padding_y
        if self._state.hint:
            bubble_height += 10 + hint_height
        if self._state.timer_ratio is not None:
            bubble_height += 12 + timer_label_height + self._timer_gap + self._timer_track_height

        return LayoutMetrics(
            bubble_width=self._max_width,
            bubble_height=max(self._min_bubble_height, bubble_height),
            content_width=content_width,
            title_width=title_width,
            title_height=title_height,
            header_height=header_height,
            body_height=body_height,
            hint_height=hint_height,
            timer_label_height=timer_label_height,
        )

    @staticmethod
    def _measure_text_height(text: str, font: QFont, width: int) -> int:
        if not text:
            return 0
        metrics = QFontMetrics(font)
        rect = metrics.boundingRect(QRect(0, 0, width, 2000), Qt.TextFlag.TextWordWrap, text)
        return rect.height()
