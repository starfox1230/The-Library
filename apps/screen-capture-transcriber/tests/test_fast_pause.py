from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import screen_capture_transcriber.main_window as main_window
from screen_capture_transcriber.main_window import StopSegmentWorker
from screen_capture_transcriber.models import (
    CaptureRegion,
    SessionManifest,
    SourceMediaSpan,
)


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
        23,
    )
    worker.frame_ready.connect(lambda *_args: events.append("frame-ready-signal"))

    worker.run()

    assert events.index("extract-frame") < events.index("convert-segment")
    assert events.index("frame-ready-signal") < events.index("convert-segment")


def test_regular_pause_processes_segment_without_finalizing_session(
    tmp_path,
    monkeypatch,
) -> None:
    session = SessionManifest.create(
        tmp_path,
        "Pause and resume",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    segment = session.begin_segment(1.0, 1.1)
    events: list[str] = []

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

    monkeypatch.setattr(main_window, "process_recording", fake_process)
    monkeypatch.setattr(
        main_window,
        "concatenate_segments",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("Pause must not finalize the session")
        ),
    )
    worker = StopSegmentWorker(
        session,
        segment,
        "pause",
        _FakeScreenRecorder(session.segment_screen_path(1), events),
        _FakeAudioRecorder(session.segment_raw_audio_path(1), events),
        Path("ffmpeg"),
        Path("ffprobe"),
        48,
        23,
    )

    worker.run()

    assert session.state == "paused"
    assert segment.state == "ready"
    assert events == ["stop-screen", "stop-audio", "convert-segment"]


def test_learning_note_pause_processes_segment_without_finalizing_session(
    tmp_path,
    monkeypatch,
) -> None:
    session = SessionManifest.create(
        tmp_path,
        "Note pause",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    segment = session.begin_segment(1.0, 1.1)
    events: list[str] = []

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

    monkeypatch.setattr(main_window, "process_recording", fake_process)
    monkeypatch.setattr(
        main_window,
        "concatenate_segments",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("A note pause must not finalize the session")
        ),
    )
    worker = StopSegmentWorker(
        session,
        segment,
        "note",
        _FakeScreenRecorder(session.segment_screen_path(1), events),
        _FakeAudioRecorder(session.segment_raw_audio_path(1), events),
        Path("ffmpeg"),
        Path("ffprobe"),
        48,
        23,
    )

    worker.run()

    assert session.state == "study_paused"
    assert segment.state == "ready"
    assert events == ["stop-screen", "stop-audio", "convert-segment"]


def test_final_linked_timeline_maps_learning_notes_from_source_time(
    tmp_path,
    monkeypatch,
) -> None:
    session = SessionManifest.create(
        tmp_path,
        "Linked notes",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    segment = session.begin_segment(1.0, 1.1)
    segment.state = "ready"
    segment.duration_seconds = 10.0
    session.segment_recording_path(1).write_bytes(b"recording")
    session.segment_audio_path(1).write_bytes(b"audio")
    session.video_link_mode = "linked"
    session.source_duration_seconds = 20.0
    session.source_spans.append(
        SourceMediaSpan(
            index=1,
            segment_index=1,
            source_start_seconds=0.0,
            source_end_seconds=20.0,
            recording_start_seconds=0.0,
            recording_end_seconds=10.0,
            playback_rate=2.0,
        )
    )
    note = session.add_learning_note(
        99.0,
        "A user-selected source-time concept.",
        10.0,
    )
    monkeypatch.setattr(
        main_window,
        "render_source_timeline",
        lambda *_args: SimpleNamespace(duration_seconds=10.0),
    )
    monkeypatch.setattr(main_window, "write_anatomy_manifest", lambda value: value)
    monkeypatch.setattr(main_window, "build_anatomy_review", lambda value: value)
    monkeypatch.setattr(main_window, "build_anatomy_apkg", lambda value: value)
    worker = StopSegmentWorker(
        session,
        None,
        "final",
        None,
        None,
        Path("ffmpeg"),
        Path("ffprobe"),
        48,
        23,
    )

    worker.run()

    assert note.timestamp_seconds == 5.0


def test_stopping_while_paused_finalizes_ready_segments_without_recorders(
    tmp_path,
    monkeypatch,
) -> None:
    session = SessionManifest.create(
        tmp_path,
        "Stop while paused",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    segment = session.begin_segment(1.0, 1.1)
    segment.state = "ready"
    segment.duration_seconds = 2.0
    session.segment_recording_path(1).write_bytes(b"recording")
    session.segment_audio_path(1).write_bytes(b"audio")
    finalized = []

    def fake_concatenate(*_args):
        finalized.append(True)
        return SimpleNamespace(duration_seconds=2.0)

    monkeypatch.setattr(main_window, "concatenate_segments", fake_concatenate)
    monkeypatch.setattr(main_window, "write_anatomy_manifest", lambda value: value)
    monkeypatch.setattr(main_window, "build_anatomy_review", lambda value: value)
    monkeypatch.setattr(main_window, "build_anatomy_apkg", lambda value: value)
    worker = StopSegmentWorker(
        session,
        None,
        "final",
        None,
        None,
        Path("ffmpeg"),
        Path("ffprobe"),
        48,
        23,
    )

    worker.run()

    assert finalized == [True]
    assert session.state == "ready"
