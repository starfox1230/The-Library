from __future__ import annotations

import json
import os
import sqlite3
import zipfile

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from screen_capture_transcriber.anki_export import build_anatomy_apkg
from screen_capture_transcriber.annotation import (
    AnatomyAnnotationDialog,
    AnnotationCanvas,
    Stroke,
)
from screen_capture_transcriber.models import CaptureRegion, SessionManifest
from screen_capture_transcriber.review import build_anatomy_review


def _session_with_capture(tmp_path) -> SessionManifest:
    session = SessionManifest.create(
        tmp_path,
        "Brachial plexus",
        CaptureRegion(0, 0, 640, 360),
        "Demo loopback",
        1,
        1.0,
        1.1,
    )
    original = session.anatomy_original_path(1)
    annotated = session.anatomy_annotated_path(1)
    image = QImage(640, 360, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(original))
    assert image.save(str(annotated))
    session.add_anatomy_capture(
        12.25,
        original,
        annotated,
        "Musculocutaneous nerve",
        True,
    )
    return session


def test_annotation_canvas_renders_at_native_resolution(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    output = tmp_path / "output.png"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#000000")
    assert image.save(str(source))

    canvas = AnnotationCanvas(source)
    canvas._strokes.append(
        Stroke(
            "arrow",
            "#FFAA00",
            8.0,
            [QPointF(100, 100), QPointF(400, 225)],
        )
    )
    canvas.save(output)

    rendered = QImage(str(output))
    assert rendered.width() == 800
    assert rendered.height() == 450
    assert app is not None


def test_crop_and_vector_state_round_trip(tmp_path) -> None:
    QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    output = tmp_path / "cropped.png"
    state = tmp_path / "edit.json"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))

    canvas = AnnotationCanvas(source)
    canvas._strokes.append(
        Stroke(
            "arrow",
            "#FFAA00",
            8,
            [QPointF(500, 100), QPointF(300, 200)],
        )
    )
    canvas.begin_crop("standard")
    canvas._crop_rect = QRectF(100, 75, 400, 250)
    canvas.commit_crop()
    canvas.save(output)
    canvas.save_state(state)

    rendered = QImage(str(output))
    assert rendered.size().width() == 400
    assert rendered.size().height() == 250
    reloaded = AnnotationCanvas()
    reloaded.load_image(source, state)
    assert len(reloaded._strokes) == 1
    assert reloaded.crop_rect == QRectF(100, 75, 400, 250)


def test_legacy_annotation_survives_crop_until_clear_drawing(tmp_path) -> None:
    QApplication.instance() or QApplication([])
    original = tmp_path / "original.png"
    preserved = tmp_path / "capture-001-preserved.png"
    unchanged = tmp_path / "unchanged.png"
    cleared = tmp_path / "cleared.png"
    state = tmp_path / "capture-001-edit.json"

    base = QImage(320, 180, QImage.Format.Format_RGB32)
    base.fill("#102030")
    assert base.save(str(original))
    annotated = base.copy()
    annotated.setPixelColor(160, 90, "#FFAA00")
    assert annotated.save(str(preserved))

    canvas = AnnotationCanvas()
    canvas.load_image(original, preserved_image_path=preserved)
    canvas._crop_rect = QRectF(100, 50, 120, 80)
    canvas.begin_crop("standard")
    canvas.commit_crop()
    canvas.save(unchanged)
    canvas.save_state(state)

    retained = QImage(str(unchanged))
    assert retained.size().width() == 120
    assert retained.size().height() == 80
    assert retained.pixelColor(60, 40).name().upper() == "#FFAA00"
    assert "capture-001-preserved.png" in state.read_text(encoding="utf-8")

    reloaded = AnnotationCanvas()
    reloaded.load_image(original, state)
    reloaded.clear()
    reloaded.save(cleared)

    restored = QImage(str(cleared))
    assert restored.size() == retained.size()
    assert restored.pixelColor(60, 40).name().upper() == "#102030"


def test_motion_crop_resize_and_control_move(tmp_path) -> None:
    QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))
    canvas = AnnotationCanvas(source)
    canvas._crop_rect = QRectF(200, 100, 300, 200)
    canvas.begin_crop("motion")
    canvas._motion_last_point = QPointF(300, 200)

    canvas._motion_crop(QPointF(320, 180), Qt.KeyboardModifier.NoModifier)
    resized = canvas.crop_rect
    assert resized is not None
    assert resized.width() > 300
    assert resized.height() > 200

    before = resized.topLeft()
    canvas._motion_crop(
        QPointF(330, 190),
        Qt.KeyboardModifier.ControlModifier,
    )
    moved = canvas.crop_rect
    assert moved is not None
    assert moved.topLeft() != before


def test_motion_crop_uses_recentered_relative_pointer_deltas(tmp_path, monkeypatch) -> None:
    QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))
    canvas = AnnotationCanvas(source)
    canvas.resize(640, 360)
    canvas._crop_rect = QRectF(200, 100, 300, 200)
    canvas.begin_crop("motion")
    assert canvas.cursor().shape() == Qt.CursorShape.BlankCursor

    recentered = []
    monkeypatch.setattr(
        canvas,
        "_recenter_motion_pointer",
        lambda: recentered.append(True),
    )
    anchor = QPointF(canvas.rect().center())
    canvas._motion_crop_from_pointer(
        anchor + QPointF(20, -10),
        Qt.KeyboardModifier.NoModifier,
    )
    first = canvas.crop_rect
    assert first is not None
    assert first.width() > 300
    assert first.height() > 200

    # Every event is measured from the center again, so neither the absolute
    # cursor position nor a monitor edge can limit subsequent movement.
    canvas._motion_crop_from_pointer(
        anchor + QPointF(20, 0),
        Qt.KeyboardModifier.NoModifier,
    )
    second = canvas.crop_rect
    assert second is not None
    assert second.width() > first.width()
    assert len(recentered) == 2

    canvas.commit_crop()
    assert canvas.cursor().shape() == Qt.CursorShape.CrossCursor


def test_annotation_keyboard_shortcuts(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))
    dialog = AnatomyAnnotationDialog(source)
    dialog.show()
    app.processEvents()

    QTest.keyClick(dialog.label_edit, Qt.Key.Key_Period)
    assert dialog.canvas.crop_mode == "motion"
    QTest.keyClick(dialog.label_edit, Qt.Key.Key_Backspace)
    assert dialog.canvas.crop_mode == ""

    QTest.keyClick(
        dialog.label_edit,
        Qt.Key.Key_Backspace,
        Qt.KeyboardModifier.ControlModifier,
    )
    assert dialog.result() == int(dialog.DialogCode.Rejected)

    dialog.prepare(source, "00:10")
    dialog.show()
    app.processEvents()
    QTest.keyClick(dialog.label_edit, Qt.Key.Key_Return)
    assert dialog.result() == int(dialog.DialogCode.Accepted)


def test_review_links_images_to_video_timestamp(tmp_path) -> None:
    QApplication.instance() or QApplication([])
    session = _session_with_capture(tmp_path)
    session.playback_path.write_bytes(b"video")

    review_path = build_anatomy_review(session)
    html = review_path.read_text(encoding="utf-8")

    assert "Musculocutaneous nerve" in html
    assert 'data-time="12.250"' in html
    assert 'src="recording.mp4"' in html
    assert "localStorage.setItem" in html
    assert "playback position is remembered" in html
    assert 'class="expand"' in html
    assert 'id="lightbox"' in html
    assert "height: clamp(190px, 34vh, 340px)" in html
    assert "object-fit: contain" in html
    assert "overflow-wrap: anywhere" in html
    assert 'lightbox.addEventListener("click", closeLightbox)' in html
    assert 'src="anatomy-review-version.js"' in html
    assert "checkForReviewUpdate" in html
    assert (session.folder / "anatomy-review-version.js").is_file()


def test_review_regeneration_updates_edits_badges_and_live_version(tmp_path) -> None:
    QApplication.instance() or QApplication([])
    session = _session_with_capture(tmp_path)
    session.playback_path.write_bytes(b"video")

    review_path = build_anatomy_review(session)
    first_version = (session.folder / "anatomy-review-version.js").read_text(
        encoding="utf-8"
    )
    assert "Anki card" in review_path.read_text(encoding="utf-8")

    capture = session.anatomy_captures[0]
    capture.label = "Median nerve"
    capture.create_anki_card = False
    session.save()
    build_anatomy_review(session)

    regenerated = review_path.read_text(encoding="utf-8")
    second_version = (session.folder / "anatomy-review-version.js").read_text(
        encoding="utf-8"
    )
    assert "Median nerve" in regenerated
    assert "<span class='badge'>Anki card</span>" not in regenerated
    assert second_version != first_version


def test_anki_export_uses_canonical_sacloze_model(tmp_path) -> None:
    pytest.importorskip("genanki")
    QApplication.instance() or QApplication([])
    session = _session_with_capture(tmp_path)

    output = build_anatomy_apkg(session)
    assert output is not None and output.is_file()
    with zipfile.ZipFile(output) as package:
        package.extract("collection.anki2", tmp_path / "unpacked")
    database = sqlite3.connect(tmp_path / "unpacked" / "collection.anki2")
    try:
        note_row = database.execute("select flds, tags from notes").fetchone()
        fields = note_row[0].split("\x1f")
        tags = note_row[1]
        models = json.loads(database.execute("select models from col").fetchone()[0])
        decks = json.loads(database.execute("select decks from col").fetchone()[0])
    finally:
        database.close()

    assert "{{c1::Musculocutaneous nerve}}" in fields[0]
    assert "capture-001-annotated.png" in fields[0]
    assert "#AnkiChat::" in tags and "_Anatomy" in tags
    assert any(model["name"] == "saCloze++" for model in models.values())
    assert any(deck["name"] == "Saved Cards" for deck in decks.values())
