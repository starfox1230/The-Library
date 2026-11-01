"""Opt-in, in-memory review bursts. Off means no review hooks or timers."""
from __future__ import annotations

from math import cos, pi, sin
from random import Random
from time import monotonic
from typing import Any

import aqt
from aqt import gui_hooks
from aqt.qt import (
    QAction, QColor, QDialog, QEvent, QFont, QHBoxLayout, QLabel, QMenu,
    QObject, QPainter, QPen, QPointF, QPushButton, QRectF, QSpinBox,
    QTimer, Qt, QVBoxLayout, QWidget,
)
from aqt.utils import showInfo

from .settings import get_setting, set_setting


_controller: BurstController | None = None
_actions: list[QAction] = []
COLORS = ("#77f6ca", "#a99aff", "#ffd378", "#ff89bb", "#88d9ff")


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
            painter.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            painter.drawText(QRectF(25, 36, 114, 60), Qt.AlignmentFlag.AlignCenter,
                             str(max(0, self.goal - self.count)))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            painter.setPen(QColor("#a8b9ca"))
            painter.drawText(QRectF(34, 87, 96, 16), Qt.AlignmentFlag.AlignCenter, "TO GO")
        badge = QRectF(6, 4 if self.complete else 147, 152, 29)
        painter.setPen(QPen(QColor("#46695f" if self.complete else "#344558"), 1))
        painter.setBrush(QColor("#142c27" if self.complete else "#172333"))
        painter.drawRoundedRect(badge, 14, 14)
        painter.setPen(QColor("#acffe1" if self.complete else "#eff6ff"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, f"{self.count} / {self.goal}")


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
        self.confetti = ConfettiOverlay(mw)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        self.animation_start = 0.0
        self.from_progress = 0.0
        self.to_progress = 0.0
        self.celebration_start: float | None = None
        self.attachments = (
            (gui_hooks.reviewer_did_answer_card, self.answered),
            (gui_hooks.state_did_change, self.state_changed),
            (gui_hooks.profile_will_close, self.profile_closing),
        )
        for hook, callback in self.attachments:
            hook.append(callback)
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

    def refresh_visibility(self) -> None:
        reviewing = self.mw.state == "review"
        self.position()
        self.overlay.setVisible(reviewing)
        if reviewing:
            self.overlay.raise_()
        else:
            self.finish_animation()

    def state_changed(self, *_args: Any) -> None:
        self.refresh_visibility()

    def eventFilter(self, _watched: Any, event: Any) -> bool:
        if event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest):
            self.position()
        return False

    def answered(self, reviewer: Any, _card: Any, _ease: int) -> None:
        if reviewer is not self.mw.reviewer:
            return
        self.overlay.count += 1
        if self.overlay.complete:
            self.overlay.update()
            return
        self.from_progress = self.overlay.progress
        self.to_progress = min(1, self.overlay.count / self.overlay.goal)
        self.animation_start = monotonic()
        self.timer.start()
        self.overlay.update()

    def tick(self) -> None:
        now = monotonic()
        t = min(1.0, (now - self.animation_start) / 0.32)
        self.overlay.progress = self.from_progress + (self.to_progress - self.from_progress) * (1 - (1 - t) ** 3)
        self.overlay.pulse = sin(t * pi)
        if t >= 1 and self.to_progress >= 1 and not self.overlay.complete:
            origin = QPointF(self.overlay.x() + 82, self.overlay.y() + 68)
            self.overlay.complete = True
            self.overlay.setFixedHeight(38)
            self.position()
            self.confetti.origin = origin
            self.celebration_start = now
            self.confetti.show()
            self.confetti.raise_()
            self.overlay.raise_()
        if self.celebration_start is not None:
            self.confetti.elapsed = now - self.celebration_start
            self.confetti.update()
            if self.confetti.elapsed >= 1.8:
                self.finish_animation()
        elif t >= 1:
            self.timer.stop()
        self.overlay.update()

    def finish_animation(self) -> None:
        self.timer.stop()
        self.celebration_start = None
        self.confetti.hide()
        self.overlay.progress = self.to_progress
        self.overlay.pulse = 0
        # Leaving the reviewer during the final animation still completes the
        # goal; returning must not replay the celebration.
        if self.overlay.count >= self.overlay.goal:
            self.overlay.complete = True
            self.overlay.setFixedHeight(38)
        self.overlay.update()

    def profile_closing(self) -> None:
        stop_burst(_profile_closing=True)

    def dispose(self, profile_closing: bool = False) -> None:
        self.timer.stop()
        for hook, callback in self.attachments:
            if profile_closing and hook is gui_hooks.profile_will_close:
                # Anki iterates the live hook list. Removing the executing hook
                # here would skip the next add-on's profile-close callback.
                QTimer.singleShot(0, lambda h=hook, cb=callback: h.remove(cb))
            else:
                hook.remove(callback)
        self.mw.removeEventFilter(self)
        self.overlay.hide()
        self.confetti.hide()
        self.overlay.deleteLater()
        self.confetti.deleteLater()
        self.deleteLater()


def is_burst_active() -> bool:
    return _controller is not None


def _sync_actions() -> None:
    for action in _actions:
        action.blockSignals(True)
        action.setChecked(is_burst_active())
        action.blockSignals(False)


def stop_burst(*_args: Any, _profile_closing: bool = False) -> None:
    global _controller
    if _controller is not None:
        _controller.dispose(_profile_closing)
        _controller = None
    _sync_actions()


def start_burst(goal: int | None = None) -> None:
    global _controller
    if aqt.mw is None or aqt.mw.col is None:
        showInfo("Open an Anki profile before starting a review burst.")
        _sync_actions()
        return
    target = max(1, min(1000, int(goal if goal is not None else get_setting("review_burst_goal") or 10)))
    stop_burst()
    set_setting("review_burst_goal", target)
    _controller = BurstController(aqt.mw, target)
    _sync_actions()


def open_burst_dialog(*_args: Any) -> None:
    dialog = QDialog(aqt.mw)
    dialog.setWindowTitle("Review Burst · Pocket Knife")
    layout = QVBoxLayout(dialog)
    copy = QLabel("One small burst. Keep going if you feel like it.\n\n"
                  "Every answer counts, including Again. At your goal, the ring\n"
                  "erupts into confetti and leaves a counter that keeps climbing.\n"
                  "Off removes all burst review hooks and stops its animations.")
    layout.addWidget(copy)
    row = QHBoxLayout()
    row.addWidget(QLabel("Answers per burst"))
    goal = QSpinBox()
    goal.setRange(1, 1000)
    goal.setValue(max(1, min(1000, int(get_setting("review_burst_goal") or 10))))
    row.addWidget(goal)
    layout.addLayout(row)
    if _controller is not None:
        layout.addWidget(QLabel(f"Current burst: {_controller.overlay.count} / {_controller.overlay.goal}"))
    buttons = QHBoxLayout()
    start = QPushButton("Start New Burst")
    start.setDefault(True)
    start.clicked.connect(lambda: (start_burst(goal.value()), dialog.accept()))
    buttons.addWidget(start)
    stop = QPushButton("Turn Off")
    stop.setEnabled(is_burst_active())
    stop.clicked.connect(lambda: (stop_burst(), dialog.accept()))
    buttons.addWidget(stop)
    cancel = QPushButton("Close")
    cancel.clicked.connect(dialog.reject)
    buttons.addWidget(cancel)
    layout.addLayout(buttons)
    dialog.exec()


def add_burst_menu(menu: QMenu, parent: QWidget) -> None:
    action = QAction("Review Burst On", parent)
    action.setCheckable(True)
    action.setChecked(is_burst_active())
    action.triggered.connect(lambda checked: start_burst() if checked else stop_burst())
    _actions.append(action)
    menu.addAction(action)
    configure = QAction("Start / Configure Review Burst…", parent)
    configure.triggered.connect(open_burst_dialog)
    menu.addAction(configure)
