"""Exercise the real Qt wiring against an isolated Anki host fixture."""
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
    from PySide6 import QtCore, QtGui, QtWidgets
except ImportError:
    QtWidgets = None

SOURCE = Path(__file__).resolve().parents[1] / "diagnostic_logging.py"


@unittest.skipIf(QtWidgets is None, "PySide6 is needed for the Qt integration fixture")
class QtIntegrationTests(unittest.TestCase):
    def test_hooks_clipboard_and_timer_preserve_original_operations(self):
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        main = QtWidgets.QWidget()
        with tempfile.TemporaryDirectory() as directory:
            spec = importlib.util.spec_from_file_location("isolated_diagnostics", SOURCE)
            logger = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(logger)
            logger._recorder = logger.SessionRecorder(directory, "qt-fixture")
            hooks = SimpleNamespace(**{name: [] for name in (
                "webview_will_set_content", "webview_did_receive_js_message", "state_did_change",
                "profile_did_open", "profile_will_close", "reviewer_did_show_question",
                "reviewer_did_show_answer", "reviewer_did_answer_card")})
            aqt = ModuleType("aqt")
            aqt.gui_hooks, aqt.mw = hooks, main
            qt = ModuleType("aqt.qt")
            for module in (QtCore, QtGui, QtWidgets):
                for name in dir(module):
                    if not name.startswith("_"):
                        setattr(qt, name, getattr(module, name))
            reviewer = ModuleType("aqt.reviewer")
            reviewer.Reviewer = type("Reviewer", (), {})
            anki = ModuleType("anki")
            anki.version = "26.08.1-fixture"
            utils = ModuleType("aqt.utils")
            tooltips = []
            utils.tooltip = tooltips.append
            sentinel = object()
            controller = SimpleNamespace(
                engine=SimpleNamespace(state=SimpleNamespace(
                    phase="idle", haptics_enabled=True, audio_enabled=True,
                    countdown_audio_enabled=False)),
                haptics=SimpleNamespace(), display_mode="sidebar", visual_mode="sphere",
                audio_feedback=SimpleNamespace(last_playback_backend="none"),
                _audio_feedback_bootstrap="const audio = new Audio();",
                _sidebar_html=lambda: "<html><head></head><body>original</body></html>",
                _play_haptic_feedback=lambda *_: sentinel,
                _menu=QtWidgets.QMenu(main))
            with patch.dict(sys.modules, {"aqt": aqt, "aqt.qt": qt, "aqt.reviewer": reviewer,
                                          "aqt.utils": utils, "anki": anki}):
                logger.attach(controller)
                self.assertIn('"event":"diagnostics_ready"', logger.support_report())
                self.assertNotIn("diagnostic_setup_failure", logger.support_report())
                self.assertIs(controller._play_haptic_feedback("boost"), sentinel)
                self.assertTrue(controller._diagnostic_timer.isActive())
                self.assertIn("original</body>", controller._sidebar_html())
                content = SimpleNamespace(head="")
                hooks.webview_will_set_content[0](content, reviewer.Reviewer())
                self.assertIn("SpeedStreakDiagnostic", content.head)
                bridge = hooks.webview_did_receive_js_message[0]
                self.assertEqual(bridge((False, "keep"), "unrelated-message", None), (False, "keep"))
                self.assertEqual(bridge((False, None), 'speed-streak:diagnostic:{"event":"pagehide"}', None), (True, None))
                for callback in hooks.reviewer_did_show_question:
                    callback(object())
                controller._menu.actions()[-1].trigger()
                self.assertIn("question_shown", app.clipboard().text())
                self.assertIn("browser:pagehide", app.clipboard().text())
                self.assertEqual(len(tooltips), 1)
                controller._diagnostic_timer.stop()
                app.aboutToQuit.emit()
                self.assertIn("qt_about_to_quit", logger.support_report())
                logger._recorder.mark("python_exit_observed")
            main.close()


if __name__ == "__main__":
    unittest.main()
