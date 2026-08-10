from __future__ import annotations

from .models import LearningNote, SessionManifest, TranscriptCue, format_duration


DEFAULT_CONTEXT_WINDOW_SECONDS = 25.0


def note_context_timestamp(note: LearningNote) -> float:
    if note.source_timestamp_seconds is not None:
        return max(0.0, float(note.source_timestamp_seconds))
    return max(0.0, float(note.timestamp_seconds))


def note_display_timestamp(note: LearningNote) -> float:
    return note_context_timestamp(note)


def nearby_transcript_cues(
    session: SessionManifest,
    timestamp_seconds: float,
    window_seconds: float = DEFAULT_CONTEXT_WINDOW_SECONDS,
) -> list[TranscriptCue]:
    timestamp = max(0.0, float(timestamp_seconds))
    window = max(0.0, float(window_seconds))
    return [
        cue
        for cue in session.source_transcript_cues
        if cue.text.strip() and abs(float(cue.seconds) - timestamp) <= window
    ]


def transcript_context_for_timestamp(
    session: SessionManifest,
    timestamp_seconds: float,
    *,
    source_timestamp_seconds: float | None = None,
    window_seconds: float = DEFAULT_CONTEXT_WINDOW_SECONDS,
) -> str:
    context_timestamp = (
        max(0.0, float(source_timestamp_seconds))
        if source_timestamp_seconds is not None
        else max(0.0, float(timestamp_seconds))
    )
    cues = nearby_transcript_cues(
        session,
        context_timestamp,
        window_seconds,
    )
    if cues:
        return "\n\n".join(
            f"[{format_duration(cue.seconds)}] {cue.text.strip()}"
            for cue in cues
        )

    chapters = sorted(session.chapters, key=lambda chapter: chapter.start_seconds)
    for index, chapter in enumerate(chapters):
        next_start = (
            chapters[index + 1].start_seconds
            if index + 1 < len(chapters)
            else float("inf")
        )
        if (
            chapter.start_seconds <= timestamp_seconds < next_start
            and chapter.transcript.strip()
        ):
            return (
                f"[{format_duration(chapter.start_seconds)}] {chapter.title}\n\n"
                f"{chapter.transcript.strip()}"
            )

    return ""


def transcript_context_for_note(
    session: SessionManifest,
    note: LearningNote,
    window_seconds: float = DEFAULT_CONTEXT_WINDOW_SECONDS,
) -> str:
    return transcript_context_for_timestamp(
        session,
        note.timestamp_seconds,
        source_timestamp_seconds=note.source_timestamp_seconds,
        window_seconds=window_seconds,
    )


def read_transcript(session: SessionManifest) -> str:
    if not session.transcript_markdown_path.is_file():
        return ""
    return session.transcript_markdown_path.read_text(
        encoding="utf-8",
        errors="replace",
    ).strip()


def render_learning_notes(session: SessionManifest) -> str:
    notes = sorted(
        session.learning_notes,
        key=lambda note: (note.timestamp_seconds, note.created_at, note.id),
    )
    if not notes:
        return ""
    return "\n\n".join(
        f"[USER LEARNING NOTE — "
        f"{format_duration(note_display_timestamp(note))}] "
        f"{note.text.strip()}"
        for note in notes
    )


def render_transcript_with_notes(session: SessionManifest) -> str:
    transcript = read_transcript(session)
    notes = render_learning_notes(session)
    sections: list[str] = []
    if transcript:
        sections.append(transcript)
    else:
        sections.append(
            f"# {session.title}\n\n_No transcript is available for this session._"
        )
    if notes:
        sections.append(f"# User Learning Notes\n\n{notes}")
    else:
        sections.append("# User Learning Notes\n\n_No learning notes were saved._")
    return "\n\n---\n\n".join(sections).rstrip() + "\n"
