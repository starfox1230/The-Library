from __future__ import annotations

from dataclasses import dataclass
import json
import re
import shutil
from pathlib import Path
from typing import Any, Optional

from .feedback_catalog import (
    AUDIO_UPLOADS_DIRECTORY_NAME,
    AUDIO_UPLOADS_MANIFEST_NAME,
    DEFAULT_AUDIO_FILE,
    HAPTIC_EVENT_OPTIONS,
    default_audio_event_files,
    normalize_audio_event_files,
)


_SUPPORTED_AUDIO_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".oga", ".ogg", ".opus", ".wav"}
_NATURAL_SPLIT_RE = re.compile(r"(\d+)")
_SANITIZE_FILE_NAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_UPLOADED_AUDIO_KEY_PREFIX = "__uploaded__/"
_FEEDBACK_CALLER = "speed-streak-feedback"
_CATEGORY_LABELS = {
    "kenney_casino-audio": "Casino",
    "kenney_impact-sounds": "Impact",
    "kenney_rpg-audio": "RPG",
    "kenney_sci-fi-sounds": "Sci-Fi",
    "kenney_ui-audio": "UI",
}
_CATEGORY_ORDER = {
    "Uploaded": 0,
    "UI": 1,
    "Impact": 2,
    "RPG": 3,
    "Sci-Fi": 4,
    "Casino": 5,
}


@dataclass(frozen=True)
class AudioFileOption:
    key: str
    label: str
    category: str
    file_label: str
    search_text: str
    is_uploaded: bool = False


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
    def __init__(self, audio_root: Path, user_files_root: Optional[Path] = None, fallback_audio_root: Optional[Path] = None) -> None:
        self.audio_root = Path(audio_root)
        self.fallback_audio_root = Path(fallback_audio_root) if fallback_audio_root is not None else None
        self.user_files_root = Path(user_files_root) if user_files_root is not None else self.audio_root.parent / "user_files"
        self.upload_root = self.user_files_root / AUDIO_UPLOADS_DIRECTORY_NAME
        self.upload_manifest_path = self.user_files_root / AUDIO_UPLOADS_MANIFEST_NAME
        self._cached_options: Optional[list[AudioFileOption]] = None
        self._option_lookup: dict[str, AudioFileOption] = {}
        self._qt_player: Any = None
        self._qt_audio_output: Any = None
        self._qt_player_supported: Optional[bool] = None

    def available_options(self) -> list[AudioFileOption]:
        if self._cached_options is None:
            options = self._uploaded_options() + self._packaged_options()
            self._cached_options = options
            self._option_lookup = {option.key: option for option in options}
        return list(self._cached_options)

    def grouped_options(self, query: str = "") -> list[tuple[str, list[AudioFileOption]]]:
        normalized_query = self._normalize_search_text(query)
        query_tokens = [token for token in normalized_query.split(" ") if token]
        groups: dict[str, list[AudioFileOption]] = {}
        for option in self.available_options():
            if query_tokens and not all(token in option.search_text for token in query_tokens):
                continue
            groups.setdefault(option.category, []).append(option)
        return [
            (category, list(options))
            for category, options in sorted(
                groups.items(),
                key=lambda item: (_CATEGORY_ORDER.get(item[0], 99), _natural_sort_key(item[0])),
            )
        ]

    def available_files(self) -> list[str]:
        return [option.key for option in self.available_options()]

    def display_label(self, file_name: str) -> str:
        normalized = self.normalize_file(file_name)
        if not normalized:
            return ""
        self.available_options()
        option = self._option_lookup.get(normalized)
        if option is not None:
            return option.label
        return normalized

    def default_file(self) -> str:
        files = self.available_files()
        if not files:
            return ""
        normalized_default = self._resolve_candidate(DEFAULT_AUDIO_FILE, files)
        if normalized_default:
            return normalized_default
        return files[0]

    def normalize_file(self, file_name: str) -> str:
        files = self.available_files()
        if not files:
            return ""
        candidate = self._resolve_candidate(file_name, files)
        if candidate:
            return candidate
        return self.default_file()

    def normalize_event_files(self, value: Any, *, legacy_file: str | None = None) -> dict[str, str]:
        raw = normalize_audio_event_files(value, fallback_file=legacy_file)
        normalized: dict[str, str] = {}
        for item in HAPTIC_EVENT_OPTIONS:
            event_key = item["event"]
            default_value = default_audio_event_files().get(event_key, legacy_file or DEFAULT_AUDIO_FILE)
            selected = self.normalize_file(raw.get(event_key, default_value))
            if not selected:
                selected = self.normalize_file(default_value)
            normalized[event_key] = selected
        return normalized

    def resolve_path(self, file_name: str) -> Optional[Path]:
        normalized = self.normalize_file(file_name)
        if not normalized:
            return None
        if normalized.startswith(_UPLOADED_AUDIO_KEY_PREFIX):
            file_name_only = normalized[len(_UPLOADED_AUDIO_KEY_PREFIX) :]
            path = self.upload_root / file_name_only
            return path if path.exists() else None
        for root in self._packaged_roots():
            path = root / Path(normalized)
            if path.exists():
                return path
        return None

    def play(self, file_name: str, *, interrupt: bool = True) -> bool:
        path = self.resolve_path(file_name)
        if path is None:
            return False
        qt_result = self._play_with_qt_player(path, interrupt=interrupt)
        if qt_result is not None:
            return qt_result
        try:
            from aqt.sound import av_player

            if interrupt or getattr(av_player, "current_player", None) is None:
                play_with_caller = getattr(av_player, "play_file_with_caller", None)
                if callable(play_with_caller):
                    play_with_caller(str(path), _FEEDBACK_CALLER)
                else:
                    av_player.play_file(str(path))
            else:
                av_player.insert_file(str(path))
            return True
        except Exception:
            return False

    def import_file(self, source_path: str) -> str:
        source = Path(str(source_path or "").strip())
        if not source.exists() or not source.is_file():
            raise FileNotFoundError("The selected audio file no longer exists.")
        if source.suffix.lower() not in _SUPPORTED_AUDIO_SUFFIXES:
            raise ValueError("Choose a standard audio file such as OGG, MP3, WAV, FLAC, M4A, AAC, or OPUS.")

        self.upload_root.mkdir(parents=True, exist_ok=True)
        self.user_files_root.mkdir(parents=True, exist_ok=True)

        safe_name = self._unique_upload_name(source.name)
        destination = self.upload_root / safe_name
        shutil.copy2(source, destination)

        ordered_names = self._load_upload_manifest()
        ordered_names.append(safe_name)
        self._save_upload_manifest(ordered_names)
        self._invalidate_catalog_cache()
        return self._upload_key(safe_name)

    def export_relative_path(self, file_name: str) -> str:
        normalized = self.normalize_file(file_name)
        if not normalized:
            return ""
        if normalized.startswith(_UPLOADED_AUDIO_KEY_PREFIX):
            uploaded_name = normalized[len(_UPLOADED_AUDIO_KEY_PREFIX) :]
            path = self.upload_root / uploaded_name
            if path.exists():
                return f"{self.user_files_root.name}/{AUDIO_UPLOADS_DIRECTORY_NAME}/{uploaded_name}".replace("\\", "/")
            return ""
        for root in self._packaged_roots():
            path = root / Path(normalized)
            if path.exists():
                return f"{root.name}/{normalized}".replace("\\", "/")
        return ""

    def _invalidate_catalog_cache(self) -> None:
        self._cached_options = None
        self._option_lookup = {}

    def _play_with_qt_player(self, path: Path, *, interrupt: bool) -> Optional[bool]:
        player = self._ensure_qt_player()
        if player is None:
            return None
        if not interrupt and self._qt_player_is_active():
            return False
        try:
            stop = getattr(player, "stop", None)
            if callable(stop):
                stop()
            from aqt.qt import QUrl

            source_url = QUrl.fromLocalFile(str(path))
            set_source = getattr(player, "setSource", None)
            if callable(set_source):
                set_source(source_url)
            else:
                from aqt.qt import QMediaContent

                player.setMedia(QMediaContent(source_url))
            self._set_qt_player_volume(player)
            player.play()
            return True
        except Exception:
            return None

    def _ensure_qt_player(self) -> Any:
        if self._qt_player_supported is False:
            return None
        if self._qt_player is not None:
            return self._qt_player
        try:
            from aqt.qt import QMediaPlayer
        except Exception:
            self._qt_player_supported = False
            return None
        try:
            player = QMediaPlayer()
            audio_output = None
            try:
                from aqt.qt import QAudioOutput

                audio_output = QAudioOutput()
                set_audio_output = getattr(player, "setAudioOutput", None)
                if callable(set_audio_output):
                    set_audio_output(audio_output)
            except Exception:
                audio_output = None
            self._qt_player = player
            self._qt_audio_output = audio_output
            self._qt_player_supported = True
            return self._qt_player
        except Exception:
            self._qt_player_supported = False
            self._qt_player = None
            self._qt_audio_output = None
            return None

    def _qt_player_is_active(self) -> bool:
        player = self._qt_player
        if player is None:
            return False
        try:
            playback_state = getattr(player, "playbackState", None)
            if callable(playback_state):
                state = playback_state()
            else:
                state_fn = getattr(player, "state", None)
                state = state_fn() if callable(state_fn) else None
            playing_state = getattr(type(player), "PlayingState", getattr(player, "PlayingState", None))
            if playing_state is not None and state == playing_state:
                return True
            state_name = str(getattr(state, "name", state or "")).lower()
            return "playingstate" in state_name
        except Exception:
            return False

    def _set_qt_player_volume(self, player: Any) -> None:
        try:
            if self._qt_audio_output is not None:
                self._qt_audio_output.setVolume(1.0)
                return
        except Exception:
            pass
        try:
            player.setVolume(100)
        except Exception:
            pass

    def _packaged_options(self) -> list[AudioFileOption]:
        options: list[AudioFileOption] = []
        seen_relative_paths: set[str] = set()
        for root in self._packaged_roots():
            if not root.exists():
                continue
            for path in sorted(root.rglob("*"), key=lambda item: _natural_sort_key(item.relative_to(root).as_posix())):
                if not path.is_file() or path.suffix.lower() not in _SUPPORTED_AUDIO_SUFFIXES:
                    continue
                relative_path = path.relative_to(root).as_posix()
                if relative_path in seen_relative_paths:
                    continue
                seen_relative_paths.add(relative_path)
                category = self._category_label(relative_path)
                file_label = self._display_file_label(relative_path)
                options.append(
                    AudioFileOption(
                        key=relative_path,
                        label=f"{category} / {file_label}",
                        category=category,
                        file_label=file_label,
                        search_text=self._search_text(category, relative_path, file_label),
                        is_uploaded=False,
                    )
                )
        return options

    def _uploaded_options(self) -> list[AudioFileOption]:
        ordered_names = self._sync_upload_manifest()
        options: list[AudioFileOption] = []
        for name in ordered_names:
            path = self.upload_root / name
            if not path.is_file():
                continue
            file_label = self._display_file_label(name)
            options.append(
                AudioFileOption(
                    key=self._upload_key(name),
                    label=f"Uploaded / {file_label}",
                    category="Uploaded",
                    file_label=file_label,
                    search_text=self._search_text("Uploaded", name, file_label),
                    is_uploaded=True,
                )
            )
        return options

    def _resolve_candidate(self, file_name: str, files: list[str]) -> str:
        candidate = str(file_name or "").strip().replace("\\", "/")
        if not candidate:
            return ""
        if candidate in files:
            return candidate
        if candidate.startswith(_UPLOADED_AUDIO_KEY_PREFIX):
            uploaded_name = candidate[len(_UPLOADED_AUDIO_KEY_PREFIX) :]
            for option in files:
                if option == self._upload_key(uploaded_name):
                    return option
        basename_matches = [option for option in files if Path(option).name == Path(candidate).name]
        if len(basename_matches) == 1:
            return basename_matches[0]
        preferred_matches = [option for option in basename_matches if option.endswith(candidate)]
        if len(preferred_matches) == 1:
            return preferred_matches[0]
        return ""

    def _sync_upload_manifest(self) -> list[str]:
        existing_names: list[str] = []
        if self.upload_root.exists():
            existing_names = sorted(
                [
                    path.name
                    for path in self.upload_root.iterdir()
                    if path.is_file() and path.suffix.lower() in _SUPPORTED_AUDIO_SUFFIXES
                ],
                key=_natural_sort_key,
            )
        ordered_names: list[str] = []
        seen: set[str] = set()
        for name in self._load_upload_manifest():
            if name in existing_names and name not in seen:
                ordered_names.append(name)
                seen.add(name)
        for name in existing_names:
            if name not in seen:
                ordered_names.append(name)
                seen.add(name)
        if ordered_names != self._load_upload_manifest():
            self._save_upload_manifest(ordered_names)
        return ordered_names

    def _load_upload_manifest(self) -> list[str]:
        if not self.upload_manifest_path.exists():
            return []
        try:
            payload = json.loads(self.upload_manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(payload, list):
            return []
        ordered_names: list[str] = []
        for item in payload:
            name = str(item or "").strip()
            if not name:
                continue
            if Path(name).suffix.lower() not in _SUPPORTED_AUDIO_SUFFIXES:
                continue
            ordered_names.append(name)
        return ordered_names

    def _save_upload_manifest(self, ordered_names: list[str]) -> None:
        self.user_files_root.mkdir(parents=True, exist_ok=True)
        self.upload_manifest_path.write_text(json.dumps(list(ordered_names), ensure_ascii=True, indent=2), encoding="utf-8")

    def _unique_upload_name(self, file_name: str) -> str:
        original = Path(file_name)
        stem = self._sanitize_file_stem(original.stem)
        suffix = original.suffix.lower()
        candidate = f"{stem}{suffix}"
        index = 2
        while (self.upload_root / candidate).exists():
            candidate = f"{stem}-{index}{suffix}"
            index += 1
        return candidate

    def _sanitize_file_stem(self, value: str) -> str:
        cleaned = _SANITIZE_FILE_NAME_RE.sub("_", str(value or "").strip())
        cleaned = cleaned.strip(" .")
        return cleaned or "custom-audio"

    def _upload_key(self, file_name: str) -> str:
        return f"{_UPLOADED_AUDIO_KEY_PREFIX}{file_name}"

    def _packaged_label(self, relative_path: str) -> str:
        return relative_path.replace("\\", "/")

    def _packaged_roots(self) -> list[Path]:
        roots = [self.audio_root]
        if self.fallback_audio_root is not None and self.fallback_audio_root not in roots:
            roots.append(self.fallback_audio_root)
        return roots

    def _category_label(self, relative_path: str) -> str:
        first_part = Path(relative_path).parts[0] if Path(relative_path).parts else ""
        if first_part in _CATEGORY_LABELS:
            return _CATEGORY_LABELS[first_part]
        cleaned = str(first_part or "Other").replace("_", " ").replace("-", " ").strip()
        return cleaned.title() or "Other"

    def _display_file_label(self, value: str) -> str:
        stem = Path(str(value or "")).stem
        cleaned = stem.replace("_", " ").replace("-", " ").strip()
        return cleaned or stem or value

    def _normalize_search_text(self, value: str) -> str:
        return " ".join(str(value or "").lower().replace("_", " ").replace("-", " ").split())

    def _search_text(self, category: str, relative_path: str, file_label: str) -> str:
        return self._normalize_search_text(f"{category} {relative_path} {file_label}")
