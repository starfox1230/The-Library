from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from .models import TranscriptCue, format_duration


TRANSCRIPT_WINDOW_SECONDS = 15.0
DEFAULT_SUGGESTION_MODEL = "gpt-5.6-luna"


@dataclass(frozen=True)
class SuggestedAnatomyTerm:
    term: str
    timestamp_seconds: float


def transcript_window(
    cues: list[TranscriptCue],
    capture_timestamp_seconds: float,
    window_seconds: float = TRANSCRIPT_WINDOW_SECONDS,
) -> list[TranscriptCue]:
    capture = max(0.0, float(capture_timestamp_seconds))
    window = max(0.0, float(window_seconds))
    return [
        cue
        for cue in cues
        if abs(float(cue.seconds) - capture) <= window
        and cue.text.strip()
    ]


def _response_output_text(response: object) -> str:
    direct = str(getattr(response, "output_text", "") or "").strip()
    if direct:
        return direct
    output = getattr(response, "output", None)
    if not isinstance(output, list):
        return ""
    pieces: list[str] = []
    for item in output:
        content = getattr(item, "content", None)
        if not isinstance(content, list):
            continue
        for part in content:
            text = getattr(part, "text", None)
            if text:
                pieces.append(str(text))
    return "\n".join(pieces).strip()


def _json_payload(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    payload = json.loads(text)
    return payload if isinstance(payload, dict) else {}


def rank_suggested_terms(
    payload: dict[str, Any],
    cues: list[TranscriptCue],
    capture_timestamp_seconds: float,
) -> list[SuggestedAnatomyTerm]:
    raw_terms = payload.get("terms", [])
    if not isinstance(raw_terms, list):
        return []

    candidates: list[tuple[int, SuggestedAnatomyTerm]] = []
    for order, item in enumerate(raw_terms):
        if not isinstance(item, dict):
            continue
        term = " ".join(str(item.get("term") or "").split()).strip(" ,;:")
        if not term or len(term) > 100:
            continue
        try:
            cue_index = int(item.get("cue_index"))
        except (TypeError, ValueError):
            continue
        if cue_index < 0 or cue_index >= len(cues):
            continue
        candidates.append(
            (
                order,
                SuggestedAnatomyTerm(term, float(cues[cue_index].seconds)),
            )
        )

    capture = max(0.0, float(capture_timestamp_seconds))
    candidates.sort(
        key=lambda item: (
            abs(item[1].timestamp_seconds - capture),
            item[0],
        )
    )
    result: list[SuggestedAnatomyTerm] = []
    seen: set[str] = set()
    for _order, suggestion in candidates:
        key = suggestion.term.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(suggestion)
    return result


def suggest_anatomy_terms(
    api_key: str,
    model: str,
    cues: list[TranscriptCue],
    capture_timestamp_seconds: float,
    *,
    client: object | None = None,
) -> list[SuggestedAnatomyTerm]:
    nearby = transcript_window(cues, capture_timestamp_seconds)
    if not api_key.strip() or not nearby:
        return []

    lines = [
        (
            f"[cue_index={index}; time={format_duration(cue.seconds)}; "
            f"offset={cue.seconds - capture_timestamp_seconds:+.2f}s] {cue.text.strip()}"
        )
        for index, cue in enumerate(nearby)
    ]
    prompt = (
        "Identify concise anatomical structure names or other useful "
        "anatomy-related terms explicitly mentioned in these timestamped transcript "
        "cues. Do not invent terms. Associate every term with the cue_index where it "
        "was mentioned. Return only JSON in this exact shape: "
        '{"terms":[{"term":"structure name","cue_index":0}]}. '
        "Use an empty terms array when nothing useful is present.\n\n"
        + "\n".join(lines)
    )
    openai_client = client or OpenAI(api_key=api_key, timeout=15.0)
    response = openai_client.responses.create(
        model=model.strip() or DEFAULT_SUGGESTION_MODEL,
        reasoning={"effort": "none"},
        max_output_tokens=600,
        input=[
            {
                "role": "system",
                "content": (
                    "You extract anatomy terminology from supplied transcript text. "
                    "Return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    payload = _json_payload(_response_output_text(response))
    return rank_suggested_terms(payload, nearby, capture_timestamp_seconds)
