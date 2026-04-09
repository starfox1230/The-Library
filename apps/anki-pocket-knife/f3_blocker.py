from __future__ import annotations

from aqt import gui_hooks
from aqt.qt import QApplication, QEvent, QKeyEvent, QObject, Qt

from .settings import get_setting, set_setting


F3_BLOCK_SETTING = "disable_default_f3_shortcut"
_HOOK_REGISTERED = False
_EVENT_FILTER: "_F3EventFilter | None" = None
_F3_DISABLED = bool(get_setting(F3_BLOCK_SETTING))


def is_default_f3_shortcut_disabled() -> bool:
    return bool(_F3_DISABLED)


def set_default_f3_shortcut_disabled(disabled: bool) -> bool:
    global _F3_DISABLED
    value = bool(set_setting(F3_BLOCK_SETTING, bool(disabled)))
    _F3_DISABLED = value
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


class _F3EventFilter(QObject):
    def eventFilter(self, _watched: QObject, event: QEvent) -> bool:
        if not _F3_DISABLED:
            return False
        return _is_plain_f3_key_event(event)


def _ensure_event_filter() -> None:
    global _EVENT_FILTER

    app = QApplication.instance()
    if app is None or _EVENT_FILTER is not None:
        return

    _EVENT_FILTER = _F3EventFilter()
    app.installEventFilter(_EVENT_FILTER)


def install() -> None:
    global _HOOK_REGISTERED

    if _HOOK_REGISTERED:
        return

    _ensure_event_filter()
    gui_hooks.main_window_did_init.append(lambda: _ensure_event_filter())
    _HOOK_REGISTERED = True
