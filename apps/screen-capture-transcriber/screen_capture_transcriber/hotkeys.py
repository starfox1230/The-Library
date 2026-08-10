from __future__ import annotations

import ctypes
from ctypes import wintypes

from PySide6.QtCore import QObject, Signal
from pynput import keyboard, mouse


def control_key_is_down() -> bool:
    return bool(
        hasattr(ctypes, "windll")
        and ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000
    )


def foreground_native_text_input_active() -> bool:
    """Best-effort guard for native editors in the foreground application."""
    if not hasattr(ctypes, "windll"):
        return False

    class GuiThreadInfo(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("hwndActive", wintypes.HWND),
            ("hwndFocus", wintypes.HWND),
            ("hwndCapture", wintypes.HWND),
            ("hwndMenuOwner", wintypes.HWND),
            ("hwndMoveSize", wintypes.HWND),
            ("hwndCaret", wintypes.HWND),
            ("rcCaret", wintypes.RECT),
        ]

    try:
        info = GuiThreadInfo()
        info.cbSize = ctypes.sizeof(GuiThreadInfo)
        if not ctypes.windll.user32.GetGUIThreadInfo(0, ctypes.byref(info)):
            return False
        focused = info.hwndFocus
        if not focused:
            return False
        buffer = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(focused, buffer, len(buffer))
        class_name = buffer.value.casefold()
    except Exception:
        return False
    return any(
        marker in class_name
        for marker in (
            "edit",
            "richedit",
            "scintilla",
            "textbox",
            "textinput",
        )
    )


class GlobalHotkeys(QObject):
    toggle_recording = Signal()
    period_capture = Signal()
    learning_note = Signal()
    error = Signal(str)

    def __init__(self, toggle_hotkey: str) -> None:
        super().__init__()
        self._toggle_hotkey = toggle_hotkey
        self._listener: keyboard.GlobalHotKeys | None = None
        self._period_listener: keyboard.Listener | None = None
        self._period_capture_enabled = False
        self._suppressing_period = False
        self._learning_note_capture_enabled = False
        self._suppressing_backspace = False

    def start(self) -> None:
        try:
            self._listener = keyboard.GlobalHotKeys(
                {
                    self._toggle_hotkey: lambda: self.toggle_recording.emit(),
                }
            )
            self._listener.start()
            period_options: dict[str, object] = {
                "on_press": self._on_period_press,
            }
            if hasattr(ctypes, "windll"):
                period_options["win32_event_filter"] = (
                    self._period_win32_event_filter
                )
            self._period_listener = keyboard.Listener(**period_options)
            self._period_listener.start()
        except Exception as exc:
            self.error.emit(str(exc))

    def set_period_capture_enabled(self, enabled: bool) -> None:
        self._period_capture_enabled = bool(enabled)

    def set_learning_note_capture_enabled(self, enabled: bool) -> None:
        self._learning_note_capture_enabled = bool(enabled)

    def _on_period_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if hasattr(ctypes, "windll"):
            return
        if self._period_capture_enabled and getattr(key, "char", None) == ".":
            self.period_capture.emit()
        elif (
            self._learning_note_capture_enabled
            and key == keyboard.Key.backspace
            and not control_key_is_down()
        ):
            self.learning_note.emit()

    def _period_win32_event_filter(self, message: int, data: object) -> bool:
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        WM_SYSKEYDOWN = 0x0104
        WM_SYSKEYUP = 0x0105
        VK_OEM_PERIOD = 0xBE
        VK_BACK = 0x08
        try:
            virtual_key = int(data.vkCode)
        except (AttributeError, TypeError, ValueError):
            return True
        if virtual_key == VK_BACK:
            if message in (WM_KEYUP, WM_SYSKEYUP) and self._suppressing_backspace:
                self._suppressing_backspace = False
                return False
            if (
                message not in (WM_KEYDOWN, WM_SYSKEYDOWN)
                or not self._learning_note_capture_enabled
                or control_key_is_down()
                or foreground_native_text_input_active()
            ):
                return True
            if not self._suppressing_backspace:
                self._suppressing_backspace = True
                self.learning_note.emit()
            return False
        if virtual_key != VK_OEM_PERIOD:
            return True
        if message in (WM_KEYUP, WM_SYSKEYUP) and self._suppressing_period:
            self._suppressing_period = False
            return False
        if (
            message not in (WM_KEYDOWN, WM_SYSKEYDOWN)
            or not self._period_capture_enabled
        ):
            return True
        if not self._suppressing_period:
            self._suppressing_period = True
            self.period_capture.emit()
        return False

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if self._period_listener is not None:
            self._period_listener.stop()
            self._period_listener = None


def replay_left_click(x: int, y: int) -> None:
    controller = mouse.Controller()
    controller.position = (x, y)
    controller.click(mouse.Button.left, 1)


def move_pointer(x: int, y: int) -> None:
    mouse.Controller().position = (x, y)
