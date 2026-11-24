from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from aqt.qt import (
    QCheckBox,
    QColor,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLinearGradient,
    QPainter,
    QPen,
    QPushButton,
    QRadialGradient,
    QRectF,
    QScrollArea,
    QSpinBox,
    Qt,
    QTimer,
    QVBoxLayout,
    QWidget,
)

from .audio_waveform import AudioWaveform, load_audio_waveform
from .countdown_audio import MAX_COUNTDOWN_AUDIO_ALIGNMENT_MS, countdown_preview_cues


SYNC_WINDOW_MS = 1000


class CueWaveformWidget(QWidget):
    def __init__(
        self,
        waveform: AudioWaveform,
        sync_ms: int,
        max_sync_ms: int,
        on_sync_changed: Callable[[int], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.waveform = waveform
        self.max_sync_ms = max(0, min(MAX_COUNTDOWN_AUDIO_ALIGNMENT_MS, int(max_sync_ms)))
        self.sync_ms = max(0, min(self.max_sync_ms, int(sync_ms)))
        self.on_sync_changed = on_sync_changed
        self.setMinimumHeight(122)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click or drag to choose the exact moment in the clip that should land on a timer beat.")

    def set_sync_ms(self, value: int) -> None:
        next_value = max(0, min(self.max_sync_ms, int(value)))
        if next_value == self.sync_ms:
            return
        self.sync_ms = next_value
        self.update()

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        bounds = QRectF(1, 1, max(1, self.width() - 2), max(1, self.height() - 2))
        painter.setPen(QPen(QColor("#263550"), 1))
        painter.setBrush(QColor("#09111f"))
        painter.drawRoundedRect(bounds, 13, 13)

        left = 18.0
        right = max(left + 1, float(self.width()) - 18.0)
        top = 26.0
        bottom = max(top + 1, float(self.height()) - 27.0)
        center_y = (top + bottom) / 2
        width = right - left
        painter.setPen(QPen(QColor("#273652"), 1))
        painter.drawLine(int(left), int(center_y), int(right), int(center_y))

        peaks = self.waveform.peaks
        if peaks:
            extent = min(1.0, max(0.01, self.waveform.duration_ms / max(1, self.waveform.visible_ms)))
            drawable_width = width * extent
            step = drawable_width / max(1, len(peaks))
            bar_width = max(1.0, min(3.0, step * 0.72))
            gradient = QLinearGradient(left, top, right, bottom)
            gradient.setColorAt(0.0, QColor("#6f9dff"))
            gradient.setColorAt(0.55, QColor("#65f0c2"))
            gradient.setColorAt(1.0, QColor("#f5aa41"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            half_height = max(4.0, (bottom - top) * 0.46)
            for index, peak in enumerate(peaks):
                height = max(2.0, half_height * float(peak))
                x = left + (index * step)
                painter.drawRoundedRect(
                    QRectF(x, center_y - height, bar_width, height * 2),
                    bar_width / 2,
                    bar_width / 2,
                )
        else:
            painter.setPen(QPen(QColor("#52617c"), 2, Qt.PenStyle.DashLine))
            painter.drawLine(int(left), int(center_y), int(right), int(center_y))

        unavailable_left = left + (width * (self.max_sync_ms / SYNC_WINDOW_MS))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 14))
        painter.drawRect(QRectF(unavailable_left, top, right - unavailable_left, bottom - top))

        marker_x = left + (width * (self.sync_ms / SYNC_WINDOW_MS))
        painter.setPen(QPen(QColor("#f5aa41"), 2))
        painter.drawLine(int(marker_x), int(top - 7), int(marker_x), int(bottom + 7))
        painter.setBrush(QColor("#f5aa41"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(marker_x - 5, top - 10, 10, 10))

        painter.setPen(QColor("#8ea0cc"))
        font = painter.font()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(left, bottom + 7, 80, 18), Qt.AlignmentFlag.AlignLeft, "CLIP START")
        painter.drawText(QRectF(right - 80, bottom + 7, 80, 18), Qt.AlignmentFlag.AlignRight, "1 SECOND")

    def mousePressEvent(self, event: Any) -> None:
        self._set_from_event(event)

    def mouseMoveEvent(self, event: Any) -> None:
        buttons = getattr(event, "buttons", lambda: Qt.MouseButton.LeftButton)()
        if buttons & Qt.MouseButton.LeftButton:
            self._set_from_event(event)

    def _set_from_event(self, event: Any) -> None:
        position = getattr(event, "position", None)
        x = float(position().x()) if callable(position) else float(event.pos().x())
        left = 18.0
        width = max(1.0, float(self.width()) - 36.0)
        value = round(((x - left) / width) * SYNC_WINDOW_MS)
        value = max(0, min(self.max_sync_ms, int(value)))
        self.set_sync_ms(value)
        self.on_sync_changed(value)


class TimerBeatPreview(QWidget):
    def __init__(self, warning_seconds: int, colors: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.warning_seconds = max(1, int(warning_seconds))
        self.total_ms = (self.warning_seconds + 1) * 1000
        self.remaining_ms = self.total_ms
        self.pulse = 0.0
        self.colors = dict(colors or {})
        self.setMinimumSize(220, 182)

    def set_remaining(self, remaining_ms: int, *, pulse: float = 0.0) -> None:
        self.remaining_ms = max(0, min(self.total_ms, int(remaining_ms)))
        self.pulse = max(0.0, min(1.0, float(pulse)))
        self.update()

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        center_x = self.width() / 2
        center_y = self.height() / 2 - 2
        diameter = min(146.0, self.width() - 44.0, self.height() - 36.0)
        circle = QRectF(center_x - diameter / 2, center_y - diameter / 2, diameter, diameter)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#060b13"))
        painter.drawEllipse(circle)
        core_gradient = QRadialGradient(center_x - diameter * 0.18, center_y - diameter * 0.24, diameter * 0.72)
        core_gradient.setColorAt(0.0, QColor("#17233a"))
        core_gradient.setColorAt(1.0, QColor("#080d17"))
        painter.setBrush(core_gradient)
        painter.drawEllipse(circle.adjusted(9, 9, -9, -9))

        progress = self.remaining_ms / max(1, self.total_ms)
        warning_color = QColor(self.colors.get("red", "#c34f69"))
        glow_color = QColor(warning_color)
        glow_color.setAlpha(70 + int(80 * self.pulse))
        painter.setPen(QPen(glow_color, 15 + (4 * self.pulse), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(circle.adjusted(5, 5, -5, -5), 90 * 16, -int(360 * 16 * progress))
        painter.setPen(QPen(warning_color, 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(circle.adjusted(5, 5, -5, -5), 90 * 16, -int(360 * 16 * progress))

        painter.setPen(QColor("#9fb0d8"))
        label_font = painter.font()
        label_font.setPointSize(9)
        label_font.setBold(True)
        label_font.setLetterSpacing(label_font.SpacingType.AbsoluteSpacing, 2.0)
        painter.setFont(label_font)
        painter.drawText(
            QRectF(circle.left(), center_y - 45, diameter, 24),
            Qt.AlignmentFlag.AlignCenter,
            "QUESTION",
        )
        painter.setPen(warning_color)
        value_font = painter.font()
        value_font.setPointSize(32)
        value_font.setBold(True)
        value_font.setLetterSpacing(value_font.SpacingType.PercentageSpacing, 100)
        painter.setFont(value_font)
        painter.drawText(
            QRectF(circle.left(), center_y - 25, diameter, 70),
            Qt.AlignmentFlag.AlignCenter,
            f"{self.remaining_ms / 1000:.1f}",
        )


class CountdownSyncPointDialog(QDialog):
    def __init__(
        self,
        controller: Any,
        *,
        audio_key: str,
        audio_label: str,
        audio_path: str,
        warning_seconds: int,
        alignment_ms: int,
        timer_colors: dict[str, str],
        volume_percent: int = 100,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.audio_key = str(audio_key or "")
        self.audio_label = str(audio_label or self.audio_key or "Countdown cue")
        self.warning_seconds = max(1, int(warning_seconds or 1))
        self.volume_percent = max(0, min(200, int(volume_percent or 0)))
        waveform = load_audio_waveform(Path(audio_path), visible_ms=SYNC_WINDOW_MS)
        self.max_alignment_ms = (
            min(MAX_COUNTDOWN_AUDIO_ALIGNMENT_MS, max(0, waveform.duration_ms - 1))
            if waveform.available and waveform.duration_ms > 0
            else MAX_COUNTDOWN_AUDIO_ALIGNMENT_MS
        )
        self.alignment_ms = max(0, min(self.max_alignment_ms, int(alignment_ms or 0)))
        self.accepted_alignment_ms = self.alignment_ms
        self._preview_started_at = 0.0
        self._fired_seconds: set[int] = set()
        self._last_boundary = self.warning_seconds + 1
        self._has_previewed = False
        self._audio_ready = False
        self._audio_prepare_started_at = time.monotonic()
        self._replay_requested = False

        self.setModal(True)
        self.setWindowTitle("Countdown Cue Sync")
        self.setObjectName("speedStreakCountdownSync")
        self.setMinimumSize(700, 650)
        self.resize(760, 780)
        self.setStyleSheet(_DIALOG_STYLESHEET)

        shell = QVBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(scroll)
        content.setObjectName("countdownSyncContent")
        outer = QVBoxLayout(content)
        outer.setContentsMargins(20, 17, 20, 15)
        outer.setSpacing(10)
        scroll.setWidget(content)
        shell.addWidget(scroll, 1)

        title = QLabel("Make the sound land exactly on the beat", self)
        title.setProperty("role", "title")
        title.setWordWrap(True)
        outer.addWidget(title)
        explanation = QLabel(
            "The sync point is the moment inside the sound that should coincide with each whole-second timer mark. "
            "Speed Streak starts the complete clip this many milliseconds early—nothing is trimmed or skipped.",
            self,
        )
        explanation.setWordWrap(True)
        explanation.setProperty("role", "help")
        outer.addWidget(explanation)

        clip_row = QLabel(f"Selected cue  ·  {self.audio_label}", self)
        clip_row.setProperty("role", "clip")
        clip_row.setWordWrap(True)
        clip_row.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        outer.addWidget(clip_row)

        waveform_card = QFrame(self)
        waveform_card.setProperty("role", "card")
        waveform_layout = QVBoxLayout(waveform_card)
        waveform_layout.setContentsMargins(14, 11, 14, 11)
        waveform_layout.setSpacing(6)
        waveform_title = QLabel("1. Choose the sync point", waveform_card)
        waveform_title.setProperty("role", "sectionTitle")
        waveform_title.setWordWrap(True)
        waveform_layout.addWidget(waveform_title)
        waveform_help = QLabel(
            "Click the waveform at the click, tick, chime, or impact you want to hear precisely when the number reaches 3.0, 2.0, and 1.0.",
            waveform_card,
        )
        waveform_help.setWordWrap(True)
        waveform_help.setProperty("role", "help")
        waveform_layout.addWidget(waveform_help)
        self.waveform_widget = CueWaveformWidget(
            waveform,
            self.alignment_ms,
            self.max_alignment_ms,
            self._on_waveform_sync_changed,
            waveform_card,
        )
        waveform_layout.addWidget(self.waveform_widget)
        if waveform.message:
            waveform_status = QLabel(waveform.message, waveform_card)
            waveform_status.setWordWrap(True)
            waveform_status.setProperty("role", "notice")
            waveform_layout.addWidget(waveform_status)

        precision_row = QHBoxLayout()
        self.sync_summary = QLabel("", waveform_card)
        self.sync_summary.setProperty("role", "sync")
        self.sync_summary.setWordWrap(True)
        waveform_layout.addWidget(self.sync_summary)
        self.sync_spin = QSpinBox(waveform_card)
        self.sync_spin.setRange(0, self.max_alignment_ms)
        self.sync_spin.setSingleStep(5)
        self.sync_spin.setSuffix(" ms into clip")
        self.sync_spin.setFixedWidth(190)
        self.sync_spin.setValue(self.alignment_ms)
        self.sync_spin.valueChanged.connect(self._on_spin_sync_changed)
        precision_row.addStretch(1)
        precision_row.addWidget(self.sync_spin)
        waveform_layout.addLayout(precision_row)
        outer.addWidget(waveform_card)

        preview_card = QFrame(self)
        preview_card.setProperty("role", "card")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(14, 11, 14, 11)
        preview_layout.setSpacing(6)
        preview_title = QLabel("2. Hear it against your countdown", preview_card)
        preview_title.setProperty("role", "sectionTitle")
        preview_title.setWordWrap(True)
        preview_layout.addWidget(preview_title)
        self.timer_preview = TimerBeatPreview(self.warning_seconds, timer_colors, preview_card)
        preview_layout.addWidget(self.timer_preview, 0, Qt.AlignmentFlag.AlignHCenter)
        self.preview_status = QLabel("Press Replay to hear the full clip align with the visible timer.", preview_card)
        self.preview_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_status.setProperty("role", "help")
        self.preview_status.setWordWrap(True)
        preview_layout.addWidget(self.preview_status)
        preview_controls = QHBoxLayout()
        preview_controls.addStretch(1)
        self.replay_button = QPushButton("▶  Replay", preview_card)
        self.replay_button.setProperty("role", "primary")
        self.replay_button.clicked.connect(self.replay)
        preview_controls.addWidget(self.replay_button)
        self.loop_check = QCheckBox("Loop", preview_card)
        preview_controls.addWidget(self.loop_check)
        preview_controls.addStretch(1)
        preview_layout.addLayout(preview_controls)
        outer.addWidget(preview_card, 1)

        action_bar = QWidget(self)
        self.action_bar = action_bar
        action_bar.setProperty("role", "actionBar")
        actions = QHBoxLayout(action_bar)
        actions.addStretch(1)
        cancel_button = QPushButton("Cancel", action_bar)
        self.cancel_button = cancel_button
        cancel_button.clicked.connect(self.reject)
        actions.addWidget(cancel_button)
        use_button = QPushButton("Use Sync Point", action_bar)
        self.use_button = use_button
        use_button.setProperty("role", "primary")
        use_button.clicked.connect(self._accept_sync_point)
        actions.addWidget(use_button)
        shell.addWidget(action_bar)

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick_preview)
        self._loop_timer = QTimer(self)
        self._loop_timer.setSingleShot(True)
        self._loop_timer.timeout.connect(self.replay)
        self._replay_debounce = QTimer(self)
        self._replay_debounce.setSingleShot(True)
        self._replay_debounce.setInterval(240)
        self._replay_debounce.timeout.connect(self._replay_after_edit)
        self._readiness_timer = QTimer(self)
        self._readiness_timer.setInterval(25)
        self._readiness_timer.timeout.connect(self._check_audio_ready)
        self._prepare_audio()
        self._readiness_timer.start()
        self._check_audio_ready()
        self._sync_summary()

    def replay(self) -> None:
        self._loop_timer.stop()
        self._replay_debounce.stop()
        if not self._audio_ready:
            self._replay_requested = True
            self.preview_status.setText("Preparing the cue so the first replay starts on time…")
            if not self._readiness_timer.isActive():
                self._audio_prepare_started_at = time.monotonic()
                self._prepare_audio()
                self._readiness_timer.start()
            return
        self._start_replay()

    def _start_replay(self) -> None:
        self._replay_requested = False
        self._preview_started_at = time.monotonic()
        self._fired_seconds.clear()
        self._last_boundary = self.warning_seconds + 1
        self._has_previewed = True
        self.timer_preview.set_remaining((self.warning_seconds + 1) * 1000)
        self.preview_status.setText(
            f"The clip starts {self.alignment_ms} ms before each whole-second mark. No cue plays at 0.0."
        )
        self._timer.start()
        self._tick_preview()

    def _prepare_audio(self) -> None:
        prepare = getattr(self.controller, "prepare_countdown_audio_preview", None)
        if not callable(prepare):
            self._audio_ready = True
            return
        try:
            prepare(self.audio_key, self.volume_percent)
        except TypeError:
            prepare(self.audio_key)
        except Exception:
            pass

    def _check_audio_ready(self) -> None:
        ready_check = getattr(self.controller, "countdown_audio_preview_ready", None)
        if callable(ready_check):
            try:
                ready = bool(ready_check(self.audio_key))
            except Exception:
                ready = False
        else:
            ready = True
        # A broken or very old multimedia backend must not trap the dialog.
        if not ready and (time.monotonic() - self._audio_prepare_started_at) < 2.0:
            return
        self._audio_ready = True
        self._readiness_timer.stop()
        if self._replay_requested:
            QTimer.singleShot(0, self._start_replay)

    def _tick_preview(self) -> None:
        if self._preview_started_at <= 0:
            return
        total_ms = (self.warning_seconds + 1) * 1000
        elapsed_ms = max(0, int(round((time.monotonic() - self._preview_started_at) * 1000)))
        remaining_ms = max(0, total_ms - elapsed_ms)
        current_boundary = max(0, (remaining_ms + 999) // 1000)
        pulse = 0.0
        if current_boundary < self._last_boundary:
            pulse = 1.0
            self._last_boundary = current_boundary
        else:
            distance = remaining_ms % 1000
            pulse = max(0.0, 1.0 - (min(distance, 1000 - distance) / 180.0))

        for cue in countdown_preview_cues(
            warning_seconds=self.warning_seconds,
            alignment_ms=self.alignment_ms,
        ):
            if elapsed_ms >= cue.delay_ms and cue.second not in self._fired_seconds:
                self._fired_seconds.add(cue.second)
                preview = getattr(self.controller, "preview_countdown_audio", None)
                try:
                    played = (
                        bool(preview(self.audio_key, self.volume_percent))
                        if callable(preview)
                        else bool(
                            self.controller.preview_audio_feedback(
                                self.audio_key,
                                self.volume_percent,
                            )
                        )
                    )
                except TypeError:
                    played = (
                        bool(preview(self.audio_key))
                        if callable(preview)
                        else bool(self.controller.preview_audio_feedback(self.audio_key))
                    )
                if not played:
                    self.preview_status.setText(
                        "This audio file could not be played through Anki's preview player. Try WAV or another cue."
                    )
        self.timer_preview.set_remaining(remaining_ms, pulse=pulse)
        if remaining_ms > 0:
            return
        self._timer.stop()
        self.preview_status.setText("Preview complete · no countdown cue is played at 0.0.")
        if self.loop_check.isChecked():
            self._loop_timer.start(550)

    def _on_waveform_sync_changed(self, value: int) -> None:
        self.sync_spin.blockSignals(True)
        try:
            self.sync_spin.setValue(int(value))
        finally:
            self.sync_spin.blockSignals(False)
        self._set_alignment(value)

    def _on_spin_sync_changed(self, value: int) -> None:
        self.waveform_widget.set_sync_ms(int(value))
        self._set_alignment(value)

    def _set_alignment(self, value: int) -> None:
        self.alignment_ms = max(0, min(self.max_alignment_ms, int(value)))
        self._sync_summary()
        if self._has_previewed:
            self._replay_debounce.start()

    def _sync_summary(self) -> None:
        self.sync_summary.setText(
            f"The sound starts {self.alignment_ms} ms early so this marker lands on the beat."
        )

    def _replay_after_edit(self) -> None:
        if self.isVisible():
            self.replay()

    def _accept_sync_point(self) -> None:
        self.accepted_alignment_ms = self.alignment_ms
        self.accept()

    def done(self, result: int) -> None:
        self._timer.stop()
        self._loop_timer.stop()
        self._replay_debounce.stop()
        self._readiness_timer.stop()
        super().done(result)


_DIALOG_STYLESHEET = """
QDialog#speedStreakCountdownSync {
  background: #0b111b;
  color: #edf3ff;
  font-size: 12px;
}
QDialog#speedStreakCountdownSync QScrollArea,
QDialog#speedStreakCountdownSync QScrollArea QWidget#qt_scrollarea_viewport,
QDialog#speedStreakCountdownSync QWidget#countdownSyncContent {
  border: none;
  background: #0b111b;
}
QDialog#speedStreakCountdownSync QLabel[role="title"] {
  color: #f4f7ff;
  font-size: 21px;
  font-weight: 800;
}
QDialog#speedStreakCountdownSync QLabel[role="help"] {
  color: #9daccb;
  line-height: 1.35;
}
QDialog#speedStreakCountdownSync QLabel[role="clip"] {
  color: #cbd8f5;
  font-weight: 700;
  padding: 7px 10px;
  border-radius: 8px;
  background: rgba(111, 157, 255, 0.08);
}
QDialog#speedStreakCountdownSync QFrame[role="card"] {
  border: 1px solid rgba(139, 174, 235, 0.18);
  border-radius: 14px;
  background: #101927;
}
QDialog#speedStreakCountdownSync QWidget[role="actionBar"] {
  padding: 10px 14px;
  border-top: 1px solid rgba(139, 174, 235, 0.14);
  background: #0b111b;
}
QDialog#speedStreakCountdownSync QLabel[role="sectionTitle"] {
  color: #eef4ff;
  font-size: 14px;
  font-weight: 800;
}
QDialog#speedStreakCountdownSync QLabel[role="sync"] {
  color: #f5aa41;
  font-weight: 750;
}
QDialog#speedStreakCountdownSync QLabel[role="notice"] {
  color: #d8c49b;
  padding: 6px 8px;
  border-radius: 7px;
  background: rgba(245, 170, 65, 0.08);
}
QDialog#speedStreakCountdownSync QPushButton,
QDialog#speedStreakCountdownSync QSpinBox {
  min-height: 31px;
  padding: 0 12px;
  border: 1px solid rgba(145, 177, 231, 0.22);
  border-radius: 8px;
  color: #edf3ff;
  background: #172235;
}
QDialog#speedStreakCountdownSync QPushButton:hover {
  border-color: rgba(127, 176, 255, 0.62);
  background: #1d2b43;
}
QDialog#speedStreakCountdownSync QPushButton[role="primary"] {
  border-color: rgba(111, 157, 255, 0.55);
  background: #365fba;
  font-weight: 800;
}
QDialog#speedStreakCountdownSync QCheckBox {
  color: #d7e1f6;
  spacing: 7px;
}
"""
