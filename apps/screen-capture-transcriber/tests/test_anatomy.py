from __future__ import annotations

import json
import inspect
import os
import sqlite3
import time
import zipfile

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from screen_capture_transcriber.anki_export import build_anatomy_apkg
import screen_capture_transcriber.annotation as annotation_module
from screen_capture_transcriber.annotation import (
    AnatomyAnnotationDialog,
    AnnotationCanvas,
    Stroke,
)
from screen_capture_transcriber.anatomy_suggestions import SuggestedAnatomyTerm
from screen_capture_transcriber.annotation_preferences import (
    DEFAULT_ANNOTATION_COLOR,
    load_annotation_preferences,
)
from screen_capture_transcriber.models import CaptureRegion, SessionManifest
from screen_capture_transcriber.models import TranscriptCue
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


def _representative_opaque_screenshot(
    width: int = 1600,
    height: int = 900,
) -> QImage:
    texture_width = max(1, width // 4)
    texture_height = max(1, height // 4)
    texture = QImage(
        texture_width,
        texture_height,
        QImage.Format.Format_RGB32,
    )
    random_state = 0x12345678
    for y in range(texture_height):
        for x in range(texture_width):
            random_state = (
                1664525 * random_state + 1013904223
            ) & 0xFFFFFFFF
            noise = (random_state >> 24) & 0xFF
            distance = (
                (x - texture_width / 2) ** 2
                + (y - texture_height / 2) ** 2
            ) ** 0.5
            base = max(20, min(210, round(185 - distance * 0.45)))
            shade = max(0, min(255, base + (noise - 128) // 5))
            texture.setPixelColor(
                x,
                y,
                QColor(
                    shade,
                    shade + min(5, 255 - shade),
                    shade + min(10, 255 - shade),
                ),
            )
    image = texture.scaled(
        width,
        height,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    ).convertToFormat(QImage.Format.Format_ARGB32)
    painter = QPainter(image)
    painter.setPen(QColor("#BCC7D4"))
    painter.setBrush(QColor("#4A5664"))
    for index in range(18):
        x = 60 + (index % 6) * 255
        y = 90 + (index // 6) * 270
        painter.drawEllipse(x, y, 190, 130)
    painter.end()
    return image


def _render_canvas_before_encoding(canvas: AnnotationCanvas) -> QImage:
    rendered = canvas._base_image().copy()
    painter = QPainter(rendered)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    for stroke in canvas._strokes:
        canvas._draw_stroke(painter, stroke)
    painter.end()
    if canvas._crop_rect is not None:
        rendered = rendered.copy(canvas._crop_rect.toAlignedRect())
    return rendered


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


def test_annotation_png_is_lossless_opaque_rgb_and_normally_compressed(
    tmp_path,
) -> None:
    QApplication.instance() or QApplication([])
    source = tmp_path / "representative-source.png"
    legacy = tmp_path / "legacy-quality-100.png"
    output = tmp_path / "capture-001-annotated.png"
    image = _representative_opaque_screenshot()
    assert image.save(str(source), "PNG")

    canvas = AnnotationCanvas(source)
    canvas._strokes.append(
        Stroke(
            "arrow",
            "#FFCC00",
            12.0,
            [QPointF(200, 300), QPointF(1200, 600)],
        )
    )
    before_encoding = _render_canvas_before_encoding(canvas)
    assert before_encoding.save(str(legacy), "PNG", 100)

    saved_path = canvas.save(output)
    reloaded = QImage(str(output))
    legacy_reloaded = QImage(str(legacy))

    assert saved_path == output
    assert output.name == "capture-001-annotated.png"
    assert reloaded.size() == before_encoding.size()
    assert (
        reloaded.convertToFormat(QImage.Format.Format_RGB888)
        == legacy_reloaded.convertToFormat(QImage.Format.Format_RGB888)
    )
    assert not reloaded.hasAlphaChannel()
    assert reloaded.pixelColor(700, 450).name().upper() == "#FFCC00"

    uncompressed_rgba_bytes = reloaded.width() * reloaded.height() * 4
    assert output.stat().st_size < uncompressed_rgba_bytes // 2
    assert output.stat().st_size < legacy.stat().st_size // 4


def test_production_annotation_save_does_not_use_png_quality_100() -> None:
    source = inspect.getsource(AnnotationCanvas.save)

    assert 'save(str(output_path), "PNG", 100)' not in source
    assert "QImage.Format.Format_RGB888" in source
    assert 'save(str(output_path), "PNG")' in source


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


def test_resave_keeps_session_manifest_image_and_edit_paths(tmp_path) -> None:
    QApplication.instance() or QApplication([])
    session = SessionManifest.create(
        tmp_path,
        "Optimized annotation paths",
        CaptureRegion(0, 0, 800, 450),
        "Demo loopback",
        1,
        1.0,
        1.1,
    )
    original = session.anatomy_original_path(1)
    annotated = session.anatomy_annotated_path(1)
    edit = session.anatomy_edit_path(1)
    image = _representative_opaque_screenshot(800, 450)
    assert image.save(str(original), "PNG")

    canvas = AnnotationCanvas(original)
    canvas._strokes.append(
        Stroke(
            "arrow",
            "#FFAA00",
            8.0,
            [QPointF(100, 100), QPointF(500, 250)],
        )
    )
    canvas._crop_rect = QRectF(50, 25, 700, 400)
    canvas.save(annotated)
    canvas.save_state(edit)
    capture = session.add_anatomy_capture(
        12.0,
        original,
        annotated,
        "Test structure",
        True,
        edit_path=edit,
    )
    manifest_paths_before = (
        capture.original_image,
        capture.annotated_image,
        capture.edit_file,
    )

    reeditor = AnnotationCanvas()
    reeditor.load_image(original, edit)
    assert len(reeditor._strokes) == 1
    assert reeditor.crop_rect == QRectF(50, 25, 700, 400)
    reeditor.save(annotated)
    reeditor.save_state(edit)

    loaded = SessionManifest.load(session.manifest_path)
    loaded_capture = loaded.anatomy_captures[0]
    assert annotated.name == "capture-001-annotated.png"
    assert edit.name == "capture-001-edit.json"
    assert (
        loaded_capture.original_image,
        loaded_capture.annotated_image,
        loaded_capture.edit_file,
    ) == manifest_paths_before
    assert not QImage(str(annotated)).hasAlphaChannel()


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


def test_new_motion_crop_is_smaller_square_centered_on_cursor(
    tmp_path,
    monkeypatch,
) -> None:
    QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))
    canvas = AnnotationCanvas(source)
    monkeypatch.setattr(
        canvas,
        "_cursor_image_point",
        lambda: QPointF(450, 250),
    )

    canvas.begin_crop("motion")

    crop = canvas.crop_rect
    assert crop is not None
    assert crop.width() == pytest.approx(450 * 0.5)
    assert crop.height() == pytest.approx(450 * 0.5)
    assert crop.center().x() == pytest.approx(450)
    assert crop.center().y() == pytest.approx(250)


def test_standard_crop_keeps_large_rectangular_default(tmp_path) -> None:
    QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))
    canvas = AnnotationCanvas(source)

    canvas.begin_crop("standard")

    crop = canvas.crop_rect
    assert crop is not None
    assert crop.width() == pytest.approx(800 * 0.84)
    assert crop.height() == pytest.approx(450 * 0.84)
    assert crop.center().x() == pytest.approx(400)
    assert crop.center().y() == pytest.approx(225)


def test_cursor_centered_motion_crop_is_clamped_inside_image(
    tmp_path,
    monkeypatch,
) -> None:
    QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))
    canvas = AnnotationCanvas(source)
    monkeypatch.setattr(
        canvas,
        "_cursor_image_point",
        lambda: QPointF(790, 440),
    )

    canvas.begin_crop("motion")

    crop = canvas.crop_rect
    assert crop is not None
    assert crop.right() == pytest.approx(800)
    assert crop.bottom() == pytest.approx(450)
    assert crop.left() >= 0
    assert crop.top() >= 0


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

    stroke = Stroke(
        "arrow",
        "#FFAA00",
        8,
        [QPointF(100, 100), QPointF(300, 200)],
    )
    dialog.canvas._strokes.append(stroke)
    QTest.keyClick(
        dialog.label_edit,
        Qt.Key.Key_Z,
        Qt.KeyboardModifier.ControlModifier,
    )
    assert dialog.canvas._strokes == []

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


def test_right_mouse_hold_shows_and_releases_magnifier(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))
    canvas = AnnotationCanvas(source)
    canvas.resize(900, 560)
    canvas.show()
    app.processEvents()

    center = canvas.rect().center()
    QTest.mousePress(canvas, Qt.MouseButton.RightButton, pos=center)
    assert canvas.magnifier_active
    assert not canvas.grab().toImage().isNull()
    QTest.mouseRelease(canvas, Qt.MouseButton.RightButton, pos=center)
    assert not canvas.magnifier_active


def test_arrow_keeps_dragging_while_right_button_magnifier_is_held(
    tmp_path,
) -> None:
    app = QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    image = QImage(1200, 800, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))
    canvas = AnnotationCanvas(source)
    canvas.resize(1000, 700)
    canvas.show()
    app.processEvents()

    start = canvas.rect().center()
    end = start + QPoint(140, 90)
    QTest.mousePress(canvas, Qt.MouseButton.LeftButton, pos=start)
    QTest.mousePress(canvas, Qt.MouseButton.RightButton, pos=start)
    QTest.mouseMove(canvas, end, delay=5)

    assert canvas.magnifier_active
    assert canvas._active is not None
    assert len(canvas._active.points) == 2
    expected = canvas._to_image(QPointF(end))
    assert expected is not None
    assert abs(canvas._active.points[-1].x() - expected.x()) < 2
    assert abs(canvas._active.points[-1].y() - expected.y()) < 2
    assert annotation_module.MAGNIFIER_WIDTH == 720.0
    assert annotation_module.MAGNIFIER_HEIGHT == 480.0

    QTest.mouseRelease(canvas, Qt.MouseButton.RightButton, pos=end)
    QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=end)


def test_color_selection_persists_but_recent_requires_saved_use(tmp_path) -> None:
    QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    output = tmp_path / "annotated.png"
    preferences_path = tmp_path / "annotation-settings.json"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))

    dialog = AnatomyAnnotationDialog(
        source,
        preferences_path=preferences_path,
    )
    dialog._apply_annotation_color("#33AAEE")
    selected_only = load_annotation_preferences(preferences_path)
    assert selected_only.selected_color == "#33AAEE"
    assert selected_only.recent_colors == []

    stroke = Stroke(
        "arrow",
        "#33AAEE",
        8,
        [QPointF(100, 100), QPointF(300, 200)],
    )
    dialog.canvas._strokes.append(stroke)
    dialog.canvas._new_stroke_ids.add(id(stroke))
    dialog.save_annotation(output)
    used = load_annotation_preferences(preferences_path)
    assert used.recent_colors == ["#33AAEE"]

    dialog._reset_annotation_color()
    reset = load_annotation_preferences(preferences_path)
    assert reset.selected_color == DEFAULT_ANNOTATION_COLOR
    assert reset.recent_colors == ["#33AAEE"]


def test_suggested_term_chip_populates_editable_label_and_scrolls(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))
    dialog = AnatomyAnnotationDialog(
        source,
        preferences_path=tmp_path / "annotation-settings.json",
    )
    dialog.resize(700, 600)
    dialog.show()
    app.processEvents()
    suggestions = [
        SuggestedAnatomyTerm(f"Structure {index}", float(index))
        for index in range(20)
    ]
    dialog._on_suggestions_ready(dialog._suggestion_request_id, suggestions)
    app.processEvents()

    first = dialog.suggestion_content.findChildren(QPushButton)[0]
    first.click()
    assert dialog.label_edit.text() == "Structure 0"
    dialog.label_edit.insert(" edited")
    assert dialog.label_edit.text() == "Structure 0 edited"

    dialog.suggestion_scroll.hovered = True
    before = dialog.suggestion_scroll.horizontalScrollBar().value()
    QTest.keyClick(dialog.label_edit, Qt.Key.Key_Right)
    after = dialog.suggestion_scroll.horizontalScrollBar().value()
    assert after > before


def test_transcript_suggestions_never_block_dialog_preparation(
    tmp_path,
    monkeypatch,
) -> None:
    app = QApplication.instance() or QApplication([])
    source = tmp_path / "source.png"
    image = QImage(800, 450, QImage.Format.Format_RGB32)
    image.fill("#102030")
    assert image.save(str(source))

    def delayed_suggestions(*_args, **_kwargs):
        time.sleep(0.4)
        return [SuggestedAnatomyTerm("Median nerve", 10.0)]

    monkeypatch.setattr(
        annotation_module,
        "suggest_anatomy_terms",
        delayed_suggestions,
    )
    dialog = AnatomyAnnotationDialog(
        preferences_path=tmp_path / "annotation-settings.json"
    )
    started = time.perf_counter()
    dialog.prepare(
        source,
        "00:10",
        transcript_cues=[TranscriptCue("00:10", 10.0, "Median nerve")],
        capture_timestamp_seconds=10.0,
        api_key="test-key",
    )
    elapsed = time.perf_counter() - started
    assert elapsed < 0.2

    deadline = time.perf_counter() + 2.0
    while dialog._suggestion_workers and time.perf_counter() < deadline:
        app.processEvents()
        QTest.qWait(20)
    app.processEvents()
    assert [
        button.text()
        for button in dialog.suggestion_content.findChildren(QPushButton)
    ] == ["Median nerve"]


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
