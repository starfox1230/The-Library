from __future__ import annotations

import audioop
import threading
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pyaudiowpatch as pyaudio


@dataclass(frozen=True)
class AudioDevice:
    index: int
    name: str
    sample_rate: int
    channels: int
    is_default: bool


@dataclass(frozen=True)
class AudioStartInfo:
    device: AudioDevice
    started_monotonic: float


def list_loopback_devices() -> list[AudioDevice]:
    devices: list[AudioDevice] = []
    with pyaudio.PyAudio() as manager:
        try:
            default = manager.get_default_wasapi_loopback()
            default_index = int(default["index"])
        except (OSError, KeyError):
            default_index = -1

        for raw in manager.get_loopback_device_info_generator():
            channels = int(raw.get("maxInputChannels", 0))
            if channels <= 0:
                continue
            devices.append(
                AudioDevice(
                    index=int(raw["index"]),
                    name=str(raw["name"]),
                    sample_rate=int(float(raw["defaultSampleRate"])),
                    channels=min(2, channels),
                    is_default=int(raw["index"]) == default_index,
                )
            )
    devices.sort(key=lambda item: (not item.is_default, item.name.casefold()))
    return devices


class LoopbackRecorder:
    def __init__(self, level_callback: Callable[[float], None] | None = None) -> None:
        self._level_callback = level_callback
        self._manager: pyaudio.PyAudio | None = None
        self._stream: object | None = None
        self._wave: wave.Wave_write | None = None
        self._path: Path | None = None
        self._device: AudioDevice | None = None
        self._started_monotonic = 0.0
        self._frames_written = 0
        self._lock = threading.Lock()
        self._warnings: list[str] = []
        self._last_callback_monotonic = 0.0

    @property
    def started_monotonic(self) -> float:
        return self._started_monotonic

    @property
    def device(self) -> AudioDevice | None:
        return self._device

    @property
    def warnings(self) -> tuple[str, ...]:
        return tuple(self._warnings)

    @property
    def seconds_since_audio_callback(self) -> float:
        if not self._last_callback_monotonic:
            return max(0.0, time.perf_counter() - self._started_monotonic)
        return max(0.0, time.perf_counter() - self._last_callback_monotonic)

    def start(self, path: Path, device_index: int | None = None) -> AudioStartInfo:
        if self._stream is not None:
            raise RuntimeError("System audio recording is already running.")

        manager = pyaudio.PyAudio()
        try:
            raw = (
                manager.get_default_wasapi_loopback()
                if device_index is None
                else manager.get_device_info_by_index(device_index)
            )
            if not raw.get("isLoopbackDevice", False):
                raw = manager.get_wasapi_loopback_analogue_by_dict(raw)

            device = AudioDevice(
                index=int(raw["index"]),
                name=str(raw["name"]),
                sample_rate=int(float(raw["defaultSampleRate"])),
                channels=min(2, int(raw["maxInputChannels"])),
                is_default=device_index is None,
            )
            if device.channels <= 0:
                raise RuntimeError(f"{device.name} is not a loopback recording device.")

            path.parent.mkdir(parents=True, exist_ok=True)
            wave_file = wave.open(str(path), "wb")
            wave_file.setnchannels(device.channels)
            wave_file.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            wave_file.setframerate(device.sample_rate)

            self._manager = manager
            self._wave = wave_file
            self._path = path
            self._device = device
            self._started_monotonic = time.perf_counter()
            self._last_callback_monotonic = 0.0
            self._frames_written = 0
            self._warnings = []

            self._stream = manager.open(
                format=pyaudio.paInt16,
                channels=device.channels,
                rate=device.sample_rate,
                frames_per_buffer=1024,
                input=True,
                input_device_index=device.index,
                stream_callback=self._on_audio,
            )
            self._stream.start_stream()
            return AudioStartInfo(device=device, started_monotonic=self._started_monotonic)
        except Exception:
            if self._wave is not None:
                self._wave.close()
            manager.terminate()
            self._manager = None
            self._wave = None
            self._path = None
            self._device = None
            raise

    def stop(self) -> Path:
        stream = self._stream
        manager = self._manager
        wave_file = self._wave
        path = self._path
        device = self._device
        if stream is None or manager is None or wave_file is None or path is None or device is None:
            raise RuntimeError("System audio recording is not running.")

        self._stream = None
        try:
            stream.stop_stream()
            stream.close()
            with self._lock:
                expected_frames = int(
                    max(0.0, time.perf_counter() - self._started_monotonic)
                    * device.sample_rate
                )
                missing = max(0, expected_frames - self._frames_written)
                if missing:
                    wave_file.writeframes(
                        b"\x00" * missing * device.channels * pyaudio.get_sample_size(pyaudio.paInt16)
                    )
                    self._frames_written += missing
                wave_file.close()
        finally:
            manager.terminate()
            self._manager = None
            self._wave = None
            self._path = None
            self._device = None
        return path

    def abort(self) -> None:
        if self._stream is None:
            return
        try:
            self.stop()
        except Exception:
            pass

    def _on_audio(
        self,
        in_data: bytes,
        frame_count: int,
        _time_info: object,
        status_flags: int,
    ) -> tuple[bytes, int]:
        now = time.perf_counter()
        if status_flags:
            self._warnings.append(f"PortAudio status: {status_flags}")

        wave_file = self._wave
        device = self._device
        if wave_file is not None and device is not None:
            with self._lock:
                expected_before = max(
                    0,
                    int((now - self._started_monotonic) * device.sample_rate) - frame_count,
                )
                missing = max(0, expected_before - self._frames_written)
                if missing:
                    wave_file.writeframes(
                        b"\x00" * missing * device.channels * pyaudio.get_sample_size(pyaudio.paInt16)
                    )
                    self._frames_written += missing
                wave_file.writeframes(in_data)
                self._frames_written += frame_count

        self._last_callback_monotonic = now
        if self._level_callback and in_data:
            rms = audioop.rms(in_data, 2)
            self._level_callback(min(1.0, rms / 10000.0))
        return in_data, pyaudio.paContinue

