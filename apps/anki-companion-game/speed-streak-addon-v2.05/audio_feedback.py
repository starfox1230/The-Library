from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from .feedback_catalog import (
    AUDIO_UPLOADS_DIRECTORY_NAME,
    AUDIO_UPLOADS_MANIFEST_NAME,
    DEFAULT_AUDIO_FILE,
    DEFAULT_AUDIO_VOLUME_PERCENT,
    HAPTIC_EVENT_OPTIONS,
    default_audio_event_files,
    normalize_audio_event_files,
    normalize_audio_volume_percent,
)


_SUPPORTED_AUDIO_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".oga", ".ogg", ".opus", ".wav"}
_NATURAL_SPLIT_RE = re.compile(r"(\d+)")
_SANITIZE_FILE_NAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_UPLOADED_AUDIO_KEY_PREFIX = "__uploaded__/"
_FEEDBACK_CALLER = "speed-streak-feedback"
_CATEGORY_LABELS = {
    "countdown-cues": "Countdown Cues",
    "kenney_casino-audio": "Casino",
    "kenney_impact-sounds": "Impact",
    "kenney_rpg-audio": "RPG",
    "kenney_sci-fi-sounds": "Sci-Fi",
    "kenney_ui-audio": "UI",
}
_CATEGORY_ORDER = {
    "Uploaded": 0,
    "Countdown Cues": 1,
    "UI": 2,
    "Impact": 3,
    "RPG": 4,
    "Sci-Fi": 5,
    "Casino": 6,
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


def native_audio_enabled() -> bool:
    # CoreAudio listener teardown can crash inside Qt even with persistent owners.
    # Do not import or construct QtMultimedia objects on macOS, including diagnostics.
    return sys.platform != "darwin"


def _new_audio_object(factory: Any) -> Any:
    """Own native audio objects until QApplication teardown, even on setup failure.

    Never parent these to a dialog or release them on a profile switch: native
    device notifications may still be queued in a nested Qt event loop.
    """
    if not native_audio_enabled():
        raise RuntimeError("QtMultimedia audio is disabled on macOS")
    from aqt.qt import QApplication

    app = QApplication.instance()
    if app is None:
        raise RuntimeError("Audio requires a running QApplication")
    retained = getattr(app, "_speed_streak_audio_objects", None)
    if retained is None:
        retained = []
        app._speed_streak_audio_objects = retained
    obj = factory(app)
    retained.append(obj)  # Before setSource/setAudioOutput or any other setup.
    return obj


class AudioFeedbackController:
    def __init__(self, audio_root: Path, user_files_root: Optional[Path] = None, fallback_audio_root: Optional[Path] = None) -> None:
        self._audio_callback_generation = 0
        self._timed_callback_generation = 0
        self.audio_root = Path(audio_root)
        self.fallback_audio_root = Path(fallback_audio_root) if fallback_audio_root is not None else None
        self.user_files_root = Path(user_files_root) if user_files_root is not None else self.audio_root.parent / "user_files"
        self._addon_root = self.audio_root.parent
        self.upload_root = self.user_files_root / AUDIO_UPLOADS_DIRECTORY_NAME
        self.upload_manifest_path = self.user_files_root / AUDIO_UPLOADS_MANIFEST_NAME
        self._cached_options: Optional[list[AudioFileOption]] = None
        self._option_lookup: dict[str, AudioFileOption] = {}
        self._qt_effects: dict[str, Any] = {}
        self._qt_effect_volume_percents: dict[str, int] = {}
        self._qt_effect_supported: Optional[bool] = None
        self._qt_players: dict[str, tuple[Any, Any]] = {}
        self._qt_player_volume_percents: dict[str, int] = {}
        self._qt_player_supported: Optional[bool] = None
        self._warming_paths: set[str] = set()
        self._warmed_paths: set[str] = set()
        self.last_playback_backend = "none"
        self.last_playback_result = "not-played"
        self._timed_qt_player: Any = None
        self._timed_qt_audio_output: Any = None
        self._timed_qt_player_supported: Optional[bool] = None
        self._timed_sound_effect: Any = None
        self._timed_sound_effect_supported: Optional[bool] = None
        self._timed_source_path = ""
        self._timed_volume_percent = DEFAULT_AUDIO_VOLUME_PERCENT
        self._timed_warming_path = ""
        self._timed_warmed_paths: set[str] = set()
        self._timed_media_warming_path = ""
        self._timed_media_warmed_paths: set[str] = set()

    def _queue_audio_callback(self, delay: int, callback: Callable[[], Any]) -> None:
        from aqt.qt import QTimer

        generation = self._audio_callback_generation
        def run() -> None:
            if generation == self._audio_callback_generation:
                callback()
        QTimer.singleShot(delay, run)

    def _queue_timed_audio_callback(self, delay: int, callback: Callable[[], Any]) -> None:
        generation = self._timed_callback_generation
        def run() -> None:
            if generation == self._timed_callback_generation:
                callback()
        self._queue_audio_callback(delay, run)

    def stop_all(self) -> None:
        """Quiesce playback and pending warm-ups without deleting native objects."""
        self._audio_callback_generation += 1
        for path in tuple(self._warming_paths):
            if path in self._qt_effects:
                self._finish_qt_sound_effect_warm_up(path)
            else:
                self._finish_warm_up(path)
        self._timed_warming_path = ""
        self._timed_media_warming_path = ""
        for effect in self._qt_effects.values():
            try:
                effect.stop()
            except Exception:
                pass
        self._stop_qt_players()
        self.stop_timed()

    def rebind_user_files_root(self, user_files_root: Path) -> None:
        """Refresh profile files while retaining the existing native audio owners."""
        self.stop_all()
        self.user_files_root = Path(user_files_root)
        self.upload_root = self.user_files_root / AUDIO_UPLOADS_DIRECTORY_NAME
        self.upload_manifest_path = self.user_files_root / AUDIO_UPLOADS_MANIFEST_NAME
        self._invalidate_catalog_cache()

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
        if normalized.startswith(_UPLOADED_AUDIO_KEY_PREFIX):
            uploaded_name = normalized[len(_UPLOADED_AUDIO_KEY_PREFIX) :]
            return f"Uploaded / {self._display_file_label(uploaded_name)} (missing)"
        return normalized

    def default_file(self) -> str:
        files = self.available_files()
        if not files:
            return ""
        normalized_default = self._resolve_candidate(DEFAULT_AUDIO_FILE, files)
        if normalized_default:
            return normalized_default
        return files[0]

    def normalize_file(self, file_name: str, *, preserve_missing_upload: bool = True) -> str:
        raw_candidate = str(file_name or "").strip().replace("\\", "/")
        files = self.available_files()
        if not files:
            return raw_candidate if preserve_missing_upload and self._is_safe_upload_key(raw_candidate) else ""
        candidate = self._resolve_candidate(raw_candidate, files)
        if candidate:
            return candidate
        # Uploaded audio belongs to the user and lives in the active profile.
        # Add-ons are imported before Anki necessarily exposes that profile,
        # so a temporarily unavailable upload must not be converted into a
        # bundled default and then written back over the user's preference.
        if preserve_missing_upload and self._is_safe_upload_key(raw_candidate):
            return raw_candidate
        return self.default_file()

    def normalize_event_files(
        self,
        value: Any,
        *,
        legacy_file: str | None = None,
        preserve_missing_uploads: bool = True,
    ) -> dict[str, str]:
        raw = normalize_audio_event_files(value, fallback_file=legacy_file)
        normalized: dict[str, str] = {}
        for item in HAPTIC_EVENT_OPTIONS:
            event_key = item["event"]
            default_value = default_audio_event_files().get(event_key, legacy_file or DEFAULT_AUDIO_FILE)
            selected = self.normalize_file(
                raw.get(event_key, default_value),
                preserve_missing_upload=preserve_missing_uploads,
            )
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

    def play(
        self,
        file_name: str,
        *,
        interrupt: bool = True,
        volume_percent: int = DEFAULT_AUDIO_VOLUME_PERCENT,
        fallback: Optional[Callable[[], bool]] = None,
    ) -> bool:
        if not native_audio_enabled():
            # A missing browser must not fall through to Anki's shared AV player:
            # that can interrupt card audio and may re-enter native audio backends.
            self.last_playback_backend = "browser-required"
            self.last_playback_result = "unavailable"
            if fallback is not None:
                try:
                    if fallback():
                        self.last_playback_backend = "review-web-fallback"
                        self.last_playback_result = "accepted"
                        return True
                except Exception:
                    pass
            return False
        path = self.resolve_path(file_name)
        if path is None:
            self.last_playback_backend = "none"
            self.last_playback_result = "file-not-found"
            return False
        qt_result = self._play_with_qt_player(
            path,
            interrupt=interrupt,
            volume_percent=volume_percent,
            require_ready=bool(fallback is not None),
        )
        if qt_result is not None:
            return qt_result
        if fallback is not None:
            try:
                if fallback():
                    self.last_playback_backend = "review-web-fallback"
                    self.last_playback_result = "accepted"
                    return True
            except Exception:
                pass
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
            self.last_playback_backend = "anki-av-player"
            self.last_playback_result = "accepted"
            return True
        except Exception:
            self.last_playback_backend = "none"
            self.last_playback_result = "failed"
            return False

    def play_native_test(
        self,
        file_name: str,
        volume_percent: int = DEFAULT_AUDIO_VOLUME_PERCENT,
    ) -> bool:
        """Exercise only the low-latency WAV path for the A/B diagnostic."""

        if not native_audio_enabled():
            self.last_playback_backend = "disabled-on-macos"
            self.last_playback_result = "native-audio-disabled"
            return False
        path = self.resolve_path(file_name)
        if path is None or path.suffix.lower() != ".wav":
            self.last_playback_backend = "qt-sound-effect"
            self.last_playback_result = "wav-required"
            return False
        result = self._play_with_qt_sound_effect(
            path,
            interrupt=True,
            volume_percent=volume_percent,
            require_ready=True,
        )
        if result is not True:
            self.last_playback_backend = "qt-sound-effect"
            self.last_playback_result = "not-ready"
            return False
        return True

    def diagnostic_snapshot(self, file_name: str) -> dict[str, Any]:
        normalized = self.normalize_file(file_name)
        path = self.resolve_path(normalized)
        snapshot: dict[str, Any] = {
            "file": normalized or str(file_name or ""),
            "exists": bool(path and path.is_file()),
            "extension": path.suffix.lower() if path else Path(normalized).suffix.lower(),
            "sizeBytes": int(path.stat().st_size) if path and path.is_file() else 0,
            "lastBackend": self.last_playback_backend,
            "lastResult": self.last_playback_result,
        }
        if not native_audio_enabled():
            snapshot.update({"nativeStatus": "disabled-on-macos", "nativeLoaded": False, "nativePlaying": False})
            return snapshot
        if path is None or path.suffix.lower() != ".wav":
            snapshot.update({"nativeStatus": "not-wav", "nativeLoaded": False, "nativePlaying": False})
            return snapshot
        effect = self._qt_effects.get(str(path.resolve()))
        if effect is None:
            snapshot.update({"nativeStatus": "not-created", "nativeLoaded": False, "nativePlaying": False})
            return snapshot
        try:
            status_fn = getattr(effect, "status", None)
            status = status_fn() if callable(status_fn) else None
            snapshot["nativeStatus"] = str(getattr(status, "name", status or "unavailable"))
        except Exception:
            snapshot["nativeStatus"] = "unavailable"
        try:
            loaded_fn = getattr(effect, "isLoaded", None)
            snapshot["nativeLoaded"] = bool(loaded_fn()) if callable(loaded_fn) else None
        except Exception:
            snapshot["nativeLoaded"] = None
        try:
            playing_fn = getattr(effect, "isPlaying", None)
            snapshot["nativePlaying"] = bool(playing_fn()) if callable(playing_fn) else None
        except Exception:
            snapshot["nativePlaying"] = None
        try:
            volume_fn = getattr(effect, "volume", None)
            snapshot["nativeLinearVolume"] = round(float(volume_fn()), 4) if callable(volume_fn) else None
        except Exception:
            snapshot["nativeLinearVolume"] = None
        try:
            device_fn = getattr(effect, "audioDevice", None)
            device = device_fn() if callable(device_fn) else None
            description_fn = getattr(device, "description", None)
            snapshot["audioDevice"] = str(description_fn() if callable(description_fn) else "")
        except Exception:
            snapshot["audioDevice"] = ""
        return snapshot

    def prepare_files(self, file_names: Any) -> int:
        """Create and source one reusable low-latency channel per event sound."""

        prepared = 0
        seen: set[str] = set()
        for file_name in list(file_names or []):
            path = self.resolve_path(str(file_name or ""))
            if path is None:
                continue
            normalized_path = str(path.resolve())
            if normalized_path in seen:
                continue
            seen.add(normalized_path)
            if self._prepare_feedback_channel(path):
                prepared += 1
        return prepared

    def warm_up(self, file_names: Any) -> None:
        """Decode selected cues and silently open the audio output before review."""

        paths: list[str] = []
        seen: set[str] = set()
        for file_name in list(file_names or []):
            path = self.resolve_path(str(file_name or ""))
            if path is None:
                continue
            normalized_path = str(path.resolve())
            if normalized_path in seen:
                continue
            seen.add(normalized_path)
            if normalized_path in self._warmed_paths or normalized_path in self._warming_paths:
                continue
            if path.suffix.lower() == ".wav":
                if self._prepare_qt_sound_effect(path) is not None:
                    self._schedule_qt_sound_effect_warm_up(normalized_path)
                continue
            if self._prepare_qt_player(path) is not None:
                paths.append(normalized_path)
        if not paths:
            return
        try:
            from aqt.qt import QTimer

            self._queue_audio_callback(0, lambda queued=tuple(paths): self._start_warm_up(queued))
        except Exception:
            self._start_warm_up(tuple(paths))

    def play_from_position(
        self,
        file_name: str,
        position_ms: int,
        volume_percent: int = DEFAULT_AUDIO_VOLUME_PERCENT,
    ) -> bool:
        """Preview a clip beginning at an exact point inside the audio file."""

        path = self.resolve_path(file_name)
        if path is None:
            return False
        normalized_path = str(path.resolve())
        prepared = self._prepare_qt_player(path)
        if prepared is None:
            return False
        player, audio_output = prepared
        self._remember_qt_player_volume(normalized_path, volume_percent)
        self._finish_warm_up(normalized_path)
        self._set_qt_player_volume(player, audio_output, volume_percent)
        self._stop_qt_players(except_path=normalized_path)
        try:
            player.stop()
            set_position = getattr(player, "setPosition", None)
            if callable(set_position):
                set_position(max(0, int(position_ms)))
            player.play()
            return True
        except Exception:
            return False

    def prepare_timed(
        self,
        file_name: str,
        volume_percent: int = DEFAULT_AUDIO_VOLUME_PERCENT,
    ) -> bool:
        """Preload the dedicated countdown player to minimize cue latency."""

        path = self.resolve_path(file_name)
        if path is None:
            return False
        normalized_path = str(path.resolve())
        safe_volume = normalize_audio_volume_percent(volume_percent)
        self._timed_volume_percent = safe_volume
        if path.suffix.lower() == ".wav":
            effect = self._ensure_timed_sound_effect()
            if effect is not None:
                if self._timed_source_path == normalized_path:
                    effect.setVolume(self._qt_linear_volume(safe_volume))
                    self._schedule_timed_sound_effect_warm_up(normalized_path)
                    return True
                try:
                    effect.stop()
                    from aqt.qt import QUrl

                    effect.setSource(QUrl.fromLocalFile(normalized_path))
                    set_loop_count = getattr(effect, "setLoopCount", None)
                    if callable(set_loop_count):
                        set_loop_count(1)
                    effect.setVolume(self._qt_linear_volume(safe_volume))
                    self._timed_source_path = normalized_path
                    self._timed_warming_path = ""
                    self._schedule_timed_sound_effect_warm_up(normalized_path)
                    return True
                except Exception:
                    self._timed_source_path = ""
        player = self._ensure_timed_qt_player()
        if player is None:
            return False
        if self._timed_source_path == normalized_path:
            self._set_qt_player_volume(player, self._timed_qt_audio_output, safe_volume)
            self._schedule_timed_media_warm_up(normalized_path)
            return True
        try:
            stop = getattr(player, "stop", None)
            if callable(stop):
                stop()
            from aqt.qt import QUrl

            source_url = QUrl.fromLocalFile(normalized_path)
            set_source = getattr(player, "setSource", None)
            if callable(set_source):
                set_source(source_url)
            else:
                from aqt.qt import QMediaContent

                player.setMedia(QMediaContent(source_url))
            self._set_qt_player_volume(player, self._timed_qt_audio_output, safe_volume)
            self._timed_source_path = normalized_path
            self._timed_media_warming_path = ""
            self._schedule_timed_media_warm_up(normalized_path)
            return True
        except Exception:
            self._timed_source_path = ""
            return False

    def play_timed(
        self,
        file_name: str,
        volume_percent: int = DEFAULT_AUDIO_VOLUME_PERCENT,
    ) -> bool:
        """Replay a preloaded clip on the separate countdown audio channel."""

        if self.prepare_timed(file_name, volume_percent):
            try:
                if self._timed_sound_effect is not None and self._timed_source_path.lower().endswith(".wav"):
                    self._finish_timed_sound_effect_warm_up(self._timed_source_path)
                    self._timed_warmed_paths.add(self._timed_source_path)
                    self._timed_sound_effect.setVolume(
                        self._qt_linear_volume(self._timed_volume_percent)
                    )
                    self._timed_sound_effect.play()
                    return True
                set_position = getattr(self._timed_qt_player, "setPosition", None)
                self._finish_timed_media_warm_up(self._timed_source_path)
                self._timed_media_warmed_paths.add(self._timed_source_path)
                self._set_qt_player_volume(
                    self._timed_qt_player,
                    self._timed_qt_audio_output,
                    self._timed_volume_percent,
                )
                if callable(set_position):
                    set_position(0)
                self._timed_qt_player.play()
                return True
            except Exception:
                pass
        # Older Qt builds still get a functional, if less tightly preloaded,
        # fallback through the same cross-platform path as event sounds.
        return self.play(file_name, interrupt=True, volume_percent=volume_percent)

    def timed_ready(self, file_name: str) -> bool:
        """Return true only after Qt has decoded the dedicated countdown cue."""

        path = self.resolve_path(file_name)
        if path is None:
            return False
        normalized_path = str(path.resolve())
        if normalized_path != self._timed_source_path:
            return False
        if path.suffix.lower() == ".wav" and self._timed_sound_effect is not None:
            try:
                is_loaded = getattr(self._timed_sound_effect, "isLoaded", None)
                if callable(is_loaded):
                    return bool(is_loaded()) and normalized_path in self._timed_warmed_paths
                status = self._timed_sound_effect.status()
                status_name = str(getattr(status, "name", status)).lower()
                return (
                    ("ready" in status_name or "loaded" in status_name)
                    and normalized_path in self._timed_warmed_paths
                )
            except Exception:
                return False
        if self._timed_qt_player is None:
            return False
        try:
            status_fn = getattr(self._timed_qt_player, "mediaStatus", None)
            if not callable(status_fn):
                return normalized_path in self._timed_media_warmed_paths
            status = status_fn()
            status_name = str(getattr(status, "name", status)).lower()
            return (
                any(token in status_name for token in ("loaded", "buffered"))
                and normalized_path in self._timed_media_warmed_paths
            )
        except Exception:
            return True

    def stop_timed(self) -> None:
        # Invalidate pending warm-up callbacks so a stopped cue cannot restart.
        self._timed_callback_generation += 1
        self._timed_warming_path = ""
        self._timed_media_warming_path = ""
        try:
            if self._timed_qt_player is not None:
                self._timed_qt_player.stop()
        except Exception:
            pass
        try:
            if self._timed_sound_effect is not None:
                self._timed_sound_effect.stop()
        except Exception:
            pass

    def _schedule_timed_sound_effect_warm_up(self, normalized_path: str, attempt: int = 0) -> None:
        if (
            normalized_path != self._timed_source_path
            or normalized_path in self._timed_warmed_paths
            or normalized_path == self._timed_warming_path
            or self._timed_sound_effect is None
        ):
            return
        try:
            is_loaded = getattr(self._timed_sound_effect, "isLoaded", None)
            loaded = bool(is_loaded()) if callable(is_loaded) else attempt >= 4
        except Exception:
            loaded = attempt >= 4
        try:
            from aqt.qt import QTimer
        except Exception:
            self._timed_warmed_paths.add(normalized_path)
            return
        if not loaded and attempt < 80:
            self._queue_timed_audio_callback(
                25,
                lambda path=normalized_path, next_attempt=attempt + 1: self._schedule_timed_sound_effect_warm_up(
                    path,
                    next_attempt,
                ),
            )
            return
        try:
            self._timed_sound_effect.stop()
            self._timed_sound_effect.setVolume(0.0)
            self._timed_sound_effect.play()
            self._timed_warming_path = normalized_path
            self._queue_timed_audio_callback(
                80,
                lambda path=normalized_path: self._finish_timed_sound_effect_warm_up(path),
            )
        except Exception:
            self._timed_warmed_paths.add(normalized_path)

    def _finish_timed_sound_effect_warm_up(self, normalized_path: str) -> None:
        if normalized_path != self._timed_warming_path:
            return
        try:
            if self._timed_sound_effect is not None:
                self._timed_sound_effect.stop()
                self._timed_sound_effect.setVolume(
                    self._qt_linear_volume(self._timed_volume_percent)
                )
        except Exception:
            pass
        self._timed_warming_path = ""
        self._timed_warmed_paths.add(normalized_path)

    def _schedule_timed_media_warm_up(self, normalized_path: str, attempt: int = 0) -> None:
        if (
            normalized_path != self._timed_source_path
            or normalized_path in self._timed_media_warmed_paths
            or normalized_path == self._timed_media_warming_path
            or self._timed_qt_player is None
        ):
            return
        try:
            status_fn = getattr(self._timed_qt_player, "mediaStatus", None)
            if callable(status_fn):
                status = status_fn()
                status_name = str(getattr(status, "name", status)).lower()
                loaded = any(token in status_name for token in ("loaded", "buffered"))
            else:
                loaded = attempt >= 4
        except Exception:
            loaded = attempt >= 4
        try:
            from aqt.qt import QTimer
        except Exception:
            self._timed_media_warmed_paths.add(normalized_path)
            return
        if not loaded and attempt < 80:
            self._queue_timed_audio_callback(
                25,
                lambda path=normalized_path, next_attempt=attempt + 1: self._schedule_timed_media_warm_up(
                    path,
                    next_attempt,
                ),
            )
            return
        try:
            self._set_player_muted(
                self._timed_qt_player,
                self._timed_qt_audio_output,
                True,
            )
            self._timed_qt_player.play()
            self._timed_media_warming_path = normalized_path
            self._queue_timed_audio_callback(
                100,
                lambda path=normalized_path: self._finish_timed_media_warm_up(path),
            )
        except Exception:
            self._timed_media_warmed_paths.add(normalized_path)

    def _finish_timed_media_warm_up(self, normalized_path: str) -> None:
        if normalized_path != self._timed_media_warming_path:
            return
        try:
            self._timed_qt_player.stop()
        except Exception:
            pass
        self._set_player_muted(
            self._timed_qt_player,
            self._timed_qt_audio_output,
            False,
        )
        self._set_qt_player_volume(
            self._timed_qt_player,
            self._timed_qt_audio_output,
            self._timed_volume_percent,
        )
        self._timed_media_warming_path = ""
        self._timed_media_warmed_paths.add(normalized_path)

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
                try:
                    relative_path = path.relative_to(self._addon_root)
                    if relative_path.parts[:2] == ("user_files", AUDIO_UPLOADS_DIRECTORY_NAME):
                        return relative_path.as_posix()
                except Exception:
                    pass
                return self._export_uploaded_file_for_browser(path)
            return ""
        for root in self._packaged_roots():
            path = root / Path(normalized)
            if path.exists():
                try:
                    return path.relative_to(self._addon_root).as_posix()
                except Exception:
                    return f"{root.name}/{normalized}".replace("\\", "/")
        return ""

    def _invalidate_catalog_cache(self) -> None:
        self._cached_options = None
        self._option_lookup = {}

    def _play_with_qt_player(
        self,
        path: Path,
        *,
        interrupt: bool,
        volume_percent: int,
        require_ready: bool = False,
    ) -> Optional[bool]:
        if path.suffix.lower() == ".wav":
            effect_result = self._play_with_qt_sound_effect(
                path,
                interrupt=interrupt,
                volume_percent=volume_percent,
                require_ready=require_ready,
            )
            if effect_result is not None:
                return effect_result
            if require_ready:
                # The answer-rating caller has an independent browser fallback.
                # Use it instead of retrying the unready WAV through another Qt
                # Multimedia class.
                return None

        normalized_path = str(path.resolve())
        prepared = self._prepare_qt_player(path)
        if prepared is None:
            return None
        player, audio_output = prepared
        self._remember_qt_player_volume(normalized_path, volume_percent)
        if not interrupt and self._feedback_channels_are_active():
            return False
        self._finish_warm_up(normalized_path)
        # Warm-up cleanup restores the channel's previous volume, so apply the
        # requested value (including an explicit mute) after cleanup.
        self._set_qt_player_volume(player, audio_output, volume_percent)
        try:
            set_position = getattr(player, "setPosition", None)
            if callable(set_position):
                set_position(0)
            player.play()
            self.last_playback_backend = "qt-media-player"
            self.last_playback_result = "accepted"
            return True
        except Exception:
            return None

    def _play_with_qt_sound_effect(
        self,
        path: Path,
        *,
        interrupt: bool,
        volume_percent: int,
        require_ready: bool = False,
    ) -> Optional[bool]:
        normalized_path = str(path.resolve())
        effect = self._prepare_qt_sound_effect(path)
        if effect is None:
            return None
        # Rating events supply an independent review-web fallback. Restrict the
        # readiness gate to those calls so Reveal and every unrelated cue retain
        # the exact non-blocking low-latency path they used before this hotfix.
        if require_ready and not self._qt_sound_effect_is_ready(effect):
            return None
        if not interrupt and self._feedback_channels_are_active():
            return False
        safe_volume = normalize_audio_volume_percent(volume_percent)
        self._qt_effect_volume_percents[normalized_path] = safe_volume
        self._finish_qt_sound_effect_warm_up(normalized_path)
        try:
            set_muted = getattr(effect, "setMuted", None)
            if callable(set_muted):
                set_muted(safe_volume <= 0)
            effect.setVolume(self._qt_linear_volume(safe_volume))
            # Each selected file owns its own persistent effect. Starting the
            # next card's effect therefore does not stop the rating/reveal cue
            # that is already finishing on another channel.
            effect.play()
            self.last_playback_backend = "qt-sound-effect"
            self.last_playback_result = "accepted"
            return True
        except Exception:
            return None

    @staticmethod
    def _qt_sound_effect_is_ready(effect: Any) -> bool:
        try:
            status_fn = getattr(effect, "status", None)
            if callable(status_fn):
                status = status_fn()
                status_name = str(getattr(status, "name", status)).lower()
                if "error" in status_name:
                    return False
                if "ready" in status_name:
                    return True
        except Exception:
            return False
        try:
            is_loaded = getattr(effect, "isLoaded", None)
            if callable(is_loaded):
                return bool(is_loaded())
        except Exception:
            return False
        # Older Qt bindings may not expose isLoaded().  Preserve their prior
        # behavior rather than disabling an otherwise functional fast path.
        return True

    def _prepare_feedback_channel(self, path: Path) -> bool:
        if path.suffix.lower() == ".wav" and self._prepare_qt_sound_effect(path) is not None:
            return True
        return self._prepare_qt_player(path) is not None

    def _prepare_qt_sound_effect(self, path: Path) -> Any:
        if not native_audio_enabled():
            return None
        normalized_path = str(path.resolve())
        existing = self._qt_effects.get(normalized_path)
        if existing is not None:
            return existing
        if self._qt_effect_supported is False:
            return None
        try:
            try:
                from aqt.qt import QSoundEffect
            except ImportError:
                from PyQt6.QtMultimedia import QSoundEffect
            from aqt.qt import QUrl

            effect = _new_audio_object(QSoundEffect)
            effect.setSource(QUrl.fromLocalFile(normalized_path))
            set_loop_count = getattr(effect, "setLoopCount", None)
            if callable(set_loop_count):
                set_loop_count(1)
            effect.setVolume(self._qt_linear_volume(DEFAULT_AUDIO_VOLUME_PERCENT))
            self._qt_effects[normalized_path] = effect
            self._qt_effect_volume_percents[normalized_path] = DEFAULT_AUDIO_VOLUME_PERCENT
            self._qt_effect_supported = True
            return effect
        except Exception:
            self._qt_effect_supported = False
            return None

    def _prepare_qt_player(self, path: Path) -> Optional[tuple[Any, Any]]:
        if not native_audio_enabled():
            return None
        normalized_path = str(path.resolve())
        existing = self._qt_players.get(normalized_path)
        if existing is not None:
            return existing
        if self._qt_player_supported is False:
            return None
        try:
            try:
                from aqt.qt import QMediaPlayer
            except ImportError:
                from PyQt6.QtMultimedia import QMediaPlayer
            from aqt.qt import QUrl
        except Exception:
            self._qt_player_supported = False
            return None
        try:
            player = _new_audio_object(QMediaPlayer)
            audio_output = None
            try:
                try:
                    from aqt.qt import QAudioOutput
                except ImportError:
                    from PyQt6.QtMultimedia import QAudioOutput

                audio_output = _new_audio_object(QAudioOutput)
                set_audio_output = getattr(player, "setAudioOutput", None)
                if callable(set_audio_output):
                    set_audio_output(audio_output)
            except Exception:
                audio_output = None
            source_url = QUrl.fromLocalFile(normalized_path)
            set_source = getattr(player, "setSource", None)
            if callable(set_source):
                set_source(source_url)
            else:
                from aqt.qt import QMediaContent

                player.setMedia(QMediaContent(source_url))
            self._set_qt_player_volume(player, audio_output, DEFAULT_AUDIO_VOLUME_PERCENT)
            prepared = (player, audio_output)
            self._qt_players[normalized_path] = prepared
            self._qt_player_volume_percents[normalized_path] = DEFAULT_AUDIO_VOLUME_PERCENT
            self._qt_player_supported = True
            return prepared
        except Exception:
            self._qt_player_supported = False
            return None

    def _start_warm_up(self, paths: tuple[str, ...]) -> None:
        for normalized_path in paths:
            self._schedule_qt_player_warm_up(normalized_path)

    def _schedule_qt_player_warm_up(self, normalized_path: str, attempt: int = 0) -> None:
        prepared = self._qt_players.get(normalized_path)
        if (
            prepared is None
            or normalized_path in self._warmed_paths
            or normalized_path in self._warming_paths
        ):
            return
        player, audio_output = prepared
        loaded = False
        try:
            status_fn = getattr(player, "mediaStatus", None)
            if callable(status_fn):
                status = status_fn()
                status_name = str(getattr(status, "name", status)).lower()
                loaded = any(token in status_name for token in ("loaded", "buffered"))
            else:
                loaded = attempt >= 4
        except Exception:
            loaded = attempt >= 4
        try:
            from aqt.qt import QTimer
        except Exception:
            self._warmed_paths.add(normalized_path)
            return
        if not loaded and attempt < 80:
            self._queue_audio_callback(
                25,
                lambda path=normalized_path, next_attempt=attempt + 1: self._schedule_qt_player_warm_up(
                    path,
                    next_attempt,
                ),
            )
            return
        try:
            self._set_player_muted(player, audio_output, True)
            player.play()
            self._warming_paths.add(normalized_path)
            self._queue_audio_callback(100, lambda path=normalized_path: self._finish_warm_up(path))
        except Exception:
            self._set_player_muted(player, audio_output, False)
            self._warmed_paths.add(normalized_path)

    def _schedule_qt_sound_effect_warm_up(self, normalized_path: str, attempt: int = 0) -> None:
        effect = self._qt_effects.get(normalized_path)
        if (
            effect is None
            or normalized_path in self._warmed_paths
            or normalized_path in self._warming_paths
        ):
            return
        try:
            is_loaded = getattr(effect, "isLoaded", None)
            loaded = bool(is_loaded()) if callable(is_loaded) else attempt >= 4
        except Exception:
            loaded = attempt >= 4
        try:
            from aqt.qt import QTimer
        except Exception:
            self._warmed_paths.add(normalized_path)
            return
        if not loaded and attempt < 80:
            self._queue_audio_callback(
                25,
                lambda path=normalized_path, next_attempt=attempt + 1: self._schedule_qt_sound_effect_warm_up(
                    path,
                    next_attempt,
                ),
            )
            return
        try:
            effect.setVolume(0.0)
            effect.play()
            self._warming_paths.add(normalized_path)
            self._queue_audio_callback(80, lambda path=normalized_path: self._finish_qt_sound_effect_warm_up(path))
        except Exception:
            self._warmed_paths.add(normalized_path)

    def _finish_qt_sound_effect_warm_up(self, normalized_path: str) -> None:
        if normalized_path not in self._warming_paths:
            return
        effect = self._qt_effects.get(normalized_path)
        if effect is not None:
            try:
                effect.stop()
                volume = self._qt_effect_volume_percents.get(
                    normalized_path,
                    DEFAULT_AUDIO_VOLUME_PERCENT,
                )
                effect.setVolume(self._qt_linear_volume(volume))
            except Exception:
                pass
        self._warming_paths.discard(normalized_path)
        self._warmed_paths.add(normalized_path)

    def _finish_warm_ups(self, paths: tuple[str, ...]) -> None:
        for normalized_path in paths:
            self._finish_warm_up(normalized_path)

    def _finish_warm_up(self, normalized_path: str) -> None:
        if normalized_path not in self._warming_paths:
            return
        prepared = self._qt_players.get(normalized_path)
        if prepared is not None:
            player, audio_output = prepared
            try:
                player.stop()
            except Exception:
                pass
            self._set_player_muted(player, audio_output, False)
        self._warming_paths.discard(normalized_path)
        self._warmed_paths.add(normalized_path)

    def _set_player_muted(self, player: Any, audio_output: Any, muted: bool) -> None:
        target = audio_output if audio_output is not None else player
        set_muted = getattr(target, "setMuted", None)
        if callable(set_muted):
            try:
                set_muted(bool(muted))
                return
            except Exception:
                pass
        try:
            if audio_output is not None:
                path = self._path_for_player(player)
                volume = self._qt_player_volume_percents.get(path, DEFAULT_AUDIO_VOLUME_PERCENT)
                audio_output.setVolume(0.0 if muted else self._qt_linear_volume(volume))
            else:
                path = self._path_for_player(player)
                volume = self._qt_player_volume_percents.get(path, DEFAULT_AUDIO_VOLUME_PERCENT)
                player.setVolume(0 if muted else round(self._qt_linear_volume(volume) * 100))
        except Exception:
            pass

    def _stop_qt_players(self, *, except_path: str = "") -> None:
        for normalized_path, (player, _audio_output) in self._qt_players.items():
            if normalized_path == except_path:
                continue
            try:
                player.stop()
            except Exception:
                pass

    def _ensure_timed_qt_player(self) -> Any:
        if not native_audio_enabled():
            return None
        if self._timed_qt_player_supported is False:
            return None
        if self._timed_qt_player is not None:
            return self._timed_qt_player
        try:
            try:
                from aqt.qt import QMediaPlayer
            except ImportError:
                from PyQt6.QtMultimedia import QMediaPlayer
        except Exception:
            self._timed_qt_player_supported = False
            return None
        try:
            player = _new_audio_object(QMediaPlayer)
            audio_output = None
            try:
                try:
                    from aqt.qt import QAudioOutput
                except ImportError:
                    from PyQt6.QtMultimedia import QAudioOutput

                audio_output = _new_audio_object(QAudioOutput)
                set_audio_output = getattr(player, "setAudioOutput", None)
                if callable(set_audio_output):
                    set_audio_output(audio_output)
            except Exception:
                audio_output = None
            self._timed_qt_player = player
            self._timed_qt_audio_output = audio_output
            self._timed_qt_player_supported = True
            return player
        except Exception:
            self._timed_qt_player_supported = False
            self._timed_qt_player = None
            self._timed_qt_audio_output = None
            return None

    def _ensure_timed_sound_effect(self) -> Any:
        if not native_audio_enabled():
            return None
        if self._timed_sound_effect_supported is False:
            return None
        if self._timed_sound_effect is not None:
            return self._timed_sound_effect
        try:
            try:
                from aqt.qt import QSoundEffect
            except ImportError:
                from PyQt6.QtMultimedia import QSoundEffect

            self._timed_sound_effect = _new_audio_object(QSoundEffect)
            self._timed_sound_effect_supported = True
            return self._timed_sound_effect
        except Exception:
            self._timed_sound_effect_supported = False
            self._timed_sound_effect = None
            return None

    def _qt_player_is_active(self, player: Any) -> bool:
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

    def _qt_players_are_active(self) -> bool:
        return any(self._qt_player_is_active(player) for player, _audio_output in self._qt_players.values())

    def _qt_effects_are_active(self) -> bool:
        for effect in self._qt_effects.values():
            try:
                is_playing = getattr(effect, "isPlaying", None)
                if callable(is_playing) and bool(is_playing()):
                    return True
            except Exception:
                continue
        return False

    def _feedback_channels_are_active(self) -> bool:
        return self._qt_effects_are_active() or self._qt_players_are_active()

    def _set_qt_player_volume(
        self,
        player: Any,
        audio_output: Any = None,
        volume_percent: int = DEFAULT_AUDIO_VOLUME_PERCENT,
    ) -> None:
        linear_volume = self._qt_linear_volume(volume_percent)
        try:
            if audio_output is not None:
                set_muted = getattr(audio_output, "setMuted", None)
                if callable(set_muted):
                    set_muted(linear_volume <= 0.0)
                audio_output.setVolume(linear_volume)
                return
        except Exception:
            pass
        try:
            set_muted = getattr(player, "setMuted", None)
            if callable(set_muted):
                set_muted(linear_volume <= 0.0)
            player.setVolume(round(linear_volume * 100))
        except Exception:
            pass

    def _remember_qt_player_volume(self, normalized_path: str, volume_percent: int) -> None:
        self._qt_player_volume_percents[normalized_path] = normalize_audio_volume_percent(volume_percent)

    def _path_for_player(self, target_player: Any) -> str:
        for normalized_path, (player, _audio_output) in self._qt_players.items():
            if player is target_player:
                return normalized_path
        return ""

    @staticmethod
    def _qt_linear_volume(volume_percent: int) -> float:
        # The slider's 100% center is deliberately half of Qt's available
        # linear output range, so 200% is a real 2x amplitude increase rather
        # than a cosmetic value that Qt silently clamps.
        return normalize_audio_volume_percent(volume_percent) / 200.0

    def _packaged_options(self) -> list[AudioFileOption]:
        options: list[AudioFileOption] = []
        seen_relative_paths: set[str] = set()
        for root in self._packaged_roots():
            if not root.exists():
                continue
            for path in sorted(root.rglob("*"), key=lambda item: _natural_sort_key(item.relative_to(root).as_posix())):
                if not path.is_file() or path.suffix.lower() not in _SUPPORTED_AUDIO_SUFFIXES:
                    continue
                if path.suffix.lower() != ".wav" and path.with_suffix(".wav").is_file():
                    # Keep the compressed sibling in the package as a legacy
                    # fallback, but show only the low-latency replacement in
                    # the selector so users do not see duplicate names.
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
            # When a packaged cue has both its old compressed version and a
            # low-latency PCM replacement, transparently migrate saved choices
            # to the WAV without resetting the user's per-event preference.
            # Uploaded files are explicit user choices and must never be
            # switched merely because another upload has the same stem.
            if candidate.startswith(_UPLOADED_AUDIO_KEY_PREFIX):
                return candidate
            candidate_path = Path(candidate)
            if candidate_path.suffix.lower() != ".wav":
                wav_candidate = candidate_path.with_suffix(".wav").as_posix()
                if wav_candidate in files:
                    return wav_candidate
            return candidate
        # v2.04 originally shipped its countdown cues as MP3. Preserve those
        # saved selections after moving the built-ins to low-latency PCM WAV.
        candidate_path = Path(candidate)
        stem_matches = [
            option
            for option in files
            if Path(option).parent == candidate_path.parent and Path(option).stem == candidate_path.stem
        ]
        if len(stem_matches) == 1:
            return stem_matches[0]
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

    def _is_safe_upload_key(self, value: str) -> bool:
        candidate = str(value or "").strip().replace("\\", "/")
        if not candidate.startswith(_UPLOADED_AUDIO_KEY_PREFIX):
            return False
        uploaded_name = candidate[len(_UPLOADED_AUDIO_KEY_PREFIX) :]
        return (
            bool(uploaded_name)
            and Path(uploaded_name).name == uploaded_name
            and Path(uploaded_name).suffix.lower() in _SUPPORTED_AUDIO_SUFFIXES
        )

    def _export_uploaded_file_for_browser(self, source: Path) -> str:
        """Mirror a profile upload into Anki's add-on web-export directory.

        Profile data intentionally lives outside the installed add-on folder,
        while Anki's ``/_addons/`` web route can only serve files underneath
        that folder. A content-addressed mirror makes uploaded MP3/OGG/etc.
        available to the smooth browser player without changing the canonical
        profile copy or allowing browser cache collisions between profiles.
        """

        try:
            digest = hashlib.sha256()
            with source.open("rb") as input_file:
                for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
                    digest.update(chunk)
            safe_stem = self._sanitize_file_stem(source.stem)
            mirrored_name = f"{safe_stem}-{digest.hexdigest()[:16]}{source.suffix.lower()}"
            mirror_root = self._addon_root / "user_files" / AUDIO_UPLOADS_DIRECTORY_NAME / "web_cache"
            mirror_root.mkdir(parents=True, exist_ok=True)
            destination = mirror_root / mirrored_name
            if not destination.exists() or destination.stat().st_size != source.stat().st_size:
                shutil.copy2(source, destination)
            return destination.relative_to(self._addon_root).as_posix()
        except Exception:
            return ""

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
