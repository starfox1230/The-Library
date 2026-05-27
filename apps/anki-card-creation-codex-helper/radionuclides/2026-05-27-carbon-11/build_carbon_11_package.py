from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import shutil
from pathlib import Path

import genanki


BATCH_TAG = "#AnkiChat::2026.05.27_Carbon_11"
BATCH_DIR = Path(__file__).resolve().parent
APPS_DIR = BATCH_DIR.parents[2]
SOURCE_DIR = APPS_DIR / "Radionuclides"
DECK_JSON = SOURCE_DIR / "deck.json"
MEDIA_DIR = BATCH_DIR / "media"
MANIFEST_PATH = BATCH_DIR / "cards.json"
README_PATH = BATCH_DIR / "README.md"
PACKAGE_PATH = BATCH_DIR / "carbon-11-reference-cards.apkg"
CANONICAL_BUILDER = APPS_DIR / "radiographics-review" / "scripts" / "build_anki_package.py"
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


def carbon_11_entry() -> dict[str, str]:
    entries = json.loads(DECK_JSON.read_text(encoding="utf-8"))
    for entry in entries:
        if entry["id"] == "Carbon-11":
            return entry
    raise ValueError("Carbon-11 is missing from apps/Radionuclides/deck.json.")


def build_extra(entry: dict[str, str], media_name: str) -> str:
    safe = lambda value: html.escape(value, quote=True)
    parts = [
        f"<div><b>{safe(entry['name'])}</b></div>",
        f"<div><b>Production</b>: {safe(entry['production'])}</div>",
        f"<div><b>Decay</b>: {safe(entry['decay'])}</div>",
        f"<div><b>Principal photon energies</b>: {safe(entry['photons'])}</div>",
        f"<div><b>Half-life</b>: {safe(entry['halfLife'])}</div>",
    ]
    if entry.get("otherFacts", "").strip():
        parts.append(f"<div><b>Notes</b>: {safe(entry['otherFacts'])}</div>")
    parts.extend(["<br>", f"<img src=\"{safe(media_name)}\">"])
    return "".join(parts)


def build_manifest(entry: dict[str, str], media_name: str) -> dict:
    extra_html = build_extra(entry, media_name)
    cards = []
    for field_name, question_pattern in QUESTION_FIELDS:
        text = (
            f"{question_pattern.format(name=html.escape(entry['name']))}"
            f"<br><br>{{{{c1::{html.escape(entry[field_name])}}}}}"
        )
        if text.count("{{c1::") != 1:
            raise ValueError(f"Text does not contain exactly one cloze: {text}")
        cards.append(
            {
                "id": f"carbon-11-{field_name.lower()}",
                "source_title": "Radionuclides Explorer",
                "note_type_style": "saCloze++",
                "deck_name": "Saved Cards",
                "fields": {"Text": text, "Extra": extra_html},
                "media_files": [media_name],
                "tags": [BATCH_TAG],
            }
        )
    return {
        "run": {
            "date": "2026-05-27",
            "source_title": "Radionuclides Explorer",
            "source_data": str(DECK_JSON),
            "deck_name": "Saved Cards",
            "note_type_style": "saCloze++",
            "package": str(PACKAGE_PATH),
        },
        "cards": cards,
        "skipped": [],
    }


def write_readme() -> None:
    content = "\n".join(
        [
            "# Carbon-11 Anki Reference Cards",
            "",
            "Source: `apps/Radionuclides/deck.json` and `apps/Radionuclides/c-11.png`.",
            "",
            f"- Deck: `Saved Cards`",
            f"- Note type: `saCloze++`",
            f"- Tag: `{BATCH_TAG}`",
            "- Radionuclides included: 1",
            "- Notes generated: 4",
            "- Media files packaged: 1",
            "",
            "Four single-cloze notes cover production, decay, principal photon energies,",
            "and half-life. The answer-side Extra field contains the full Carbon-11",
            "reference summary and the app image.",
            "",
            "## Build",
            "",
            "```powershell",
            "python .\\build_carbon_11_package.py",
            "```",
            "",
            "The generated `media/` folder and `.apkg` are kept locally for import but ignored by git.",
            "",
        ]
    )
    README_PATH.write_text(content, encoding="utf-8")


def build_package(manifest: dict, media_path: Path) -> None:
    model = load_canonical_model()
    deck = genanki.Deck(stable_int("Saved Cards::Carbon-11::2026-05-27"), "Saved Cards")
    for card in manifest["cards"]:
        deck.add_note(
            genanki.Note(
                model=model,
                fields=[card["fields"]["Text"], card["fields"]["Extra"]],
                guid=genanki.guid_for("carbon-11-reference-cards", card["id"]),
                tags=card["tags"],
            )
        )
    package = genanki.Package(deck)
    package.media_files = [str(media_path)]
    package.write_to_file(PACKAGE_PATH)


def main() -> int:
    entry = carbon_11_entry()
    source_image = SOURCE_DIR / entry["image"]
    if not source_image.exists():
        raise FileNotFoundError(f"Missing Carbon-11 image: {source_image}")
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    media_path = MEDIA_DIR / "radionuclides_carbon-11_main.png"
    shutil.copy2(source_image, media_path)
    manifest = build_manifest(entry, media_path.name)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_readme()
    build_package(manifest, media_path)
    print(f"Generated {len(manifest['cards'])} notes with 1 media file.")
    print(PACKAGE_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
