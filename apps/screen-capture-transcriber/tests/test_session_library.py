from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from screen_capture_transcriber.models import CaptureRegion, SessionManifest
from screen_capture_transcriber.session_library import (
    SessionLibraryDialog,
    delete_session_folder,
    discover_sessions,
    format_file_size,
    session_folder_size,
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


def test_session_size_includes_all_nested_files_and_formats_cleanly(tmp_path) -> None:
    folder = tmp_path / "session"
    screenshots = folder / "screenshots"
    screenshots.mkdir(parents=True)
    (folder / "recording.mp4").write_bytes(b"x" * 1024)
    (screenshots / "capture.png").write_bytes(b"x" * 512)

    assert session_folder_size(folder) == 1536
    assert format_file_size(1536) == "1.5 KB"
    assert format_file_size(3 * 1024 * 1024) == "3.0 MB"


def test_past_sessions_shows_total_size_in_table_and_details(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    session = SessionManifest.create(
        tmp_path,
        "Sized lecture",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    (session.folder / "recording.mp4").write_bytes(b"x" * 2048)

    dialog = SessionLibraryDialog([tmp_path])
    app.processEvents()
    entry = dialog._entries[0]
    expected = format_file_size(entry.total_size_bytes)

    assert dialog.tree.headerItem().text(3) == "Size"
    assert dialog.tree.topLevelItem(0).text(3) == expected
    assert expected in dialog.detail_meta.text()
    assert expected in dialog.count_label.text()


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


def test_past_sessions_edits_copies_and_deletes_timestamped_notes(
    tmp_path,
    monkeypatch,
) -> None:
    app = QApplication.instance() or QApplication([])
    session = SessionManifest.create(
        tmp_path,
        "Learning notes lecture",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    note = session.add_learning_note(
        12.0,
        "Initial user learning point.",
        24.0,
    )
    session.transcript_markdown_path.write_text(
        "# Transcript\n\nThe original spoken transcript.",
        encoding="utf-8",
    )
    dialog = SessionLibraryDialog([tmp_path])
    app.processEvents()

    assert dialog.tree.headerItem().text(5) == "Notes"
    assert dialog.tree.topLevelItem(0).text(5) == "1"
    assert (
        dialog.notes_list.currentItem().data(Qt.ItemDataRole.UserRole)
        == note.id
    )

    dialog.note_edit.setPlainText("Edited intentional learning point.")
    dialog.save_note_button.click()
    app.processEvents()
    assert (
        SessionManifest.load(session.manifest_path).learning_notes[0].text
        == "Edited intentional learning point."
    )

    dialog.copy_transcript_notes_button.click()
    app.processEvents()
    copied = QApplication.clipboard().text()
    assert "The original spoken transcript." in copied
    assert "[USER LEARNING NOTE — 00:24]" in copied
    assert "Edited intentional learning point." in copied

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    dialog.delete_note_button.click()
    app.processEvents()

    assert SessionManifest.load(session.manifest_path).learning_notes == []
    assert dialog.tree.topLevelItem(0).text(5) == "0"


def test_delete_session_folder_removes_every_associated_file(tmp_path) -> None:
    recordings = tmp_path / "recordings"
    recordings.mkdir()
    session = SessionManifest.create(
        recordings,
        "Delete me",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    (session.folder / "video.mp4").write_bytes(b"video")
    (session.folder / "audio.wav").write_bytes(b"audio")
    screenshots = session.folder / "screenshots"
    screenshots.mkdir()
    (screenshots / "anatomy.png").write_bytes(b"image")

    delete_session_folder(session.folder, [recordings])

    assert not session.folder.exists()


def test_delete_session_folder_rejects_folder_outside_recording_roots(
    tmp_path,
) -> None:
    recordings = tmp_path / "recordings"
    recordings.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "session.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="direct child"):
        delete_session_folder(outside, [recordings])

    assert outside.is_dir()


def test_delete_button_removes_session_from_disk_and_library(
    tmp_path,
    monkeypatch,
) -> None:
    app = QApplication.instance() or QApplication([])
    session = SessionManifest.create(
        tmp_path,
        "Old lecture",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    (session.folder / "recording.mp4").write_bytes(b"video")
    dialog = SessionLibraryDialog([tmp_path])
    monkeypatch.setattr(dialog, "_confirm_delete", lambda _session: True)

    dialog.delete_button.click()
    app.processEvents()

    assert not session.folder.exists()
    assert dialog.tree.topLevelItemCount() == 0
    assert session.folder.resolve() in dialog.deleted_folders
    assert not dialog.delete_button.isEnabled()


def test_delete_button_cancellation_preserves_session(tmp_path, monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    session = SessionManifest.create(
        tmp_path,
        "Keep me",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    dialog = SessionLibraryDialog([tmp_path])
    monkeypatch.setattr(dialog, "_confirm_delete", lambda _session: False)

    dialog.delete_button.click()
    app.processEvents()

    assert session.folder.is_dir()
    assert dialog.tree.topLevelItemCount() == 1
    assert not dialog.deleted_folders
