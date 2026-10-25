from __future__ import annotations

import logging
import sys
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Event
from time import perf_counter

import sounddevice


@dataclass(frozen=True)
class RecordingResult:
    path: Path
    warnings: tuple[str, ...]
    capture_error: str | None = None


def _input_candidates() -> list[tuple[str, dict[str, object]]]:
    """Prefer shared WASAPI without device effects on Windows."""
    candidates: list[tuple[str, dict[str, object]]] = []
    if sys.platform == "win32":
        for api in sounddevice.query_hostapis():
            if api["name"] == "Windows WASAPI" and api["default_input_device"] >= 0:
                device = api["default_input_device"]
                raw = sounddevice.WasapiSettings(auto_convert=True)
                # sounddevice exposes this PortAudio option in its CFFI
                # structure, but has no public raw-mode constructor argument.
                raw._streaminfo.streamOption = sounddevice._lib.eStreamOptionRaw
                candidates.append(("Windows WASAPI raw", {"device": device, "extra_settings": raw}))
                candidates.append(("Windows WASAPI", {
                    "device": device,
                    "extra_settings": sounddevice.WasapiSettings(auto_convert=True),
                }))
                break
    candidates.append(("PortAudio default", {}))
    return candidates


class MicrophoneRecorder:
    def __init__(self, runtime_dir: Path, sample_rate_hz: int, channels: int) -> None:
        self._runtime_dir = runtime_dir
        self._sample_rate_hz = sample_rate_hz
        self._channels = channels
        self._stream: sounddevice.RawInputStream | None = None
        self._wave_path: Path | None = None
        self._audio_chunks: list[bytes] = []
        self._warnings: list[str] = []
        self._received_first_chunk = Event()
        self._started_at = 0.0
        self._backend = ""

    def start(self) -> Path:
        if self._stream is not None:
            raise RuntimeError("The microphone recorder is already running.")

        self._runtime_dir.mkdir(parents=True, exist_ok=True)
        self._wave_path = self._runtime_dir / f"recording-{datetime.now():%Y%m%d-%H%M%S}.wav"
        self._audio_chunks = []
        self._warnings = []
        self._received_first_chunk.clear()

        for backend, options in _input_candidates():
            stream = None
            try:
                stream = sounddevice.RawInputStream(
                    samplerate=self._sample_rate_hz,
                    channels=self._channels,
                    dtype="int16",
                    callback=self._on_audio,
                    **options,
                )
                self._started_at = perf_counter()
                stream.start()
            except sounddevice.PortAudioError:
                if stream is not None:
                    stream.close()
                if backend == "PortAudio default":
                    raise
                logging.warning("Could not open %s input; trying the next backend", backend, exc_info=True)
                self._audio_chunks = []
                self._warnings = []
                self._received_first_chunk.clear()
                continue
            self._stream = stream
            self._backend = backend
            logging.info("Audio input: %s, %s Hz, %s channel(s)", backend, self._sample_rate_hz, self._channels)
            break
        return self._wave_path

    def stop(self) -> RecordingResult:
        stream = self._stream
        wave_path = self._wave_path

        if stream is None or wave_path is None:
            raise RuntimeError("The microphone recorder is not running.")

        self._stream = None
        self._wave_path = None

        was_active = stream.active
        elapsed_seconds = perf_counter() - self._started_at
        try:
            stream.stop()
        finally:
            stream.close()

        audio = b"".join(self._audio_chunks)
        captured_seconds = len(audio) / (2 * self._channels * self._sample_rate_hz)
        logging.info("Audio capture: %.3f seconds captured in %.3f seconds via %s; stream active=%s",
                     captured_seconds, elapsed_seconds, self._backend, was_active)
        capture_error = None
        if not was_active or (elapsed_seconds >= 1 and captured_seconds < elapsed_seconds * 0.5):
            capture_error = "Audio capture stopped unexpectedly. Press F3 to record again."
        elif captured_seconds < 0.1:
            capture_error = "The recording was too short to transcribe. Press F3 and try again."
        elif not any(audio):
            capture_error = "No microphone signal was captured. Press F3 to record again."

        # Keep disk I/O out of PortAudio's real-time callback.
        with wave.open(str(wave_path), "wb") as wave_file:
            wave_file.setnchannels(self._channels)
            wave_file.setsampwidth(2)
            wave_file.setframerate(self._sample_rate_hz)
            wave_file.writeframes(audio)
        self._audio_chunks = []

        return RecordingResult(path=wave_path, warnings=tuple(self._warnings), capture_error=capture_error)

    def discard(self) -> None:
        if self._stream is not None:
            result = self.stop()
            self.cleanup(result.path)

    @staticmethod
    def cleanup(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    def has_received_audio(self) -> bool:
        return self._received_first_chunk.is_set() and self.is_active()

    def is_active(self) -> bool:
        return self._stream is not None and self._stream.active

    def _on_audio(self, indata: bytes, _frames: int, _time: object, status: sounddevice.CallbackFlags) -> None:
        if status:
            self._warnings.append(str(status))
        if indata:
            self._received_first_chunk.set()
            self._audio_chunks.append(bytes(indata))
