from __future__ import annotations

import ctypes

from PySide6.QtCore import QObject, Signal
from pynput import keyboard, mouse


def control_key_is_down() -> bool:
    return bool(
        hasattr(ctypes, "windll")
        and ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000
    )


class GlobalHotkeys(QObject):
    toggle_recording = Signal()
    add_chapter = Signal()
    anatomy_capture = Signal()
    period_capture = Signal()
    ctrl_click = Signal(int, int)
    error = Signal(str)

    def __init__(
        self,
        toggle_hotkey: str,
        chapter_hotkey: str,
        anatomy_hotkey: str,
    ) -> None:
        super().__init__()
        self._toggle_hotkey = toggle_hotkey
        self._chapter_hotkey = chapter_hotkey
        self._anatomy_hotkey = anatomy_hotkey
        self._listener: keyboard.GlobalHotKeys | None = None
        self._period_listener: keyboard.Listener | None = None
        self._mouse_listener: mouse.Listener | None = None
        self._period_capture_enabled = False
        self._suppressing_period = False
        self._ctrl_click_capture_region: tuple[int, int, int, int] | None = None
        self._suppressing_ctrl_left_click = False

    def start(self) -> None:
        try:
            self._listener = keyboard.GlobalHotKeys(
                {
                    self._toggle_hotkey: lambda: self.toggle_recording.emit(),
                    self._chapter_hotkey: lambda: self.add_chapter.emit(),
                    self._anatomy_hotkey: lambda: self.anatomy_capture.emit(),
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
            mouse_options: dict[str, object] = {"on_click": self._on_click}
            if hasattr(ctypes, "windll"):
                mouse_options["win32_event_filter"] = self._win32_event_filter
            self._mouse_listener = mouse.Listener(**mouse_options)
            self._mouse_listener.start()
        except Exception as exc:
            self.error.emit(str(exc))

    def set_period_capture_enabled(self, enabled: bool) -> None:
        self._period_capture_enabled = bool(enabled)

    def _on_period_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if hasattr(ctypes, "windll") or not self._period_capture_enabled:
            return
        if getattr(key, "char", None) == ".":
            self.period_capture.emit()

    def _period_win32_event_filter(self, message: int, data: object) -> bool:
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        WM_SYSKEYDOWN = 0x0104
        WM_SYSKEYUP = 0x0105
        VK_OEM_PERIOD = 0xBE
        try:
            virtual_key = int(data.vkCode)
        except (AttributeError, TypeError, ValueError):
            return True
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

    def _on_click(
        self,
        x: int,
        y: int,
        button: mouse.Button,
        pressed: bool,
    ) -> None:
        if self._inside_ctrl_click_capture_region(int(x), int(y)):
            # The Windows event filter emits this click and suppresses it before
            # it can accidentally toggle the underlying player a second time.
            return
        if (
            pressed
            and button == mouse.Button.left
            and control_key_is_down()
        ):
            self.ctrl_click.emit(int(x), int(y))

    def set_ctrl_click_capture_region(
        self,
        region: tuple[int, int, int, int] | None,
    ) -> None:
        self._ctrl_click_capture_region = region

    def _inside_ctrl_click_capture_region(self, x: int, y: int) -> bool:
        region = self._ctrl_click_capture_region
        if region is None:
            return False
        region_x, region_y, width, height = region
        return (
            region_x <= x < region_x + width
            and region_y <= y < region_y + height
        )

    def _win32_event_filter(self, message: int, data: object) -> bool:
        WM_LBUTTONDOWN = 0x0201
        WM_LBUTTONUP = 0x0202
        if message == WM_LBUTTONUP and self._suppressing_ctrl_left_click:
            self._suppressing_ctrl_left_click = False
            return False
        if message != WM_LBUTTONDOWN or not hasattr(ctypes, "windll"):
            return True
        if not control_key_is_down():
            return True
        try:
            x = int(data.pt.x)
            y = int(data.pt.y)
        except (AttributeError, TypeError, ValueError):
            return True
        if not self._inside_ctrl_click_capture_region(x, y):
            return True
        self._suppressing_ctrl_left_click = True
        self.ctrl_click.emit(x, y)
        return False

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if self._period_listener is not None:
            self._period_listener.stop()
            self._period_listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None


def replay_left_click(x: int, y: int) -> None:
    controller = mouse.Controller()
    controller.position = (x, y)
    controller.click(mouse.Button.left, 1)


def move_pointer(x: int, y: int) -> None:
    mouse.Controller().position = (x, y)
