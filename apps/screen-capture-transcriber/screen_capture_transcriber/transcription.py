from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from openai import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from .media import (
    extract_audio_range,
    probe_duration,
    split_large_audio,
)
from .models import Chapter, SessionManifest, format_duration


APPROXIMATE_COST_PER_MINUTE = {
    "gpt-transcribe": 0.0045,
    "gpt-4o-mini-transcribe": 0.003,
    "gpt-4o-transcribe": 0.006,
    "gpt-4o-transcribe-diarize": 0.006,
    "whisper-1": 0.006,
}

DURATION_PRICES_PER_MINUTE = {
    "gpt-transcribe": 0.0045,
    "whisper-1": 0.006,
}

TOKEN_PRICES_PER_MILLION = {
    "gpt-4o-mini-transcribe": (1.25, 5.00),
    "gpt-4o-transcribe": (2.50, 10.00),
    "gpt-4o-transcribe-diarize": (2.50, 10.00),
}


def estimate_cost(model: str, duration_seconds: float) -> float:
    rate = APPROXIMATE_COST_PER_MINUTE.get(model, 0.006)
    return max(0.0, duration_seconds) / 60.0 * rate


def _usage_dict(response: object) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    if isinstance(usage, dict):
        return dict(usage)
    return {
        key: getattr(usage, key)
        for key in (
            "type",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "seconds",
        )
        if hasattr(usage, key)
    }


def actual_cost(model: str, usage: dict[str, Any]) -> float | None:
    duration_price = DURATION_PRICES_PER_MINUTE.get(model)
    if duration_price is not None:
        seconds = usage.get("seconds") or usage.get("duration")
        if seconds is None:
            return None
        return float(seconds) / 60.0 * duration_price

    prices = TOKEN_PRICES_PER_MILLION.get(model)
    if prices is None:
        return None
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if input_tokens is None or output_tokens is None:
        return None
    input_price, output_price = prices
    return (
        float(input_tokens) * input_price + float(output_tokens) * output_price
    ) / 1_000_000


def merge_overlapping_text(previous: str, current: str, max_words: int = 40) -> str:
    previous = previous.strip()
    current = current.strip()
    if not previous:
        return current
    if not current:
        return previous

    left = previous.split()
    right = current.split()
    left_folded = [word.casefold().strip(".,!?;:\"'()[]") for word in left]
    right_folded = [word.casefold().strip(".,!?;:\"'()[]") for word in right]
    overlap = 0
    limit = min(max_words, len(left_folded), len(right_folded))
    for count in range(limit, 3, -1):
        if left_folded[-count:] == right_folded[:count]:
            overlap = count
            break
    return f"{previous} {' '.join(right[overlap:])}".strip()


@dataclass
class TranscriptionResult:
    markdown: str
    usage: dict[str, Any] = field(default_factory=dict)
    actual_cost_usd: float | None = None


class SessionTranscriber:
    def __init__(
        self,
        api_key: str,
        model: str,
        ffmpeg_path: Path,
        ffprobe_path: Path,
        bitrate_kbps: int,
        prompt: str | None = None,
    ) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._ffmpeg_path = ffmpeg_path
        self._ffprobe_path = ffprobe_path
        self._bitrate_kbps = bitrate_kbps
        self._prompt = prompt

    def transcribe(
        self,
        session: SessionManifest,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> TranscriptionResult:
        work_dir = session.folder / "transcription"
        work_dir.mkdir(parents=True, exist_ok=True)
        chapters = self._chapter_ranges(session)
        total_request_count = self._estimate_request_count(session, chapters)
        request_index = 0
        aggregate_usage: dict[str, Any] = {
            "requests": [],
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        total_cost = 0.0
        has_actual_cost = True
        previous_context = self._prompt or ""

        for chapter, start, duration in chapters:
            chapter_dir = work_dir / f"chapter-{chapter.index:03d}"
            chapter_dir.mkdir(parents=True, exist_ok=True)
            chapter_audio = chapter_dir / "chapter.mp3"
            if start <= 0.01 and abs(duration - session.duration_seconds) <= 0.1:
                source = session.audio_path
            else:
                source = extract_audio_range(
                    self._ffmpeg_path,
                    session.audio_path,
                    chapter_audio,
                    start,
                    duration,
                    self._bitrate_kbps,
                )
            parts = split_large_audio(
                self._ffmpeg_path,
                self._ffprobe_path,
                source,
                chapter_dir / "parts",
                self._bitrate_kbps,
            )

            chapter_text = ""
            for part_index, part in enumerate(parts, start=1):
                request_index += 1
                if progress_callback:
                    progress_callback(
                        f"Transcribing {chapter.title}",
                        request_index,
                        max(total_request_count, request_index),
                    )
                response = self._transcribe_file(part, previous_context)
                text = self._response_text(response)
                (chapter_dir / f"response-{part_index:03d}.txt").write_text(
                    text,
                    encoding="utf-8",
                )
                chapter_text = merge_overlapping_text(chapter_text, text)
                previous_context = text[-1600:]

                usage = _usage_dict(response)
                aggregate_usage["requests"].append(usage)
                for key in ("input_tokens", "output_tokens", "total_tokens"):
                    if usage.get(key) is not None:
                        aggregate_usage[key] += int(usage[key])
                request_cost = actual_cost(self._model, usage)
                if request_cost is None:
                    has_actual_cost = False
                else:
                    total_cost += request_cost

            chapter.transcript = chapter_text
            (chapter_dir / "transcript.txt").write_text(chapter_text, encoding="utf-8")
            session.save()

        markdown = self._markdown(session)
        session.transcript_markdown_path.write_text(markdown, encoding="utf-8")
        cost = total_cost if has_actual_cost else None
        session.actual_cost_usd = cost
        session.save()
        session.transcript_json_path.write_text(
            json.dumps(
                session.to_transcript_payload(aggregate_usage),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return TranscriptionResult(
            markdown=markdown,
            usage=aggregate_usage,
            actual_cost_usd=cost,
        )

    def _transcribe_file(self, path: Path, context: str) -> object:
        request: dict[str, Any] = {"model": self._model}
        if self._model == "gpt-4o-transcribe-diarize":
            request["chunking_strategy"] = "auto"
            request["response_format"] = "diarized_json"
        elif context:
            request["prompt"] = context
        with path.open("rb") as audio_file:
            return self._client.audio.transcriptions.create(
                file=audio_file,
                **request,
            )

    def _response_text(self, response: object) -> str:
        if self._model != "gpt-4o-transcribe-diarize":
            return (getattr(response, "text", "") or "").strip()

        rendered: list[str] = []
        for segment in getattr(response, "segments", ()) or ():
            speaker = getattr(segment, "speaker", None)
            text = (getattr(segment, "text", "") or "").strip()
            if not text:
                continue
            rendered.append(f"{speaker}: {text}" if speaker else text)
        if rendered:
            return "\n".join(rendered)
        return (getattr(response, "text", "") or "").strip()

    @staticmethod
    def _chapter_ranges(
        session: SessionManifest,
    ) -> list[tuple[Chapter, float, float]]:
        chapters = sorted(session.chapters, key=lambda item: item.start_seconds)
        ranges: list[tuple[Chapter, float, float]] = []
        for index, chapter in enumerate(chapters):
            end = (
                chapters[index + 1].start_seconds
                if index + 1 < len(chapters)
                else session.duration_seconds
            )
            ranges.append(
                (chapter, chapter.start_seconds, max(0.1, end - chapter.start_seconds))
            )
        return ranges

    def _estimate_request_count(
        self,
        session: SessionManifest,
        chapters: list[tuple[Chapter, float, float]],
    ) -> int:
        count = 0
        for _chapter, _start, duration in chapters:
            estimated_bytes = duration * self._bitrate_kbps * 1000 / 8
            count += max(1, int(estimated_bytes // (24 * 1024 * 1024)) + 1)
        return count

    @staticmethod
    def _markdown(session: SessionManifest) -> str:
        lines = [
            f"# {session.title}",
            "",
            f"- Duration: {format_duration(session.duration_seconds)}",
            f"- Model: `{session.transcription_model}`",
            "",
        ]
        for chapter in session.chapters:
            lines.extend(
                [
                    f"## {chapter.title}",
                    "",
                    f"*Starts at {format_duration(chapter.start_seconds)}*",
                    "",
                    chapter.transcript.strip(),
                    "",
                ]
            )
        return "\n".join(lines).strip() + "\n"


def recover_completed_transcript(
    session: SessionManifest,
) -> TranscriptionResult | None:
    if not session.chapters or any(
        not chapter.transcript.strip() for chapter in session.chapters
    ):
        return None
    markdown = SessionTranscriber._markdown(session)
    usage = {"recovered_from_session": True, "requests": []}
    session.transcript_markdown_path.write_text(markdown, encoding="utf-8")
    session.actual_cost_usd = None
    session.state = "transcribed"
    session.save()
    session.transcript_json_path.write_text(
        json.dumps(
            session.to_transcript_payload(usage),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return TranscriptionResult(markdown=markdown, usage=usage)


def friendly_openai_error(exc: Exception) -> str:
    if isinstance(exc, AuthenticationError):
        return "OpenAI rejected the API key. Check OPENAI_API_KEY in .env."
    if isinstance(exc, RateLimitError):
        return "OpenAI rate-limited the request. Wait a moment and try again."
    if isinstance(exc, APIConnectionError):
        return "The app could not reach OpenAI. Check the internet connection."
    if isinstance(exc, BadRequestError):
        return f"OpenAI rejected the audio request: {exc}"
    if isinstance(exc, OpenAIError):
        return f"OpenAI returned an API error: {exc}"
    return str(exc) or exc.__class__.__name__
