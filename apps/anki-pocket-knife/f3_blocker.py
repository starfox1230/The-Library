from __future__ import annotations

import json

from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QApplication,
    QEvent,
    QKeyEvent,
    QKeySequence,
    QObject,
    Qt,
    QTimer,
    QWidget,
)

from .settings import get_setting, set_setting


F3_BLOCK_SETTING = "disable_default_f3_shortcut"
_ALLOW_F3_PROPERTY = "_anki_pocket_knife_allow_f3"
_BLOCKED_F3_PROPERTY = "_anki_pocket_knife_blocked_f3"
_SAVED_SHORTCUTS_PROPERTY = "_anki_pocket_knife_saved_shortcuts"
_HOOK_REGISTERED = False
_EVENT_FILTER: "_F3RefreshEventFilter | None" = None


def is_default_f3_shortcut_disabled() -> bool:
    return bool(get_setting(F3_BLOCK_SETTING))


def set_default_f3_shortcut_disabled(disabled: bool) -> bool:
    value = bool(set_setting(F3_BLOCK_SETTING, bool(disabled)))
    refresh_f3_blocking()
    return value


def allow_action_to_keep_f3(action: QAction) -> None:
    try:
        action.setProperty(_ALLOW_F3_PROPERTY, True)
    except Exception:
        return


def _portable_shortcut_text(sequence: QKeySequence) -> str:
    try:
        return sequence.toString(QKeySequence.SequenceFormat.PortableText)
    except Exception:
        return sequence.toString()


def _load_saved_shortcut_texts(action: QAction) -> list[str]:
    raw = action.property(_SAVED_SHORTCUTS_PROPERTY)
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item or "").strip()]
    if isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
        except Exception:
            return []
        if isinstance(data, list):
            return [str(item) for item in data if str(item or "").strip()]
    return []


def _save_shortcut_texts(action: QAction, shortcuts: list[str]) -> None:
    try:
        action.setProperty(_SAVED_SHORTCUTS_PROPERTY, json.dumps(shortcuts))
    except Exception:
        pass


def _current_shortcut_texts(action: QAction) -> list[str]:
    shortcuts_fn = getattr(action, "shortcuts", None)
    if callable(shortcuts_fn):
        try:
            sequences = list(shortcuts_fn())
        except Exception:
            sequences = []
        texts = [_portable_shortcut_text(sequence) for sequence in sequences]
        kept = [text for text in texts if text.strip()]
        if kept:
            return kept

    shortcut_fn = getattr(action, "shortcut", None)
    if callable(shortcut_fn):
        try:
            shortcut = shortcut_fn()
        except Exception:
            shortcut = None
        if shortcut is not None:
            text = _portable_shortcut_text(shortcut)
            if text.strip():
                return [text]
    return []


def _has_plain_f3(shortcut_texts: list[str]) -> bool:
    return any(text.strip().casefold() == "f3" for text in shortcut_texts)


def _all_actions() -> list[QAction]:
    app = QApplication.instance()
    if app is None:
        return []

    actions: list[QAction] = []
    seen: set[int] = set()

    roots: list[QObject] = []
    try:
        roots.extend(app.topLevelWidgets())
    except Exception:
        pass
    if mw is not None:
        roots.append(mw)

    for root in roots:
        if root is None:
            continue
        try:
            candidates = [root, *root.findChildren(QAction)]
        except Exception:
            candidates = []
        for candidate in candidates:
            if not isinstance(candidate, QAction):
                continue
            ident = id(candidate)
            if ident in seen:
                continue
            seen.add(ident)
            actions.append(candidate)
    return actions


def _set_action_shortcuts(action: QAction, shortcut_texts: list[str]) -> None:
    sequences = [QKeySequence(text) for text in shortcut_texts if str(text or "").strip()]
    try:
        action.setShortcuts(sequences)
    except Exception:
        if sequences:
            try:
                action.setShortcut(sequences[0])
            except Exception:
                return
        else:
            try:
                action.setShortcut(QKeySequence())
            except Exception:
                return


def _restore_action_shortcuts(action: QAction) -> None:
    saved = _load_saved_shortcut_texts(action)
    if not saved:
        return
    try:
        action.setShortcuts([QKeySequence(text) for text in saved])
    except Exception:
        if saved:
            try:
                action.setShortcut(QKeySequence(saved[0]))
            except Exception:
                return
    try:
        action.setProperty(_BLOCKED_F3_PROPERTY, False)
    except Exception:
        pass


def refresh_f3_blocking() -> None:
    disable_f3 = is_default_f3_shortcut_disabled()
    for action in _all_actions():
        try:
            if bool(action.property(_ALLOW_F3_PROPERTY)):
                continue
        except Exception:
            pass

        current_shortcuts = _current_shortcut_texts(action)
        previously_blocked = False
        try:
            previously_blocked = bool(action.property(_BLOCKED_F3_PROPERTY))
        except Exception:
            previously_blocked = False

        if disable_f3:
            if _has_plain_f3(current_shortcuts):
                if not _load_saved_shortcut_texts(action):
                    _save_shortcut_texts(action, current_shortcuts)
                _set_action_shortcuts(
                    action,
                    [text for text in current_shortcuts if text.strip().casefold() != "f3"],
                )
                try:
                    action.setProperty(_BLOCKED_F3_PROPERTY, True)
                except Exception:
                    pass
            continue

        if previously_blocked:
            _restore_action_shortcuts(action)


def _is_plain_f3_key_event(event: QEvent) -> bool:
    if not isinstance(event, QKeyEvent):
        return False
    try:
        if event.key() != Qt.Key.Key_F3:
            return False
    except Exception:
        return False
    try:
        return event.modifiers() == Qt.KeyboardModifier.NoModifier
    except Exception:
        return False


class _F3RefreshEventFilter(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        event_type = event.type()
        if is_default_f3_shortcut_disabled() and event_type in (
            QEvent.Type.ShortcutOverride,
            QEvent.Type.KeyPress,
            QEvent.Type.KeyRelease,
        ):
            if _is_plain_f3_key_event(event):
                return True

        if not is_default_f3_shortcut_disabled():
            return False

        if event_type not in (QEvent.Type.Show, QEvent.Type.WindowActivate):
            return False
        if not isinstance(watched, QWidget):
            return False
        QTimer.singleShot(0, refresh_f3_blocking)
        return False


def install() -> None:
    global _HOOK_REGISTERED
    global _EVENT_FILTER

    if _HOOK_REGISTERED:
        return

    app = QApplication.instance()
    if app is not None and _EVENT_FILTER is None:
        _EVENT_FILTER = _F3RefreshEventFilter()
        app.installEventFilter(_EVENT_FILTER)

    gui_hooks.main_window_did_init.append(lambda: refresh_f3_blocking())
    _HOOK_REGISTERED = True
