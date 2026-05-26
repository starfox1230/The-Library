from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import re
import shutil
from pathlib import Path

import genanki


BATCH_TAG = "#AnkiChat::2026.05.26_Radionuclides"
BATCH_DIR = Path(__file__).resolve().parent
APPS_DIR = BATCH_DIR.parents[2]
SOURCE_DIR = APPS_DIR / "Radionuclides"
DECK_JSON = SOURCE_DIR / "deck.json"
ADDITIONAL_DIR = SOURCE_DIR / "additional images"
MEDIA_DIR = BATCH_DIR / "media"
MANIFEST_PATH = BATCH_DIR / "cards.json"
README_PATH = BATCH_DIR / "README.md"
PACKAGE_PATH = BATCH_DIR / "radionuclides-reference-cards.apkg"
CANONICAL_BUILDER = APPS_DIR / "radiographics-review" / "scripts" / "build_anki_package.py"
IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".webp"}
QUESTION_FIELDS = (
    ("production", "What is the method of production of {name}?"),
    ("decay", "What is the mode of decay of {name}?"),
    ("photons", "What are the principal photon energies of {name}?"),
    ("halfLife", "What is the half-life of {name}?"),
)


def load_canonical_model() -> genanki.Model:
    spec = importlib.util.spec_from_file_location("radiographics_anki_builder", CANONICAL_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import canonical model from {CANONICAL_BUILDER}.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.MODEL


def stable_int(value: str) -> int:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return (int(digest[:9], 16) % 2_000_000_000) + 1_000_000


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def copy_media(source: Path, destination_name: str) -> str:
    destination = MEDIA_DIR / destination_name
    shutil.copy2(source, destination)
    return destination_name


def additional_images(source_slug: str) -> list[Path]:
    folder = ADDITIONAL_DIR / source_slug
    if not folder.exists():
        return []
    return sorted(
        (
            item
            for item in folder.iterdir()
            if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS
        ),
        key=lambda item: item.name.casefold(),
    )


def build_extra(entry: dict[str, str], main_media: str, extra_media: list[str]) -> str:
    def safe(value: str) -> str:
        return html.escape(value, quote=True)

    parts = [
        f"<div><b>{safe(entry['name'])}</b></div>",
        f"<div><b>Production</b>: {safe(entry['production'])}</div>",
        f"<div><b>Decay</b>: {safe(entry['decay'])}</div>",
        f"<div><b>Principal photon energies</b>: {safe(entry['photons'])}</div>",
        f"<div><b>Half-life</b>: {safe(entry['halfLife'])}</div>",
    ]
    if entry.get("otherFacts", "").strip():
        parts.append(f"<div><b>Notes</b>: {safe(entry['otherFacts'])}</div>")
    parts.extend(["<br>", f"<img src=\"{safe(main_media)}\">"])
    if extra_media:
        parts.extend(["<br><hr><div><b>Additional images</b></div><br>"])
        parts.extend(f"<img src=\"{safe(media_name)}\">" for media_name in extra_media)
    return "".join(parts)


def validate_text(text: str) -> None:
    if text.count("{{c1::") != 1 or re.search(r"{{c[2-9]\d*::", text):
        raise ValueError(f"Text does not contain exactly one c1 cloze: {text}")
    if "<br><br>" not in text:
        raise ValueError(f"Question and answer are not separated correctly: {text}")


def build_manifest(entries: list[dict[str, str]]) -> tuple[dict, list[str]]:
    cards: list[dict] = []
    skipped: list[dict] = []
    packaged_media: list[str] = []

    for entry in entries:
        source_main = SOURCE_DIR / entry["image"]
        if not source_main.exists():
            skipped.append(
                {
                    "name": entry["name"],
                    "reason": f"Main image is missing from the Radionuclides app: {entry['image']}",
                }
            )
            continue

        entry_slug = slugify(entry["name"])
        source_slug = source_main.stem.lower()
        main_media = copy_media(source_main, f"radionuclides_{entry_slug}_main{source_main.suffix.lower()}")
        extra_media: list[str] = []
        for index, source_extra in enumerate(additional_images(source_slug), start=1):
            copied_name = (
                f"radionuclides_{entry_slug}_additional_{index:02d}"
                f"{source_extra.suffix.lower()}"
            )
            extra_media.append(copy_media(source_extra, copied_name))

        media_files = [main_media, *extra_media]
        packaged_media.extend(media_files)
        extra_html = build_extra(entry, main_media, extra_media)
        for field_name, question_pattern in QUESTION_FIELDS:
            text = (
                f"{question_pattern.format(name=html.escape(entry['name']))}"
                f"<br><br>{{{{c1::{html.escape(entry[field_name])}}}}}"
            )
            validate_text(text)
            cards.append(
                {
                    "id": f"{entry_slug}-{field_name.lower()}",
                    "source_title": "Radionuclides Explorer",
                    "note_type_style": "saCloze++",
                    "deck_name": "Saved Cards",
                    "fields": {"Text": text, "Extra": extra_html},
                    "media_files": media_files,
                    "tags": [BATCH_TAG],
                }
            )

    manifest = {
        "run": {
            "date": "2026-05-26",
            "source_title": "Radionuclides Explorer",
            "source_data": str(DECK_JSON),
            "deck_name": "Saved Cards",
            "note_type_style": "saCloze++",
            "package": str(PACKAGE_PATH),
        },
        "cards": cards,
        "skipped": skipped,
    }
    return manifest, sorted(set(packaged_media))


def write_readme(manifest: dict, media_files: list[str]) -> None:
    card_count = len(manifest["cards"])
    included_count = card_count // len(QUESTION_FIELDS)
    skipped_lines = [
        f"- {item['name']}: {item['reason']}" for item in manifest["skipped"]
    ] or ["- None."]
    content = "\n".join(
        [
            "# Radionuclides Anki Reference Cards",
            "",
            "Source: `apps/Radionuclides/deck.json` and associated local images.",
            "",
            f"- Deck: `Saved Cards`",
            f"- Note type: `saCloze++`",
            f"- Tag: `{BATCH_TAG}`",
            f"- Radionuclides included: {included_count}",
            f"- Notes generated: {card_count}",
            f"- Media files packaged: {len(media_files)}",
            "",
            "Each included radionuclide has four single-cloze notes covering production, decay,",
            "principal photon energies, and half-life. The answer-side Extra field contains the",
            "full reference summary, the main app image, and an Additional images section when",
            "associated images exist in the app.",
            "",
            "## Skipped",
            "",
            *skipped_lines,
            "",
            "## Build",
            "",
            "```powershell",
            "python .\\build_radionuclides_package.py",
            "```",
            "",
        ]
    )
    README_PATH.write_text(content, encoding="utf-8")


def build_package(manifest: dict, media_files: list[str]) -> None:
    model = load_canonical_model()
    deck = genanki.Deck(stable_int("Saved Cards::Radionuclides::2026-05-26"), "Saved Cards")
    for card in manifest["cards"]:
        deck.add_note(
            genanki.Note(
                model=model,
                fields=[card["fields"]["Text"], card["fields"]["Extra"]],
                guid=genanki.guid_for("radionuclides-reference-cards", card["id"]),
                tags=card["tags"],
            )
        )
    package = genanki.Package(deck)
    package.media_files = [str(MEDIA_DIR / filename) for filename in media_files]
    package.write_to_file(PACKAGE_PATH)


def main() -> int:
    entries = json.loads(DECK_JSON.read_text(encoding="utf-8"))
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    manifest, media_files = build_manifest(entries)
    current_media = set(media_files)
    for media_path in MEDIA_DIR.iterdir():
        if media_path.is_file() and media_path.name not in current_media:
            media_path.unlink()
    if len(manifest["cards"]) % len(QUESTION_FIELDS) != 0:
        raise ValueError("Unexpected card count; notes are not grouped four per radionuclide.")
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_readme(manifest, media_files)
    build_package(manifest, media_files)
    print(f"Generated {len(manifest['cards'])} notes with {len(media_files)} media files.")
    print(PACKAGE_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
