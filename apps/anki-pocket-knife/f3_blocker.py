from __future__ import annotations

from aqt import gui_hooks
from aqt.qt import QApplication, QEvent, QKeyEvent, QObject, Qt

from .settings import get_setting, set_setting


F3_BLOCK_SETTING = "disable_default_f3_shortcut"
CTRL_SHIFT_P_BLOCK_SETTING = "block_ctrl_shift_p_shortcut"
_HOOK_REGISTERED = False
_EVENT_FILTER: "_ShortcutBlockerEventFilter | None" = None
_F3_DISABLED = bool(get_setting(F3_BLOCK_SETTING))
_CTRL_SHIFT_P_BLOCKED = bool(get_setting(CTRL_SHIFT_P_BLOCK_SETTING))


def is_default_f3_shortcut_disabled() -> bool:
    return bool(_F3_DISABLED)


def set_default_f3_shortcut_disabled(disabled: bool) -> bool:
    global _F3_DISABLED
    value = bool(set_setting(F3_BLOCK_SETTING, bool(disabled)))
    _F3_DISABLED = value
    return value


def is_ctrl_shift_p_shortcut_blocked() -> bool:
    return bool(_CTRL_SHIFT_P_BLOCKED)


def set_ctrl_shift_p_shortcut_blocked(blocked: bool) -> bool:
    global _CTRL_SHIFT_P_BLOCKED
    value = bool(set_setting(CTRL_SHIFT_P_BLOCK_SETTING, bool(blocked)))
    _CTRL_SHIFT_P_BLOCKED = value
    return value


def allow_action_to_keep_f3(_action) -> None:
    return


def _is_plain_f3_key_event(event: QEvent) -> bool:
    if event.type() not in (
        QEvent.Type.ShortcutOverride,
        QEvent.Type.KeyPress,
        QEvent.Type.KeyRelease,
    ):
        return False
    if not isinstance(event, QKeyEvent):
        return False
    try:
        return (
            event.key() == Qt.Key.Key_F3
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
        )
    except Exception:
        return False


def _is_ctrl_shift_p_key_event(event: QEvent) -> bool:
    if event.type() not in (
        QEvent.Type.ShortcutOverride,
        QEvent.Type.KeyPress,
        QEvent.Type.KeyRelease,
    ):
        return False
    if not isinstance(event, QKeyEvent):
        return False

    try:
        modifiers = event.modifiers()
        wanted_modifiers = (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        )
        return event.key() == Qt.Key.Key_P and modifiers == wanted_modifiers
    except Exception:
        return False


class _ShortcutBlockerEventFilter(QObject):
    def eventFilter(self, _watched: QObject, event: QEvent) -> bool:
        if _F3_DISABLED and _is_plain_f3_key_event(event):
            return True
        if _CTRL_SHIFT_P_BLOCKED and _is_ctrl_shift_p_key_event(event):
            return True
        return False


def _ensure_event_filter() -> None:
    global _EVENT_FILTER

    app = QApplication.instance()
    if app is None or _EVENT_FILTER is not None:
        return

    _EVENT_FILTER = _ShortcutBlockerEventFilter()
    app.installEventFilter(_EVENT_FILTER)


def install() -> None:
    global _HOOK_REGISTERED

    if _HOOK_REGISTERED:
        return

    _ensure_event_filter()
    gui_hooks.main_window_did_init.append(lambda: _ensure_event_filter())
    _HOOK_REGISTERED = True
