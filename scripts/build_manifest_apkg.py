from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
import tempfile
from pathlib import Path

try:
    import genanki
except ImportError as exc:  # pragma: no cover - dependency guard
    raise SystemExit(
        "Missing dependency: genanki\n\n"
        "Install it with:\n"
        "  py -m pip install --user genanki\n"
    ) from exc


BASE_CSS = """
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
}
a {
  color: LightBlue !important;
  text-decoration: none;
}
""".strip()


TEXT_MODEL = genanki.Model(
    1065123401,
    "Codex Radiology saCloze+",
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
    css=BASE_CSS,
    model_type=genanki.Model.CLOZE,
)


VISUAL_MODEL = genanki.Model(
    1065123402,
    "Codex Radiology saCloze++",
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
    css=BASE_CSS,
    model_type=genanki.Model.CLOZE,
)


MODEL_BY_STYLE = {
    "sacloze+": TEXT_MODEL,
    "sacloze++": VISUAL_MODEL,
    "cloze": VISUAL_MODEL,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an Anki .apkg from a manifest of cards. "
            "Each card may specify a deck, cloze HTML, extra HTML, tags, and media files."
        )
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def stable_int(value: str, digits: int = 9) -> int:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return (int(digest[:digits], 16) % 2_000_000_000) + 1_000_000


def _ensure_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value


def _normalize_tags(raw_tags: object) -> list[str]:
    if raw_tags is None:
        return []
    if not isinstance(raw_tags, list):
        raise ValueError("tags must be an array of strings if present.")

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_tag in raw_tags:
        tag = str(raw_tag or "").strip()
        if not tag:
            continue
        if " " in tag:
            tag = tag.replace(" ", "_")
        if tag in seen:
            continue
        seen.add(tag)
        normalized.append(tag)
    return normalized


def _normalize_style(raw_style: object) -> str:
    if raw_style is None:
        return "saCloze++"
    style = str(raw_style).strip()
    if not style:
        return "saCloze++"
    key = style.casefold()
    if key not in MODEL_BY_STYLE:
        raise ValueError(
            f"Unsupported note_type_style '{style}'. "
            "Expected saCloze+, saCloze++, or cloze."
        )
    return style


def _normalize_media(raw_media: object) -> list[dict[str, str]]:
    if raw_media is None:
        return []
    if not isinstance(raw_media, list):
        raise ValueError("media_files must be an array if present.")

    normalized: list[dict[str, str]] = []
    for index, item in enumerate(raw_media, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"media_files[{index}] must be an object.")
        filename = _ensure_text(item.get("filename"), field_name=f"media_files[{index}].filename")
        local_path = _ensure_text(item.get("local_path"), field_name=f"media_files[{index}].local_path")
        normalized.append(
            {
                "filename": filename,
                "local_path": local_path,
            }
        )
    return normalized


def load_manifest(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list):
        raise ValueError("Manifest root must be a JSON array.")

    cards: list[dict[str, object]] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Card {index} must be an object.")

        fields = item.get("fields")
        if not isinstance(fields, dict):
            raise ValueError(f"Card {index}: fields must be an object.")

        text = _ensure_text(fields.get("Text"), field_name=f"Card {index} fields.Text")
        extra = str(fields.get("Extra") or "")
        deck_name = _ensure_text(item.get("deck_name"), field_name=f"Card {index} deck_name")
        style = _normalize_style(item.get("note_type_style"))

        cards.append(
            {
                "source_page_id": str(item.get("source_page_id") or ""),
                "source_title": str(item.get("source_title") or ""),
                "deck_name": deck_name,
                "note_type_style": style,
                "fields": {
                    "Text": text,
                    "Extra": extra,
                },
                "tags": _normalize_tags(item.get("tags")),
                "media_files": _normalize_media(item.get("media_files")),
                "guid": str(item.get("guid") or ""),
            }
        )

    return cards


def _copy_media_file(source_path: Path, destination_path: Path) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination_path)


def prepare_media_files(cards: list[dict[str, object]]) -> list[str]:
    temp_dir = Path(tempfile.mkdtemp(prefix="codex_manifest_apkg_media_"))
    filename_to_packaged_path: dict[str, Path] = {}
    filename_to_hash: dict[str, str] = {}

    for card in cards:
        for media in card["media_files"]:
            filename = str(media["filename"])
            local_path = Path(str(media["local_path"]))
            if not local_path.exists():
                raise FileNotFoundError(f"Media file not found: {local_path}")

            file_hash = hashlib.sha1(local_path.read_bytes()).hexdigest()
            existing_hash = filename_to_hash.get(filename)
            if existing_hash is not None:
                if existing_hash != file_hash:
                    raise ValueError(
                        f"Conflicting media contents for filename '{filename}'. "
                        "Use unique packaged filenames per distinct image."
                    )
                continue

            packaged_path = temp_dir / filename
            _copy_media_file(local_path, packaged_path)
            filename_to_packaged_path[filename] = packaged_path
            filename_to_hash[filename] = file_hash

    return [str(path) for path in filename_to_packaged_path.values()]


def model_for_style(style: str) -> genanki.Model:
    return MODEL_BY_STYLE[str(style).casefold()]


def guid_for_card(card: dict[str, object]) -> str:
    explicit = str(card.get("guid") or "").strip()
    if explicit:
        return explicit

    source_page_id = str(card.get("source_page_id") or "")
    deck_name = str(card["deck_name"])
    text = str(card["fields"]["Text"])
    extra = str(card["fields"]["Extra"])
    return genanki.guid_for(source_page_id, deck_name, text, extra)


def build_decks(cards: list[dict[str, object]]) -> list[genanki.Deck]:
    decks_by_name: dict[str, genanki.Deck] = {}

    for card in cards:
        deck_name = str(card["deck_name"])
        deck = decks_by_name.get(deck_name)
        if deck is None:
            deck = genanki.Deck(
                stable_int(f"deck::{deck_name}"),
                deck_name,
            )
            decks_by_name[deck_name] = deck

        note = genanki.Note(
            model=model_for_style(str(card["note_type_style"])),
            fields=[
                str(card["fields"]["Text"]),
                str(card["fields"]["Extra"]),
            ],
            guid=guid_for_card(card),
            tags=list(card["tags"]),
        )
        deck.add_note(note)

    return list(decks_by_name.values())


def main() -> int:
    args = parse_args()
    cards = load_manifest(args.manifest)
    if not cards:
        raise SystemExit("Manifest does not contain any cards.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    media_files = prepare_media_files(cards)
    decks = build_decks(cards)

    package = genanki.Package(decks)
    package.media_files = media_files
    package.write_to_file(args.output)

    summary = {
        "output": str(args.output),
        "cards": len(cards),
        "decks": len(decks),
        "media_files": len(media_files),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
