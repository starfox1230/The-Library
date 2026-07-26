from __future__ import annotations

import ctypes
import os
import sys
import threading
import time
from pathlib import Path
from typing import List, Tuple

from .feedback_catalog import HAPTIC_PATTERN_LIBRARY

XINPUT_USER_COUNT = 4
STEAM_INPUT_MAX_COUNT = 16
STEAM_CONTROLLER_PAD_LEFT = 0
STEAM_CONTROLLER_PAD_RIGHT = 1
STEAMWORKS_APP_ID_SPACEWAR = "480"


class XInputVibration(ctypes.Structure):
    _fields_ = [
        ("wLeftMotorSpeed", ctypes.c_ushort),
        ("wRightMotorSpeed", ctypes.c_ushort),
    ]


class XInputGamepad(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XInputState(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XInputGamepad),
    ]


class SteamInputBridge:
    """Optional Steamworks flat-API haptics bridge.

    This path stays dormant unless a compatible steam_api64.dll is available.
    It lets a future bundled helper/DLL use Valve's native Steam Input haptics
    without changing the add-on UI or the existing XInput fallback.
    """

    def __init__(self, addon_root: Path) -> None:
        self._dll = None
        self._steam_input = None
        self._available = False
        self._handles: List[int] = []
        self._handles_checked_at = 0.0
        self._load(addon_root)

    @property
    def available(self) -> bool:
        return self._available and bool(self._connected_handles())

    def trigger(self, left_motor: int, right_motor: int, duration_ms: int) -> bool:
        handles = self._connected_handles()
        if not handles:
            return False

        left = max(0, min(65535, int(left_motor)))
        right = max(0, min(65535, int(right_motor)))
        duration = max(0, int(duration_ms))
        fired = False

        for handle in handles:
            try:
                self._dll.SteamAPI_ISteamInput_TriggerVibration(
                    self._steam_input,
                    ctypes.c_uint64(handle),
                    ctypes.c_ushort(left),
                    ctypes.c_ushort(right),
                )
                fired = True
            except Exception:
                pass

            if duration > 0 and (left > 0 or right > 0):
                fired = self._trigger_haptic_pulse(handle, duration) or fired
        return fired

    def shutdown(self) -> None:
        if not self._dll or not self._steam_input:
            return
        try:
            self._dll.SteamAPI_ISteamInput_Shutdown(self._steam_input)
        except Exception:
            pass
        try:
            self._dll.SteamAPI_Shutdown()
        except Exception:
            pass

    def _load(self, addon_root: Path) -> None:
        if not sys.platform.startswith("win"):
            return

        dll_path = self._find_steam_api_dll(addon_root)
        if not dll_path:
            return

        previous_cwd = Path.cwd()
        added_directory = None
        old_app_id = os.environ.get("SteamAppId")
        old_game_id = os.environ.get("SteamGameId")
        try:
            if hasattr(os, "add_dll_directory"):
                added_directory = os.add_dll_directory(str(dll_path.parent))
            os.environ.setdefault("SteamAppId", STEAMWORKS_APP_ID_SPACEWAR)
            os.environ.setdefault("SteamGameId", STEAMWORKS_APP_ID_SPACEWAR)
            os.chdir(str(dll_path.parent))
            self._dll = ctypes.WinDLL(str(dll_path))
            self._configure_functions()
            if not self._dll.SteamAPI_Init():
                self._dll = None
                return
            self._steam_input = self._steam_input_interface()
            if not self._steam_input:
                self.shutdown()
                self._dll = None
                return
            try:
                initialized = self._dll.SteamAPI_ISteamInput_Init(self._steam_input, True)
            except TypeError:
                initialized = self._dll.SteamAPI_ISteamInput_Init(self._steam_input)
            if not initialized:
                self.shutdown()
                self._dll = None
                return
            self._available = True
        except Exception:
            self._dll = None
            self._steam_input = None
            self._available = False
        finally:
            os.chdir(str(previous_cwd))
            if added_directory is not None:
                added_directory.close()
            if old_app_id is None:
                os.environ.pop("SteamAppId", None)
            if old_game_id is None:
                os.environ.pop("SteamGameId", None)

    def _find_steam_api_dll(self, addon_root: Path) -> Path | None:
        candidates = [
            addon_root / "steam_api64.dll",
            addon_root / "steamworks" / "steam_api64.dll",
            addon_root / "steam_haptics" / "steam_api64.dll",
        ]
        env_path = os.environ.get("SPEED_STREAK_STEAM_API64")
        if env_path:
            candidates.insert(0, Path(env_path))
        for candidate in candidates:
            try:
                if candidate.is_file():
                    return candidate.resolve()
            except Exception:
                continue
        return None

    def _configure_functions(self) -> None:
        self._dll.SteamAPI_Init.restype = ctypes.c_bool
        self._dll.SteamAPI_Shutdown.restype = None
        self._dll.SteamAPI_ISteamInput_GetConnectedControllers.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint64),
        ]
        self._dll.SteamAPI_ISteamInput_GetConnectedControllers.restype = ctypes.c_int
        self._dll.SteamAPI_ISteamInput_TriggerVibration.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.c_ushort,
            ctypes.c_ushort,
        ]
        self._dll.SteamAPI_ISteamInput_TriggerVibration.restype = None
        self._dll.SteamAPI_ISteamInput_TriggerRepeatedHapticPulse.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.c_int,
            ctypes.c_ushort,
            ctypes.c_ushort,
            ctypes.c_ushort,
            ctypes.c_uint,
        ]
        self._dll.SteamAPI_ISteamInput_TriggerRepeatedHapticPulse.restype = None

        try:
            self._dll.SteamAPI_ISteamInput_Init.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        except Exception:
            pass
        self._dll.SteamAPI_ISteamInput_Init.restype = ctypes.c_bool
        self._dll.SteamAPI_ISteamInput_Shutdown.argtypes = [ctypes.c_void_p]
        self._dll.SteamAPI_ISteamInput_Shutdown.restype = ctypes.c_bool

        run_frame = getattr(self._dll, "SteamAPI_ISteamInput_RunFrame", None)
        if run_frame is not None:
            run_frame.argtypes = [ctypes.c_void_p, ctypes.c_bool]
            run_frame.restype = None

    def _steam_input_interface(self):
        for version in ("SteamAPI_SteamInput_v006", "SteamAPI_SteamInput_v005", "SteamAPI_SteamInput_v004"):
            try:
                getter = getattr(self._dll, version)
                getter.restype = ctypes.c_void_p
                return getter()
            except Exception:
                continue
        return None

    def _connected_handles(self) -> List[int]:
        if not self._available or not self._dll or not self._steam_input:
            return []
        now = time.monotonic()
        if now - self._handles_checked_at < 1.0:
            return list(self._handles)
        self._handles_checked_at = now
        handles = (ctypes.c_uint64 * STEAM_INPUT_MAX_COUNT)()
        try:
            run_frame = getattr(self._dll, "SteamAPI_ISteamInput_RunFrame", None)
            if run_frame is not None:
                run_frame(self._steam_input, True)
            count = int(self._dll.SteamAPI_ISteamInput_GetConnectedControllers(self._steam_input, handles))
        except Exception:
            count = 0
        self._handles = [int(handles[index]) for index in range(max(0, min(count, STEAM_INPUT_MAX_COUNT))) if handles[index]]
        return list(self._handles)

    def _trigger_haptic_pulse(self, handle: int, duration_ms: int) -> bool:
        pulse_on = 50000
        pulse_off = 25000
        repeat = max(1, min(65535, int(round((duration_ms * 1000) / (pulse_on + pulse_off)))))
        fired = False
        for pad in (STEAM_CONTROLLER_PAD_LEFT, STEAM_CONTROLLER_PAD_RIGHT):
            try:
                self._dll.SteamAPI_ISteamInput_TriggerRepeatedHapticPulse(
                    self._steam_input,
                    ctypes.c_uint64(handle),
                    ctypes.c_int(pad),
                    ctypes.c_ushort(pulse_on),
                    ctypes.c_ushort(pulse_off),
                    ctypes.c_ushort(repeat),
                    ctypes.c_uint(0),
                )
                fired = True
            except Exception:
                pass
        return fired


class HapticsController:
    def __init__(self) -> None:
        self._dll = None
        self._enabled = sys.platform.startswith("win")
        self._user_enabled = True
        self._connected_indices: List[int] = []
        self._indices_checked_at = 0.0
        self._steam = SteamInputBridge(Path(__file__).resolve().parent)
        self._load_dll()

    @property
    def available(self) -> bool:
        return self._steam.available or bool(self._connected_xinput_indices())

    @property
    def user_enabled(self) -> bool:
        return self._user_enabled

    def set_enabled(self, enabled: bool) -> None:
        self._user_enabled = bool(enabled)
        if not self._user_enabled:
            self._steam.trigger(0, 0, 0)
            self.set_rumble(0, 0)

    def _load_dll(self) -> None:
        if not self._enabled:
            return
        for name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
            try:
                self._dll = ctypes.WinDLL(name)
                self._dll.XInputSetState.argtypes = [
                    ctypes.c_uint,
                    ctypes.POINTER(XInputVibration),
                ]
                self._dll.XInputSetState.restype = ctypes.c_ulong
                self._dll.XInputGetState.argtypes = [
                    ctypes.c_uint,
                    ctypes.POINTER(XInputState),
                ]
                self._dll.XInputGetState.restype = ctypes.c_ulong
                return
            except OSError:
                continue
            except Exception:
                self._dll = None
                continue

    def set_rumble(self, left_motor: int, right_motor: int, user_index: int | None = None) -> bool:
        if not self._enabled or self._dll is None:
            return False
        vibration = XInputVibration(
            max(0, min(65535, int(left_motor))),
            max(0, min(65535, int(right_motor))),
        )
        indices = [user_index] if user_index is not None else self._connected_xinput_indices()
        fired = False
        for index in indices:
            try:
                rc = self._dll.XInputSetState(int(index), ctypes.byref(vibration))
                fired = rc == 0 or fired
            except Exception:
                continue
        return fired

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
            self._steam.trigger(left_motor, right_motor, duration_ms)
            self.set_rumble(left_motor, right_motor)
            time.sleep(duration_ms / 1000)
        self._steam.trigger(0, 0, 0)
        self.set_rumble(0, 0)

    def _connected_xinput_indices(self) -> List[int]:
        if not self._enabled or self._dll is None:
            return []
        now = time.monotonic()
        if now - self._indices_checked_at < 1.0:
            return list(self._connected_indices)
        self._indices_checked_at = now
        connected: List[int] = []
        for index in range(XINPUT_USER_COUNT):
            state = XInputState()
            try:
                if self._dll.XInputGetState(index, ctypes.byref(state)) == 0:
                    connected.append(index)
            except Exception:
                if index == 0:
                    connected.append(index)
                break
        self._connected_indices = connected
        return list(self._connected_indices)

    def __del__(self) -> None:
        try:
            self._steam.shutdown()
        except Exception:
            pass
