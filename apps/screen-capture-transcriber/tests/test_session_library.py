from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from screen_capture_transcriber.models import CaptureRegion, SessionManifest
from screen_capture_transcriber.session_library import (
    SessionLibraryDialog,
    discover_sessions,
)


def test_discovers_sessions_newest_first_and_ignores_bad_manifests(tmp_path) -> None:
    first = SessionManifest.create(
        tmp_path,
        "First lecture",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    second = SessionManifest.create(
        tmp_path,
        "Second lecture",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    first.manifest_path.touch()
    second.manifest_path.touch()
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "session.json").write_text("{not json", encoding="utf-8")

    entries, errors = discover_sessions([tmp_path])

    assert {entry.session.title for entry in entries} == {
        "First lecture",
        "Second lecture",
    }
    assert len(errors) == 1


def test_duplicate_roots_do_not_duplicate_sessions(tmp_path) -> None:
    SessionManifest.create(
        tmp_path,
        "One lecture",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )

    entries, errors = discover_sessions([tmp_path, tmp_path])

    assert len(entries) == 1
    assert errors == []


def test_past_sessions_button_copies_and_saves_codex_prompt(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    session = SessionManifest.create(
        tmp_path,
        "Anatomy lecture",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    original = session.anatomy_original_path(1)
    annotated = session.anatomy_annotated_path(1)
    original.write_bytes(b"original")
    annotated.write_bytes(b"annotated")
    session.add_anatomy_capture(
        12.0,
        original,
        annotated,
        "Median nerve",
        True,
    )
    dialog = SessionLibraryDialog([tmp_path])

    dialog.copy_codex_anki_button.click()
    app.processEvents()

    copied = QApplication.clipboard().text()
    assert "Median nerve" in copied
    assert "`saCloze++`" in copied
    assert (session.folder / "codex-anki-prompt.txt").read_text(
        encoding="utf-8"
    ) == copied
