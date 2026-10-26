"""Real Qt rendering with simulated clipboard failures; no user clipboard changes.

Run with Anki's Python (PyQt6 required): python tests/test_draw_on_image_copy.py
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
try:
    from PyQt6 import QtCore, QtGui, QtWidgets, QtTest
except ImportError:
    raise unittest.SkipTest("Run the image-copy tests with Anki's Python (PyQt6 required).")


ROOT = Path(__file__).resolve().parents[1]


class Clipboard:
    def __init__(self, blocked=0, missing_png=False):
        self.blocked = blocked
        self.missing_png = missing_png
        self.writes = 0
        self.mime = QtCore.QMimeData()

    def setMimeData(self, mime):
        self.writes += 1
        if self.writes > self.blocked:
            self.mime = mime
            if self.missing_png:
                self.mime.removeFormat("image/png")

    def image(self):
        return self.mime.imageData() if self.mime.hasImage() else QtGui.QImage()

    def mimeData(self):
        return self.mime

    def ownsClipboard(self):
        return self.writes > self.blocked


class ImageCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        package = ModuleType("draw_copy_test")
        package.__path__ = [str(ROOT / "apps/anki-pocket-knife")]
        aqt = ModuleType("aqt")
        aqt.gui_hooks = SimpleNamespace(editor_did_init=[], editor_did_load_note=[])
        aqt.mw = None
        qt = ModuleType("aqt.qt")
        for source in (QtCore, QtGui, QtWidgets):
            for name in dir(source):
                if name.startswith("Q"):
                    setattr(qt, name, getattr(source, name))
        editor = ModuleType("aqt.editor")
        editor.Editor = object
        utils = ModuleType("aqt.utils")
        utils.showWarning = lambda *args, **kwargs: None
        utils.tooltip = lambda *args, **kwargs: None
        common = ModuleType("draw_copy_test.common")
        common.collection_media_dir = lambda: Path(".")
        common.user_files_dir = lambda: Path(".")
        settings = ModuleType("draw_copy_test.settings")
        settings.load_settings = lambda: {}
        settings.save_settings = lambda value: None
        cls.modules = patch.dict(sys.modules, {
            "draw_copy_test": package, "aqt": aqt, "aqt.qt": qt,
            "aqt.editor": editor, "aqt.utils": utils,
            common.__name__: common, settings.__name__: settings,
        })
        cls.modules.start()
        spec = importlib.util.spec_from_file_location(
            "draw_copy_test.draw_on_image", ROOT / "apps/anki-pocket-knife/draw_on_image.py"
        )
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)

    @classmethod
    def tearDownClass(cls):
        cls.modules.stop()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.image = QtGui.QImage(80, 60, QtGui.QImage.Format.Format_ARGB32)
        self.image.fill(QtGui.QColor(20, 40, 60, 120))
        self.source = self.root / "original.png"
        self.assertTrue(self.image.save(str(self.source)))
        self.original_bytes = self.source.read_bytes()
        self.clipboard = Clipboard()
        for target, name, value in (
            (self.module, "user_files_dir", lambda: self.root / "user_files"),
            (self.module, "QGuiApplication", SimpleNamespace(
                clipboard=lambda: self.clipboard, primaryScreen=lambda: None)),
        ):
            p = patch.object(target, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.warning = patch.object(self.module, "showWarning").start()
        self.notice = patch.object(self.module, "tooltip").start()
        self.addCleanup(patch.stopall)
        self.dialog = self.module.DrawOnImageDialog(self.source)
        self.dialog.canvas._strokes.append(self.module.Stroke(
            "arrow", "#FFAA00", 4,
            [QtCore.QPointF(10, 10), QtCore.QPointF(60, 40)],
        ))
        self.dialog.show()
        self.app.processEvents()
        self.addCleanup(self.dialog.deleteLater)

    def finish_copy(self):
        # Drive timer stages deterministically; every real write has a later read.
        for _ in range(30):
            if not self.dialog._copying:
                return
            self.dialog._copy_timer.stop()
            self.dialog._copy_step()
        self.fail("Copy retries never finished")

    def assert_saved_image(self):
        files = list((self.root / "user_files/annotated_images").glob("*.png"))
        self.assertEqual(len(files), 1)
        self.assertEqual(QtGui.QImage(str(files[0])), self.dialog.canvas.rendered_image())
        self.assertEqual(self.source.read_bytes(), self.original_bytes)
        return files[0]

    def test_success_saves_png_and_closes_only_after_verification(self):
        self.dialog.accept()
        self.assertTrue(self.dialog.isVisible())
        self.assert_saved_image()
        self.finish_copy()
        self.assertEqual(self.dialog.result(), QtWidgets.QDialog.DialogCode.Accepted)
        self.assertEqual(self.clipboard.writes, 1)
        self.assertEqual(self.clipboard.image(), self.dialog.canvas.rendered_image())
        png = QtGui.QImage.fromData(self.clipboard.mimeData().data("image/png"), "PNG")
        self.assertEqual(png, self.clipboard.image())
        self.warning.assert_not_called()

    def test_busy_clipboard_recovers_without_duplicate_success_write(self):
        self.clipboard.blocked = 2
        self.dialog.copy_to_clipboard_and_close()
        self.finish_copy()
        self.assertEqual(self.clipboard.writes, 3)
        self.assertFalse(self.dialog.isVisible())
        self.warning.assert_not_called()
        self.assert_saved_image()

    def test_real_qt_timer_finishes_the_copy(self):
        loop = QtCore.QEventLoop()
        self.dialog.finished.connect(loop.quit)
        timeout = QtCore.QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)
        timeout.start(3000)
        self.dialog.accept()
        loop.exec()
        timeout.stop()
        self.assertEqual(self.dialog.result(), QtWidgets.QDialog.DialogCode.Accepted)
        self.assertEqual(self.clipboard.writes, 1)

    def test_clipboard_write_exception_is_retried_and_keeps_drawing(self):
        with patch.object(self.clipboard, "setMimeData", side_effect=RuntimeError("clipboard locked")) as write:
            self.dialog.accept()
            self.finish_copy()
        self.assertEqual(write.call_count, self.module.COPY_ATTEMPTS)
        self.assertTrue(self.dialog.isVisible())
        self.assert_saved_image()
        self.assertIn("clipboard locked", self.warning.call_args.args[0])

    def test_persistent_failure_preserves_drawing_and_allows_manual_retry(self):
        self.clipboard.blocked = 100
        self.dialog.copy_to_clipboard_and_close()
        self.finish_copy()
        self.assertEqual(self.clipboard.writes, self.module.COPY_ATTEMPTS)
        self.assertTrue(self.dialog.isVisible())
        self.assertTrue(self.dialog.canvas.isEnabled())
        self.assertIn(str(self.assert_saved_image()), self.warning.call_args.args[0])
        self.clipboard.blocked = 0
        self.dialog.accept()
        self.finish_copy()
        self.assertEqual(self.dialog.result(), QtWidgets.QDialog.DialogCode.Accepted)

    def test_unavailable_clipboard_has_bounded_retries(self):
        self.clipboard = None
        self.dialog.accept()
        self.finish_copy()
        self.assertEqual(self.dialog._copy_attempts, self.module.COPY_ATTEMPTS)
        self.assertTrue(self.dialog.isVisible())
        self.assert_saved_image()
        self.warning.assert_called_once()

    def test_save_failure_leaves_editor_open_and_does_not_touch_clipboard(self):
        with patch.object(self.module, "user_files_dir", side_effect=OSError("disk full")):
            self.dialog.accept()
        self.assertEqual(self.clipboard.writes, 0)
        self.assertTrue(self.dialog.isVisible())
        self.assertFalse(self.dialog._copying)
        self.assertIn("disk full", self.warning.call_args.args[0])

    def test_clipboard_overwritten_before_verify_is_detected(self):
        self.dialog.accept()
        self.dialog._copy_timer.stop()
        self.dialog._copy_step()
        self.clipboard.mime = QtCore.QMimeData()
        self.clipboard.mime.setText("another application changed the clipboard")
        self.finish_copy()
        self.assertEqual(self.clipboard.writes, 2)
        self.assertEqual(self.clipboard.image(), self.dialog.canvas.rendered_image())

    def test_partial_formats_never_report_success(self):
        self.clipboard.missing_png = True
        self.dialog.accept()
        self.finish_copy()
        self.assertTrue(self.dialog.isVisible())
        self.assertEqual(self.clipboard.writes, self.module.COPY_ATTEMPTS)
        self.notice.assert_not_called()

    @unittest.skipUnless(sys.platform == "win32", "Windows clipboard ownership check")
    def test_cached_image_without_windows_ownership_is_not_success(self):
        self.clipboard.ownsClipboard = lambda: False
        self.dialog.accept()
        self.finish_copy()
        self.assertTrue(self.dialog.isVisible())
        self.assertEqual(self.clipboard.writes, self.module.COPY_ATTEMPTS)
        self.assert_saved_image()
        self.notice.assert_not_called()

    def test_wrong_pixels_at_same_dimensions_never_report_success(self):
        self.clipboard.image = lambda: self.image
        self.dialog.accept()
        self.finish_copy()
        self.assertTrue(self.dialog.isVisible())
        self.assert_saved_image()
        self.notice.assert_not_called()

    def test_repeated_copy_and_close_during_copy_cannot_discard_image(self):
        self.dialog.accept()
        self.dialog.accept()
        self.dialog.reject()
        self.dialog.close()
        self.assertTrue(self.dialog.isVisible())
        self.finish_copy()
        self.assertEqual(self.clipboard.writes, 1)
        self.assert_saved_image()

    def test_copy_includes_in_progress_stroke(self):
        self.dialog.canvas._strokes.clear()
        self.dialog.canvas._active = self.module.Stroke(
            "pen", "#FFAA00", 4,
            [QtCore.QPointF(10, 10), QtCore.QPointF(60, 40)],
        )
        self.dialog.accept()
        self.finish_copy()
        self.assertNotEqual(self.clipboard.image(), self.image)
        self.assert_saved_image()

    def test_ctrl_c_works_with_toolbar_child_focused(self):
        self.dialog.draw_button.setFocus()
        QtTest.QTest.keyClick(self.dialog.draw_button, QtCore.Qt.Key.Key_C,
                              QtCore.Qt.KeyboardModifier.ControlModifier)
        self.assertTrue(self.dialog._copying)
        self.finish_copy()
        self.assertEqual(self.clipboard.writes, 1)

    def test_bridge_does_not_copy_again_after_dialog_closes(self):
        fake = SimpleNamespace(exec=lambda: 1)
        with patch.object(self.module, "_source_image_path", return_value=self.source), \
             patch.object(self.module, "DrawOnImageDialog", return_value=fake):
            self.assertTrue(self.module._handle_draw_command(
                SimpleNamespace(parentWindow=None), self.module.COMMAND_PREFIX + "{}"))
        self.warning.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
