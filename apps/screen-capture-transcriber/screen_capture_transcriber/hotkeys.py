from __future__ import annotations

import ctypes

from PySide6.QtCore import QObject, Signal
from pynput import keyboard, mouse


class GlobalHotkeys(QObject):
    toggle_recording = Signal()
    add_chapter = Signal()
    anatomy_capture = Signal()
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
        self._mouse_listener: mouse.Listener | None = None

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
            self._mouse_listener = mouse.Listener(on_click=self._on_click)
            self._mouse_listener.start()
        except Exception as exc:
            self.error.emit(str(exc))

    def _on_click(
        self,
        x: int,
        y: int,
        button: mouse.Button,
        pressed: bool,
    ) -> None:
        if (
            pressed
            and button == mouse.Button.left
            and hasattr(ctypes, "windll")
            and ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000
        ):
            self.ctrl_click.emit(int(x), int(y))

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None


def replay_left_click(x: int, y: int) -> None:
    controller = mouse.Controller()
    controller.position = (x, y)
    controller.click(mouse.Button.left, 1)
