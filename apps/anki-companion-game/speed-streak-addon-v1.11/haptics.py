from __future__ import annotations

import ctypes
import sys
import threading
import time
from typing import List, Tuple


class XInputVibration(ctypes.Structure):
    _fields_ = [
        ("wLeftMotorSpeed", ctypes.c_ushort),
        ("wRightMotorSpeed", ctypes.c_ushort),
    ]


class HapticsController:
    def __init__(self) -> None:
        self._dll = None
        self._enabled = sys.platform.startswith("win")
        self._load_dll()

    @property
    def available(self) -> bool:
        return self._enabled and self._dll is not None

    def _load_dll(self) -> None:
        if not self._enabled:
            return
        for name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
            try:
                self._dll = ctypes.WinDLL(name)
                return
            except OSError:
                continue

    def set_rumble(self, left_motor: int, right_motor: int, user_index: int = 0) -> bool:
        if not self.available:
            return False
        vibration = XInputVibration(
            max(0, min(65535, int(left_motor))),
            max(0, min(65535, int(right_motor))),
        )
        rc = self._dll.XInputSetState(user_index, ctypes.byref(vibration))
        return rc == 0

    def play_pattern(self, kind: str) -> None:
        patterns = {
            "reveal": [(90, 42000, 65535)],
            "again": [(80, 42000, 58000), (55, 0, 0), (80, 42000, 62000)],
            "hard": [(95, 24000, 36000)],
            "good": [(120, 52000, 65535)],
            "easy": [(125, 22000, 30000)],
            "skip": [(80, 12000, 19000)],
            "sync": [(95, 13000, 18000)],
            "reset": [(120, 17000, 26000)],
            "bossStart": [(80, 22000, 38000), (70, 0, 0), (110, 26000, 43000)],
            "bossClear": [(180, 32000, 52000)],
            "timeout": [(420, 52000, 65535), (95, 0, 0), (180, 36000, 50000)],
        }
        sequence = patterns.get(kind)
        if not sequence or not self.available:
            return
        threading.Thread(target=self._run_sequence, args=(sequence,), daemon=True).start()

    def _run_sequence(self, sequence: List[Tuple[int, int, int]]) -> None:
        for duration_ms, left_motor, right_motor in sequence:
            self.set_rumble(left_motor, right_motor)
            time.sleep(duration_ms / 1000)
        self.set_rumble(0, 0)
