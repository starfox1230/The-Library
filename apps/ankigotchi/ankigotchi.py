from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
import time
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QApplication,
    QBrush,
    QCheckBox,
    QColor,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPainter,
    QPainterPath,
    QPen,
    QPoint,
    QRect,
    QRectF,
    QSize,
    QSizeGrip,
    QSizePolicy,
    QSpinBox,
    QTimer,
    Qt,
    QVBoxLayout,
    QWidget,
)

from .settings import get_setting, set_setting


ADDON_NAME = "Ankigotchi"
GOAL_MODE_TOTAL = "total"
GOAL_MODE_DAY_DONE = "day_done"
CHARACTERS = {
    "moth": {
        "name": "Leaf Moth",
        "folder": "moth",
    },
    "unicorn": {
        "name": "Leafwing Unicorn",
        "folder": "unicorn",
    },
    "puppy_turtle": {
        "name": "Puppy Shellcat",
        "folder": "puppy_turtle",
    },
}
_HOOK_REGISTERED = False
_controller: "AnkigotchiController | None" = None

FRAME_IDLE = 0
FRAME_BLINK = 1
FRAME_HAPPY = 2
FRAME_TALK = 3
FRAME_WALK_LEFT_A = 4
FRAME_WALK_LEFT_B = 5
FRAME_WALK_RIGHT_A = 6
FRAME_WALK_RIGHT_B = 7
FRAME_DRAG_LEFT = 8
FRAME_DRAG_RIGHT = 9
FRAME_CHEER = 10
FRAME_SLEEP = 11


def addon_root() -> Path:
    return Path(__file__).resolve().parent


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_goal_mode(value: Any) -> str:
    return GOAL_MODE_DAY_DONE if str(value or "") == GOAL_MODE_DAY_DONE else GOAL_MODE_TOTAL


def _safe_character(value: Any) -> str:
    key = str(value or "").strip()
    return key if key in CHARACTERS else "moth"


def _event_global_point(event: Any) -> QPoint:
    global_position = getattr(event, "globalPosition", None)
    if callable(global_position):
        try:
            return global_position().toPoint()
        except Exception:
            pass
    global_pos = getattr(event, "globalPos", None)
    if callable(global_pos):
        try:
            return global_pos()
        except Exception:
            pass
    return QPoint(0, 0)


def _available_geometry_for_point(point: QPoint) -> QRect | None:
    screen = None
    try:
        screen = QApplication.screenAt(point)
    except Exception:
        screen = None
    if screen is None:
        try:
            screen = mw.screen()
        except Exception:
            screen = None
    if screen is None:
        try:
            screen = QApplication.primaryScreen()
        except Exception:
            screen = None
    if screen is None:
        return None
    try:
        return screen.availableGeometry()
    except Exception:
        return None


def _clamp_to_available_screen(x: int, y: int, width: int, height: int) -> QPoint:
    geometry = _available_geometry_for_point(QPoint(int(x), int(y)))
    if geometry is None:
        return QPoint(max(0, int(x)), max(0, int(y)))
    left = int(geometry.left())
    top = int(geometry.top())
    right = int(geometry.right()) - max(1, int(width))
    bottom = int(geometry.bottom()) - max(1, int(height))
    return QPoint(max(left, min(int(x), right)), max(top, min(int(y), bottom)))


def _card_interval_is_tomorrow_or_later(card: Any) -> bool:
    card_id = int(getattr(card, "id", 0) or 0)
    if card_id > 0:
        try:
            getter = getattr(mw.col, "get_card", None)
            if callable(getter):
                card = getter(card_id)
            else:
                legacy_getter = getattr(mw.col, "getCard", None)
                if callable(legacy_getter):
                    card = legacy_getter(card_id)
        except Exception:
            pass
    try:
        return int(getattr(card, "ivl", 0) or 0) >= 1
    except Exception:
        return False


@dataclass
class GoalState:
    completed: int
    goal: int
    elapsed_seconds: int
    paused: bool
    mode: str

    @property
    def remaining(self) -> int:
        return max(0, int(self.goal) - int(self.completed))

    @property
    def ratio(self) -> float:
        return max(0.0, min(1.0, float(self.completed) / max(1, float(self.goal))))


class PetSpriteWidget(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap = None
        self._frame_index = FRAME_IDLE
        self.setMinimumSize(170, 170)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_frame(self, pixmap: Any, frame_index: int) -> None:
        self._pixmap = pixmap
        self._frame_index = int(frame_index)
        self.update()

    def paintEvent(self, event: Any) -> None:
        if self._pixmap is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            x = max(0, (self.width() - self._pixmap.width()) // 2)
            y = max(0, (self.height() - self._pixmap.height()) // 2)
            painter.drawPixmap(x, y, self._pixmap)
            painter.end()
            return
        self._paint_vector_pet()

    def _paint_vector_pet(self) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        width = max(1, self.width())
        height = max(1, self.height())
        size = min(width, height)
        origin_x = (width - size) / 2
        origin_y = (height - size) / 2

        def sx(value: float) -> float:
            return origin_x + value * size / 170.0

        def sy(value: float) -> float:
            return origin_y + value * size / 170.0

        frame = self._frame_index
        bob = 4 if frame in {FRAME_WALK_LEFT_B, FRAME_WALK_RIGHT_B, FRAME_CHEER} else 0
        lean = -7 if frame in {FRAME_WALK_LEFT_A, FRAME_DRAG_LEFT} else 7 if frame in {FRAME_WALK_RIGHT_A, FRAME_DRAG_RIGHT} else 0
        sleepy = frame == FRAME_SLEEP
        happy = frame in {FRAME_HAPPY, FRAME_TALK, FRAME_CHEER}
        blink = frame == FRAME_BLINK or sleepy
        painter.translate(lean * size / 170.0, -bob * size / 170.0)

        painter.setPen(QPen(QColor(38, 139, 129), max(2, int(size / 80))))
        painter.setBrush(QBrush(QColor(248, 230, 170, 235)))
        painter.drawEllipse(QRectF(sx(10), sy(54), size * 0.40, size * 0.48))
        painter.drawEllipse(QRectF(sx(92), sy(54), size * 0.40, size * 0.48))
        painter.setPen(QPen(QColor(28, 86, 84), max(2, int(size / 72))))
        painter.setBrush(QBrush(QColor(82, 178, 160)))
        body_path = QPainterPath()
        body_path.addRoundedRect(QRectF(sx(43), sy(36), size * 0.49, size * 0.66), size * 0.16, size * 0.16)
        painter.drawPath(body_path)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 232, 166)))
        star = QPainterPath()
        star.moveTo(sx(85), sy(48))
        star.lineTo(sx(91), sy(58))
        star.lineTo(sx(103), sy(60))
        star.lineTo(sx(94), sy(68))
        star.lineTo(sx(96), sy(80))
        star.lineTo(sx(85), sy(74))
        star.lineTo(sx(74), sy(80))
        star.lineTo(sx(76), sy(68))
        star.lineTo(sx(67), sy(60))
        star.lineTo(sx(79), sy(58))
        star.closeSubpath()
        painter.drawPath(star)
        painter.setBrush(QBrush(QColor(255, 238, 188)))
        painter.setPen(QPen(QColor(190, 150, 61), max(2, int(size / 88))))
        painter.drawRoundedRect(QRectF(sx(53), sy(70), size * 0.38, size * 0.28), size * 0.12, size * 0.12)
        painter.setPen(QPen(QColor(18, 33, 43), max(2, int(size / 85))))
        if blink:
            painter.drawArc(QRectF(sx(67), sy(85), size * 0.10, size * 0.05), 0, 180 * 16)
            painter.drawArc(QRectF(sx(96), sy(85), size * 0.10, size * 0.05), 0, 180 * 16)
        else:
            painter.setBrush(QBrush(QColor(18, 33, 43)))
            painter.drawEllipse(QRectF(sx(68), sy(80), size * 0.08, size * 0.11))
            painter.drawEllipse(QRectF(sx(96), sy(80), size * 0.08, size * 0.11))
            painter.setBrush(QBrush(QColor(255, 255, 255, 210)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(sx(72), sy(83), size * 0.025, size * 0.025))
            painter.drawEllipse(QRectF(sx(100), sy(83), size * 0.025, size * 0.025))
        painter.setPen(QPen(QColor(18, 33, 43), max(2, int(size / 95))))
        painter.drawArc(QRectF(sx(78), sy(94 if not sleepy else 98), size * 0.16, size * 0.10), 180 * 16, 180 * 16)
        painter.setPen(QPen(QColor(18, 60, 55), max(2, int(size / 90))))
        painter.drawLine(int(sx(70)), int(sy(42)), int(sx(56)), int(sy(16)))
        painter.drawLine(int(sx(100)), int(sy(42)), int(sx(114)), int(sy(16)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 217, 120)))
        painter.drawEllipse(QRectF(sx(49), sy(8), size * 0.11, size * 0.11))
        painter.drawEllipse(QRectF(sx(109), sy(8), size * 0.11, size * 0.11))
        painter.setBrush(QBrush(QColor(53, 132, 125)))
        painter.drawEllipse(QRectF(sx(58), sy(126), size * 0.16, size * 0.12))
        painter.drawEllipse(QRectF(sx(95), sy(126), size * 0.16, size * 0.12))
        if frame == FRAME_CHEER:
            painter.setPen(QPen(QColor(255, 217, 120), max(3, int(size / 55))))
            painter.drawLine(int(sx(42)), int(sy(42)), int(sx(26)), int(sy(28)))
            painter.drawLine(int(sx(128)), int(sy(42)), int(sx(144)), int(sy(28)))
        painter.end()


class PetWindow(QWidget):
    def __init__(self, controller: "AnkigotchiController") -> None:
        super().__init__(
            None,
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._controller = controller
        self._dragging = False
        self._drag_offset = QPoint()
        self._last_drag_x = 0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setWindowTitle(ADDON_NAME)
        self.setMinimumSize(190, 190)
        self.resize(240, 230)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.bubble = QLabel("", self)
        self.bubble.setWordWrap(True)
        self.bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bubble.setStyleSheet(
            """
            QLabel {
                color: #eef3ff;
                background: rgba(10, 16, 30, 0.94);
                border: 1px solid rgba(137, 180, 255, 0.28);
                border-radius: 12px;
                padding: 8px 10px;
                font: 800 12px "Segoe UI";
            }
            """
        )
        self.bubble.hide()
        layout.addWidget(self.bubble, 0, Qt.AlignmentFlag.AlignHCenter)
        self.sprite = PetSpriteWidget(self)
        self.sprite.setFixedSize(170, 170)
        self.sprite.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.sprite, 1, Qt.AlignmentFlag.AlignHCenter)

    def set_frame(self, pixmap: Any, frame_index: int) -> None:
        self.sprite.set_frame(pixmap, frame_index)

    def say(self, text: str) -> None:
        self.bubble.setText(str(text))
        self.bubble.adjustSize()
        self.bubble.show()
        self.resize(max(self.width(), self.bubble.width() + 20), self.height())

    def clear_speech(self) -> None:
        self.bubble.hide()
        self.resize(max(190, self.sprite.width() + 20), max(190, self.sprite.height() + 24))

    def contextMenuEvent(self, event: Any) -> None:
        menu = QMenu(self)
        settings_action = menu.addAction("Ankigotchi Settings")
        reset_action = menu.addAction("Reset Session")
        hide_action = menu.addAction("Hide Pet")
        chosen = menu.exec(event.globalPos())
        if chosen is settings_action:
            self._controller.open_settings_dialog()
        elif chosen is reset_action:
            self._controller.reset_session()
        elif chosen is hide_action:
            set_setting("pet_visible", False)
            self.hide()

    def mousePressEvent(self, event: Any) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._dragging = True
        point = _event_global_point(event)
        self._drag_offset = point - self.frameGeometry().topLeft()
        self._last_drag_x = point.x()
        self._controller.set_dragging(True, 0)
        event.accept()

    def mouseMoveEvent(self, event: Any) -> None:
        if not self._dragging:
            return
        point = _event_global_point(event)
        delta_x = point.x() - self._last_drag_x
        self._last_drag_x = point.x()
        self.move(point - self._drag_offset)
        self._controller.set_dragging(True, delta_x)
        event.accept()

    def mouseReleaseEvent(self, event: Any) -> None:
        self._dragging = False
        self._controller.set_dragging(False, 0)
        set_setting("pet_x", self.x())
        set_setting("pet_y", self.y())
        event.accept()


class GoalWindow(QWidget):
    def __init__(self, controller: "AnkigotchiController") -> None:
        super().__init__(
            None,
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._controller = controller
        self._dragging = False
        self._drag_offset = QPoint()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setWindowTitle(f"{ADDON_NAME} Goal")
        self.setMinimumSize(260, 210)
        self.resize(360, 300)
        self.setStyleSheet(
            """
            QWidget#GoalShell {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(5,8,22,245), stop:1 rgba(11,17,36,240));
                border: 1px solid rgba(137, 180, 255, 0.32);
                border-radius: 18px;
                color: #eef3ff;
                font-family: "Segoe UI";
            }
            QLabel#Title { color: #8ea0cc; font-size: 11px; font-weight: 800; letter-spacing: 1px; }
            QLabel#Score { color: #eef3ff; font-size: 28px; font-weight: 900; }
            QLabel#Timer { color: #eef3ff; font-size: 38px; font-weight: 900; }
            QLabel#Muted { color: #8ea0cc; font-size: 11px; font-weight: 800; }
            """
        )
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.shell = QWidget(self)
        self.shell.setObjectName("GoalShell")
        outer.addWidget(self.shell)
        layout = QVBoxLayout(self.shell)
        layout.setContentsMargins(14, 12, 14, 10)
        layout.setSpacing(10)
        header = QHBoxLayout()
        self.title = QLabel("ANKIGOTCHI GOAL")
        self.title.setObjectName("Title")
        header.addWidget(self.title)
        header.addStretch(1)
        close = QLabel("x")
        close.setObjectName("Muted")
        close.mousePressEvent = lambda _event: self.hide_and_remember()
        header.addWidget(close)
        layout.addLayout(header)
        self.score = QLabel("0 / 100")
        self.score.setObjectName("Score")
        layout.addWidget(self.score)
        self.progress = QWidget(self)
        self.progress.setMinimumHeight(10)
        self.progress.setMaximumHeight(10)
        layout.addWidget(self.progress)
        layout.addStretch(1)
        self.timer = QLabel("0.0")
        self.timer.setObjectName("Timer")
        self.timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer)
        self.status = QLabel("RUNNING - MINUTES")
        self.status.setObjectName("Muted")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)
        self.remaining = QLabel("100 LEFT")
        self.remaining.setObjectName("Muted")
        self.remaining.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.remaining)
        grip_row = QHBoxLayout()
        grip_row.addStretch(1)
        grip_row.addWidget(QSizeGrip(self), 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        layout.addLayout(grip_row)

    def hide_and_remember(self) -> None:
        set_setting("goal_window_visible", False)
        self.hide()

    def update_state(self, state: GoalState) -> None:
        self.score.setText(f"{state.completed} / {state.goal}")
        minutes = max(0.0, float(state.elapsed_seconds) / 60.0)
        self.timer.setText(f"{minutes:.1f}" if minutes < 10 else str(int(minutes)))
        self.status.setText(("PAUSED" if state.paused else "RUNNING") + " - MINUTES")
        self.remaining.setText(f"{state.remaining} LEFT")
        fill = max(0, min(100, int(round(state.ratio * 100))))
        color = "#ffd978" if state.paused else "#7fb0ff"
        self.progress.setStyleSheet(
            f"""
            QWidget {{
                border-radius: 5px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:{fill / 100:.3f} #65f0c2,
                    stop:{fill / 100:.3f} rgba(255,255,255,0.08), stop:1 rgba(255,255,255,0.08));
            }}
            """
        )

    def contextMenuEvent(self, event: Any) -> None:
        menu = QMenu(self)
        settings_action = menu.addAction("Ankigotchi Settings")
        reset_action = menu.addAction("Reset Session")
        chosen = menu.exec(event.globalPos())
        if chosen is settings_action:
            self._controller.open_settings_dialog()
        elif chosen is reset_action:
            self._controller.reset_session()

    def mousePressEvent(self, event: Any) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._dragging = True
        self._drag_offset = _event_global_point(event) - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event: Any) -> None:
        if not self._dragging:
            return
        self.move(_event_global_point(event) - self._drag_offset)
        event.accept()

    def mouseReleaseEvent(self, event: Any) -> None:
        self._dragging = False
        self._controller.remember_goal_geometry()
        event.accept()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._controller.remember_goal_geometry()


class SettingsDialog(QDialog):
    def __init__(self, controller: "AnkigotchiController") -> None:
        super().__init__(mw)
        self._controller = controller
        self.setWindowTitle("Ankigotchi Settings")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.character = QComboBox()
        for key, info in CHARACTERS.items():
            self.character.addItem(str(info["name"]), key)
        character_index = self.character.findData(_safe_character(get_setting("character")))
        self.character.setCurrentIndex(max(0, character_index))
        form.addRow("Character:", self.character)
        self.preview = PetSpriteWidget(self)
        self.preview.setFixedSize(126, 126)
        preview_row = QHBoxLayout()
        preview_row.addStretch(1)
        preview_row.addWidget(self.preview)
        preview_row.addStretch(1)
        layout.addLayout(preview_row)
        self.goal = QSpinBox()
        self.goal.setRange(1, 10000)
        self.goal.setValue(_safe_int(get_setting("goal_count"), 100))
        form.addRow("Goal cards:", self.goal)
        self.mode = QComboBox()
        self.mode.addItem("Total answered cards", GOAL_MODE_TOTAL)
        self.mode.addItem("Done for today only", GOAL_MODE_DAY_DONE)
        index = self.mode.findData(_safe_goal_mode(get_setting("goal_mode")))
        self.mode.setCurrentIndex(max(0, index))
        form.addRow("Count:", self.mode)
        self.paused = QCheckBox("Pause timer")
        self.paused.setChecked(bool(get_setting("paused")))
        form.addRow("", self.paused)
        self.pet_visible = QCheckBox("Show pet")
        self.pet_visible.setChecked(bool(get_setting("pet_visible")))
        form.addRow("", self.pet_visible)
        self.goal_visible = QCheckBox("Show goal window")
        self.goal_visible.setChecked(bool(get_setting("goal_window_visible")))
        form.addRow("", self.goal_visible)
        layout.addLayout(form)
        self.character.currentIndexChanged.connect(self._refresh_preview)
        self._refresh_preview()
        buttons = QHBoxLayout()
        save = QLabel("Save")
        save.setStyleSheet("QLabel { padding: 7px 14px; background: #7fb0ff; color: #06101e; border-radius: 8px; font-weight: 900; }")
        save.mousePressEvent = lambda _event: self._save()
        reset = QLabel("Reset Session")
        reset.setStyleSheet("QLabel { padding: 7px 14px; background: rgba(255,255,255,0.08); border-radius: 8px; font-weight: 800; }")
        reset.mousePressEvent = lambda _event: self._reset()
        buttons.addWidget(reset)
        buttons.addStretch(1)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def _save(self) -> None:
        set_setting("goal_count", self.goal.value())
        set_setting("goal_mode", self.mode.currentData())
        set_setting("character", _safe_character(self.character.currentData()))
        self._controller.set_paused(self.paused.isChecked())
        set_setting("pet_visible", self.pet_visible.isChecked())
        set_setting("goal_window_visible", self.goal_visible.isChecked())
        self._controller.reload_character()
        self._controller.sync_visibility()
        self._controller.push_state()
        self.accept()

    def _reset(self) -> None:
        self._controller.reset_session()
        self.accept()

    def _refresh_preview(self) -> None:
        pixmap = self._controller.preview_pixmap(_safe_character(self.character.currentData()))
        self.preview.set_frame(pixmap, FRAME_IDLE)


class AnkigotchiController:
    def __init__(self) -> None:
        self._pet_window: PetWindow | None = None
        self._goal_window: GoalWindow | None = None
        self._frames: list[Any] = []
        self._loaded_character = ""
        self._current_frame = FRAME_IDLE
        self._dragging = False
        self._drag_direction = 0
        self._walk_step = 0
        self._answer_events: list[dict[str, Any]] = []
        self._started_at_monotonic = time.monotonic()
        self._last_announced_decade = -1
        self._menu_registered = False
        self._animation_timer = QTimer(mw)
        self._animation_timer.setInterval(480)
        self._animation_timer.timeout.connect(self._animate)
        self._tick_timer = QTimer(mw)
        self._tick_timer.setInterval(10000)
        self._tick_timer.timeout.connect(self.push_state)
        self._speech_timer = QTimer(mw)
        self._speech_timer.setSingleShot(True)
        self._speech_timer.timeout.connect(self._clear_speech)

    def install(self) -> None:
        gui_hooks.main_window_did_init.append(self._register_menu)
        reviewer_answer = getattr(gui_hooks, "reviewer_did_answer_card", None)
        if reviewer_answer is not None:
            reviewer_answer.append(self.on_reviewer_did_answer_card)
        state_undo = getattr(gui_hooks, "state_did_undo", None)
        if state_undo is not None:
            state_undo.append(self.on_state_did_undo)
        QTimer.singleShot(1000, self.sync_visibility)

    def _register_menu(self) -> None:
        if self._menu_registered:
            return
        menu = QMenu(ADDON_NAME, mw)
        mw.form.menuTools.addMenu(menu)
        show_pet = QAction("Show Ankigotchi Pet", mw)
        show_pet.triggered.connect(lambda *_args: self.show_pet())
        menu.addAction(show_pet)
        show_goal = QAction("Show Frameless Goal Window", mw)
        show_goal.triggered.connect(lambda *_args: self.show_goal_window())
        menu.addAction(show_goal)
        settings = QAction("Ankigotchi Settings", mw)
        settings.triggered.connect(lambda *_args: self.open_settings_dialog())
        menu.addAction(settings)
        reset = QAction("Reset Ankigotchi Session", mw)
        reset.triggered.connect(lambda *_args: self.reset_session())
        menu.addAction(reset)
        self._menu_registered = True

    def sync_visibility(self) -> None:
        if bool(get_setting("pet_visible")):
            self.show_pet()
        elif self._pet_window is not None:
            self._pet_window.hide()
        if bool(get_setting("goal_window_visible")):
            self.show_goal_window()
        elif self._goal_window is not None:
            self._goal_window.hide()
        if not self.is_paused():
            self._tick_timer.start()
        self._animation_timer.start()
        self.push_state()

    def show_pet(self) -> None:
        set_setting("pet_visible", True)
        self._ensure_pet_window()
        if self._pet_window is None:
            return
        x = _safe_int(get_setting("pet_x"), 90)
        y = _safe_int(get_setting("pet_y"), 130)
        point = _clamp_to_available_screen(x, y, self._pet_window.width(), self._pet_window.height())
        self._pet_window.move(point)
        set_setting("pet_x", point.x())
        set_setting("pet_y", point.y())
        self._set_frame(FRAME_IDLE)
        self._pet_window.show()
        self._pet_window.raise_()
        self._animation_timer.start()

    def show_goal_window(self) -> None:
        set_setting("goal_window_visible", True)
        self._ensure_goal_window()
        if self._goal_window is None:
            return
        width = max(260, _safe_int(get_setting("goal_width"), 360))
        height = max(210, _safe_int(get_setting("goal_height"), 300))
        x = _safe_int(get_setting("goal_x"), 360)
        y = _safe_int(get_setting("goal_y"), 130)
        point = _clamp_to_available_screen(x, y, width, height)
        self._goal_window.resize(width, height)
        self._goal_window.move(point)
        self._goal_window.show()
        self._goal_window.raise_()
        self.push_state()

    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def remember_goal_geometry(self) -> None:
        if self._goal_window is None:
            return
        set_setting("goal_x", self._goal_window.x())
        set_setting("goal_y", self._goal_window.y())
        set_setting("goal_width", self._goal_window.width())
        set_setting("goal_height", self._goal_window.height())

    def reset_session(self) -> None:
        self._answer_events = []
        set_setting("elapsed_seconds", 0.0)
        self._started_at_monotonic = time.monotonic()
        self._last_announced_decade = -1
        self.say("Fresh start.")
        self.push_state()

    def set_paused(self, paused: bool) -> None:
        if bool(paused) == self.is_paused():
            return
        if paused:
            set_setting("elapsed_seconds", self.elapsed_seconds())
            set_setting("paused", True)
            self._tick_timer.stop()
        else:
            self._started_at_monotonic = time.monotonic()
            set_setting("paused", False)
            self._tick_timer.start()
        self.push_state()

    def is_paused(self) -> bool:
        return bool(get_setting("paused"))

    def elapsed_seconds(self) -> float:
        elapsed = _safe_float(get_setting("elapsed_seconds"), 0.0)
        if self.is_paused():
            return elapsed
        return elapsed + max(0.0, time.monotonic() - self._started_at_monotonic)

    def state(self) -> GoalState:
        goal = max(1, _safe_int(get_setting("goal_count"), 100))
        completed = min(goal, sum(1 for event in self._answer_events if bool(event.get("counted"))))
        return GoalState(
            completed=completed,
            goal=goal,
            elapsed_seconds=int(self.elapsed_seconds()),
            paused=self.is_paused(),
            mode=_safe_goal_mode(get_setting("goal_mode")),
        )

    def push_state(self) -> None:
        if self._goal_window is not None:
            self._goal_window.update_state(self.state())

    def on_reviewer_did_answer_card(self, reviewer: Any, card: Any, ease: int) -> None:
        del reviewer
        del ease
        mode = _safe_goal_mode(get_setting("goal_mode"))
        counted = mode == GOAL_MODE_TOTAL or _card_interval_is_tomorrow_or_later(card)
        self._answer_events.append({"card_id": int(getattr(card, "id", 0) or 0), "counted": counted})
        state = self.state()
        self.push_state()
        if state.completed > 0 and state.completed % 10 == 0:
            decade = state.completed // 10
            if decade != self._last_announced_decade:
                self._last_announced_decade = decade
                self._set_frame(FRAME_CHEER)
                self.say(self._milestone_message(state))
        elif random.random() < 0.08:
            self._set_frame(FRAME_HAPPY)

    def on_state_did_undo(self, changes: Any) -> None:
        del changes
        if self._answer_events:
            self._answer_events.pop()
        self.push_state()

    def set_dragging(self, dragging: bool, delta_x: int) -> None:
        self._dragging = bool(dragging)
        if abs(int(delta_x)) >= 1:
            self._drag_direction = -1 if int(delta_x) < 0 else 1
        elif not dragging:
            self._drag_direction = 0
        self._animate()

    def say(self, text: str) -> None:
        self.show_pet()
        if self._pet_window is None:
            return
        self._pet_window.say(str(text))
        self._speech_timer.start(5200)

    def _clear_speech(self) -> None:
        if self._pet_window is not None:
            self._pet_window.clear_speech()

    def _milestone_message(self, state: GoalState) -> str:
        if state.remaining <= 0:
            return "Goal reached. Nice work."
        return random.choice(
            [
                f"{state.remaining} to go.",
                f"{state.completed} done. {state.remaining} left.",
                f"Keep going. {state.remaining} left.",
                f"Good pace. {state.remaining} more.",
            ]
        )

    def _ensure_pet_window(self) -> None:
        if self._pet_window is not None:
            return
        self._load_frames()
        self._pet_window = PetWindow(self)

    def _ensure_goal_window(self) -> None:
        if self._goal_window is not None:
            return
        self._goal_window = GoalWindow(self)

    def _load_frames(self) -> None:
        character = _safe_character(get_setting("character"))
        if self._frames and self._loaded_character == character:
            return
        try:
            from aqt.qt import QPixmap
        except Exception:
            return
        self._frames = []
        self._loaded_character = character
        pet_root = self._character_root(character)
        frames = []
        for index in range(12):
            pixmap = QPixmap(str(pet_root / f"frame_{index:02d}.png"))
            if pixmap.isNull():
                frames = []
                break
            frames.append(
                pixmap.scaled(
                    154,
                    154,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self._frames = frames

    def _character_root(self, character: str) -> Path:
        safe_character = _safe_character(character)
        folder = str(CHARACTERS[safe_character]["folder"])
        root = addon_root() / "assets" / "characters" / folder
        if root.exists():
            return root
        return addon_root() / "assets" / "pocket_pet"

    def preview_pixmap(self, character: str) -> Any:
        try:
            from aqt.qt import QPixmap
        except Exception:
            return None
        pixmap = QPixmap(str(self._character_root(character) / "frame_00.png"))
        if pixmap.isNull():
            return None
        return pixmap.scaled(
            112,
            112,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def reload_character(self) -> None:
        self._frames = []
        self._loaded_character = ""
        self._load_frames()
        self._set_frame(FRAME_IDLE)

    def _set_frame(self, frame_index: int) -> None:
        self._ensure_pet_window()
        if self._pet_window is None:
            return
        self._current_frame = max(0, min(11, int(frame_index)))
        pixmap = self._frames[self._current_frame] if self._frames else None
        self._pet_window.set_frame(pixmap, self._current_frame)

    def _animate(self) -> None:
        if self._pet_window is None or not self._pet_window.isVisible():
            return
        if self._dragging:
            self._walk_step = 1 - self._walk_step
            if self._drag_direction < 0:
                self._set_frame(FRAME_WALK_LEFT_A if self._walk_step == 0 else FRAME_WALK_LEFT_B)
            elif self._drag_direction > 0:
                self._set_frame(FRAME_WALK_RIGHT_A if self._walk_step == 0 else FRAME_WALK_RIGHT_B)
            else:
                self._set_frame(FRAME_DRAG_LEFT if self._walk_step == 0 else FRAME_DRAG_RIGHT)
            return
        if self._speech_timer.isActive():
            self._set_frame(FRAME_TALK)
            return
        roll = random.random()
        if roll < 0.08:
            self._set_frame(FRAME_BLINK)
        elif roll < 0.11:
            self._set_frame(FRAME_SLEEP)
        elif roll < 0.16:
            self._set_frame(FRAME_HAPPY)
        else:
            self._set_frame(FRAME_IDLE)


def install() -> None:
    global _HOOK_REGISTERED
    global _controller
    if _HOOK_REGISTERED:
        return
    _controller = AnkigotchiController()
    _controller.install()
    _HOOK_REGISTERED = True
