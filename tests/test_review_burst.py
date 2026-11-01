"""Native Qt lifecycle and Anki hook integration; no live profile is opened."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    import aqt
    from aqt import gui_hooks
    from aqt.qt import QApplication, QFont, QFontDatabase, QLabel, QMenu, QVBoxLayout, QWidget
except ImportError:
    raise unittest.SkipTest("Run with Anki's Python for native Qt integration")

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "_pocketknife_burst_tests"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT / "apps/anki-pocket-knife")]
sys.modules[PACKAGE] = package
settings = types.ModuleType(f"{PACKAGE}.settings")
settings.values = {"review_burst_goal": 10}
settings.get_setting = lambda key: settings.values[key]
settings.set_setting = lambda key, value: settings.values.update({key: value})
sys.modules[settings.__name__] = settings
spec = importlib.util.spec_from_file_location(f"{PACKAGE}.review_burst", Path(package.__path__[0]) / "review_burst.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ReviewBurstTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/segoeui.ttf"
        if font.exists():
            QFontDatabase.addApplicationFont(str(font))
        cls.app.setFont(QFont("Segoe UI", 10))

    def setUp(self):
        self.mw = QWidget()
        self.mw.setStyleSheet("background: #0e1726; color: #eaf3ff;")
        self.mw.resize(940, 680)
        self.mw.state = "review"
        self.mw.col = object()  # No DB/query API: any collection work would fail.
        self.mw.reviewer = object()
        layout = QVBoxLayout(self.mw)
        card = QLabel("What is the next small step?")
        layout.addWidget(card, 1)
        self.mw.bottomWeb = QLabel("Again          Hard          Good          Easy")
        self.mw.bottomWeb.setFixedHeight(48)
        layout.addWidget(self.mw.bottomWeb)
        self.mw.show()
        self.app.processEvents()
        self.aqt_patch = patch.object(aqt, "mw", self.mw)
        self.aqt_patch.start()
        self.clock = patch.object(module, "monotonic", return_value=100.0)
        self.now = self.clock.start()
        self.hooks = (gui_hooks.reviewer_did_answer_card, gui_hooks.state_did_change, gui_hooks.profile_will_close)
        self.before = [hook.count() for hook in self.hooks]
        settings.values["review_burst_goal"] = 10

    def tearDown(self):
        module.stop_burst()
        module._actions.clear()
        self.app.processEvents()
        self.assertEqual([hook.count() for hook in self.hooks], self.before)
        self.clock.stop()
        self.aqt_patch.stop()
        self.mw.close()
        self.mw.deleteLater()
        self.app.processEvents()

    def answer(self, ease=3):
        gui_hooks.reviewer_did_answer_card(self.mw.reviewer, object(), ease)

    def settle(self):
        self.now.return_value += 0.4
        module._controller.tick()
        self.app.processEvents()

    def screenshot(self, name):
        if os.environ.get("BURST_QA_DIR"):
            out = Path(os.environ["BURST_QA_DIR"])
            out.mkdir(parents=True, exist_ok=True)
            self.mw.grab().save(str(out / f"{name}.png"))

    def test_counts_crossing_goal_once_and_overrun_stays_static(self):
        module.start_burst(10)
        controller = module._controller
        self.screenshot("start")
        for i in range(5):
            self.answer(1 if i == 0 else 3)
            self.settle()
        self.assertEqual(controller.overlay.count, 5)
        self.assertAlmostEqual(controller.overlay.progress, 0.5)
        self.assertFalse(controller.timer.isActive())
        self.screenshot("half")
        for _ in range(5):
            self.answer()
            self.settle()
        self.assertTrue(controller.overlay.complete)
        self.assertTrue(controller.confetti.isVisible())
        self.now.return_value += 0.35
        controller.tick()
        self.app.processEvents()
        self.screenshot("confetti")
        self.now.return_value += 2
        controller.tick()
        self.answer()
        self.app.processEvents()
        self.assertEqual(controller.overlay.count, 11)
        self.assertFalse(controller.timer.isActive())
        self.assertFalse(controller.confetti.isVisible())
        self.assertEqual(controller.overlay.height(), 38)
        self.screenshot("overrun")

    def test_off_removes_callbacks_and_cancels_mid_animation(self):
        module.start_burst(1)
        controller = module._controller
        self.answer()
        self.settle()
        module.stop_burst()
        self.assertFalse(module.is_burst_active())
        self.assertFalse(controller.timer.isActive())
        self.assertFalse(controller.overlay.isVisible())
        self.assertFalse(controller.confetti.isVisible())
        self.assertEqual([hook.count() for hook in self.hooks], self.before)
        self.answer()
        self.assertEqual(controller.overlay.count, 1)

    def test_leave_review_return_restart_and_resize(self):
        module.start_burst(2)
        controller = module._controller
        self.answer()
        self.mw.state = "deckBrowser"
        gui_hooks.state_did_change("deckBrowser", "review")
        self.assertFalse(controller.overlay.isVisible())
        self.assertFalse(controller.timer.isActive())
        self.mw.state = "review"
        gui_hooks.state_did_change("review", "deckBrowser")
        self.assertTrue(controller.overlay.isVisible())
        self.assertEqual(controller.overlay.count, 1)
        self.mw.resize(500, 420)
        self.app.processEvents()
        self.assertLessEqual(controller.overlay.geometry().right(), self.mw.width())
        bottom = self.mw.bottomWeb.mapTo(self.mw, self.mw.bottomWeb.rect().topLeft()).y()
        self.assertLess(controller.overlay.geometry().bottom(), bottom)
        module.start_burst(3)
        self.assertEqual(module._controller.overlay.count, 0)
        self.assertEqual(settings.values["review_burst_goal"], 3)
        self.assertEqual([hook.count() for hook in self.hooks], [x + 1 for x in self.before])

    def test_profile_close_does_not_skip_other_addons(self):
        module.start_burst()
        called = []
        callback = lambda: called.append(True)
        gui_hooks.profile_will_close.append(callback)
        try:
            gui_hooks.profile_will_close()
            self.assertEqual(called, [True])
            self.assertFalse(module.is_burst_active())
            self.app.processEvents()
        finally:
            gui_hooks.profile_will_close.remove(callback)

    def test_menu_toggle_and_goal_bounds(self):
        menu = QMenu(self.mw)
        module.add_burst_menu(menu, self.mw)
        action = menu.actions()[0]
        action.trigger()
        self.assertTrue(module.is_burst_active())
        self.assertEqual(module._controller.overlay.goal, 10)
        action.trigger()
        self.assertFalse(module.is_burst_active())
        module.start_burst(-3)
        self.assertEqual(module._controller.overlay.goal, 1)
        module.start_burst(50000)
        self.assertEqual(module._controller.overlay.goal, 1000)


if __name__ == "__main__":
    unittest.main()
