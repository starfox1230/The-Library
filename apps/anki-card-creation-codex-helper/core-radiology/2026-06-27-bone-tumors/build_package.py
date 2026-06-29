from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import genanki


ROOT = Path(__file__).resolve().parents[4]
RADIOGRAPHICS_SCRIPTS = ROOT / "apps" / "radiographics-review" / "scripts"
sys.path.insert(0, str(RADIOGRAPHICS_SCRIPTS))

from build_anki_package import MODEL  # noqa: E402


HERE = Path(__file__).resolve().parent
NOTES_PATH = HERE / "notes.json"
MANIFEST_PATH = HERE / "manifest.json"
OUTPUT_PATH = HERE / "bone-tumors.apkg"
IMG_RE = re.compile(r'<img\s+[^>]*src="([^"]+)"', re.IGNORECASE)


def stable_int(value: str) -> int:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return (int(digest[:9], 16) % 2_000_000_000) + 1_000_000


def validate(notes: list[dict], manifest: dict) -> None:
    expected_tag = manifest["anki"]["tag"]
    if len(notes) != manifest["anki"]["note_count"]:
        raise ValueError("Manifest note count does not match notes.json.")

    ids: set[str] = set()
    media_names = {Path(item).name for item in manifest["media"]}
    for media_path in manifest["media"]:
        if not (HERE / media_path).exists():
            raise ValueError(f"Missing media file: {media_path}")

    for note in notes:
        if set(note) != {"content", "tags", "id"}:
            raise ValueError(f"Invalid note keys for {note.get('id', '<unknown')}.")
        if note["id"] in ids:
            raise ValueError(f"Duplicate note id: {note['id']}")
        ids.add(note["id"])
        if note["tags"] != [expected_tag]:
            raise ValueError(f"Invalid tag for {note['id']}.")
        if not re.search(r"\{\{c\d+::.+?\}\}", note["content"]):
            raise ValueError(f"Missing cloze syntax in {note['id']}.")
        for src in IMG_RE.findall(note["content"]):
            if src not in media_names:
                raise ValueError(f"{note['id']} references unpackaged media: {src}")


def build_extra(source: dict) -> str:
    pages = [
        "core-radiology-bone-tumors-msk-934-source-page.jpg",
        "core-radiology-bone-tumors-msk-935-source-page.jpg",
        "core-radiology-bone-tumors-msk-936-source-page.jpg",
    ]
    page_imgs = "".join(f'<div><img src="{page}"></div>' for page in pages)
    return (
        f"<div><b>Source</b> {source['book']}, section {source['section_key']}, "
        f"{source['section_title']}, printed pages {source['printed_pages']}.</div>"
        "<div>Periosteal reaction morphology, margin analysis, matrix, age, and location were "
        "selected as board-relevant discriminators for nonspecific bone lesions.</div>"
        f"{page_imgs}"
    )


def main() -> int:
    notes = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    validate(notes, manifest)

    deck = genanki.Deck(
        stable_int("Saved Cards"),
        manifest["anki"]["deck"],
    )
    extra = build_extra(manifest["source"])

    for note_def in notes:
        deck.add_note(
            genanki.Note(
                model=MODEL,
                fields=[note_def["content"], extra],
                guid=genanki.guid_for(manifest["batch_id"], note_def["id"]),
                tags=note_def["tags"],
            )
        )

    package = genanki.Package(deck)
    package.media_files = [str(HERE / media_path) for media_path in manifest["media"]]
    package.write_to_file(OUTPUT_PATH)
    print(f"Built {OUTPUT_PATH} with {len(notes)} notes and {len(package.media_files)} media files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
