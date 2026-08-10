from __future__ import annotations

import json
from dataclasses import asdict

from .models import SessionManifest, TranscriptCue, format_duration


def apply_source_transcript(
    session: SessionManifest,
    payload: dict[str, object],
) -> str:
    raw_cues = payload.get("cues")
    if not isinstance(raw_cues, list):
        raise ValueError("The source transcript did not contain cue data.")
    cues: list[TranscriptCue] = []
    for raw in raw_cues:
        if not isinstance(raw, dict):
            continue
        text = str(raw.get("text") or "").strip()
        if not text:
            continue
        try:
            seconds = max(0.0, float(raw.get("seconds") or 0.0))
        except (TypeError, ValueError):
            continue
        timestamp = str(raw.get("timestamp") or format_duration(seconds))
        cues.append(
            TranscriptCue(
                timestamp=timestamp,
                seconds=seconds,
                text=text,
            )
        )
    if not cues:
        raise ValueError("The source transcript did not contain usable cues.")

    default_provider = (
        "YouTube built-in transcript"
        if "youtube.com/" in session.source_url.casefold()
        else (
            "Medality built-in transcript"
            if "medality.com/" in session.source_url.casefold()
            else "Built-in source transcript"
        )
    )
    provider = str(payload.get("provider") or default_provider).strip()
    provider_key = (
        "youtube"
        if "youtube" in provider.casefold()
        else (
            "medality"
            if "medality" in provider.casefold()
            else "source"
        )
    )
    session.transcript_source = provider_key
    session.source_transcript_cues = cues
    markdown = render_source_transcript_markdown(session, provider)
    session.transcript_markdown_path.write_text(markdown, encoding="utf-8")
    session.transcript_json_path.write_text(
        json.dumps(
            {
                "title": session.title,
                "source": provider,
                "source_url": session.source_url,
                "cues": [asdict(cue) for cue in cues],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    session.save()
    return markdown


def render_source_transcript_markdown(
    session: SessionManifest,
    provider: str | None = None,
) -> str:
    source_label = (
        provider
        or (
            "YouTube built-in transcript"
            if session.transcript_source == "youtube"
            else "Medality built-in transcript"
        )
    )
    lines = [
        f"# {session.title}",
        "",
        f"_Source: {source_label}._",
        "",
    ]
    for cue in session.source_transcript_cues:
        lines.append(f"**[{format_duration(cue.seconds)}]** {cue.text}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
