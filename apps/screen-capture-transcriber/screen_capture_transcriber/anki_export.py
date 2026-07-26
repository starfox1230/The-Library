from __future__ import annotations

import hashlib
import html
import importlib.util
from pathlib import Path

from .models import SessionManifest, format_duration, safe_slug


def _stable_int(value: str) -> int:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return (int(digest[:9], 16) % 2_000_000_000) + 1_000_000


def _load_canonical_model() -> tuple[object, object]:
    try:
        import genanki
    except ImportError as exc:
        raise RuntimeError("Anki export needs genanki. Run setup.ps1 again.") from exc

    apps_dir = Path(__file__).resolve().parents[2]
    builder_path = apps_dir / "radiographics-review" / "scripts" / "build_anki_package.py"
    if not builder_path.is_file():
        raise RuntimeError(f"Canonical saCloze++ builder not found: {builder_path}")
    spec = importlib.util.spec_from_file_location(
        "_screen_capture_canonical_anki_builder", builder_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the canonical saCloze++ model.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return genanki, module.MODEL


def build_anatomy_apkg(session: SessionManifest) -> Path | None:
    captures = [
        capture
        for capture in session.anatomy_captures
        if capture.create_anki_card and capture.label.strip()
    ]
    if not captures:
        return None

    genanki, model = _load_canonical_model()
    deck = genanki.Deck(
        _stable_int("Saved Cards"),
        "Saved Cards",
    )
    local_date = session.folder.name[:10].replace("-", ".")
    batch_tag = f"#AnkiChat::{local_date}_Anatomy"
    media_files: list[str] = []
    for capture in captures:
        image_path = session.folder / capture.annotated_image
        if not image_path.is_file():
            raise RuntimeError(f"Anatomy image is missing: {image_path.name}")
        image_name = image_path.name
        prompt = (
            'What is indicated by the '
            '<span style="color: #FFAA00;">yellow arrow</span>?'
            f"<br><br>{{{{c1::{html.escape(capture.label)}}}}}"
            f'<br><br><img src="{html.escape(image_name, quote=True)}">'
        )
        extra = (
            f"Captured at {format_duration(capture.timestamp_seconds)} "
            f"in {html.escape(session.title)}."
        )
        note = genanki.Note(
            model=model,
            fields=[prompt, extra],
            guid=genanki.guid_for(
                session.created_at, f"anatomy-capture-{capture.index:03d}"
            ),
            tags=[batch_tag],
        )
        deck.add_note(note)
        media_files.append(str(image_path))

    output_path = session.folder / f"{safe_slug(session.title)}-anatomy.apkg"
    package = genanki.Package(deck)
    package.media_files = sorted(set(media_files))
    package.write_to_file(output_path)
    return output_path
