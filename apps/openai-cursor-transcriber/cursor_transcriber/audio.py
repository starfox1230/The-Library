from __future__ import annotations

import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Event, Lock

import sounddevice


@dataclass(frozen=True)
class RecordingResult:
    path: Path
    warnings: tuple[str, ...]


class MicrophoneRecorder:
    def __init__(self, runtime_dir: Path, sample_rate_hz: int, channels: int) -> None:
        self._runtime_dir = runtime_dir
        self._sample_rate_hz = sample_rate_hz
        self._channels = channels
        self._stream: sounddevice.RawInputStream | None = None
        self._wave_file: wave.Wave_write | None = None
        self._wave_path: Path | None = None
        self._warnings: list[str] = []
        self._lock = Lock()
        self._received_first_chunk = Event()

    def start(self) -> Path:
        if self._stream is not None:
            raise RuntimeError("The microphone recorder is already running.")

        self._runtime_dir.mkdir(parents=True, exist_ok=True)
        self._wave_path = self._runtime_dir / f"recording-{datetime.now():%Y%m%d-%H%M%S}.wav"
        self._wave_file = wave.open(str(self._wave_path), "wb")
        self._wave_file.setnchannels(self._channels)
        self._wave_file.setsampwidth(2)
        self._wave_file.setframerate(self._sample_rate_hz)
        self._warnings = []
        self._received_first_chunk.clear()

        self._stream = sounddevice.RawInputStream(
            samplerate=self._sample_rate_hz,
            channels=self._channels,
            dtype="int16",
            callback=self._on_audio,
        )
        self._stream.start()
        return self._wave_path

    def stop(self) -> RecordingResult:
        stream = self._stream
        wave_file = self._wave_file
        wave_path = self._wave_path

        if stream is None or wave_file is None or wave_path is None:
            raise RuntimeError("The microphone recorder is not running.")

        self._stream = None
        self._wave_file = None
        self._wave_path = None

        stream.stop()
        stream.close()
        with self._lock:
            wave_file.close()

        return RecordingResult(path=wave_path, warnings=tuple(self._warnings))

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
        return self._received_first_chunk.is_set()

    def _on_audio(self, indata: bytes, _frames: int, _time: object, status: sounddevice.CallbackFlags) -> None:
        if status:
            self._warnings.append(str(status))
        if indata:
            self._received_first_chunk.set()
        with self._lock:
            if self._wave_file is not None:
                self._wave_file.writeframes(indata)
