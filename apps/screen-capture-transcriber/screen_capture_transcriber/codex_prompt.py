from __future__ import annotations

from pathlib import Path

from .learning_notes import read_transcript, transcript_context_for_note
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
            f"- Capture {capture.index:03d} | "
            f"{format_duration(capture.timestamp_seconds)} | {disposition}\n"
            f"  Answer/name: {label}\n"
            f"  Annotation color: {capture.color}\n"
            f"  Annotated image: {image_path}"
        )
    return "\n".join(rows) or "- No anatomy captures are present."


def _learning_note_inventory(session: SessionManifest) -> str:
    rows: list[str] = []
    for note in sorted(
        session.learning_notes,
        key=lambda item: (item.timestamp_seconds, item.created_at, item.id),
    ):
        source_timestamp = (
            f" | source video {format_duration(note.source_timestamp_seconds)}"
            if note.source_timestamp_seconds is not None
            else ""
        )
        context = transcript_context_for_note(session, note)
        context_block = (
            "\n".join(f"    {line}" for line in context.splitlines())
            if context
            else "    (No nearby timestamped transcript context is available.)"
        )
        rows.append(
            f"- Note ID: {note.id} | recording "
            f"{format_duration(note.timestamp_seconds)}{source_timestamp}\n"
            f"  User-selected learning point: {note.text.strip()}\n"
            f"  Nearby transcript context:\n{context_block}"
        )
    return "\n".join(rows) or "- No timestamped learning notes are present."


def build_codex_anki_prompt(session: SessionManifest) -> str:
    """Build the combined visual and non-visual Anki APKG prompt."""
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
        session.folder / f"{safe_slug(session.title)}-study-codex.apkg"
    ).resolve()
    transcript_path = (
        str(session.transcript_markdown_path.resolve())
        if session.transcript_markdown_path.is_file()
        else "(No saved transcript file is available.)"
    )
    full_transcript = read_transcript(session)
    transcript_block = (
        full_transcript
        if full_transcript
        else "(No saved transcript content is available.)"
    )

    return f"""Create one verified Anki APKG from the intentional study targets in this recording session.

Before doing any card work, read and follow these local source-of-truth files:
- Card style guide: {style_guide.resolve()}
- APKG packaging guide: {packaging_guide.resolve()}
- Canonical saCloze++ MODEL source: {canonical_builder.resolve()}

Session:
- Title: {session.title}
- Manifest: {session.manifest_path.resolve()}
- Session folder: {session.folder.resolve()}
- Full transcript: {transcript_path}

VISUAL CARD TARGETS — intentional anatomy captures:
{_capture_inventory(session)}

NON-VISUAL CARD TARGETS — intentional timestamped learning notes:
{_learning_note_inventory(session)}

FULL TIMESTAMPED TRANSCRIPT — use this to resolve every learning note in context:
--- BEGIN FULL TRANSCRIPT ---
{transcript_block}
--- END FULL TRANSCRIPT ---

Shared requirements:
1. Use the existing canonical `saCloze++` note type exactly. Import/reuse `MODEL` from the canonical builder above; do not make a Basic card, `saCloze+`, or a look-alike model.
2. Use the `Saved Cards` deck and fields named `Text` and `Extra`.
3. Use one shared dated tag in the canonical `#AnkiChat::YYYY.MM.DD_Subject` format, using America/Chicago local time and a concise subject derived from the session title.
4. Create a machine-readable manifest before packaging. Use deterministic/stable GUIDs based on the capture index or learning-note ID.
5. Validate cloze syntax, exact field names, note type, tag format, note keys, and every local media reference before saying the package is ready.

Visual-card requirements:
1. Create exactly one visual note for every capture marked CREATE CARD. Do not create visual cards for skipped captures, and do not guess missing structure names.
2. Treat the saved label as the answer and the annotated screenshot as the intentional visual target.
3. Use this structure, substituting the accurate arrow color phrase, cloze answer, and packaged annotated-image basename:

What is indicated by the <span style="color: ARROW_HEX;">ARROW_COLOR arrow</span>?<br><br>{{{{c1::ANSWER}}}}<br><br><img src="ANNOTATED_IMAGE_BASENAME.png">

The two `<br><br>` pairs are required. Match `ARROW_HEX` to the capture's Annotation color and use a reasonable human-readable color name.
For the default `#FFAA00` annotation, the exact shape is:

What is indicated by the <span style="color: #FFAA00;">yellow arrow</span>?<br><br>{{{{c1::ANSWER}}}}<br><br><img src="ANNOTATED_IMAGE_BASENAME.png">

4. Put only concise session context and the capture timestamp in `Extra`. Do not put source/provenance text on the front.
5. Package each annotated image as local APKG media and reference it only by its basename. Do not modify the source images.

Non-visual-card requirements:
1. Every saved learning note is an explicit user-selected target. Create at least one distinct non-visual candidate for every Note ID; do not skip a note merely because the nearby transcript contains other topics.
2. Treat the user's `User-selected learning point` as the primary specification of what the card must teach. Use the timestamp and transcript only to clarify terminology or resolve context. Do not replace the selected point with an independent transcript summary.
3. Follow the canonical guide's text-first cloze conventions: one clean idea per note, short natural prose, usually one or two clozes, and enough locking context to pass the Smart Student Test.
4. If one user note deliberately contains multiple independently testable facts, split it only as needed for one-clean-idea cards while retaining the same stable Note ID as the GUID namespace.
5. Put the learning-note timestamp, concise source context, and a brief helpful explanation in `Extra`. Do not place provenance framing on the card front.
6. Non-visual cards normally contain no image unless the user's selected learning point genuinely requires one. Do not attach an anatomy capture merely because it is nearby in time.

Scope:
- Visual captures and timestamped learning notes were both deliberately selected by the user.
- Do not mine the complete transcript for additional cards in this workflow.
- The transcript is supporting context, not a request to generate every potentially important fact.

Write the completed APKG here:
{output_path}

After building it, report the visual-note count, non-visual-note count, skipped captures, source Note IDs covered, validation results, and any missing files or labels.

Make the result directly openable in Codex. Do not report only a bare filesystem path. Include these two local-file Markdown links in the final response, using the exact absolute targets:
- [Open generated APKG](<{output_path}>)
- [Open containing folder](<{session.folder.resolve()}>)

Do not merely describe how to build it—create and verify the APKG."""


def save_codex_anki_prompt(session: SessionManifest) -> Path:
    output_path = session.folder / "codex-anki-prompt.txt"
    output_path.write_text(build_codex_anki_prompt(session), encoding="utf-8")
    return output_path
