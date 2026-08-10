from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog

from screen_capture_transcriber.learning_note_dialog import LearningNoteDialog
from screen_capture_transcriber.learning_note_preferences import (
    MAX_TEXT_SIZE_POINTS,
    MIN_TEXT_SIZE_POINTS,
    LearningNotePreferences,
    load_learning_note_preferences,
    save_learning_note_preferences,
)
from screen_capture_transcriber.learning_notes import (
    render_transcript_with_notes,
    transcript_context_for_note,
)
from screen_capture_transcriber.models import (
    CaptureRegion,
    SessionManifest,
    TranscriptCue,
)
from screen_capture_transcriber.review import build_anatomy_review


def _session_with_note(tmp_path) -> SessionManifest:
    session = SessionManifest.create(
        tmp_path,
        "ACL concepts",
        CaptureRegion(0, 0, 1280, 720),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    session.source_transcript_cues = [
        TranscriptCue("1:10", 70.0, "Earlier unrelated discussion."),
        TranscriptCue("1:35", 95.0, "The ACL restrains anterior translation."),
        TranscriptCue("1:42", 102.0, "The posterolateral bundle resists hyperextension."),
        TranscriptCue("2:20", 140.0, "Later unrelated discussion."),
    ]
    session.transcript_markdown_path.write_text(
        "# ACL concepts\n\n**[01:35]** The ACL restrains anterior translation.\n",
        encoding="utf-8",
    )
    session.add_learning_note(
        48.0,
        "The ACL is the primary restraint to anterior tibial translation.",
        100.0,
    )
    return session


def test_note_context_uses_source_video_timestamp_and_nearby_cues(tmp_path) -> None:
    session = _session_with_note(tmp_path)

    context = transcript_context_for_note(session, session.learning_notes[0])

    assert "[01:35]" in context
    assert "[01:42]" in context
    assert "Earlier unrelated" not in context
    assert "Later unrelated" not in context


def test_transcript_plus_notes_keeps_user_text_clearly_separate(tmp_path) -> None:
    session = _session_with_note(tmp_path)

    combined = render_transcript_with_notes(session)

    assert "# ACL concepts" in combined
    assert "# User Learning Notes" in combined
    assert (
        "[USER LEARNING NOTE — 01:40] "
        "The ACL is the primary restraint"
    ) in combined


def test_learning_note_dialog_prepares_without_network_work() -> None:
    app = QApplication.instance() or QApplication([])
    dialog = LearningNoteDialog()

    dialog.prepare(123.0, "[02:01] Nearby transcript sentence.")
    dialog.show()
    app.processEvents()

    assert "02:03" in dialog.timestamp_label.text()
    assert "Nearby transcript sentence" in dialog.context_edit.toPlainText()
    assert dialog.note_edit.hasFocus()
    assert not dialog.save_button.isEnabled()

    dialog.note_edit.setPlainText("A durable learning point.")
    app.processEvents()

    assert dialog.note_text == "A durable learning point."
    assert dialog.timestamp_seconds == 123.0
    assert dialog.save_button.isEnabled()
    dialog.reject()


def test_ctrl_enter_saves_a_nonempty_learning_note() -> None:
    app = QApplication.instance() or QApplication([])
    dialog = LearningNoteDialog()
    dialog.prepare(10.0, "Nearby transcript.")
    dialog.show()
    app.processEvents()
    dialog.note_edit.setPlainText("Remember this.")

    QTest.keyClick(
        dialog.note_edit,
        Qt.Key.Key_Return,
        Qt.KeyboardModifier.ControlModifier,
    )
    app.processEvents()

    assert dialog.result() == QDialog.DialogCode.Accepted


def test_note_and_transcript_text_size_persists_across_dialogs(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    preferences_path = tmp_path / "learning-note-settings.json"
    first = LearningNoteDialog(preferences_path=preferences_path)

    first.increase_text_size_button.click()
    first.increase_text_size_button.click()
    app.processEvents()

    assert first.text_size_points == 14
    assert first.text_size_label.text() == "14 pt"
    assert "font-size:14pt" in first.note_edit.styleSheet()
    assert first.note_edit.styleSheet() == first.context_edit.styleSheet()

    reopened = LearningNoteDialog(preferences_path=preferences_path)

    assert reopened.text_size_points == 14
    assert reopened.text_size_label.text() == "14 pt"
    assert reopened.note_edit.styleSheet() == reopened.context_edit.styleSheet()
    assert "font-size:14pt" in reopened.context_edit.styleSheet()


def test_learning_note_text_size_preferences_are_clamped(tmp_path) -> None:
    preferences_path = tmp_path / "learning-note-settings.json"
    save_learning_note_preferences(
        LearningNotePreferences(MAX_TEXT_SIZE_POINTS + 100),
        preferences_path,
    )

    assert (
        load_learning_note_preferences(preferences_path).text_size_points
        == MAX_TEXT_SIZE_POINTS
    )

    save_learning_note_preferences(
        LearningNotePreferences(MIN_TEXT_SIZE_POINTS - 100),
        preferences_path,
    )

    assert (
        load_learning_note_preferences(preferences_path).text_size_points
        == MIN_TEXT_SIZE_POINTS
    )


def test_existing_html_review_includes_notes_transcript_and_seek_target(
    tmp_path,
) -> None:
    session = _session_with_note(tmp_path)

    path = build_anatomy_review(session)
    html = path.read_text(encoding="utf-8")

    assert "Session review" in html
    assert "Timestamped Learning Notes" in html
    assert session.learning_notes[0].id in html
    assert 'data-time="48.000"' in html
    assert "01:40" in html
    assert "Copy Transcript + Notes" in html
    assert "The ACL restrains anterior translation" in html
