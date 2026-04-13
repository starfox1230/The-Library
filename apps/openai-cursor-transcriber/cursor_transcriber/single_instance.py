from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

ERROR_ALREADY_EXISTS = 183


class SingleInstanceLock:
    def __init__(self, handle: int | None, kernel32) -> None:
        self._handle = handle
        self._kernel32 = kernel32

    def close(self) -> None:
        if self._handle is None or self._kernel32 is None:
            return
        self._kernel32.CloseHandle(self._handle)
        self._handle = None


def _load_kernel32():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


def acquire_single_instance(
    name: str,
    *,
    kernel32=None,
    get_last_error=ctypes.get_last_error,
    set_last_error=ctypes.set_last_error,
) -> SingleInstanceLock | None:
    if kernel32 is None:
        if os.name != "nt":
            return SingleInstanceLock(handle=None, kernel32=None)
        kernel32 = _load_kernel32()

    set_last_error(0)
    handle = kernel32.CreateMutexW(None, False, name)
    if not handle:
        raise ctypes.WinError(get_last_error())

    if get_last_error() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return None

    return SingleInstanceLock(handle=handle, kernel32=kernel32)
