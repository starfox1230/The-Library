from __future__ import annotations

from pathlib import Path

from .models import SessionManifest, format_duration, safe_slug


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _capture_inventory(session: SessionManifest) -> str:
    rows: list[str] = []
    for capture in session.anatomy_captures:
        image_path = (session.folder / capture.annotated_image).resolve()
        label = capture.label.strip() or "(unlabeled)"
        disposition = (
            "CREATE CARD"
            if capture.create_anki_card and capture.label.strip()
            else "SKIP (not labeled and marked for Anki)"
        )
        rows.append(
            f"- Capture {capture.index:03d} | {format_duration(capture.timestamp_seconds)}"
            f" | {disposition}\n"
            f"  Answer/name: {label}\n"
            f"  Annotated image: {image_path}"
        )
    return "\n".join(rows) or "- No anatomy captures are present."


def build_codex_anki_prompt(session: SessionManifest) -> str:
    """Build a self-contained prompt for creating the session's anatomy APKG."""
    repo_root = _repo_root()
    style_guide = (
        repo_root
        / "apps"
        / "anki-card-creation-codex-helper"
        / "CARD_STYLE_GUIDE.md"
    )
    packaging_guide = (
        repo_root
        / "apps"
        / "anki-card-creation-codex-helper"
        / "APKG_PACKAGING.md"
    )
    canonical_builder = (
        repo_root
        / "apps"
        / "radiographics-review"
        / "scripts"
        / "build_anki_package.py"
    )
    output_path = (
        session.folder / f"{safe_slug(session.title)}-anatomy-codex.apkg"
    ).resolve()

    return f"""Create an Anki APKG from the labeled anatomy screenshots in this recording session.

Before doing any card work, read and follow these local source-of-truth files:
- Card style guide: {style_guide.resolve()}
- APKG packaging guide: {packaging_guide.resolve()}
- Canonical saCloze++ MODEL source: {canonical_builder.resolve()}

Session:
- Title: {session.title}
- Manifest: {session.manifest_path.resolve()}
- Session folder: {session.folder.resolve()}

Capture inventory:
{_capture_inventory(session)}

Requirements:
1. Create exactly one note for every capture marked CREATE CARD. Do not create cards for skipped captures, and do not guess missing structure names.
2. Use the existing canonical `saCloze++` note type exactly. Import/reuse `MODEL` from the canonical builder above; do not make a Basic card, `saCloze+`, or a look-alike model.
3. Use the `Saved Cards` deck and fields named `Text` and `Extra`.
4. For each note, set `Text` to this exact structure, substituting the capture's Answer/name and the packaged annotated-image basename:

What is indicated by the <span style="color: #FFAA00;">yellow arrow</span>?<br><br>{{{{c1::ANSWER}}}}<br><br><img src="ANNOTATED_IMAGE_BASENAME.png">

The two `<br><br>` pairs are required. Preserve the answer text accurately. The yellow wording/color matches the app's `#FFAA00` annotation color.
5. Put only concise session context and the capture timestamp in `Extra`. Do not put source/provenance text on the front.
6. Package each annotated image as local APKG media and reference it only by its basename in `<img src>`. Do not modify the original or annotated screenshots.
7. Use one shared dated tag in the canonical `#AnkiChat::YYYY.MM.DD_Subject` format, using America/Chicago local time and `Anatomy` as the subject unless the guides require a more specific safe subject.
8. Create a machine-readable manifest before packaging. Use deterministic/stable GUIDs, and validate cloze syntax, exact field names, note type, tag format, note keys, and every local media reference before saying the package is ready.
9. Write the completed APKG here:
{output_path}

After building it, report the output path, number of notes, skipped captures, validation results, and any missing files or labels. Do not merely describe how to build it—create and verify the APKG."""


def save_codex_anki_prompt(session: SessionManifest) -> Path:
    output_path = session.folder / "codex-anki-prompt.txt"
    output_path.write_text(build_codex_anki_prompt(session), encoding="utf-8")
    return output_path
