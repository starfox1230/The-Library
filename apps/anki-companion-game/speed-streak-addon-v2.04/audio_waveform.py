from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
import wave


@dataclass(frozen=True)
class AudioWaveform:
    peaks: tuple[float, ...]
    duration_ms: int
    visible_ms: int
    available: bool
    message: str = ""


def load_audio_waveform(
    path: str | Path,
    *,
    visible_ms: int = 1000,
    point_count: int = 320,
) -> AudioWaveform:
    """Read a compact peak envelope for the selectable first second of a WAV.

    Countdown cues repeat every second, so sync points are intentionally kept
    inside the first second. Reading only that window keeps uploaded files from
    making the settings screen slow even when the source clip is very long.
    """

    safe_visible_ms = max(1, int(visible_ms or 1000))
    safe_point_count = max(32, min(1200, int(point_count or 320)))
    source = Path(path)
    if source.suffix.lower() != ".wav":
        return AudioWaveform(
            peaks=(),
            duration_ms=0,
            visible_ms=safe_visible_ms,
            available=False,
            message="Waveform preview is available for WAV files. Timing preview still works for this clip.",
        )
    try:
        with wave.open(str(source), "rb") as audio:
            if audio.getcomptype() != "NONE":
                raise ValueError("compressed WAV")
            channel_count = max(1, int(audio.getnchannels()))
            sample_width = int(audio.getsampwidth())
            sample_rate = max(1, int(audio.getframerate()))
            total_frames = max(0, int(audio.getnframes()))
            duration_ms = int(round((total_frames / sample_rate) * 1000))
            visible_frames = min(
                total_frames,
                max(1, int(round(sample_rate * (safe_visible_ms / 1000)))),
            )
            if visible_frames <= 0 or sample_width not in {1, 2, 3, 4}:
                raise ValueError("unsupported PCM layout")
            frames_per_point = max(1, (visible_frames + safe_point_count - 1) // safe_point_count)
            raw_peaks: list[int] = []
            frames_read = 0
            while frames_read < visible_frames:
                requested = min(frames_per_point, visible_frames - frames_read)
                raw = audio.readframes(requested)
                if not raw:
                    break
                raw_peaks.append(_pcm_peak(raw, sample_width, channel_count))
                frames_read += requested
    except Exception:
        try:
            raw_peaks, duration_ms = _load_riff_wave_peaks(
                source,
                visible_ms=safe_visible_ms,
                point_count=safe_point_count,
            )
        except Exception:
            return AudioWaveform(
                peaks=(),
                duration_ms=0,
                visible_ms=safe_visible_ms,
                available=False,
                message="This WAV uses an audio layout that cannot be drawn here. Timing preview still works.",
            )

    strongest = max(raw_peaks, default=0)
    if strongest <= 0:
        peaks = tuple(0.04 for _ in raw_peaks)
    else:
        peaks = tuple(max(0.025, min(1.0, peak / strongest)) for peak in raw_peaks)
    return AudioWaveform(
        peaks=peaks,
        duration_ms=max(0, duration_ms),
        visible_ms=safe_visible_ms,
        available=bool(peaks),
    )


def _pcm_peak(raw: bytes, sample_width: int, channel_count: int) -> int:
    del channel_count  # Every interleaved channel sample contributes equally.
    if sample_width == 1:
        return max((abs(value - 128) for value in raw), default=0)
    peak = 0
    byte_order = "little"
    for offset in range(0, len(raw) - sample_width + 1, sample_width):
        sample = int.from_bytes(
            raw[offset : offset + sample_width],
            byteorder=byte_order,
            signed=True,
        )
        peak = max(peak, abs(sample))
    return peak


def _load_riff_wave_peaks(
    source: Path,
    *,
    visible_ms: int,
    point_count: int,
) -> tuple[list[int], int]:
    """Read PCM and IEEE-float RIFF WAVs unsupported by older Python builds.

    Python versions bundled with some Anki releases reject WAVE_FORMAT_EXTENSIBLE,
    even when it contains ordinary PCM. The lightweight parser reads only the
    first visible second and therefore also remains responsive for large uploads.
    """

    with source.open("rb") as handle:
        header = handle.read(12)
        if len(header) != 12 or header[:4] != b"RIFF" or header[8:12] != b"WAVE":
            raise ValueError("not a little-endian RIFF WAVE")
        format_data = b""
        data_offset = -1
        data_size = 0
        while True:
            chunk_header = handle.read(8)
            if len(chunk_header) < 8:
                break
            chunk_id, chunk_size = struct.unpack("<4sI", chunk_header)
            chunk_start = handle.tell()
            if chunk_id == b"fmt ":
                format_data = handle.read(min(chunk_size, 64))
            elif chunk_id == b"data":
                data_offset = chunk_start
                data_size = chunk_size
            handle.seek(chunk_start + chunk_size + (chunk_size & 1))
        if len(format_data) < 16 or data_offset < 0:
            raise ValueError("missing WAV format or data")
        format_tag, channels, sample_rate, _byte_rate, block_align, bits_per_sample = struct.unpack(
            "<HHIIHH",
            format_data[:16],
        )
        if format_tag == 0xFFFE and len(format_data) >= 26:
            format_tag = struct.unpack("<H", format_data[24:26])[0]
        if format_tag not in {1, 3} or channels <= 0 or sample_rate <= 0 or block_align <= 0:
            raise ValueError("unsupported WAV encoding")
        sample_width = max(1, (bits_per_sample + 7) // 8)
        total_frames = data_size // block_align
        duration_ms = int(round((total_frames / sample_rate) * 1000))
        visible_frames = min(
            total_frames,
            max(1, int(round(sample_rate * (visible_ms / 1000)))),
        )
        frames_per_point = max(1, (visible_frames + point_count - 1) // point_count)
        handle.seek(data_offset)
        peaks: list[int] = []
        frames_read = 0
        while frames_read < visible_frames:
            requested = min(frames_per_point, visible_frames - frames_read)
            raw = handle.read(requested * block_align)
            if not raw:
                break
            if format_tag == 3 and sample_width == 4:
                values = struct.iter_unpack("<f", raw[: len(raw) - (len(raw) % 4)])
                peak = int(max((abs(value[0]) for value in values), default=0.0) * 2_147_483_647)
            else:
                peak = _pcm_peak(raw, sample_width, channels)
            peaks.append(peak)
            frames_read += requested
    if not peaks:
        raise ValueError("empty WAV")
    return peaks, duration_ms
