from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

import genanki


CSS = """
html { overflow: scroll; overflow-x: hidden; }
.card {
  font-family: helvetica;
  font-size: 20px;
  text-align: center;
  color: #D7DEE9;
  line-height: 1.6em;
  background-color: #2F2F31;
}
#kard {
  max-width: 760px;
  margin: 0 auto;
  word-wrap: break-word;
  padding: 0;
}
.cloze, .cloze b, .cloze u, .cloze i {
  font-weight: bold;
  color: MediumSeaGreen !important;
}
#extra, #extra i {
  font-size: 15px;
  color: #D7DEE9;
  font-style: italic;
}
img {
  display: block;
  max-width: 100%;
  max-height: none;
  margin: 12px auto;
  border-radius: 12px;
}
a {
  color: LightBlue !important;
  text-decoration: none;
}
.source {
  margin-top: 14px;
  font-size: 13px;
  color: #A6ABB9;
}
.figure-caption {
  font-size: 13px;
  line-height: 1.5em;
}
"""


MODEL = genanki.Model(
    1089573412,
    "Radiographics Visual Cloze",
    fields=[
        {"name": "Text"},
        {"name": "Extra"},
    ],
    templates=[
        {
            "name": "Cloze",
            "qfmt": "<div id='kard'>{{cloze:Text}}</div>",
            "afmt": "<div id='kard'>{{cloze:Text}}<div>&nbsp;</div><div id='extra'>{{Extra}}</div></div>",
        }
    ],
    css=CSS,
    model_type=genanki.Model.CLOZE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an Anki package for one RadioGraphics article.")
    parser.add_argument("--article-json", type=Path, required=True)
    parser.add_argument("--notes-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def stable_int(value: str, digits: int = 9) -> int:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return (int(digest[:digits], 16) % 2_000_000_000) + 1_000_000


def escape_text(text: str) -> str:
    return html.escape(text or "", quote=True)


def build_key_fact_list(article: dict) -> str:
    summary_sections = article.get("summarySections") or []
    if summary_sections:
        return "".join(
            f"<li><b>{escape_text(section.get('label', 'Key point'))}</b> {escape_text(section.get('text', ''))}</li>"
            for section in summary_sections[:5]
        )

    return "".join(f"<li>{escape_text(fact)}</li>" for fact in article.get("keyFacts", [])[:5])


def build_figure_appendix(article: dict) -> str:
    parts: list[str] = []
    for figure in article.get("figures", []):
        image_name = figure.get("localImageName")
        if image_name:
            parts.append(f"<div><b>{escape_text(figure.get('label', 'Figure'))}</b></div>")
            parts.append(f"<img src=\"{escape_text(image_name)}\">")
        if figure.get("caption"):
            parts.append(f"<div class='figure-caption'>{escape_text(figure['caption'])}</div>")
        parts.append("<hr>")

    return "".join(parts)


def extra_html(article: dict) -> str:
    facts = build_key_fact_list(article)
    metadata_bits = [
        article.get("journal") or "RadioGraphics",
        article.get("publishedAt", "")[:10] if article.get("publishedAt") else "",
        f"Vol {article['volume']}" if article.get("volume") else "",
        f"Issue {article['issue']}" if article.get("issue") else "",
    ]
    metadata = " | ".join(bit for bit in metadata_bits if bit)
    parts = [
        f"<div><b>{escape_text(article.get('title', 'Untitled article'))}</b></div>",
        f"<div>{escape_text(metadata)}</div>" if metadata else "",
        "<hr>",
        f"<div><b>Key facts</b><ul>{facts}</ul></div>",
        (
            f"<div class='source'><a href=\"{escape_text(article.get('link', ''))}\">Open article</a>"
            f" &middot; DOI: {escape_text(article.get('doi', ''))}</div>"
        ),
        "<hr>",
        "<div><b>All article figures</b></div>",
        build_figure_appendix(article),
    ]
    return "".join(part for part in parts if part)


def validate_note_definitions(note_defs: list[dict]) -> None:
    for note in note_defs:
        if not isinstance(note, dict):
            raise ValueError("Each note must be an object.")
        keys = set(note.keys())
        if not keys.issubset({"content", "html", "tags", "id"}):
            raise ValueError(f"Invalid note keys: {keys}")
        has_content = "content" in note
        has_html = "html" in note
        if (1 if has_content else 0) + (1 if has_html else 0) != 1:
            raise ValueError("Each note must have exactly one of content or html.")
        if not isinstance(note.get("tags"), list) or len(note["tags"]) != 1:
            raise ValueError("Each note must have exactly one batch tag.")


def build_notes(article: dict, note_defs: list[dict]) -> tuple[list[genanki.Note], list[str]]:
    validate_note_definitions(note_defs)

    extra = extra_html(article)
    notes: list[genanki.Note] = []
    media_files: list[str] = [
        figure["localImagePath"]
        for figure in article.get("figures", [])
        if figure.get("localImagePath")
    ]

    for index, note_def in enumerate(note_defs):
        text = note_def.get("content") or note_def.get("html") or ""
        note = genanki.Note(
            model=MODEL,
            fields=[text, extra],
            guid=genanki.guid_for(article["doi"], note_def.get("id", f"note-{index + 1:03d}")),
            tags=note_def.get("tags", []),
        )
        notes.append(note)

    return notes, sorted(set(media_files))


def main() -> int:
    args = parse_args()
    article = json.loads(args.article_json.read_text(encoding="utf-8"))
    note_defs = json.loads(args.notes_json.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)

    deck = genanki.Deck(
        stable_int(article["doi"]),
        f"Radiographics::{article['title'][:90]}",
    )
    notes, media_files = build_notes(article, note_defs)
    for note in notes:
        deck.add_note(note)

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(args.output)

    print(str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
