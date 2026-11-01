"""A quiet reviewer start button with opt-in, in-memory review bursts."""
from __future__ import annotations

from math import cos, pi, sin
from random import Random
from time import monotonic
from typing import Any

import aqt
from aqt import gui_hooks
from aqt.qt import (
    QAction, QCheckBox, QColor, QDialog, QEvent, QFont, QHBoxLayout, QLabel, QMenu,
    QObject, QPainter, QPen, QPointF, QPushButton, QRectF, QSpinBox,
    QTimer, Qt, QVBoxLayout, QWidget,
)
from aqt.utils import showInfo

from .settings import get_setting, set_setting


_controller: BurstController | None = None
_actions: list[QAction] = []
_presence: BurstButtonController | None = None
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

    def refresh_visibility(self) -> None:
        reviewing = self.mw.state == "review"
        self.position()
        self.overlay.setVisible(reviewing)
        if reviewing:
            self.overlay.raise_()
        else:
            self.finish_animation()

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
        if self.overlay.count >= self.overlay.goal:
            self.overlay.complete = True
            self.overlay.setFixedHeight(38)
        self.overlay.update()

    def dispose(self) -> None:
        self.timer.stop()
        gui_hooks.reviewer_did_answer_card.remove(self.answered)
        self.mw.removeEventFilter(self)
        self.overlay.hide()
        self.confetti.hide()
        self.overlay.deleteLater()
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
    _presence.refresh()


def open_burst_dialog(*_args: Any) -> None:
    dialog = QDialog(aqt.mw)
    dialog.setWindowTitle("Review Burst · Pocket Knife")
    layout = QVBoxLayout(dialog)
    copy = QLabel("Click Start Burst in the reviewer's bottom-right corner when you want a burst.\n"
                  "Leaving review ends it; returning waits for another click.\n\n"
                  "Every answer counts, including Again. At your goal, the ring\n"
                  "erupts into confetti and leaves a counter that keeps climbing.")
    layout.addWidget(copy)
    present = QCheckBox("Show Start Burst button in reviewer")
    present.setChecked(is_burst_present())
    present.toggled.connect(set_burst_present)
    layout.addWidget(present)
    row = QHBoxLayout()
    row.addWidget(QLabel("Answers per burst"))
    goal = QSpinBox()
    goal.setRange(1, 1000)
    goal.setValue(max(1, min(1000, int(get_setting("review_burst_goal") or 10))))
    goal.valueChanged.connect(lambda value: set_setting("review_burst_goal", value))
    row.addWidget(goal)
    layout.addLayout(row)
    if _controller is not None:
        layout.addWidget(QLabel(f"Current burst: {_controller.overlay.count} / {_controller.overlay.goal}"))
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
