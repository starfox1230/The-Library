from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from .models import CaptureRegion
from .source_timeline import TimelinePiece


class MediaError(RuntimeError):
    """Raised when FFmpeg capture or processing fails."""


def _winget_ffmpeg_candidates() -> list[Path]:
    local_app_data = os.getenv("LOCALAPPDATA", "").strip()
    if not local_app_data:
        return []
    packages = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
    if not packages.exists():
        return []
    return sorted(
        packages.glob("Gyan.FFmpeg*/*/bin/ffmpeg.exe"),
        reverse=True,
    )


def resolve_ffmpeg(configured_path: str | None = None) -> Path:
    candidates: list[Path] = []
    if configured_path:
        candidates.append(Path(configured_path).expanduser())
    discovered = shutil.which("ffmpeg")
    if discovered:
        candidates.append(Path(discovered))
    candidates.extend(_winget_ffmpeg_candidates())

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise MediaError(
        "FFmpeg was not found. Install it with `winget install Gyan.FFmpeg`, "
        "or set FFMPEG_PATH in .env."
    )


def resolve_ffprobe(ffmpeg_path: Path) -> Path:
    adjacent = ffmpeg_path.with_name("ffprobe.exe")
    if adjacent.is_file():
        return adjacent
    discovered = shutil.which("ffprobe")
    if discovered:
        return Path(discovered).resolve()
    raise MediaError("ffprobe.exe was not found beside FFmpeg or on PATH.")


def _run_checked(
    arguments: Sequence[str],
    *,
    progress_callback: Callable[[str], None] | None = None,
) -> subprocess.CompletedProcess[str]:
    if progress_callback:
        progress_callback(" ".join(arguments[1:4]))
    result = subprocess.run(
        list(arguments),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise MediaError(details or f"Command failed with exit code {result.returncode}.")
    return result


def probe_duration(ffprobe_path: Path, media_path: Path) -> float:
    result = _run_checked(
        [
            str(ffprobe_path),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(media_path),
        ]
    )
    try:
        payload = json.loads(result.stdout)
        return max(0.0, float(payload["format"]["duration"]))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise MediaError(f"Could not read duration from {media_path.name}.") from exc


@dataclass(frozen=True)
class ScreenStartInfo:
    started_monotonic: float
    command: tuple[str, ...]


class ScreenRecorder:
    def __init__(self, ffmpeg_path: Path, frame_rate: int, video_crf: int) -> None:
        self._ffmpeg_path = ffmpeg_path
        self._frame_rate = frame_rate
        self._video_crf = video_crf
        self._process: subprocess.Popen[str] | None = None
        self._log_handle: object | None = None
        self._output_path: Path | None = None
        self._started_monotonic = 0.0

    @property
    def started_monotonic(self) -> float:
        return self._started_monotonic

    def start(self, region: CaptureRegion, output_path: Path) -> ScreenStartInfo:
        if self._process is not None:
            raise MediaError("Screen recording is already running.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        log_path = output_path.with_suffix(".ffmpeg.log")
        command = [
            str(self._ffmpeg_path),
            "-hide_banner",
            "-loglevel",
            "warning",
            "-y",
            "-f",
            "gdigrab",
            "-framerate",
            str(self._frame_rate),
            "-offset_x",
            str(region.x),
            "-offset_y",
            str(region.y),
            "-video_size",
            region.ffmpeg_size(),
            "-draw_mouse",
            "1",
            "-i",
            "desktop",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            str(self._video_crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]

        log_handle = log_path.open("w", encoding="utf-8")
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=log_handle,
                stderr=log_handle,
                text=True,
                encoding="utf-8",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception:
            log_handle.close()
            raise

        self._process = process
        self._log_handle = log_handle
        self._output_path = output_path
        self._started_monotonic = time.perf_counter()
        time.sleep(0.15)
        if process.poll() is not None:
            self._close_log()
            self._process = None
            details = log_path.read_text(encoding="utf-8", errors="replace")
            raise MediaError(details.strip() or "FFmpeg could not start screen capture.")
        return ScreenStartInfo(
            started_monotonic=self._started_monotonic,
            command=tuple(command),
        )

    def stop(self, timeout_seconds: float = 15.0) -> Path:
        process = self._process
        output_path = self._output_path
        if process is None or output_path is None:
            raise MediaError("Screen recording is not running.")
        self._process = None
        self._output_path = None

        try:
            if process.stdin:
                try:
                    process.stdin.write("q\n")
                    process.stdin.flush()
                except (BrokenPipeError, OSError):
                    pass
            try:
                process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        finally:
            self._close_log()

        if process.returncode not in (0, 255) or not output_path.is_file():
            raise MediaError("FFmpeg did not finish a usable screen recording.")
        return output_path

    def abort(self) -> None:
        if self._process is None:
            return
        try:
            self.stop(timeout_seconds=3)
        except Exception:
            pass

    def _close_log(self) -> None:
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None


@dataclass(frozen=True)
class ProcessedMedia:
    recording_path: Path
    audio_path: Path
    duration_seconds: float


def extract_last_frame(
    ffmpeg_path: Path,
    screen_path: Path,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run_checked(
        [
            str(ffmpeg_path),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-sseof",
            "-0.12",
            "-i",
            str(screen_path),
            "-frames:v",
            "1",
            "-update",
            "1",
            str(output_path),
        ]
    )
    if not output_path.is_file():
        raise MediaError("Could not extract the paused video frame.")
    return output_path


def _write_concat_list(paths: Sequence[Path], list_path: Path) -> None:
    def escaped(path: Path) -> str:
        return str(path.resolve()).replace("\\", "/").replace("'", "'\\''")

    list_path.write_text(
        "\n".join(f"file '{escaped(path)}'" for path in paths) + "\n",
        encoding="utf-8",
    )


def concatenate_segments(
    ffmpeg_path: Path,
    ffprobe_path: Path,
    recording_segments: Sequence[Path],
    audio_segments: Sequence[Path],
    recording_path: Path,
    audio_path: Path,
    playback_path: Path,
    progress_callback: Callable[[str], None] | None = None,
) -> ProcessedMedia:
    if not recording_segments or len(recording_segments) != len(audio_segments):
        raise MediaError("No complete recording segments are available to combine.")

    recording_path.parent.mkdir(parents=True, exist_ok=True)
    video_list = recording_path.parent / ".video-segments.txt"
    audio_list = recording_path.parent / ".audio-segments.txt"
    _write_concat_list(recording_segments, video_list)
    _write_concat_list(audio_segments, audio_list)
    try:
        if progress_callback:
            progress_callback("Joining study segments…")
        _run_checked(
            [
                str(ffmpeg_path),
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(video_list),
                "-c",
                "copy",
                str(recording_path),
            ]
        )
        _run_checked(
            [
                str(ffmpeg_path),
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(audio_list),
                "-c",
                "copy",
                str(audio_path),
            ]
        )
        if progress_callback:
            progress_callback("Creating review-friendly video…")
        _run_checked(
            [
                str(ffmpeg_path),
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(recording_path),
                "-map",
                "0:v:0",
                "-map",
                "0:a:0",
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(playback_path),
            ]
        )
    finally:
        for list_path in (video_list, audio_list):
            list_path.unlink(missing_ok=True)

    duration = min(
        probe_duration(ffprobe_path, recording_path),
        probe_duration(ffprobe_path, audio_path),
    )
    return ProcessedMedia(recording_path, audio_path, duration)


def render_source_timeline(
    ffmpeg_path: Path,
    ffprobe_path: Path,
    pieces: Sequence[TimelinePiece],
    recording_segments: dict[int, Path],
    audio_segments: dict[int, Path],
    recording_path: Path,
    audio_path: Path,
    playback_path: Path,
    video_crf: int,
    audio_bitrate_kbps: int,
    progress_callback: Callable[[str], None] | None = None,
) -> ProcessedMedia:
    if not pieces:
        raise MediaError("No browser-linked source coverage is available to render.")
    clips_dir = recording_path.parent / ".source-timeline-clips"
    if clips_dir.exists():
        shutil.rmtree(clips_dir)
    clips_dir.mkdir(parents=True)
    video_clips: list[Path] = []
    audio_clips: list[Path] = []
    try:
        total = len(pieces)
        for index, piece in enumerate(pieces, start=1):
            source_recording = recording_segments.get(piece.segment_index)
            source_audio = audio_segments.get(piece.segment_index)
            if (
                source_recording is None
                or source_audio is None
                or not source_recording.is_file()
                or not source_audio.is_file()
            ):
                raise MediaError(
                    f"Source segment {piece.segment_index} is unavailable."
                )
            start = max(0.0, piece.recording_start_seconds)
            duration = max(
                0.04,
                piece.recording_end_seconds - piece.recording_start_seconds,
            )
            video_clip = clips_dir / f"clip-{index:04d}.mkv"
            audio_clip = clips_dir / f"clip-{index:04d}.mp3"
            if progress_callback:
                progress_callback(
                    f"Building clean source timeline {index} of {total}…"
                )
            _run_checked(
                [
                    str(ffmpeg_path),
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-ss",
                    f"{start:.6f}",
                    "-t",
                    f"{duration:.6f}",
                    "-i",
                    str(source_recording),
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a:0",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    str(video_crf),
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "160k",
                    str(video_clip),
                ]
            )
            _run_checked(
                [
                    str(ffmpeg_path),
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-ss",
                    f"{start:.6f}",
                    "-t",
                    f"{duration:.6f}",
                    "-i",
                    str(source_audio),
                    "-map",
                    "0:a:0",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "libmp3lame",
                    "-b:a",
                    f"{audio_bitrate_kbps}k",
                    str(audio_clip),
                ]
            )
            video_clips.append(video_clip)
            audio_clips.append(audio_clip)
        return concatenate_segments(
            ffmpeg_path,
            ffprobe_path,
            video_clips,
            audio_clips,
            recording_path,
            audio_path,
            playback_path,
            progress_callback,
        )
    finally:
        if clips_dir.exists():
            shutil.rmtree(clips_dir, ignore_errors=True)


def process_recording(
    ffmpeg_path: Path,
    ffprobe_path: Path,
    screen_path: Path,
    raw_audio_path: Path,
    recording_path: Path,
    audio_path: Path,
    audio_lead_seconds: float,
    audio_bitrate_kbps: int,
    progress_callback: Callable[[str], None] | None = None,
) -> ProcessedMedia:
    lead = max(0.0, audio_lead_seconds)
    if progress_callback:
        progress_callback("Combining video and system audio…")
    _run_checked(
        [
            str(ffmpeg_path),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(screen_path),
            "-ss",
            f"{lead:.6f}",
            "-i",
            str(raw_audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            str(recording_path),
        ]
    )

    if progress_callback:
        progress_callback("Creating transcription-ready audio…")
    _run_checked(
        [
            str(ffmpeg_path),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{lead:.6f}",
            "-i",
            str(raw_audio_path),
            "-map",
            "0:a:0",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "libmp3lame",
            "-b:a",
            f"{audio_bitrate_kbps}k",
            str(audio_path),
        ]
    )

    if not recording_path.is_file() or not audio_path.is_file():
        raise MediaError("Media processing completed without producing all output files.")
    return ProcessedMedia(
        recording_path=recording_path,
        audio_path=audio_path,
        duration_seconds=min(
            probe_duration(ffprobe_path, recording_path),
            probe_duration(ffprobe_path, audio_path),
        ),
    )


def extract_audio_range(
    ffmpeg_path: Path,
    source_path: Path,
    output_path: Path,
    start_seconds: float,
    duration_seconds: float,
    bitrate_kbps: int,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run_checked(
        [
            str(ffmpeg_path),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{max(0.0, start_seconds):.3f}",
            "-t",
            f"{max(0.1, duration_seconds):.3f}",
            "-i",
            str(source_path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "libmp3lame",
            "-b:a",
            f"{bitrate_kbps}k",
            str(output_path),
        ]
    )
    return output_path


def split_large_audio(
    ffmpeg_path: Path,
    ffprobe_path: Path,
    source_path: Path,
    output_dir: Path,
    bitrate_kbps: int,
    max_bytes: int = 24 * 1024 * 1024,
    segment_seconds: float = 20 * 60,
    overlap_seconds: float = 2.0,
) -> list[Path]:
    if source_path.stat().st_size <= max_bytes:
        return [source_path]

    duration = probe_duration(ffprobe_path, source_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    chunks: list[Path] = []
    start = 0.0
    index = 1
    while start < duration:
        length = min(segment_seconds, duration - start)
        chunk_path = output_dir / f"part-{index:03d}.mp3"
        extract_audio_range(
            ffmpeg_path,
            source_path,
            chunk_path,
            start,
            length,
            bitrate_kbps,
        )
        if chunk_path.stat().st_size > max_bytes:
            raise MediaError(
                f"{chunk_path.name} still exceeds the OpenAI upload limit. "
                "Lower TRANSCRIPTION_AUDIO_BITRATE_KBPS."
            )
        chunks.append(chunk_path)
        if start + length >= duration:
            break
        start += max(1.0, length - overlap_seconds)
        index += 1
    return chunks
