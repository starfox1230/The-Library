from __future__ import annotations

import ctypes
import sys
from dataclasses import dataclass


MODIFIER_VKS = {
    "ctrl": (0x11, 0xA2, 0xA3),
    "control": (0x11, 0xA2, 0xA3),
    "shift": (0x10, 0xA0, 0xA1),
    "alt": (0x12, 0xA4, 0xA5),
    "cmd": (0x5B, 0x5C),
    "win": (0x5B, 0x5C),
}

KEY_VKS = {
    **{f"f{index}": 0x6F + index for index in range(1, 25)},
    "insert": 0x2D,
    "esc": 0x1B,
    "escape": 0x1B,
    "space": 0x20,
    "enter": 0x0D,
    "return": 0x0D,
    "tab": 0x09,
    "backspace": 0x08,
    "delete": 0x2E,
    "home": 0x24,
    "end": 0x23,
    "page_up": 0x21,
    "page_down": 0x22,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
}


@dataclass(frozen=True)
class PollableHotkey:
    source: str
    key_vk: int
    modifiers: frozenset[str]


def is_windows_hotkey_polling_available() -> bool:
    return sys.platform == "win32"


def parse_pollable_hotkey(hotkey: str) -> PollableHotkey | None:
    modifiers: set[str] = set()
    key_vk: int | None = None

    for raw_chunk in hotkey.split("+"):
        chunk = raw_chunk.strip().lower()
        if chunk.startswith("<") and chunk.endswith(">"):
            chunk = chunk[1:-1]
        chunk = chunk.replace("pageup", "page_up").replace("pagedown", "page_down")

        if chunk in MODIFIER_VKS:
            modifiers.add(_normalize_modifier(chunk))
            continue

        if len(chunk) == 1 and "a" <= chunk <= "z":
            key_vk = ord(chunk.upper())
            continue

        if len(chunk) == 1 and "0" <= chunk <= "9":
            key_vk = ord(chunk)
            continue

        if chunk in KEY_VKS:
            key_vk = KEY_VKS[chunk]

    if key_vk is None:
        return None
    return PollableHotkey(source=hotkey, key_vk=key_vk, modifiers=frozenset(modifiers))


def is_pollable_hotkey_down(hotkey: PollableHotkey) -> bool:
    if not _is_vk_down(hotkey.key_vk):
        return False

    for modifier in hotkey.modifiers:
        if not any(_is_vk_down(vk) for vk in MODIFIER_VKS[modifier]):
            return False

    for modifier, vks in MODIFIER_VKS.items():
        normalized = _normalize_modifier(modifier)
        if normalized in hotkey.modifiers:
            continue
        if any(_is_vk_down(vk) for vk in vks):
            return False

    return True


def _normalize_modifier(modifier: str) -> str:
    if modifier == "control":
        return "ctrl"
    if modifier == "cmd":
        return "win"
    return modifier


def _is_vk_down(vk: int) -> bool:
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
