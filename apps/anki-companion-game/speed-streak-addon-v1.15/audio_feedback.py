from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .feedback_catalog import DEFAULT_AUDIO_FILE


_SUPPORTED_AUDIO_SUFFIXES = {".ogg", ".mp3", ".wav", ".flac", ".m4a"}
_NATURAL_SPLIT_RE = re.compile(r"(\d+)")


def _natural_sort_key(value: str) -> list[object]:
    parts = _NATURAL_SPLIT_RE.split(str(value).lower())
    key: list[object] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    return key


class AudioFeedbackController:
    def __init__(self, audio_root: Path) -> None:
        self.audio_root = Path(audio_root)

    def available_files(self) -> list[str]:
        if not self.audio_root.exists():
            return []
        names = [
            path.name
            for path in self.audio_root.iterdir()
            if path.is_file() and path.suffix.lower() in _SUPPORTED_AUDIO_SUFFIXES
        ]
        return sorted(names, key=_natural_sort_key)

    def default_file(self) -> str:
        files = self.available_files()
        if not files:
            return ""
        if DEFAULT_AUDIO_FILE in files:
            return DEFAULT_AUDIO_FILE
        return files[0]

    def normalize_file(self, file_name: str) -> str:
        files = self.available_files()
        if not files:
            return ""
        candidate = str(file_name or "").strip()
        if candidate in files:
            return candidate
        return self.default_file()

    def resolve_path(self, file_name: str) -> Optional[Path]:
        normalized = self.normalize_file(file_name)
        if not normalized:
            return None
        path = self.audio_root / normalized
        return path if path.exists() else None

    def play(self, file_name: str) -> bool:
        path = self.resolve_path(file_name)
        if path is None:
            return False
        try:
            from aqt.sound import av_player

            av_player.play_file(str(path))
            return True
        except Exception:
            return False
