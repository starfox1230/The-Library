from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def format_duration(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def safe_slug(value: str, fallback: str = "recording") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return cleaned[:60] or fallback


@dataclass(frozen=True)
class CaptureRegion:
    x: int
    y: int
    width: int
    height: int
    screen_name: str = ""

    def ffmpeg_size(self) -> str:
        return f"{self.width}x{self.height}"

    def label(self) -> str:
        screen = f" on {self.screen_name}" if self.screen_name else ""
        return f"{self.width} × {self.height} at ({self.x}, {self.y}){screen}"


@dataclass
class Chapter:
    index: int
    start_seconds: float
    title: str
    transcript: str = ""


@dataclass
class CaptureSegment:
    index: int
    screen_file: str
    raw_audio_file: str
    recording_file: str
    audio_file: str
    video_start_monotonic: float = 0.0
    audio_start_monotonic: float = 0.0
    duration_seconds: float = 0.0
    state: str = "recording"


@dataclass
class AnatomyCapture:
    index: int
    timestamp_seconds: float
    original_image: str
    annotated_image: str
    label: str = ""
    create_anki_card: bool = False
    color: str = "#FFAA00"
    source_click_x: int | None = None
    source_click_y: int | None = None
    created_at: str = field(default_factory=utc_now_iso)
    edit_file: str = ""


@dataclass
class SessionManifest:
    folder: Path
    title: str
    created_at: str
    state: str
    region: CaptureRegion
    audio_device_name: str
    audio_device_index: int
    video_start_monotonic: float
    audio_start_monotonic: float
    duration_seconds: float = 0.0
    chapters: list[Chapter] = field(default_factory=list)
    segments: list[CaptureSegment] = field(default_factory=list)
    anatomy_captures: list[AnatomyCapture] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    transcription_model: str = ""
    estimated_cost_usd: float | None = None
    actual_cost_usd: float | None = None
    playback_toggle_x: int | None = None
    playback_toggle_y: int | None = None

    @property
    def manifest_path(self) -> Path:
        return self.folder / "session.json"

    @property
    def screen_path(self) -> Path:
        return self.segment_screen_path(1)

    @property
    def raw_audio_path(self) -> Path:
        return self.segment_raw_audio_path(1)

    @property
    def recording_path(self) -> Path:
        return self.folder / "recording.mkv"

    @property
    def audio_path(self) -> Path:
        return self.folder / "audio.mp3"

    @property
    def playback_path(self) -> Path:
        return self.folder / "recording.mp4"

    @property
    def review_path(self) -> Path:
        return self.folder / "anatomy-review.html"

    @property
    def anatomy_dir(self) -> Path:
        return self.folder / "anatomy"

    @property
    def segments_dir(self) -> Path:
        return self.folder / "segments"

    @property
    def transcript_markdown_path(self) -> Path:
        return self.folder / "transcript.md"

    @property
    def transcript_json_path(self) -> Path:
        return self.folder / "transcript.json"

    def segment_screen_path(self, index: int) -> Path:
        return self.segments_dir / f"segment-{index:03d}-screen.mp4"

    def segment_raw_audio_path(self, index: int) -> Path:
        return self.segments_dir / f"segment-{index:03d}-audio.wav"

    def segment_recording_path(self, index: int) -> Path:
        return self.segments_dir / f"segment-{index:03d}.mkv"

    def segment_audio_path(self, index: int) -> Path:
        return self.segments_dir / f"segment-{index:03d}.mp3"

    def anatomy_original_path(self, index: int) -> Path:
        return self.anatomy_dir / f"capture-{index:03d}-original.png"

    def anatomy_annotated_path(self, index: int) -> Path:
        return self.anatomy_dir / f"capture-{index:03d}-annotated.png"

    def anatomy_edit_path(self, index: int) -> Path:
        return self.anatomy_dir / f"capture-{index:03d}-edit.json"

    def anatomy_preserved_path(self, index: int) -> Path:
        return self.anatomy_dir / f"capture-{index:03d}-preserved.png"

    def begin_segment(
        self,
        audio_start_monotonic: float,
        video_start_monotonic: float,
    ) -> CaptureSegment:
        index = len(self.segments) + 1
        segment = CaptureSegment(
            index=index,
            screen_file=str(self.segment_screen_path(index).relative_to(self.folder)),
            raw_audio_file=str(
                self.segment_raw_audio_path(index).relative_to(self.folder)
            ),
            recording_file=str(
                self.segment_recording_path(index).relative_to(self.folder)
            ),
            audio_file=str(self.segment_audio_path(index).relative_to(self.folder)),
            audio_start_monotonic=audio_start_monotonic,
            video_start_monotonic=video_start_monotonic,
        )
        self.segments.append(segment)
        self.audio_start_monotonic = audio_start_monotonic
        self.video_start_monotonic = video_start_monotonic
        self.save()
        return segment

    def add_anatomy_capture(
        self,
        timestamp_seconds: float,
        original_path: Path,
        annotated_path: Path,
        label: str,
        create_anki_card: bool,
        source_click: tuple[int, int] | None = None,
        edit_path: Path | None = None,
    ) -> AnatomyCapture:
        capture = AnatomyCapture(
            index=len(self.anatomy_captures) + 1,
            timestamp_seconds=max(0.0, timestamp_seconds),
            original_image=str(original_path.relative_to(self.folder)),
            annotated_image=str(annotated_path.relative_to(self.folder)),
            label=label.strip(),
            create_anki_card=create_anki_card and bool(label.strip()),
            source_click_x=source_click[0] if source_click else None,
            source_click_y=source_click[1] if source_click else None,
            edit_file=(
                str(edit_path.relative_to(self.folder)) if edit_path is not None else ""
            ),
        )
        self.anatomy_captures.append(capture)
        self.save()
        return capture

    def save(self) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        payload = asdict(self)
        payload["folder"] = str(self.folder)
        self.manifest_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, manifest_path: Path) -> "SessionManifest":
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["folder"] = manifest_path.resolve().parent
        payload["region"] = CaptureRegion(**payload["region"])
        payload["chapters"] = [
            Chapter(**chapter) for chapter in payload.get("chapters", [])
        ]
        payload["segments"] = [
            CaptureSegment(**segment) for segment in payload.get("segments", [])
        ]
        payload["anatomy_captures"] = [
            AnatomyCapture(**capture)
            for capture in payload.get("anatomy_captures", [])
        ]
        return cls(**payload)

    @classmethod
    def create(
        cls,
        recordings_dir: Path,
        title: str,
        region: CaptureRegion,
        audio_device_name: str,
        audio_device_index: int,
        audio_start_monotonic: float,
        video_start_monotonic: float,
    ) -> "SessionManifest":
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder = recordings_dir / f"{timestamp}_{safe_slug(title)}"
        suffix = 2
        while folder.exists():
            folder = recordings_dir / f"{timestamp}_{safe_slug(title)}-{suffix}"
            suffix += 1
        folder.mkdir(parents=True)
        session = cls(
            folder=folder,
            title=title.strip() or "Untitled recording",
            created_at=utc_now_iso(),
            state="recording",
            region=region,
            audio_device_name=audio_device_name,
            audio_device_index=audio_device_index,
            audio_start_monotonic=audio_start_monotonic,
            video_start_monotonic=video_start_monotonic,
            chapters=[Chapter(index=1, start_seconds=0.0, title="Chapter 1")],
        )
        session.segments_dir.mkdir(parents=True, exist_ok=True)
        session.anatomy_dir.mkdir(parents=True, exist_ok=True)
        session.save()
        return session

    def add_chapter(self, start_seconds: float, title: str | None = None) -> Chapter:
        index = len(self.chapters) + 1
        chapter = Chapter(
            index=index,
            start_seconds=max(0.0, start_seconds),
            title=title or f"Chapter {index}",
        )
        self.chapters.append(chapter)
        self.save()
        return chapter

    def to_transcript_payload(self, usage: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": self.title,
            "created_at": self.created_at,
            "duration_seconds": self.duration_seconds,
            "model": self.transcription_model,
            "estimated_cost_usd": self.estimated_cost_usd,
            "actual_cost_usd": self.actual_cost_usd,
            "usage": usage,
            "chapters": [asdict(chapter) for chapter in self.chapters],
        }
