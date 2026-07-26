from __future__ import annotations

from screen_capture_transcriber.codex_prompt import (
    build_codex_anki_prompt,
    save_codex_anki_prompt,
)
from screen_capture_transcriber.models import CaptureRegion, SessionManifest


def _session_with_captures(tmp_path) -> SessionManifest:
    session = SessionManifest.create(
        tmp_path,
        "Upper limb anatomy",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    for index, label, create_card in (
        (1, "Musculocutaneous nerve", True),
        (2, "", False),
    ):
        original = session.anatomy_original_path(index)
        annotated = session.anatomy_annotated_path(index)
        original.write_bytes(b"original")
        annotated.write_bytes(b"annotated")
        session.add_anatomy_capture(
            10.0 * index,
            original,
            annotated,
            label,
            create_card,
        )
    return session


def test_codex_prompt_is_local_file_aware_and_uses_canonical_card_shape(
    tmp_path,
) -> None:
    session = _session_with_captures(tmp_path)

    prompt = build_codex_anki_prompt(session)

    assert str(session.manifest_path.resolve()) in prompt
    assert str(session.anatomy_annotated_path(1).resolve()) in prompt
    assert "CARD_STYLE_GUIDE.md" in prompt
    assert "APKG_PACKAGING.md" in prompt
    assert "build_anki_package.py" in prompt
    assert "`saCloze++`" in prompt
    assert "`Saved Cards`" in prompt
    assert "fields named `Text` and `Extra`" in prompt
    assert (
        'What is indicated by the <span style="color: #FFAA00;">'
        "yellow arrow</span>?<br><br>{{c1::ANSWER}}<br><br>"
        '<img src="ANNOTATED_IMAGE_BASENAME.png">'
    ) in prompt
    assert "Answer/name: Musculocutaneous nerve" in prompt
    assert "SKIP (not labeled and marked for Anki)" in prompt
    assert "do not guess missing structure names" in prompt
    assert str(
        (session.folder / "Upper-limb-anatomy-anatomy-codex.apkg").resolve()
    ) in prompt


def test_codex_prompt_is_saved_beside_session(tmp_path) -> None:
    session = _session_with_captures(tmp_path)

    output_path = save_codex_anki_prompt(session)

    assert output_path == session.folder / "codex-anki-prompt.txt"
    assert output_path.is_file()
    assert output_path.read_text(encoding="utf-8") == build_codex_anki_prompt(session)
