from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QCursor,
    QDateTime,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    Qt,
    QTimer,
    QVBoxLayout,
    QWidget,
)

from .settings import get_setting, set_setting


ENABLED_SETTING = "floating_card_tracker_enabled"
START_MS_SETTING = "floating_card_tracker_start_ms"
POS_X_SETTING = "floating_card_tracker_x"
POS_Y_SETTING = "floating_card_tracker_y"
WIDTH_SETTING = "floating_card_tracker_width"
NIGHT_BACKGROUND_SETTING = "floating_card_tracker_night_background"
BASE_WIDTH = 190
BASE_HEIGHT = 188
MIN_WIDTH = 155
MAX_WIDTH = 420
_HOOK_REGISTERED = False
_WIDGET: "FloatingCardTracker | None" = None


@dataclass(frozen=True)
class CardTrackerStats:
    total: int = 0
    again: int = 0
    hard: int = 0
    good: int = 0
    easy: int = 0
    unique_cards: int = 0
    elapsed_seconds: float = 0.0

    @property
    def correct(self) -> int:
        return self.hard + self.good + self.easy

    @property
    def cards_per_minute(self) -> float:
        elapsed_minutes = max(self.elapsed_seconds / 60.0, 1.0 / 60.0)
        return self.total / elapsed_minutes

    @property
    def seconds_per_card(self) -> float:
        if self.total <= 0:
            return 0.0
        return self.elapsed_seconds / float(self.total)


def is_floating_card_tracker_enabled() -> bool:
    return bool(get_setting(ENABLED_SETTING))


def set_floating_card_tracker_enabled(enabled: bool) -> bool:
    value = bool(set_setting(ENABLED_SETTING, bool(enabled)))
    if value:
        ensure_tracker_visible()
    else:
        hide_tracker()
    return value


def is_tracker_night_background_enabled() -> bool:
    return bool(get_setting(NIGHT_BACKGROUND_SETTING))


def set_tracker_night_background_enabled(enabled: bool) -> bool:
    value = bool(set_setting(NIGHT_BACKGROUND_SETTING, bool(enabled)))
    if _WIDGET is not None:
        _WIDGET.apply_visual_style()
    return value


def tracker_start_ms() -> int:
    value = int(get_setting(START_MS_SETTING) or 0)
    if value <= 0:
        value = int(time.time() * 1000)
        set_setting(START_MS_SETTING, value)
    return value


def set_tracker_start_ms(value: int) -> int:
    normalized = max(0, int(value))
    set_setting(START_MS_SETTING, normalized)
    refresh_tracker()
    return normalized


def reset_tracker_from_now() -> None:
    set_tracker_start_ms(int(time.time() * 1000))


def _qt_window_type(name: str, fallback: Any = None) -> Any:
    window_type = getattr(Qt, "WindowType", None)
    if window_type is not None and hasattr(window_type, name):
        return getattr(window_type, name)
    return getattr(Qt, name, fallback)


def _qt_alignment(name: str, fallback: Any = None) -> Any:
    alignment = getattr(Qt, "AlignmentFlag", None)
    if alignment is not None and hasattr(alignment, name):
        return getattr(alignment, name)
    return getattr(Qt, name, fallback)


def _qt_mouse_button(name: str, fallback: Any) -> Any:
    mouse_button = getattr(Qt, "MouseButton", None)
    if mouse_button is not None and hasattr(mouse_button, name):
        return getattr(mouse_button, name)
    return getattr(Qt, name, fallback)


def _qt_widget_attribute(name: str, fallback: Any = None) -> Any:
    widget_attribute = getattr(Qt, "WidgetAttribute", None)
    if widget_attribute is not None and hasattr(widget_attribute, name):
        return getattr(widget_attribute, name)
    return getattr(Qt, name, fallback)


def _event_global_pos(event: Any) -> Any:
    global_position = getattr(event, "globalPosition", None)
    if callable(global_position):
        position = global_position()
        to_point = getattr(position, "toPoint", None)
        return to_point() if callable(to_point) else position

    global_pos = getattr(event, "globalPos", None)
    if callable(global_pos):
        return global_pos()

    return QCursor.pos()


def _format_start_label(start_ms: int) -> str:
    dt = QDateTime.fromMSecsSinceEpoch(int(start_ms))
    return dt.toString("MMM d, h:mm AP")


def _format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, _seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _load_stats() -> CardTrackerStats:
    start_ms = tracker_start_ms()
    elapsed_seconds = max(0.0, (time.time() * 1000.0 - float(start_ms)) / 1000.0)
    col = getattr(mw, "col", None)
    db = getattr(col, "db", None)
    if db is None:
        return CardTrackerStats(elapsed_seconds=elapsed_seconds)

    try:
        rows = db.all("select cid, ease from revlog where id >= ?", int(start_ms))
    except Exception:
        return CardTrackerStats(elapsed_seconds=elapsed_seconds)

    again = hard = good = easy = 0
    card_ids: set[int] = set()
    for cid, ease in rows:
        try:
            card_ids.add(int(cid))
            ease_int = int(ease)
        except Exception:
            continue
        if ease_int == 1:
            again += 1
        elif ease_int == 2:
            hard += 1
        elif ease_int == 3:
            good += 1
        elif ease_int == 4:
            easy += 1

    return CardTrackerStats(
        total=again + hard + good + easy,
        again=again,
        hard=hard,
        good=good,
        easy=easy,
        unique_cards=len(card_ids),
        elapsed_seconds=elapsed_seconds,
    )


class TrackerStartDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle("Card Tracker Start Time")
        self.setMinimumWidth(360)
        layout = QVBoxLayout(self)
        label = QLabel("Count cards answered since:")
        layout.addWidget(label)
        self.start_edit = QDateTimeEdit(self)
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDisplayFormat("yyyy-MM-dd h:mm AP")
        self.start_edit.setDateTime(QDateTime.fromMSecsSinceEpoch(tracker_start_ms()))
        layout.addWidget(self.start_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_start_ms(self) -> int:
        return int(self.start_edit.dateTime().toMSecsSinceEpoch())


class ResizeHandle(QFrame):
    def __init__(self, owner: "FloatingCardTracker", corner: str) -> None:
        super().__init__(owner)
        self.owner = owner
        self.corner = corner
        self.setObjectName("trackerResizeHandle")
        self.setCursor(owner._resize_cursor(corner))
        self.hide()

    def mousePressEvent(self, event) -> None:
        if event.button() == _qt_mouse_button("LeftButton", None):
            self.owner.start_resize(self.corner, _event_global_pos(event))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self.owner.is_resizing:
            self.owner.update_resize(_event_global_pos(event))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self.owner.is_resizing:
            self.owner.finish_resize()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class FloatingCardTracker(QWidget):
    def __init__(self) -> None:
        super().__init__(None)
        self._drag_start = None
        self._resize_mode = False
        self._resize_corner: str | None = None
        self._resize_origin_pos = None
        self._resize_origin_geometry = None
        self._handles: list[ResizeHandle] = []
        self._build_ui()
        self._apply_window_flags()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(3000)
        self.refresh()

    def _apply_window_flags(self) -> None:
        flags = (
            _qt_window_type("Tool")
            | _qt_window_type("FramelessWindowHint")
            | _qt_window_type("WindowStaysOnTopHint")
        )
        self.setWindowFlags(flags)
        translucent = _qt_widget_attribute("WA_TranslucentBackground")
        if translucent is not None:
            self.setAttribute(translucent, True)

    def _build_ui(self) -> None:
        self.setObjectName("pocketKnifeCardTracker")
        outer = QVBoxLayout(self)
        self._outer_layout = outer

        title_row = QHBoxLayout()
        self.title = QLabel("Pocket Tracker", self)
        self.title.setObjectName("trackerTitle")
        title_row.addWidget(self.title)
        title_row.addStretch(1)
        self.elapsed = QLabel("", self)
        self.elapsed.setObjectName("trackerSubtle")
        title_row.addWidget(self.elapsed)
        outer.addLayout(title_row)

        self.since = QLabel("", self)
        self.since.setObjectName("trackerSince")
        outer.addWidget(self.since)

        total_row = QHBoxLayout()
        self.total = QLabel("0", self)
        self.total.setObjectName("trackerTotal")
        total_row.addWidget(self.total)
        total_copy = QLabel("cards seen", self)
        total_copy.setObjectName("trackerSubtle")
        total_row.addWidget(total_copy)
        total_row.addStretch(1)
        outer.addLayout(total_row)

        grid = QGridLayout()
        self._metric_grid = grid
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)
        self.again = self._metric_chip("Again", "#e05252")
        self.hard = self._metric_chip("Hard", "#f2a23a")
        self.good = self._metric_chip("Good", "#41b36a")
        self.easy = self._metric_chip("Easy", "#4d8dff")
        self._metric_chips = [self.again, self.hard, self.good, self.easy]
        grid.addWidget(self.again, 0, 0)
        grid.addWidget(self.hard, 0, 1)
        grid.addWidget(self.good, 1, 0)
        grid.addWidget(self.easy, 1, 1)
        outer.addLayout(grid)

        self.rate = QLabel("", self)
        self.rate.setObjectName("trackerSubtle")
        outer.addWidget(self.rate)
        self._handles = [
            ResizeHandle(self, "top-left"),
            ResizeHandle(self, "top-right"),
            ResizeHandle(self, "bottom-left"),
            ResizeHandle(self, "bottom-right"),
        ]
        self.set_tracker_width(int(get_setting(WIDTH_SETTING) or BASE_WIDTH), save=False)
        self.apply_visual_style()

    def _metric_chip(self, label: str, color: str) -> QFrame:
        frame = QFrame(self)
        frame.setToolTip(label)
        frame.setProperty("class", "metricChip")
        frame.setStyleSheet(
            f"QFrame {{ background: {color}; border-radius: 7px; }}"
            "QLabel { background: transparent; }"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(0)
        value = QLabel("0", frame)
        value.setProperty("class", "metricValue")
        value.setAlignment(_qt_alignment("AlignCenter"))
        layout.addWidget(value)
        frame.value_label = value
        return frame

    def refresh(self) -> None:
        stats = _load_stats()
        start_ms = tracker_start_ms()
        self.since.setText(f"Since {_format_start_label(start_ms)}")
        self.elapsed.setText(_format_duration(stats.elapsed_seconds))
        self.total.setText(str(stats.total))
        self.again.value_label.setText(str(stats.again))
        self.hard.value_label.setText(str(stats.hard))
        self.good.value_label.setText(str(stats.good))
        self.easy.value_label.setText(str(stats.easy))
        self.rate.setText(
            f"{stats.correct} right / {stats.again} wrong - "
            f"{stats.cards_per_minute:.1f}/min - {stats.seconds_per_card:.0f}s/card"
        )

    @property
    def is_resizing(self) -> bool:
        return self._resize_corner is not None

    def _scale(self) -> float:
        return max(0.74, min(2.21, self.width() / float(BASE_WIDTH)))

    def _scaled(self, value: float) -> int:
        return max(1, int(round(value * self._scale())))

    def _resize_cursor(self, corner: str) -> Any:
        cursor_shape = getattr(Qt, "CursorShape", None)
        if corner in {"top-left", "bottom-right"}:
            name = "SizeFDiagCursor"
        else:
            name = "SizeBDiagCursor"
        if cursor_shape is not None and hasattr(cursor_shape, name):
            return getattr(cursor_shape, name)
        return getattr(Qt, name, QCursor().shape())

    def apply_visual_style(self) -> None:
        scale = self._scale()
        radius = self._scaled(12)
        if is_tracker_night_background_enabled():
            bg = "rgb(31, 34, 39)"
            border = "rgba(255, 255, 255, 55)"
        else:
            bg = "rgba(22, 24, 29, 232)"
            border = "rgba(255, 255, 255, 42)"
        title = "#eaf0ff"
        subtle = "#9aa8bf"
        total = "#ffffff"
        self.setStyleSheet(
            f"""
            QWidget#pocketKnifeCardTracker {{
                background: {bg};
                border: 1px solid {border};
                border-radius: {radius}px;
                color: {total};
                font-family: Segoe UI, Arial, sans-serif;
            }}
            QLabel#trackerTitle {{ font-size: {max(8, int(12 * scale))}px; font-weight: 700; color: {title}; }}
            QLabel#trackerSince {{ font-size: {max(8, int(10 * scale))}px; color: {subtle}; }}
            QLabel#trackerTotal {{ font-size: {max(18, int(28 * scale))}px; font-weight: 800; color: {total}; }}
            QLabel#trackerSubtle {{ font-size: {max(7, int(9 * scale))}px; color: {subtle}; }}
            QLabel.metricValue {{ font-size: {max(13, int(19 * scale))}px; font-weight: 800; color: #ffffff; }}
            QFrame.metricChip {{ border-radius: {self._scaled(7)}px; }}
            QFrame#trackerResizeHandle {{
                background: rgba(255, 255, 255, 220);
                border: 1px solid rgba(25, 35, 52, 150);
                border-radius: {self._scaled(5)}px;
            }}
            """
        )
        self._outer_layout.setContentsMargins(
            self._scaled(12),
            self._scaled(9),
            self._scaled(12),
            self._scaled(9),
        )
        self._outer_layout.setSpacing(self._scaled(7))
        metric_value_height = max(self._scaled(24), int(24 * scale))
        metric_chip_height = metric_value_height + self._scaled(8)
        for chip in getattr(self, "_metric_chips", []):
            chip.setMinimumHeight(metric_chip_height)
            chip.value_label.setMinimumHeight(metric_value_height)
        metric_grid = getattr(self, "_metric_grid", None)
        if metric_grid is not None:
            metric_grid.setVerticalSpacing(self._scaled(6))
            metric_grid.setHorizontalSpacing(self._scaled(6))
            metric_grid.setRowMinimumHeight(0, metric_chip_height)
            metric_grid.setRowMinimumHeight(1, metric_chip_height)
        self._position_resize_handles()

    def set_tracker_width(self, width: int, *, save: bool = True, anchor_corner: str | None = None) -> None:
        old_geometry = self.geometry()
        new_width = max(MIN_WIDTH, min(MAX_WIDTH, int(width)))
        new_height = int(round(new_width * BASE_HEIGHT / BASE_WIDTH))
        if anchor_corner is None:
            self.setFixedSize(new_width, new_height)
        else:
            x = old_geometry.x()
            y = old_geometry.y()
            if "left" in anchor_corner:
                x = old_geometry.right() - new_width + 1
            if "top" in anchor_corner:
                y = old_geometry.bottom() - new_height + 1
            self.setFixedSize(new_width, new_height)
            self.move(x, y)
        if save:
            set_setting(WIDTH_SETTING, int(new_width))
            set_setting(POS_X_SETTING, int(self.x()))
            set_setting(POS_Y_SETTING, int(self.y()))
        self.apply_visual_style()

    def _position_resize_handles(self) -> None:
        if not self._handles:
            return
        size = self._scaled(14)
        positions = {
            "top-left": (2, 2),
            "top-right": (self.width() - size - 2, 2),
            "bottom-left": (2, self.height() - size - 2),
            "bottom-right": (self.width() - size - 2, self.height() - size - 2),
        }
        for handle in self._handles:
            x, y = positions[handle.corner]
            handle.setGeometry(x, y, size, size)
            handle.raise_()

    def set_resize_mode(self, enabled: bool) -> None:
        self._resize_mode = bool(enabled)
        for handle in self._handles:
            handle.setVisible(self._resize_mode)
        self._position_resize_handles()

    def start_resize(self, corner: str, global_pos: Any) -> None:
        self._resize_corner = corner
        self._resize_origin_pos = global_pos
        self._resize_origin_geometry = self.geometry()

    def update_resize(self, global_pos: Any) -> None:
        if self._resize_origin_pos is None or self._resize_origin_geometry is None or self._resize_corner is None:
            return
        delta = global_pos - self._resize_origin_pos
        dx = int(delta.x())
        dy = int(delta.y())
        origin_width = max(1, int(self._resize_origin_geometry.width()))
        origin_height = max(1, int(self._resize_origin_geometry.height()))
        width_delta = dx if "right" in self._resize_corner else -dx
        height_delta = dy if "bottom" in self._resize_corner else -dy
        width_candidate = origin_width + width_delta
        height_candidate = int(round((origin_height + height_delta) * BASE_WIDTH / BASE_HEIGHT))
        if abs(width_delta / origin_width) >= abs(height_delta / origin_height):
            new_width = width_candidate
        else:
            new_width = height_candidate
        self.set_tracker_width(new_width, save=False, anchor_corner=self._resize_corner)

    def finish_resize(self) -> None:
        self._resize_corner = None
        self._resize_origin_pos = None
        self._resize_origin_geometry = None
        set_setting(WIDTH_SETTING, int(self.width()))
        set_setting(POS_X_SETTING, int(self.x()))
        set_setting(POS_Y_SETTING, int(self.y()))

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        reset_action = QAction("Reset From Now", self)
        edit_action = QAction("Edit Start Time...", self)
        resize_action = QAction("Resize", self)
        resize_action.setCheckable(True)
        resize_action.setChecked(self._resize_mode)
        night_action = QAction("Night Mode Background", self)
        night_action.setCheckable(True)
        night_action.setChecked(is_tracker_night_background_enabled())
        refresh_action = QAction("Refresh", self)
        hide_action = QAction("Hide Tracker", self)
        reset_action.triggered.connect(reset_tracker_from_now)
        edit_action.triggered.connect(lambda *_args: open_tracker_start_dialog(self))
        resize_action.triggered.connect(lambda checked: self.set_resize_mode(bool(checked)))
        night_action.triggered.connect(lambda checked: set_tracker_night_background_enabled(bool(checked)))
        refresh_action.triggered.connect(self.refresh)
        hide_action.triggered.connect(lambda *_args: set_floating_card_tracker_enabled(False))
        menu.addAction(reset_action)
        menu.addAction(edit_action)
        menu.addAction(resize_action)
        menu.addAction(night_action)
        menu.addAction(refresh_action)
        menu.addSeparator()
        menu.addAction(hide_action)
        menu.exec(QCursor.pos())

    def mousePressEvent(self, event) -> None:
        if event.button() == _qt_mouse_button("LeftButton", None):
            self._drag_start = _event_global_pos(event) - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_start is not None:
            self.move(_event_global_pos(event) - self._drag_start)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_start is not None:
            self._drag_start = None
            set_setting(POS_X_SETTING, int(self.x()))
            set_setting(POS_Y_SETTING, int(self.y()))
            event.accept()
            return
        super().mouseReleaseEvent(event)


def open_tracker_start_dialog(parent: QWidget | None = None) -> None:
    dialog = TrackerStartDialog(parent)
    if dialog.exec():
        set_tracker_start_ms(dialog.selected_start_ms())


def ensure_tracker_visible() -> None:
    global _WIDGET
    if not is_floating_card_tracker_enabled():
        return
    if _WIDGET is None:
        _WIDGET = FloatingCardTracker()
        _WIDGET.move(int(get_setting(POS_X_SETTING) or 80), int(get_setting(POS_Y_SETTING) or 120))
    _WIDGET.refresh()
    _WIDGET.show()
    _WIDGET.raise_()


def hide_tracker() -> None:
    if _WIDGET is not None:
        _WIDGET.hide()


def refresh_tracker() -> None:
    if _WIDGET is not None:
        _WIDGET.refresh()


def _refresh_tracker_soon(*_args: Any) -> None:
    refresh_tracker()
    if mw is not None:
        QTimer.singleShot(250, refresh_tracker)


def _on_reviewer_did_answer_card(_reviewer: Any, _card: Any, _ease: int) -> None:
    _refresh_tracker_soon()


def _on_state_did_undo(_changes: Any) -> None:
    _refresh_tracker_soon()


def _on_operation_did_execute(changes: Any, _handler: object | None) -> None:
    if getattr(changes, "card", False) or getattr(changes, "review", False):
        _refresh_tracker_soon()


def _on_main_window_did_init() -> None:
    tracker_start_ms()
    ensure_tracker_visible()


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    reviewer_answer = getattr(gui_hooks, "reviewer_did_answer_card", None)
    if reviewer_answer is not None:
        reviewer_answer.append(_on_reviewer_did_answer_card)
    state_did_undo = getattr(gui_hooks, "state_did_undo", None)
    if state_did_undo is not None:
        state_did_undo.append(_on_state_did_undo)
    operation_did_execute = getattr(gui_hooks, "operation_did_execute", None)
    if operation_did_execute is not None:
        operation_did_execute.append(_on_operation_did_execute)
    gui_hooks.main_window_did_init.append(_on_main_window_did_init)
    _HOOK_REGISTERED = True
