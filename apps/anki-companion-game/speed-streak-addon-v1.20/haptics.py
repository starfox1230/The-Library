from __future__ import annotations

import ctypes
import sys
import threading
import time
from typing import List, Tuple

from .feedback_catalog import HAPTIC_PATTERN_LIBRARY


class XInputVibration(ctypes.Structure):
    _fields_ = [
        ("wLeftMotorSpeed", ctypes.c_ushort),
        ("wRightMotorSpeed", ctypes.c_ushort),
    ]


class HapticsController:
    def __init__(self) -> None:
        self._dll = None
        self._enabled = sys.platform.startswith("win")
        self._user_enabled = True
        self._load_dll()

    @property
    def available(self) -> bool:
        return self._enabled and self._dll is not None

    @property
    def user_enabled(self) -> bool:
        return self._user_enabled

    def set_enabled(self, enabled: bool) -> None:
        self._user_enabled = bool(enabled)
        if not self._user_enabled:
            self.set_rumble(0, 0)

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
        self._play_pattern(kind, ignore_user_enabled=False)

    def preview_pattern(self, kind: str) -> bool:
        return self._play_pattern(kind, ignore_user_enabled=True)

    def _play_pattern(self, kind: str, *, ignore_user_enabled: bool) -> bool:
        sequence = self._native_sequence(kind)
        if not sequence or not self.available or (not ignore_user_enabled and not self._user_enabled):
            return False
        threading.Thread(target=self._run_sequence, args=(sequence,), daemon=True).start()
        return True

    def _native_sequence(self, kind: str) -> List[Tuple[int, int, int]]:
        meta = HAPTIC_PATTERN_LIBRARY.get(str(kind or "").strip())
        if not meta:
            return []
        sequence: List[Tuple[int, int, int]] = []
        for step in meta.get("sequence", []):
            duration = max(0, int(step.get("duration", 0) or 0))
            weak = max(0.0, min(1.0, float(step.get("weak", 0) or 0.0)))
            strong = max(0.0, min(1.0, float(step.get("strong", 0) or 0.0)))
            sequence.append((duration, int(round(weak * 65535)), int(round(strong * 65535))))
        return sequence

    def _run_sequence(self, sequence: List[Tuple[int, int, int]]) -> None:
        for duration_ms, left_motor, right_motor in sequence:
            self.set_rumble(left_motor, right_motor)
            time.sleep(duration_ms / 1000)
        self.set_rumble(0, 0)
