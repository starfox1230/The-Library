"""A quiet reviewer start button with opt-in, in-memory review bursts."""
from __future__ import annotations

from math import ceil, cos, pi, sin
from random import Random
from time import monotonic
from typing import Any

import aqt
from aqt import gui_hooks
from aqt.qt import (
    QAction, QCheckBox, QColor, QComboBox, QDialog, QDialogButtonBox, QEvent, QFont, QHBoxLayout, QLabel, QMenu,
    QObject, QPainter, QPen, QPointF, QPushButton, QRectF, QSpinBox,
    QTimer, Qt, QVBoxLayout, QWidget,
)
from aqt.utils import showInfo

from .settings import get_setting, set_setting


_controller: BurstController | None = None
_actions: list[QAction] = []
_presence: BurstButtonController | None = None
COLORS = ("#77f6ca", "#a99aff", "#ffd378", "#ff89bb", "#88d9ff")


def clock_text(seconds: int) -> str:
    minutes, seconds = divmod(max(0, seconds), 60)
    return f"{minutes}:{seconds:02d}"


class BurstChoice(QWidget):
    """One mode selector and one number; values survive switching modes."""
    def __init__(self, mode: str, answers: int, minutes: int, *, allow_zero: bool = False) -> None:
        super().__init__()
        self.values = {"cards": answers, "timer": minutes}
        self.allow_zero = allow_zero
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        self.mode = QComboBox()
        self.mode.addItem("Answers remaining", "cards")
        self.mode.addItem("Focus timer", "timer")
        self.mode.setCurrentIndex(1 if mode == "timer" else 0)
        row.addWidget(self.mode, 1)
        self.amount = QSpinBox()
        self.amount.setMinimumWidth(98)
        row.addWidget(self.amount)
        self.sync_amount()
        self.amount.valueChanged.connect(self.remember_amount)
        self.mode.currentIndexChanged.connect(self.sync_amount)

    def sync_amount(self, *_args: Any) -> None:
        mode = self.mode.currentData()
        self.amount.blockSignals(True)
        self.amount.setRange(0 if mode == "cards" and self.allow_zero else 1, 1000)
        self.amount.setSuffix(" min" if mode == "timer" else "")
        self.amount.setValue(self.values[mode])
        self.amount.blockSignals(False)

    def remember_amount(self, value: int) -> None:
        self.values[self.mode.currentData()] = value

    def selection(self) -> tuple[str, int]:
        return self.mode.currentData(), self.amount.value()


class BurstEditDialog(QDialog):
    def __init__(self, parent: QWidget, mode: str, answers: int, minutes: int) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit burst")
        self.setMinimumWidth(330)
        self.setStyleSheet("""
            QDialog { background: #172333; color: #eff6ff; }
            QComboBox, QSpinBox { color: #eff6ff; background: #203146;
                border: 1px solid #456052; border-radius: 7px; padding: 8px; }
            QComboBox QAbstractItemView { background: #203146; color: #eff6ff;
                selection-background-color: #315746; }
            QPushButton { color: #b7f9df; background: #19382e;
                border: 1px solid #456b5d; border-radius: 7px; padding: 7px 18px; }
            QPushButton:hover { background: #24503f; }
            QPushButton:default { border-color: #77f6ca; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)
        self.choice = BurstChoice(mode, answers, minutes, allow_zero=True)
        layout.addWidget(self.choice)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class BurstOverlay(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.count = 0
        self.goal = 10
        self.progress = 0.0
        self.pulse = 0.0
        self.complete = False
        self.mode = "cards"
        self.seconds_remaining = 0
        self.setFixedSize(164, 178)
        self.hide()

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        if not self.complete:
            # Layered halo, solid arc, and a bright leading bead.
            painter.setBrush(QColor("#172333"))
            painter.drawEllipse(QRectF(22, 8, 120, 120))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            ring = QRectF(32, 18, 100, 100)
            painter.setPen(QPen(QColor("#28384c"), 9))
            painter.drawEllipse(ring)
            for width, alpha in ((22, 12), (15, 30), (9, 255)):
                color = QColor("#77f6ca")
                color.setAlpha(alpha)
                pen = QPen(color, width)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawArc(ring, 90 * 16, -round(self.progress * 360 * 16))
            angle = self.progress * 2 * pi - pi / 2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#e0fff5"))
            radius = 4 + 2 * self.pulse
            painter.drawEllipse(QPointF(82 + 50 * cos(angle), 68 + 50 * sin(angle)), radius, radius)
            painter.setPen(QColor("#effff9"))
            painter.setFont(QFont("Segoe UI", 20 if self.mode == "timer" else 24, QFont.Weight.Bold))
            painter.drawText(QRectF(25, 36, 114, 60), Qt.AlignmentFlag.AlignCenter,
                             clock_text(self.seconds_remaining) if self.mode == "timer"
                             else str(max(0, self.goal - self.count)))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            painter.setPen(QColor("#a8b9ca"))
            painter.drawText(QRectF(34, 87, 96, 16), Qt.AlignmentFlag.AlignCenter,
                             "REMAINING" if self.mode == "timer" else "TO GO")
        badge = QRectF(6, 4 if self.complete else 147, 152, 29)
        painter.setPen(QPen(QColor("#46695f" if self.complete else "#344558"), 1))
        painter.setBrush(QColor("#142c27" if self.complete else "#172333"))
        painter.drawRoundedRect(badge, 14, 14)
        painter.setPen(QColor("#acffe1" if self.complete else "#eff6ff"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        label = ("Focus complete" if self.complete else "FOCUS TIMER") if self.mode == "timer" else f"{self.count} / {self.goal}"
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, label)


class ConfettiOverlay(QWidget):
    """Short, bounded animation over the review window; never captures input."""
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.elapsed = 0.0
        self.origin = QPointF()
        rng = Random()
        self.particles = [
            (rng.uniform(-850, 220), rng.uniform(-800, -170), rng.uniform(4, 9),
             rng.uniform(0, 360), rng.uniform(-540, 540), COLORS[i % len(COLORS)])
            for i in range(110)
        ]
        self.hide()

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        t = self.elapsed
        painter.setOpacity(max(0, min(1, (1.8 - t) / 0.6)))
        for vx, vy, size, angle, spin, color in self.particles:
            painter.save()
            painter.translate(self.origin.x() + vx * t, self.origin.y() + vy * t + 420 * t * t)
            painter.rotate(angle + spin * t)
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(QRectF(-size / 2, -size / 4, size, size / 2), 1, 1)
            painter.restore()


class BurstController(QObject):
    def __init__(self, mw: Any, goal: int) -> None:
        super().__init__(mw)
        self.mw = mw
        self.overlay = BurstOverlay(mw)
        self.overlay.goal = goal
        # A separate, transparent hit target keeps the rest of the painted
        # overlay click-through, so it cannot cover the card's controls.
        self.edit_button = QPushButton("", mw)
        self.edit_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_button.setAccessibleName("Edit burst target or switch to focus timer")
        self.edit_button.setToolTip("Edit remaining answers or switch to a focus timer")
        self.edit_button.setStyleSheet("QPushButton { background: transparent; border: none; border-radius: 12px; }"
                                      "QPushButton:hover { background: rgba(119, 246, 202, 18); }")
        self.edit_button.clicked.connect(self.open_editor)
        self.confetti = ConfettiOverlay(mw)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        self.animation_start = 0.0
        self.from_progress = 0.0
        self.to_progress = 0.0
        self.celebration_start: float | None = None
        self.duration_seconds = 0
        self.deadline = 0.0
        gui_hooks.reviewer_did_answer_card.append(self.answered)
        mw.installEventFilter(self)
        self.refresh_visibility()

    def position(self) -> None:
        bottom = self.mw.height() - 16
        bottom_web = getattr(self.mw, "bottomWeb", None)
        if bottom_web is not None and bottom_web.isVisible():
            bottom = bottom_web.mapTo(self.mw, bottom_web.rect().topLeft()).y() - 12
        self.overlay.move(max(0, self.mw.width() - self.overlay.width() - 16),
                          max(0, bottom - self.overlay.height()))
        self.confetti.setGeometry(self.mw.rect())
        area = QRectF(6, 4, 152, 29) if self.overlay.complete else QRectF(30, 35, 104, 72)
        self.edit_button.setGeometry(area.translated(self.overlay.x(), self.overlay.y()).toRect())

    def refresh_visibility(self) -> None:
        reviewing = self.mw.state == "review"
        self.position()
        self.overlay.setVisible(reviewing)
        self.edit_button.setVisible(reviewing)
        if reviewing:
            self.overlay.raise_()
            self.edit_button.raise_()
        else:
            self.finish_animation()

    def eventFilter(self, _watched: Any, event: Any) -> bool:
        if event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest):
            self.position()
        return False

    def answered(self, reviewer: Any, _card: Any, _ease: int) -> None:
        if reviewer is not self.mw.reviewer or self.overlay.mode == "timer":
            return
        self.overlay.count += 1
        if self.overlay.complete:
            self.overlay.update()
            return
        self.from_progress = self.overlay.progress
        self.to_progress = min(1, self.overlay.count / self.overlay.goal)
        self.animation_start = monotonic()
        self.timer.setInterval(16)
        self.timer.start()
        self.overlay.update()

    def tick(self) -> None:
        now = monotonic()
        timed = self.overlay.mode == "timer"
        if timed:
            remaining = max(0.0, self.deadline - now)
            self.overlay.seconds_remaining = ceil(remaining)
            self.to_progress = max(0.0, min(1.0, 1 - remaining / self.duration_seconds))
            self.overlay.progress = self.to_progress
            t = 1.0
        else:
            t = max(0.0, min(1.0, (now - self.animation_start) / 0.32))
            self.overlay.progress = self.from_progress + (self.to_progress - self.from_progress) * (1 - (1 - t) ** 3)
            self.overlay.pulse = sin(t * pi)
        if t >= 1 and self.to_progress >= 1 and not self.overlay.complete:
            origin = QPointF(self.overlay.x() + 82, self.overlay.y() + 68)
            self.overlay.complete = True
            self.overlay.setFixedHeight(38)
            self.position()
            self.confetti.origin = origin
            self.celebration_start = now
            self.timer.setInterval(16)
            self.confetti.show()
            self.confetti.raise_()
            self.overlay.raise_()
            self.edit_button.raise_()
        if self.celebration_start is not None:
            self.confetti.elapsed = now - self.celebration_start
            self.confetti.update()
            if self.confetti.elapsed >= 1.8:
                self.finish_animation()
        elif t >= 1 and not timed:
            self.timer.stop()
        self.overlay.update()

    def finish_animation(self) -> None:
        self.timer.stop()
        self.celebration_start = None
        self.confetti.hide()
        self.overlay.progress = self.to_progress
        self.overlay.pulse = 0
        if self.to_progress >= 1:
            self.overlay.complete = True
            self.overlay.setFixedHeight(38)
        self.overlay.update()

    def configure(self, mode: str, amount: int) -> None:
        previous_mode = self.overlay.mode
        self.timer.stop()
        self.confetti.hide()
        self.celebration_start = None
        self.overlay.complete = False
        self.overlay.pulse = 0
        self.overlay.setFixedHeight(178)
        self.overlay.mode = mode
        self.animation_start = monotonic()
        if mode == "timer":
            minutes = max(1, min(1000, amount))
            self.duration_seconds = minutes * 60
            self.deadline = monotonic() + self.duration_seconds
            self.overlay.seconds_remaining = self.duration_seconds
            self.from_progress = self.to_progress = self.overlay.progress = 0.0
            self.timer.setInterval(250)
            self.timer.start()
            set_setting("review_burst_minutes", minutes)
        else:
            if previous_mode == "timer":
                self.overlay.count = 0
            remaining = max(0, min(1000, amount))
            self.overlay.goal = self.overlay.count + remaining
            self.to_progress = self.overlay.count / self.overlay.goal if self.overlay.goal else 1.0
            self.from_progress = self.overlay.progress = self.to_progress
            if remaining:
                set_setting("review_burst_goal", remaining)
            else:
                self.timer.setInterval(16)
                self.timer.start()
        set_setting("review_burst_mode", mode)
        self.position()
        self.overlay.update()
        self.edit_button.raise_()

    def open_editor(self, *_args: Any) -> None:
        timed = self.overlay.mode == "timer"
        was_complete = self.overlay.complete
        answers = int(get_setting("review_burst_goal") or 10) if timed else max(0, self.overlay.goal - self.overlay.count)
        minutes = max(1, ceil((self.deadline - monotonic()) / 60)) if timed else int(get_setting("review_burst_minutes") or 10)
        dialog = BurstEditDialog(self.mw, self.overlay.mode, answers, minutes)
        initial = dialog.choice.selection()
        if dialog.exec() == QDialog.DialogCode.Accepted and _controller is self:
            selection = dialog.choice.selection()
            if selection != initial or (was_complete and selection[0] == "timer"):
                self.configure(*selection)

    def dispose(self) -> None:
        self.timer.stop()
        gui_hooks.reviewer_did_answer_card.remove(self.answered)
        self.mw.removeEventFilter(self)
        self.overlay.hide()
        self.edit_button.hide()
        self.confetti.hide()
        self.overlay.deleteLater()
        self.edit_button.deleteLater()
        self.confetti.deleteLater()
        self.deleteLater()


class BurstButtonController(QObject):
    """Static affordance only: no timer, collection queries, or answer hook."""
    def __init__(self, mw: Any) -> None:
        super().__init__(mw)
        self.mw = mw
        self.profile_closed = False
        self.button = QPushButton("Start Burst", mw)
        self.button.setObjectName("pocketKnifeStartBurst")
        self.button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.button.setFixedSize(104, 30)
        self.button.setToolTip("Start a review burst with your saved goal")
        self.button.setStyleSheet("""
            QPushButton { color: #b7f9df; background: #19382e;
                border: 1px solid #456b5d; border-radius: 14px;
                font-size: 12px; padding: 3px 10px; }
            QPushButton:hover { background: #24503f; border-color: #77f6ca; }
            QPushButton:pressed { background: #10271f; }
        """)
        self.button.clicked.connect(lambda _checked=False: start_burst())
        self.attachments = (
            (gui_hooks.state_did_change, self.state_changed),
            (gui_hooks.profile_will_close, self.profile_closing),
            (gui_hooks.profile_did_open, self.profile_opened),
        )
        for hook, callback in self.attachments:
            hook.append(callback)
        mw.installEventFilter(self)
        self.refresh()

    def refresh(self) -> None:
        bottom = self.mw.height() - 16
        bottom_web = getattr(self.mw, "bottomWeb", None)
        if bottom_web is not None and bottom_web.isVisible():
            bottom = bottom_web.mapTo(self.mw, bottom_web.rect().topLeft()).y() - 12
        self.button.move(max(0, self.mw.width() - self.button.width() - 16),
                         max(0, bottom - self.button.height()))
        visible = (not self.profile_closed and self.mw.col is not None
                   and self.mw.state == "review" and not is_burst_active())
        self.button.setVisible(visible)
        if visible:
            self.button.raise_()

    def state_changed(self, new_state: str, _old_state: str) -> None:
        if new_state != "review":
            stop_burst()
        self.refresh()

    def profile_closing(self) -> None:
        self.profile_closed = True
        stop_burst()
        self.refresh()

    def profile_opened(self, *_args: Any) -> None:
        self.profile_closed = False
        self.refresh()

    def eventFilter(self, _watched: Any, event: Any) -> bool:
        if event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest):
            self.refresh()
        return False

    def dispose(self) -> None:
        for hook, callback in self.attachments:
            hook.remove(callback)
        self.mw.removeEventFilter(self)
        self.button.hide()
        self.button.deleteLater()
        self.deleteLater()


def is_burst_active() -> bool:
    return _controller is not None


def is_burst_present() -> bool:
    return bool(get_setting("review_burst_present"))


def _sync_actions() -> None:
    for action in _actions:
        action.blockSignals(True)
        action.setChecked(is_burst_present())
        action.blockSignals(False)


def ensure_burst_button(*_args: Any) -> None:
    global _presence
    if is_burst_present() and _presence is None and aqt.mw is not None:
        _presence = BurstButtonController(aqt.mw)


def set_burst_present(present: bool) -> None:
    global _presence
    set_setting("review_burst_present", bool(present))
    if present:
        ensure_burst_button()
    else:
        stop_burst()
        if _presence is not None:
            _presence.dispose()
            _presence = None
    _sync_actions()


def stop_burst(*_args: Any) -> None:
    global _controller
    if _controller is not None:
        _controller.dispose()
        _controller = None
    if _presence is not None:
        _presence.refresh()


def start_burst(goal: int | None = None) -> None:
    global _controller
    if aqt.mw is None or aqt.mw.col is None or aqt.mw.state != "review":
        showInfo("Open a deck in review before starting a burst.")
        return
    if not is_burst_present():
        return
    ensure_burst_button()
    target = max(1, min(1000, int(goal if goal is not None else get_setting("review_burst_goal") or 10)))
    stop_burst()
    set_setting("review_burst_goal", target)
    _controller = BurstController(aqt.mw, target)
    if goal is None and get_setting("review_burst_mode") == "timer":
        _controller.configure("timer", int(get_setting("review_burst_minutes") or 10))
    _presence.refresh()


def open_burst_dialog(*_args: Any) -> None:
    dialog = QDialog(aqt.mw)
    dialog.setWindowTitle("Review Burst · Pocket Knife")
    layout = QVBoxLayout(dialog)
    copy = QLabel("Click Start Burst in the reviewer's bottom-right corner when you want a burst.\n"
                  "Leaving review ends it; returning waits for another click.\n\n"
                  "Choose an answer goal or a focus countdown. Click the number\n"
                  "in the ring to adjust it. Reaching the goal celebrates with confetti.")
    layout.addWidget(copy)
    present = QCheckBox("Show Start Burst button in reviewer")
    present.setChecked(is_burst_present())
    present.toggled.connect(set_burst_present)
    layout.addWidget(present)
    choice = BurstChoice(str(get_setting("review_burst_mode")), int(get_setting("review_burst_goal") or 10),
                         int(get_setting("review_burst_minutes") or 10))
    def save_choice(*_args: Any) -> None:
        mode, amount = choice.selection()
        set_setting("review_burst_mode", mode)
        set_setting("review_burst_minutes" if mode == "timer" else "review_burst_goal", amount)
    choice.mode.currentIndexChanged.connect(save_choice)
    choice.amount.valueChanged.connect(save_choice)
    layout.addWidget(choice)
    if _controller is not None:
        current = clock_text(_controller.overlay.seconds_remaining) if _controller.overlay.mode == "timer" else f"{_controller.overlay.count} / {_controller.overlay.goal}"
        layout.addWidget(QLabel(f"Current burst: {current}"))
    buttons = QHBoxLayout()
    stop = QPushButton("End Current Burst")
    stop.setEnabled(is_burst_active())
    stop.clicked.connect(lambda: (stop_burst(), dialog.accept()))
    buttons.addWidget(stop)
    close = QPushButton("Close")
    close.clicked.connect(dialog.accept)
    buttons.addWidget(close)
    layout.addLayout(buttons)
    dialog.exec()


def add_burst_menu(menu: QMenu, parent: QWidget) -> None:
    action = QAction("Show Review Burst Button", parent)
    action.setCheckable(True)
    action.setChecked(is_burst_present())
    action.triggered.connect(set_burst_present)
    _actions.append(action)
    menu.addAction(action)
    configure = QAction("Review Burst Settings…", parent)
    configure.triggered.connect(open_burst_dialog)
    menu.addAction(configure)
    ensure_burst_button()
