from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Iterable, Sequence


_ANSWER_SEPARATOR_RE = re.compile(
    r"<hr\b[^>]*\bid\s*=\s*(?:[\"']answer[\"']|answer)[^>]*>",
    flags=re.IGNORECASE,
)
_SOUND_RE = re.compile(r"\[sound:([^\]]+)\]", flags=re.IGNORECASE)
_SPACE_RE = re.compile(r"[ \t]+")
_EXCESS_NEWLINES_RE = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class ExportCard:
    card_id: int
    note_id: int
    deck_name: str
    original_deck_name: str
    note_type_name: str
    card_template_name: str
    tags: Sequence[str]
    front_html: str
    back_html: str
    fields: Sequence[tuple[str, str]]


class _ReadableTextParser(HTMLParser):
    _BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "div",
        "dl",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
        "ul",
    }
    _IGNORED_TAGS = {"head", "script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        tag = tag.lower()
        if tag in self._IGNORED_TAGS:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag == "br" or tag in self._BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "li":
            self.parts.append("- ")
        elif tag == "img":
            attributes = {key.lower(): value or "" for key, value in attrs}
            label = (
                attributes.get("alt")
                or attributes.get("title")
                or attributes.get("src")
                or "embedded image"
            )
            self.parts.append(f"[Image: {label}]")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self._IGNORED_TAGS:
            if self._ignored_depth:
                self._ignored_depth -= 1
            return
        if not self._ignored_depth and tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def answer_side_only(answer_html: str) -> str:
    """Remove Anki's repeated question from a rendered answer."""
    match = _ANSWER_SEPARATOR_RE.search(answer_html)
    return answer_html[match.end() :] if match else answer_html


def html_to_readable_text(value: str) -> str:
    """Convert Anki field/template HTML to readable text without losing media names."""
    value = _SOUND_RE.sub(lambda match: f"[Audio: {match.group(1)}]", value or "")
    parser = _ReadableTextParser()
    try:
        parser.feed(value)
        parser.close()
        text = "".join(parser.parts)
    except Exception:
        # A malformed field should not prevent the rest of the selection exporting.
        text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [_SPACE_RE.sub(" ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return _EXCESS_NEWLINES_RE.sub("\n\n", text).strip()


def render_text_export(cards: Iterable[ExportCard]) -> str:
    cards = list(cards)
    lines = [
        "Anki Pocket Knife - Selected Card Export",
        f"Selected cards: {len(cards)}",
        "",
    ]

    for index, card in enumerate(cards, start=1):
        lines.extend(
            [
                "=" * 72,
                f"CARD {index} OF {len(cards)}",
                "=" * 72,
                f"Card ID: {card.card_id}",
                f"Note ID: {card.note_id}",
                f"Deck: {card.deck_name}",
            ]
        )
        if card.original_deck_name:
            lines.append(f"Original deck: {card.original_deck_name}")
        lines.extend(
            [
                f"Note type: {card.note_type_name}",
                f"Card template: {card.card_template_name}",
                f"Tags: {' '.join(card.tags) if card.tags else '(none)'}",
                "",
                "FRONT (rendered)",
                "-" * 72,
                html_to_readable_text(card.front_html) or "(empty)",
                "",
                "BACK (rendered)",
                "-" * 72,
                html_to_readable_text(answer_side_only(card.back_html)) or "(empty)",
                "",
                "NOTE FIELDS",
                "-" * 72,
            ]
        )
        for field_name, field_html in card.fields:
            lines.extend(
                [
                    f"[{field_name}]",
                    html_to_readable_text(field_html) or "(empty)",
                    "",
                ]
            )

    return "\n".join(lines).rstrip() + "\n"
