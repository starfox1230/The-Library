from __future__ import annotations

from pathlib import Path

from openai import APIConnectionError, AuthenticationError, BadRequestError, OpenAI, OpenAIError, RateLimitError


class TranscriptionClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def transcribe(self, audio_path: Path, prompt: str | None = None) -> str:
        request_kwargs: dict[str, object] = {
            "model": self._model,
        }
        if prompt:
            request_kwargs["prompt"] = prompt

        with audio_path.open("rb") as audio_file:
            transcription = self._client.audio.transcriptions.create(
                file=audio_file,
                **request_kwargs,
            )

        text = getattr(transcription, "text", "") or ""
        return text.strip()


def friendly_openai_error(exc: Exception) -> str:
    if isinstance(exc, AuthenticationError):
        return "OpenAI rejected the API key. Check OPENAI_API_KEY in the .env file."
    if isinstance(exc, RateLimitError):
        return "OpenAI rate-limited the request. Wait a moment and try again."
    if isinstance(exc, APIConnectionError):
        return "The app could not reach OpenAI. Check your internet connection."
    if isinstance(exc, BadRequestError):
        return "OpenAI rejected the audio request. Check the model name and audio file."
    if isinstance(exc, OpenAIError):
        return f"OpenAI returned an API error: {exc}"
    return str(exc) or exc.__class__.__name__
