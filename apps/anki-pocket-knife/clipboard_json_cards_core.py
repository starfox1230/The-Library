from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import json
import re


_CODE_FENCE_RE = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class ClipboardJsonCard:
    html: str
    tags: tuple[str, ...]


def _strip_code_fence(raw_text: str) -> str:
    text = str(raw_text or "").lstrip("\ufeff")
    match = _CODE_FENCE_RE.match(text)
    if match:
        return str(match.group(1) or "")
    return text


def _normalize_tags(raw_tags: object, *, item_index: int) -> tuple[str, ...]:
    if raw_tags is None:
        return ()

    if isinstance(raw_tags, str):
        parts: Sequence[object] = [part for part in raw_tags.split() if part]
    elif isinstance(raw_tags, Sequence) and not isinstance(raw_tags, (str, bytes, bytearray)):
        parts = raw_tags
    else:
        raise ValueError(
            f"Card {item_index}: 'tags' must be a list of strings or a whitespace-separated string."
        )

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_tag in parts:
        tag = str(raw_tag or "").strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        normalized.append(tag)
    return tuple(normalized)


def parse_clipboard_json_cards(raw_text: str) -> list[ClipboardJsonCard]:
    text = _strip_code_fence(raw_text).strip()
    if not text:
        raise ValueError("Clipboard is empty.")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Clipboard does not contain valid JSON.\n\n"
            f"{exc.msg} (line {exc.lineno}, column {exc.colno})."
        ) from exc

    if not isinstance(payload, list):
        raise ValueError("Clipboard JSON must be an array of card objects.")

    cards: list[ClipboardJsonCard] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Card {index}: each item must be a JSON object.")

        html = item.get("html")
        if not isinstance(html, str):
            html = item.get("originalHtml")
        if not isinstance(html, str) or not html.strip():
            raise ValueError(
                f"Card {index}: 'html' must be a non-empty string."
            )

        cards.append(
            ClipboardJsonCard(
                html=html,
                tags=_normalize_tags(item.get("tags"), item_index=index),
            )
        )

    return cards
