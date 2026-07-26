from __future__ import annotations

from screen_capture_transcriber.media import resolve_ffmpeg, resolve_ffprobe


def test_resolves_configured_ffmpeg(tmp_path) -> None:
    ffmpeg = tmp_path / "ffmpeg.exe"
    ffprobe = tmp_path / "ffprobe.exe"
    ffmpeg.write_bytes(b"")
    ffprobe.write_bytes(b"")

    assert resolve_ffmpeg(str(ffmpeg)) == ffmpeg.resolve()
    assert resolve_ffprobe(ffmpeg) == ffprobe

