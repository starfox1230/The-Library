from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = APP_DIR / ".env"


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}.") from exc


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    model: str
    transcription_prompt: str | None
    recordings_dir: Path
    ffmpeg_path: str | None
    frame_rate: int
    video_crf: int
    transcription_audio_bitrate_kbps: int
    toggle_recording_hotkey: str
    add_chapter_hotkey: str
    anatomy_capture_hotkey: str


def load_config() -> AppConfig:
    load_dotenv(ENV_PATH)

    recordings_value = os.getenv("RECORDINGS_DIR", "recordings").strip() or "recordings"
    recordings_dir = Path(recordings_value)
    if not recordings_dir.is_absolute():
        recordings_dir = APP_DIR / recordings_dir
    recordings_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg_path = os.getenv("FFMPEG_PATH", "").strip() or None
    return AppConfig(
        api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        model=(
            os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe").strip()
            or "gpt-4o-mini-transcribe"
        ),
        transcription_prompt=os.getenv("OPENAI_TRANSCRIBE_PROMPT", "").strip() or None,
        recordings_dir=recordings_dir,
        ffmpeg_path=ffmpeg_path,
        frame_rate=max(1, _int_env("FRAME_RATE", 30)),
        video_crf=min(51, max(0, _int_env("VIDEO_CRF", 23))),
        transcription_audio_bitrate_kbps=max(
            16, _int_env("TRANSCRIPTION_AUDIO_BITRATE_KBPS", 48)
        ),
        toggle_recording_hotkey=(
            os.getenv("TOGGLE_RECORDING_HOTKEY", "<f8>").strip() or "<f8>"
        ),
        add_chapter_hotkey=(
            os.getenv("ADD_CHAPTER_HOTKEY", "<f9>").strip() or "<f9>"
        ),
        anatomy_capture_hotkey=(
            os.getenv("ANATOMY_CAPTURE_HOTKEY", "<f10>").strip() or "<f10>"
        ),
    )
