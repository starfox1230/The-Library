from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .helpers import hotkey_to_label, parse_hotkey_list

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False


APP_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = APP_DIR / ".env"


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    model: str
    transcription_prompt: str | None
    toggle_hotkey: str
    toggle_hotkey_label: str
    exit_hotkey: str
    exit_hotkey_label: str
    paste_hotkeys: tuple[str, ...]
    max_recording_seconds: int
    sample_rate_hz: int
    channels: int
    overlay_offset_x: int
    overlay_offset_y: int
    overlay_max_width: int
    runtime_dir: Path


def _get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(
            "OPENAI_API_KEY is missing.\n\n"
            f"Add it to:\n{ENV_PATH}\n\n"
            "Example:\nOPENAI_API_KEY=sk-..."
        )
    return value


def _get_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw_value!r}.") from exc


def load_config() -> AppConfig:
    load_dotenv(ENV_PATH)

    runtime_dir = APP_DIR / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    toggle_hotkey = os.getenv("TOGGLE_HOTKEY", "<f3>").strip() or "<f3>"
    exit_hotkey = os.getenv("EXIT_HOTKEY", "<shift>+<f3>").strip() or "<shift>+<f3>"
    paste_hotkeys = parse_hotkey_list(
        os.getenv("PASTE_HOTKEYS", "<ctrl>+v,<ctrl>+<shift>+v,<shift>+<insert>")
    )

    return AppConfig(
        api_key=_get_required_env("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe").strip() or "gpt-4o-transcribe",
        transcription_prompt=os.getenv("OPENAI_TRANSCRIBE_PROMPT", "").strip() or None,
        toggle_hotkey=toggle_hotkey,
        toggle_hotkey_label=hotkey_to_label(toggle_hotkey),
        exit_hotkey=exit_hotkey,
        exit_hotkey_label=hotkey_to_label(exit_hotkey),
        paste_hotkeys=paste_hotkeys,
        max_recording_seconds=_get_int("MAX_RECORDING_SECONDS", 60),
        sample_rate_hz=_get_int("SAMPLE_RATE_HZ", 16000),
        channels=_get_int("CHANNELS", 1),
        overlay_offset_x=_get_int("OVERLAY_OFFSET_X", 24),
        overlay_offset_y=_get_int("OVERLAY_OFFSET_Y", 24),
        overlay_max_width=_get_int("OVERLAY_MAX_WIDTH", 360),
        runtime_dir=runtime_dir,
    )
