from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import screen_capture_transcriber.main_window as main_window
from screen_capture_transcriber.main_window import StopSegmentWorker
from screen_capture_transcriber.models import CaptureRegion, SessionManifest


class _FakeScreenRecorder:
    def __init__(self, path: Path, events: list[str]) -> None:
        self.path = path
        self.events = events

    def stop(self) -> Path:
        self.events.append("stop-screen")
        self.path.write_bytes(b"screen")
        return self.path

    def abort(self) -> None:
        pass


class _FakeAudioRecorder:
    def __init__(self, path: Path, events: list[str]) -> None:
        self.path = path
        self.events = events
        self.warnings: tuple[str, ...] = ()

    def stop(self) -> Path:
        self.events.append("stop-audio")
        self.path.write_bytes(b"audio")
        return self.path

    def abort(self) -> None:
        pass


def test_paused_frame_is_emitted_before_segment_conversion(
    tmp_path,
    monkeypatch,
) -> None:
    session = SessionManifest.create(
        tmp_path,
        "Fast anatomy pause",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    segment = session.begin_segment(1.0, 1.1)
    events: list[str] = []

    def fake_extract(_ffmpeg, _screen, output):
        events.append("extract-frame")
        output.write_bytes(b"png")
        return output

    def fake_probe(_ffprobe, _screen):
        events.append("probe-frame-time")
        return 2.0

    def fake_process(
        _ffmpeg,
        _ffprobe,
        _screen,
        _audio,
        recording,
        audio_output,
        *_args,
    ):
        events.append("convert-segment")
        recording.write_bytes(b"recording")
        audio_output.write_bytes(b"mp3")
        return SimpleNamespace(duration_seconds=2.0)

    monkeypatch.setattr(main_window, "extract_last_frame", fake_extract)
    monkeypatch.setattr(main_window, "probe_duration", fake_probe)
    monkeypatch.setattr(main_window, "process_recording", fake_process)
    worker = StopSegmentWorker(
        session,
        segment,
        "anatomy",
        _FakeScreenRecorder(session.segment_screen_path(1), events),
        _FakeAudioRecorder(session.segment_raw_audio_path(1), events),
        Path("ffmpeg"),
        Path("ffprobe"),
        48,
    )
    worker.frame_ready.connect(lambda *_args: events.append("frame-ready-signal"))

    worker.run()

    assert events.index("extract-frame") < events.index("convert-segment")
    assert events.index("frame-ready-signal") < events.index("convert-segment")
