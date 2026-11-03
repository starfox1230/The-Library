"""Run with Anki's Python: python tests/test_pocket_knife_authoring.py.

Real Qt mouse, keyboard, layout and image rendering; no user's collection or clipboard.
"""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6 import QtCore, QtGui, QtWidgets, QtTest


ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "apps/anki-pocket-knife"


class AddCards:
    def __init__(self, *, blank=True, has_model=True):
        self.selected = "Basic"
        self.col = SimpleNamespace(models=SimpleNamespace(
            by_name=lambda name: {"id": 42, "name": name}
            if has_model and name == "saCloze++" else None))
        self.editor = SimpleNamespace(fieldsAreBlank=lambda: blank)

    def set_note_type(self, model_id):
        self.selected = model_id

    def reopen(self, mw):
        if self.editor.fieldsAreBlank():
            self.selected = "Basic"


class Note(dict):
    def __init__(self, text, *, cloze=True):
        super().__init__(Text=text, Extra="Keep this context")
        self.cloze = cloze

    def note_type(self):
        return {"name": "saCloze++" if self.cloze else "Basic",
                "type": 1 if self.cloze else 0,
                "flds": [{"name": "Text"}, {"name": "Extra"}]}


class AuthoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        # The offscreen Qt plugin does not discover Windows system fonts itself.
        for font_name in ("segoeui.ttf", "segoeuib.ttf"):
            font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / font_name
            if font_path.exists():
                QtGui.QFontDatabase.addApplicationFont(str(font_path))
        package = ModuleType("pocket_authoring_test")
        package.__path__ = [str(ADDON)]
        aqt = ModuleType("aqt")
        aqt.gui_hooks = SimpleNamespace(editor_did_init_buttons=[], editor_did_load_note=[],
                                        add_cards_did_init=[])
        aqt.mw = None
        qt = ModuleType("aqt.qt")
        for source in (QtCore, QtGui, QtWidgets):
            for name in dir(source):
                if name.startswith("Q"):
                    setattr(qt, name, getattr(source, name))
        editor = ModuleType("aqt.editor")
        editor.Editor = object
        addcards = ModuleType("aqt.addcards")
        addcards.AddCards = AddCards
        theme = ModuleType("aqt.theme")
        theme.theme_manager = SimpleNamespace(night_mode=False)
        utils = ModuleType("aqt.utils")
        utils.showWarning = lambda *args, **kwargs: None
        utils.tooltip = lambda *args, **kwargs: None
        common = ModuleType(package.__name__ + ".common")
        common.collection_media_dir = lambda: Path(".")
        common.user_files_dir = lambda: Path(tempfile.gettempdir()) / "pocket-authoring-tests"
        common.addon_root = lambda: ADDON
        settings = ModuleType(package.__name__ + ".settings")
        settings.load_settings = lambda: {}
        settings.save_settings = lambda value: None
        settings.get_setting = lambda key: False
        settings.set_setting = lambda key, value: value
        cls.modules = patch.dict(sys.modules, {
            package.__name__: package, "aqt": aqt, "aqt.qt": qt,
            "aqt.editor": editor, "aqt.utils": utils, "aqt.addcards": addcards,
            "aqt.theme": theme, common.__name__: common, settings.__name__: settings,
        })
        cls.modules.start()
        for name in ("draw_on_image", "visual_card_multitude"):
            spec = importlib.util.spec_from_file_location(
                package.__name__ + "." + name, ADDON / (name + ".py"))
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            setattr(cls, name, module)

    @classmethod
    def tearDownClass(cls):
        cls.modules.stop()

    def setUp(self):
        self.drawing = self.draw_on_image
        self.visual = self.visual_card_multitude
        image = QtGui.QImage(600, 400, QtGui.QImage.Format.Format_ARGB32)
        image.fill(QtGui.QColor("#123456"))
        self.canvas = self.drawing.DrawingCanvas(image)
        self.canvas.resize(916, 616)
        self.canvas.show()
        self.app.processEvents()
        self.addCleanup(self.canvas.deleteLater)

    def click_image(self, x=50, y=70):
        target = self.canvas._target_rect()
        scale = target.width() / 600
        QtTest.QTest.mouseClick(self.canvas, QtCore.Qt.MouseButton.LeftButton,
                               pos=QtCore.QPoint(round(target.x() + x * scale),
                                                round(target.y() + y * scale)))

    def type_label(self, text="Aorta"):
        self.canvas.set_tool("text")
        self.click_image()
        self.app.processEvents()
        QtTest.QTest.keyClicks(self.canvas._text_box.editor, text)

    def test_text_uses_selected_color_and_export_has_no_box_background(self):
        self.canvas.set_pen_color(QtGui.QColor("#ff0000"))
        self.type_label()
        image = self.canvas.rendered_image()
        annotation = self.canvas._strokes[0]
        self.assertEqual(annotation.color, "#FF0000")
        self.assertEqual(annotation.text, "Aorta")
        red = [(x, y) for y in range(400) for x in range(600)
               if image.pixelColor(x, y).red() > 180
               and image.pixelColor(x, y).green() < 80]
        self.assertGreater(len(red), 30)
        for x, y in red:
            self.assertTrue(annotation.rect.contains(QtCore.QPointF(x, y)))
        self.assertEqual(image.pixelColor(250, 140), QtGui.QColor("#123456"))
        self.assertEqual(image.pixelColor(5, 5), QtGui.QColor("#123456"))

    def test_drag_move_resize_wrap_and_export_without_resizing_dialog(self):
        self.type_label("Aortic arch and descending aorta")
        box = self.canvas._text_box
        before = QtCore.QRectF(self.canvas._text_annotation.rect)
        canvas_size = self.canvas.size()
        QtTest.QTest.mousePress(box, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(15, 10))
        QtTest.QTest.mouseMove(box, QtCore.QPoint(55, 30))
        QtTest.QTest.mouseRelease(box, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(15, 10))
        self.assertGreater(self.canvas._text_annotation.rect.x(), before.x())
        grip = box.grip
        QtTest.QTest.mousePress(grip, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(5, 5))
        QtTest.QTest.mouseMove(grip, QtCore.QPoint(-130, 65))
        QtTest.QTest.mouseRelease(grip, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(5, 5))
        self.app.processEvents()
        self.assertLess(self.canvas._text_annotation.rect.width(), before.width())
        self.assertGreater(self.canvas._text_annotation.rect.height(), before.height())
        self.assertEqual(self.canvas.size(), canvas_size)
        self.assertGreater(box.editor.document().size().height(), 2 * 24 * 1.5)
        expected = QtCore.QRectF(self.canvas._text_annotation.rect)
        self.canvas.rendered_image()
        self.assertEqual(self.canvas._strokes[0].rect, expected)

    def test_text_edit_recolor_undo_redo_and_clear(self):
        self.type_label()
        original = self.canvas.rendered_image()
        annotation = self.canvas._strokes[0]
        self.canvas.start_text(annotation.rect.center())
        self.canvas._text_box.editor.setPlainText("Renal artery")
        self.canvas.set_pen_color(QtGui.QColor("#00ff00"))
        self.canvas.set_text_size(36)
        changed = self.canvas.rendered_image()
        self.assertNotEqual(original, changed)
        self.canvas.undo()
        self.assertEqual(self.canvas.rendered_image(), original)
        self.canvas.redo()
        self.assertEqual(self.canvas.rendered_image(), changed)
        self.canvas.clear()
        self.assertEqual(self.canvas.rendered_image(), self.canvas._image)
        self.canvas.undo()
        self.assertEqual(self.canvas.rendered_image(), changed)
        self.canvas.undo()
        self.canvas.undo()
        self.assertEqual(self.canvas.rendered_image(), self.canvas._image)

    def test_canvas_resize_keeps_text_anchored_in_image_coordinates(self):
        self.type_label()
        before = QtCore.QRectF(self.canvas._text_annotation.rect)
        self.canvas.resize(616, 416)
        self.app.processEvents()
        self.assertEqual(self.canvas._text_annotation.rect, before)
        self.canvas.finish_text()
        self.assertEqual(self.canvas._strokes[0].rect, before)

    def test_empty_text_is_discarded_and_switching_tools_keeps_written_text(self):
        self.canvas.set_tool("text")
        self.click_image()
        self.canvas.set_tool("arrow")
        self.assertEqual(self.canvas._strokes, [])
        self.type_label()
        self.canvas.set_tool("pen")
        self.assertEqual(self.canvas._strokes[0].text, "Aorta")

    def test_text_preferences_are_independent_of_arrow_and_pen_width(self):
        preferences = self.drawing.AnnotationPreferences()
        preferences.set_width_for("text", 60)
        preferences.set_width_for("pen", 4)
        self.assertEqual(preferences.width_for("text"), 60)
        self.assertEqual(preferences.width_for("arrow"), 8)
        self.assertEqual(preferences.width_for("pen"), 4)
        with patch.object(self.drawing, "load_settings", return_value={
            "draw_on_image_tool": "text", "draw_on_image_text_size": 36,
        }):
            loaded = self.drawing._load_annotation_preferences()
        self.assertEqual(loaded.tool, "text")
        self.assertEqual(loaded.text_size, 36)

    def test_dialog_text_controls_and_real_font_under_dialog_stylesheet(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "image.png"
            self.canvas._image.save(str(source))
            dialog = self.drawing.DrawOnImageDialog(source)
            self.addCleanup(dialog.deleteLater)
            dialog.setWindowState(QtCore.Qt.WindowState.WindowNoState)
            dialog.resize(1440, 900)
            dialog.show()
            self.app.processEvents()
            dialog.text_button.click()
            self.assertTrue(dialog.text_button.isChecked())
            self.assertEqual(dialog.size_slider.maximum(), 144)
            dialog.size_slider.setValue(36)
            dialog.canvas.start_text(QtCore.QPointF(40, 60))
            self.app.processEvents()
            editor = dialog.canvas._text_box.editor
            QtTest.QTest.keyClicks(editor, "Ascending aorta")
            QtTest.QTest.keyClick(editor, QtCore.Qt.Key.Key_Return)
            QtTest.QTest.keyClicks(editor, "Text annotation")
            scale = dialog.canvas._target_rect().width() / 600
            self.assertEqual(editor.font().pixelSize(), round(36 * scale))
            self.assertTrue(dialog.isVisible())
            with patch.object(dialog, "copy_to_clipboard_and_close") as copy:
                QtTest.QTest.keyClick(editor, QtCore.Qt.Key.Key_C,
                                      QtCore.Qt.KeyboardModifier.ControlModifier)
                copy.assert_called_once()
            dialog.canvas.rendered_image()
            self.assertEqual(dialog.canvas._strokes[0].text, "Ascending aorta\nText annotation")
            dialog.draw_button.click()
            self.assertEqual(dialog.size_slider.maximum(), 30)
            self.assertEqual(dialog.size_slider.value(), 8)
            dialog.text_button.click()
            self.assertEqual(dialog.size_slider.value(), 36)
            dialog.close()

    def test_resize_handle_remains_visible_in_fullscreen(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "image.png"
            self.canvas._image.save(str(source))
            dialog = self.drawing.DrawOnImageDialog(source)
            self.addCleanup(dialog.deleteLater)
            dialog.show()
            self.app.processEvents()
            self.assertTrue(dialog.isFullScreen())
            dialog.text_button.click()
            dialog.canvas.start_text(QtCore.QPointF(50, 70))
            self.app.processEvents()
            self.assertTrue(dialog.canvas._text_box.grip.isVisible())
            dialog.close()

    def test_both_question_buttons_are_registered_together(self):
        class ToolbarEditor:
            parentWindow = AddCards()

            def __init__(self):
                self.buttons = {}

            def addButton(self, icon, command, callback, **kwargs):
                self.buttons[kwargs.get("label")] = callback
                return command

        editor = ToolbarEditor()
        with patch.object(self.visual, "is_add_cards_diagnosis_button_enabled", return_value=True):
            self.visual._on_setup_editor_buttons([], editor)
        self.assertIs(editor.buttons["Dx"], self.visual.apply_diagnosis_template)
        self.assertIs(editor.buttons["Struct"], self.visual.apply_structure_template)

    def test_structure_and_diagnosis_preserve_answer_images_and_extra(self):
        for structure in (False, True):
            note = Note('Old question {{c4::<b>Femoral artery</b>::hint}} '
                        '<img src="one.png"><br><img src="two.png">')
            editor = SimpleNamespace(parentWindow=AddCards(), note=note, loadNote=lambda *args: None)
            with patch.object(self.visual, "_apply_auto_deck_rules"), \
                 patch.object(self.visual, "is_add_cards_multi_image_counter_enabled", return_value=True):
                self.visual._apply_image_question_template(editor, structure=structure)
            prompt = "What structure is this?" if structure else "Most likely diagnosis?"
            self.assertEqual(note["Text"], prompt + '<br><br>{{c1::<b>Femoral artery</b>}}'
                             '<br><br><div data-pocket-knife-image-counter="true">1/2</div>'
                             '<img src="one.png"><img src="two.png">')
            self.assertEqual(note["Extra"], "Keep this context")
            self.assertEqual(editor._anki_pocket_knife_pending_diagnosis_cursor_ord, 0)

    def test_blank_structure_template_and_noncloze_guard(self):
        note = Note("")
        editor = SimpleNamespace(parentWindow=AddCards(), note=note, loadNote=lambda *args: None)
        with patch.object(self.visual, "_apply_auto_deck_rules"):
            self.visual.apply_structure_template(editor)
        self.assertEqual(note["Text"], "What structure is this?<br><br>{{c1::}}<br><br>")
        editor.note = Note("Original", cloze=False)
        self.visual.apply_structure_template(editor)
        self.assertEqual(editor.note["Text"], "Original")

    def test_add_cards_open_defaults_to_exact_sacloze_and_missing_model_is_safe(self):
        window = AddCards()
        self.visual._default_add_cards_to_sacloze(window)
        self.assertEqual(window.selected, 42)
        window = AddCards(has_model=False)
        self.visual._default_add_cards_to_sacloze(window)
        self.assertEqual(window.selected, "Basic")

    def test_reopen_blank_defaults_to_sacloze_but_keeps_unfinished_notes(self):
        self.visual._patch_add_cards_reopen()
        window = AddCards()
        window.reopen(None)
        self.assertEqual(window.selected, 42)
        window = AddCards(blank=False)
        window.selected = "Visual_Card_Multitude"
        window.reopen(None)
        self.assertEqual(window.selected, "Visual_Card_Multitude")


if __name__ == "__main__":
    unittest.main(verbosity=2)
