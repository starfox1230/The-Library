from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QFontMetrics, QGuiApplication, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from .helpers import format_duration, preview_text


@dataclass
class OverlayState:
    mode: str
    title: str
    body: str
    hint: str
    accent: QColor
    timer_ratio: float | None = None
    timer_label: str = ""


@dataclass(frozen=True)
class BubbleLayoutMetrics:
    bubble_width: int
    bubble_height: int
    content_width: int
    title_width: int
    title_height: int
    header_height: int
    body_height: int
    hint_height: int
    timer_label_height: int


@dataclass(frozen=True)
class RecordingChipMetrics:
    chip_width: int
    chip_height: int
    time_width: int
    time_height: int


class CursorOverlay(QWidget):
    _shadow_margin = 0
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

    _chip_height = 54
    _chip_padding_x = 10
    _chip_gap = 12
    _chip_ring_size = 34
    _chip_ring_width = 4

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
            mode="bubble",
            title="",
            body="",
            hint="",
            accent=QColor("#22c55e"),
        )

        self._title_font = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
        self._body_font = QFont("Segoe UI", 10)
        self._hint_font = QFont("Segoe UI", 8)
        self._time_font = QFont("Consolas", 11, QFont.Weight.Bold)
        self._time_font.setStyleHint(QFont.StyleHint.Monospace)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

        self._follow_timer = QTimer(self)
        self._follow_timer.setInterval(33)
        self._follow_timer.timeout.connect(self._follow_cursor)
        self._last_anchor = "br"
        self._spinner_angle = 0

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
            mode="recording_chip",
            title="",
            body=format_duration(seconds_remaining),
            hint="",
            accent=self._recording_timer_color(ratio),
            timer_ratio=ratio,
        )

    def show_transcribing(self) -> None:
        self._set_state(
            mode="loading_chip",
            title="",
            body="",
            hint="",
            accent="#fbbf24",
        )

    def show_transcript(self, text: str) -> None:
        self._set_state(
            title="Copied to clipboard",
            body=preview_text(text),
            hint="Paste or copy with your keyboard shortcut to dismiss",
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
        if self._state.mode == "recording_chip":
            chip = self._measure_recording_chip()
            return QSize(chip.chip_width, chip.chip_height)
        if self._state.mode == "loading_chip":
            chip = self._measure_loading_chip()
            return QSize(chip.chip_width, chip.chip_height)

        layout = self._measure_bubble_layout()
        return QSize(layout.bubble_width, layout.bubble_height)

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if self._state.mode == "recording_chip":
            self._paint_recording_chip(painter)
            return
        if self._state.mode == "loading_chip":
            self._paint_loading_chip(painter)
            return

        self._paint_bubble(painter)

    def _paint_bubble(self, painter: QPainter) -> None:
        layout = self._measure_bubble_layout()
        bubble_rect = QRectF(
            0.5,
            0.5,
            max(1.0, layout.bubble_width - 1.0),
            max(1.0, layout.bubble_height - 1.0),
        )
        bubble_path = QPainterPath()
        bubble_path.addRoundedRect(bubble_rect, self._corner_radius, self._corner_radius)

        self._draw_bubble_shell(painter, bubble_rect, bubble_path)
        self._draw_bubble_content(painter, bubble_rect, layout)

    def _paint_recording_chip(self, painter: QPainter) -> None:
        chip = self._measure_recording_chip()
        chip_rect = QRectF(
            0.5,
            0.5,
            max(1.0, chip.chip_width - 1.0),
            max(1.0, chip.chip_height - 1.0),
        )
        chip_path = QPainterPath()
        chip_path.addRoundedRect(chip_rect, chip.chip_height / 2, chip.chip_height / 2)

        self._draw_recording_chip_shell(painter, chip_rect, chip_path)

        ring_rect = QRectF(
            chip_rect.left() + self._chip_padding_x,
            chip_rect.top() + ((chip_rect.height() - self._chip_ring_size) / 2),
            self._chip_ring_size,
            self._chip_ring_size,
        )
        self._draw_recording_ring(painter, ring_rect)

        text_rect = QRect(
            round(ring_rect.right() + self._chip_gap),
            round(chip_rect.top()),
            chip.time_width,
            round(chip_rect.height()),
        )
        painter.save()
        painter.setPen(QColor("#f8fafc"))
        painter.setFont(self._time_font)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._state.body)
        painter.restore()

    def _paint_loading_chip(self, painter: QPainter) -> None:
        chip = self._measure_loading_chip()
        chip_rect = QRectF(
            0.5,
            0.5,
            max(1.0, chip.chip_width - 1.0),
            max(1.0, chip.chip_height - 1.0),
        )
        chip_path = QPainterPath()
        chip_path.addRoundedRect(chip_rect, chip.chip_height / 2, chip.chip_height / 2)

        self._draw_recording_chip_shell(painter, chip_rect, chip_path)

        ring_rect = QRectF(
            chip_rect.left() + ((chip_rect.width() - self._chip_ring_size) / 2),
            chip_rect.top() + ((chip_rect.height() - self._chip_ring_size) / 2),
            self._chip_ring_size,
            self._chip_ring_size,
        )
        self._draw_loading_spinner(painter, ring_rect)

    def _draw_bubble_shell(self, painter: QPainter, bubble_rect: QRectF, bubble_path: QPainterPath) -> None:
        painter.save()

        fill_gradient = QLinearGradient(bubble_rect.topLeft(), bubble_rect.bottomLeft())
        top_color, mid_color, bottom_color = self._bubble_fill_colors()
        fill_gradient.setColorAt(0.0, top_color)
        fill_gradient.setColorAt(0.45, mid_color)
        fill_gradient.setColorAt(1.0, bottom_color)
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

        painter.restore()

    def _draw_recording_chip_shell(self, painter: QPainter, chip_rect: QRectF, chip_path: QPainterPath) -> None:
        painter.save()

        chip_gradient = QLinearGradient(chip_rect.topLeft(), chip_rect.bottomLeft())
        chip_gradient.setColorAt(0.0, QColor("#162538"))
        chip_gradient.setColorAt(1.0, QColor("#0e1828"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(chip_gradient)
        painter.drawPath(chip_path)

        shine_gradient = QLinearGradient(chip_rect.topLeft(), chip_rect.bottomLeft())
        shine_gradient.setColorAt(0.0, QColor(255, 255, 255, 26))
        shine_gradient.setColorAt(0.35, QColor(255, 255, 255, 10))
        shine_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setClipPath(chip_path)
        painter.setBrush(shine_gradient)
        painter.drawRect(chip_rect)
        painter.setClipping(False)

        painter.restore()

    def _draw_bubble_content(self, painter: QPainter, bubble_rect: QRectF, layout: BubbleLayoutMetrics) -> None:
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

    def _draw_recording_ring(self, painter: QPainter, ring_rect: QRectF) -> None:
        ratio = self._state.timer_ratio or 0.0

        painter.save()
        painter.setBrush(Qt.BrushStyle.NoBrush)

        track_pen = QPen(QColor(255, 255, 255, 32), self._chip_ring_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawEllipse(ring_rect)

        if ratio > 0:
            glow_color = QColor(self._state.accent)
            glow_color.setAlpha(46)
            glow_pen = QPen(glow_color, self._chip_ring_width + 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(glow_pen)
            painter.drawArc(ring_rect, 90 * 16, int(-360 * ratio * 16))

            arc_pen = QPen(self._state.accent, self._chip_ring_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(arc_pen)
            painter.drawArc(ring_rect, 90 * 16, int(-360 * ratio * 16))

        core_rect = ring_rect.adjusted(9, 9, -9, -9)
        halo_rect = core_rect.adjusted(-3, -3, 3, 3)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 94, 106, 60))
        painter.drawEllipse(halo_rect)

        core_gradient = QLinearGradient(core_rect.topLeft(), core_rect.bottomLeft())
        core_gradient.setColorAt(0.0, QColor("#ff7580"))
        core_gradient.setColorAt(1.0, QColor("#ef4444"))
        painter.setBrush(core_gradient)
        painter.drawEllipse(core_rect)

        highlight_rect = core_rect.adjusted(2, 2, -5, -6)
        painter.setBrush(QColor(255, 255, 255, 120))
        painter.drawEllipse(highlight_rect)
        painter.restore()

    def _draw_loading_spinner(self, painter: QPainter, ring_rect: QRectF) -> None:
        painter.save()
        painter.setBrush(Qt.BrushStyle.NoBrush)

        track_pen = QPen(QColor(255, 255, 255, 24), self._chip_ring_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawEllipse(ring_rect)

        glow_color = QColor(self._state.accent)
        glow_color.setAlpha(56)
        glow_pen = QPen(glow_color, self._chip_ring_width + 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(glow_pen)
        painter.drawArc(ring_rect, self._spinner_angle * 16, -120 * 16)

        arc_pen = QPen(self._state.accent, self._chip_ring_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)
        painter.drawArc(ring_rect, self._spinner_angle * 16, -120 * 16)

        core_rect = ring_rect.adjusted(10, 10, -10, -10)
        core_gradient = QLinearGradient(core_rect.topLeft(), core_rect.bottomLeft())
        core_gradient.setColorAt(0.0, QColor("#fde68a"))
        core_gradient.setColorAt(1.0, QColor("#f59e0b"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(core_gradient)
        painter.drawEllipse(core_rect)
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
        accent: str | QColor,
        timer_ratio: float | None = None,
        timer_label: str = "",
        mode: str = "bubble",
    ) -> None:
        self._state = OverlayState(
            mode=mode,
            title=title,
            body=body,
            hint=hint,
            accent=QColor(accent),
            timer_ratio=timer_ratio,
            timer_label=timer_label,
        )
        if mode != "loading_chip":
            self._spinner_angle = 0
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
        anchor = self._last_anchor if self._last_anchor else "br"
        rect = self._overlay_rect_for_anchor(cursor_pos, available, anchor)

        if self._state.mode == "bubble" and rect.contains(cursor_pos):
            for alternate_anchor in self._alternate_anchors(anchor):
                alternate_rect = self._overlay_rect_for_anchor(cursor_pos, available, alternate_anchor)
                if not alternate_rect.contains(cursor_pos):
                    rect = alternate_rect
                    anchor = alternate_anchor
                    break

        self._last_anchor = anchor
        self.move(rect.topLeft())

        if self._state.mode == "loading_chip":
            self._spinner_angle = (self._spinner_angle + 10) % 360
            self.update()

    def _measure_bubble_layout(self) -> BubbleLayoutMetrics:
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

        return BubbleLayoutMetrics(
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

    def _measure_recording_chip(self) -> RecordingChipMetrics:
        metrics = QFontMetrics(self._time_font)
        time_width = metrics.horizontalAdvance("00:00")
        time_height = metrics.height()
        chip_width = self._chip_padding_x + self._chip_ring_size + self._chip_gap + time_width + self._chip_padding_x
        return RecordingChipMetrics(
            chip_width=chip_width,
            chip_height=self._chip_height,
            time_width=time_width,
            time_height=time_height,
        )

    def _measure_loading_chip(self) -> RecordingChipMetrics:
        metrics = QFontMetrics(self._time_font)
        chip_width = self._chip_ring_size + (self._chip_padding_x * 2)
        return RecordingChipMetrics(
            chip_width=chip_width,
            chip_height=self._chip_height,
            time_width=0,
            time_height=metrics.height(),
        )

    @staticmethod
    def _measure_text_height(text: str, font: QFont, width: int) -> int:
        if not text:
            return 0
        metrics = QFontMetrics(font)
        rect = metrics.boundingRect(QRect(0, 0, width, 2000), Qt.TextFlag.TextWordWrap, text)
        return rect.height()

    @staticmethod
    def _blend_colors(start: QColor, end: QColor, ratio: float) -> QColor:
        mix = max(0.0, min(1.0, ratio))
        return QColor(
            round(start.red() + ((end.red() - start.red()) * mix)),
            round(start.green() + ((end.green() - start.green()) * mix)),
            round(start.blue() + ((end.blue() - start.blue()) * mix)),
            round(start.alpha() + ((end.alpha() - start.alpha()) * mix)),
        )

    def _recording_timer_color(self, ratio: float) -> QColor:
        full = QColor("#34d399")
        middle = QColor("#fbbf24")
        empty = QColor("#ef4444")

        if ratio >= 0.5:
            return self._blend_colors(middle, full, (ratio - 0.5) / 0.5)
        return self._blend_colors(empty, middle, ratio / 0.5)

    def _bubble_fill_colors(self) -> tuple[QColor, QColor, QColor]:
        top_base = QColor("#17263a")
        mid_base = QColor("#122033")
        bottom_base = QColor("#0d1727")

        if self._state.title == "Copied to clipboard":
            return (
                self._blend_colors(top_base, self._state.accent, 0.24),
                self._blend_colors(mid_base, self._state.accent, 0.20),
                self._blend_colors(bottom_base, self._state.accent, 0.16),
            )

        if self._state.title == "Something went wrong":
            return (
                self._blend_colors(top_base, self._state.accent, 0.22),
                self._blend_colors(mid_base, self._state.accent, 0.18),
                self._blend_colors(bottom_base, self._state.accent, 0.14),
            )

        return top_base, mid_base, bottom_base

    @staticmethod
    def _alternate_anchors(anchor: str) -> tuple[str, ...]:
        if anchor == "br":
            return ("tl", "tr", "bl")
        if anchor == "tl":
            return ("br", "bl", "tr")
        if anchor == "tr":
            return ("bl", "br", "tl")
        return ("tr", "tl", "br")

    def _overlay_rect_for_anchor(self, cursor_pos, available: QRect, anchor: str) -> QRect:
        width = self.width()
        height = self.height()

        if anchor == "tl":
            x = cursor_pos.x() - width - self._offset_x
            y = cursor_pos.y() - height - self._offset_y
        elif anchor == "tr":
            x = cursor_pos.x() + self._offset_x
            y = cursor_pos.y() - height - self._offset_y
        elif anchor == "bl":
            x = cursor_pos.x() - width - self._offset_x
            y = cursor_pos.y() + self._offset_y
        else:
            x = cursor_pos.x() + self._offset_x
            y = cursor_pos.y() + self._offset_y

        x = max(available.left() + 8, min(x, available.left() + available.width() - width - 8))
        y = max(available.top() + 8, min(y, available.top() + available.height() - height - 8))
        return QRect(x, y, width, height)
