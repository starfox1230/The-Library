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
  max-width: 700px;
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
.prompt {
  font-size: 19px;
  margin-bottom: 12px;
}
.source {
  margin-top: 14px;
  font-size: 13px;
  color: #A6ABB9;
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
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def stable_int(value: str, digits: int = 9) -> int:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return (int(digest[:digits], 16) % 2_000_000_000) + 1_000_000


def escape_text(text: str) -> str:
    return html.escape(text or "", quote=True)


def cloze_html(prompt: str, answer: str, image_names: list[str] | None = None) -> str:
    parts = [f"<div class='prompt'>{escape_text(prompt)}</div>"]
    parts.append(f"{{{{c1::{escape_text(answer)}}}}}")
    for image_name in image_names or []:
        parts.append(f"<img src=\"{escape_text(image_name)}\">")
    return "<br><br>".join(parts)


def extra_html(article: dict, *, caption: str = "", lead: str = "") -> str:
    facts = "".join(f"<li>{escape_text(fact)}</li>" for fact in article.get("keyFacts", [])[:5])
    parts = [f"<div><b>{escape_text(article['title'])}</b></div>"]
    if lead:
        parts.append(f"<div>{escape_text(lead)}</div>")
    if caption:
        parts.append(f"<div>{escape_text(caption)}</div>")
    parts.extend(
        [
            "<hr>",
            f"<div><b>Key facts</b><ul>{facts}</ul></div>",
            f"<div class='source'><a href=\"{escape_text(article['link'])}\">Open article</a> · DOI: {escape_text(article['doi'])}</div>",
        ]
    )
    return "".join(parts)


def build_notes(article: dict) -> tuple[list[genanki.Note], list[str]]:
    notes: list[genanki.Note] = []
    media_files: list[str] = []
    tags = [
        "radiographics",
        "radiographics_review",
        f"rg_{str(article.get('publishedAt', 'unknown'))[:4]}",
        f"rg_{article['slug'][:30]}",
    ]

    figures = article.get("ankiFigures", [])
    visual = next((figure for figure in figures if figure.get("isVisualAbstract")), None)
    key_facts = article.get("keyFacts", [])[:3]

    for index, fact in enumerate(key_facts):
        image_names = []
        if index == 0 and visual and visual.get("localImageName"):
            image_names = [visual["localImageName"]]
            media_files.append(visual["localImagePath"])
        note = genanki.Note(
            model=MODEL,
            fields=[
                cloze_html("High-yield takeaway?", fact, image_names=image_names),
                extra_html(article, lead="Article-level summary"),
            ],
            guid=genanki.guid_for(article["doi"], "summary", str(index)),
            tags=tags,
        )
        notes.append(note)

    for index, figure in enumerate(figures):
        image_name = figure.get("localImageName")
        image_path = figure.get("localImagePath")
        if not image_name or not image_path:
            continue
        media_files.append(image_path)
        prompt = "Visual abstract takeaway?" if figure.get("isVisualAbstract") else "Key teaching point?"
        note = genanki.Note(
            model=MODEL,
            fields=[
                cloze_html(prompt, figure["teachingPoint"], image_names=[image_name]),
                extra_html(article, caption=figure.get("caption", ""), lead=figure.get("label", "")),
            ],
            guid=genanki.guid_for(article["doi"], "figure", str(index)),
            tags=tags,
        )
        notes.append(note)

    return notes, sorted(set(media_files))


def main() -> int:
    args = parse_args()
    article = json.loads(args.article_json.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)

    deck = genanki.Deck(
        stable_int(article["doi"]),
        f"Radiographics::{article['title'][:90]}",
    )
    notes, media_files = build_notes(article)
    for note in notes:
        deck.add_note(note)

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(args.output)

    print(str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
