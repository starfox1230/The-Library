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
    from aqt.qt import QApplication, QCheckBox, QFont, QFontDatabase, QLabel, QMenu, QSpinBox, QTimer, QVBoxLayout, QWidget
except ImportError:
    raise unittest.SkipTest("Run with Anki's Python for native Qt integration")

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "_pocketknife_burst_tests"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT / "apps/anki-pocket-knife")]
sys.modules[PACKAGE] = package
settings = types.ModuleType(f"{PACKAGE}.settings")
settings.values = {"review_burst_goal": 10, "review_burst_present": True, "review_burst_mode": "cards", "review_burst_minutes": 10}
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
        self.hooks = (gui_hooks.reviewer_did_answer_card, gui_hooks.state_did_change, gui_hooks.profile_will_close, gui_hooks.profile_did_open)
        self.before = [hook.count() for hook in self.hooks]
        settings.values["review_burst_goal"] = 10
        settings.values["review_burst_present"] = True
        settings.values["review_burst_mode"] = "cards"
        settings.values["review_burst_minutes"] = 10
        module.ensure_burst_button()

    def tearDown(self):
        module.set_burst_present(False)
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

    def test_hiding_feature_removes_callbacks_and_cancels_mid_animation(self):
        module.start_burst(1)
        controller = module._controller
        self.answer()
        self.settle()
        module.set_burst_present(False)
        self.assertFalse(module.is_burst_active())
        self.assertFalse(controller.timer.isActive())
        self.assertFalse(controller.overlay.isVisible())
        self.assertFalse(controller.confetti.isVisible())
        self.assertEqual([hook.count() for hook in self.hooks], self.before)
        self.answer()
        self.assertEqual(controller.overlay.count, 1)

    def leave_and_return(self):
        self.mw.state = "overview"
        gui_hooks.state_did_change("overview", "review")
        self.mw.state = "deckBrowser"
        gui_hooks.state_did_change("deckBrowser", "overview")
        self.mw.state = "review"
        gui_hooks.state_did_change("review", "deckBrowser")

    def test_default_button_waits_without_counting_or_timers(self):
        self.assertTrue(module._presence.button.isVisible())
        self.assertFalse(module.is_burst_active())
        self.assertEqual(gui_hooks.reviewer_did_answer_card.count(), self.before[0])
        self.assertEqual(self.mw.findChildren(QTimer), [])
        self.answer()
        self.assertFalse(module.is_burst_active())
        self.screenshot("idle-button")
        module._presence.button.click()
        self.assertTrue(module.is_burst_active())
        self.assertEqual(module._controller.overlay.count, 0)
        self.assertFalse(module._presence.button.isVisible())

    def test_leaving_review_ends_burst_and_return_waits_for_click(self):
        for _ in range(2):
            module._presence.button.click()
            controller = module._controller
            self.answer()
            gui_hooks.state_did_change("review", "review")
            self.assertEqual(controller.overlay.count, 1)
            self.leave_and_return()
            self.assertFalse(module.is_burst_active())
            self.assertFalse(controller.overlay.isVisible())
            self.assertFalse(controller.timer.isActive())
            self.assertTrue(module._presence.button.isVisible())
            self.answer()
            self.assertFalse(module.is_burst_active())
        module._presence.button.click()
        self.assertEqual(module._controller.overlay.count, 0)

    def test_leaving_completed_burst_cancels_confetti_and_discards_overrun(self):
        module.start_burst(1)
        controller = module._controller
        self.answer()
        self.settle()
        self.answer()
        self.assertEqual(controller.overlay.count, 2)
        self.assertTrue(controller.confetti.isVisible())
        self.leave_and_return()
        self.assertFalse(module.is_burst_active())
        self.assertFalse(controller.confetti.isVisible())
        self.assertFalse(controller.timer.isActive())
        module._presence.button.click()
        self.assertEqual(module._controller.overlay.count, 0)
        self.assertEqual(module._controller.overlay.height(), 178)
        self.answer()
        self.settle()
        self.assertTrue(module._controller.confetti.isVisible())

    def test_end_burst_restores_button_and_resize_keeps_it_above_controls(self):
        module.start_burst(2)
        self.answer()
        module.stop_burst()
        self.assertTrue(module._presence.button.isVisible())
        self.mw.resize(500, 420)
        self.app.processEvents()
        button = module._presence.button
        self.assertLessEqual(button.geometry().right(), self.mw.width())
        bottom = self.mw.bottomWeb.mapTo(self.mw, self.mw.bottomWeb.rect().topLeft()).y()
        self.assertLess(button.geometry().bottom(), bottom)
        self.mw.state = "deckBrowser"
        gui_hooks.state_did_change("deckBrowser", "review")
        self.assertFalse(button.isVisible())

    def test_settings_save_presence_and_goal_without_starting_burst(self):
        def configure(dialog):
            checkbox = dialog.findChild(QCheckBox)
            self.assertTrue(checkbox.isChecked())
            checkbox.setChecked(False)
            self.assertFalse(settings.values["review_burst_present"])
            self.assertIsNone(module._presence)
            dialog.findChild(QSpinBox).setValue(15)
            self.assertEqual(settings.values["review_burst_goal"], 15)
            checkbox.setChecked(True)
            self.assertTrue(module._presence.button.isVisible())
            self.assertFalse(module.is_burst_active())
        with patch.object(module.QDialog, "exec", configure):
            module.open_burst_dialog()
        module._presence.button.click()
        self.assertEqual(module._controller.overlay.goal, 15)

    def test_profile_close_does_not_skip_other_addons_and_reopen_waits(self):
        module.start_burst()
        called = []
        callback = lambda: called.append(True)
        gui_hooks.profile_will_close.append(callback)
        try:
            gui_hooks.profile_will_close()
            self.assertEqual(called, [True])
            self.assertFalse(module.is_burst_active())
            self.assertFalse(module._presence.button.isVisible())
            gui_hooks.profile_did_open()
            self.assertTrue(module._presence.button.isVisible())
            self.assertFalse(module.is_burst_active())
        finally:
            gui_hooks.profile_will_close.remove(callback)

    def test_menu_toggles_presence_without_starting_and_disabled_stays_hidden(self):
        menu = QMenu(self.mw)
        module.add_burst_menu(menu, self.mw)
        action = menu.actions()[0]
        self.assertTrue(action.isChecked())
        action.trigger()
        self.assertIsNone(module._presence)
        self.leave_and_return()
        self.assertIsNone(module._presence)
        module.start_burst()
        self.assertFalse(module.is_burst_active())
        self.assertEqual([hook.count() for hook in self.hooks], self.before)
        action.trigger()
        self.assertTrue(module._presence.button.isVisible())
        self.assertFalse(module.is_burst_active())
        module.start_burst(-3)
        self.assertEqual(module._controller.overlay.goal, 1)
        module.start_burst(50000)
        self.assertEqual(module._controller.overlay.goal, 1000)

    def test_start_outside_review_does_not_queue_an_automatic_burst(self):
        self.mw.state = "deckBrowser"
        gui_hooks.state_did_change("deckBrowser", "review")
        with patch.object(module, "showInfo") as info:
            module.start_burst()
            info.assert_called_once()
        self.mw.state = "review"
        gui_hooks.state_did_change("review", "deckBrowser")
        self.assertFalse(module.is_burst_active())
        self.assertTrue(module._presence.button.isVisible())

    def test_click_remaining_edits_target_and_preserves_answer_count(self):
        module.start_burst(10)
        for _ in range(4):
            self.answer()
        def edit(dialog):
            self.assertEqual(dialog.choice.selection(), ("cards", 6))
            dialog.choice.amount.setValue(3)
            return module.QDialog.DialogCode.Accepted
        with patch.object(module.BurstEditDialog, "exec", edit):
            module._controller.edit_button.click()
        controller = module._controller
        self.assertEqual(controller.overlay.count, 4)
        self.assertEqual(controller.overlay.goal, 7)
        self.assertAlmostEqual(controller.overlay.progress, 4 / 7)
        self.assertFalse(controller.timer.isActive())
        for _ in range(3):
            self.answer()
            self.settle()
        self.assertTrue(controller.overlay.complete)

    def test_editor_default_timer_and_cancel_leave_current_burst_unchanged(self):
        module.start_burst(10)
        self.answer()
        def cancel(dialog):
            dialog.choice.mode.setCurrentIndex(1)
            self.assertEqual(dialog.choice.selection(), ("timer", 10))
            dialog.choice.amount.setValue(2)
            return module.QDialog.DialogCode.Rejected
        with patch.object(module.BurstEditDialog, "exec", cancel):
            module._controller.edit_button.click()
        self.assertEqual(module._controller.overlay.mode, "cards")
        self.assertEqual(module._controller.overlay.count, 1)
        self.assertEqual(module._controller.overlay.goal, 10)
        self.assertEqual(settings.values["review_burst_mode"], "cards")
        self.assertEqual(settings.values["review_burst_minutes"], 10)

    def test_timer_uses_elapsed_time_finishes_once_and_ignores_answers(self):
        module.start_burst()
        controller = module._controller
        controller.configure("timer", 10)
        self.assertEqual(controller.overlay.seconds_remaining, 600)
        self.assertEqual(controller.timer.interval(), 250)
        self.answer()
        self.assertEqual(controller.overlay.count, 0)
        self.now.return_value += 120.3
        controller.tick()
        self.assertEqual(controller.overlay.seconds_remaining, 480)
        self.assertAlmostEqual(controller.overlay.progress, 120.3 / 600)
        self.screenshot("timer-running")
        self.now.return_value += 479.6
        controller.tick()
        self.assertEqual(controller.overlay.seconds_remaining, 1)
        self.assertFalse(controller.overlay.complete)
        self.now.return_value += 0.1
        controller.tick()
        self.assertEqual(controller.overlay.seconds_remaining, 0)
        self.assertTrue(controller.overlay.complete)
        self.assertTrue(controller.confetti.isVisible())
        self.now.return_value += 2
        controller.tick()
        self.assertFalse(controller.timer.isActive())
        self.assertFalse(controller.confetti.isVisible())
        self.answer()
        controller.tick()
        self.assertFalse(controller.confetti.isVisible())
        self.assertEqual(controller.overlay.seconds_remaining, 0)
        self.screenshot("timer-complete")

    def test_timer_editor_ok_switches_mode_and_start_reuses_saved_choice(self):
        module.start_burst()
        def edit(dialog):
            dialog.choice.mode.setCurrentIndex(1)
            dialog.choice.amount.setValue(7)
            if os.environ.get("BURST_QA_DIR"):
                dialog.show()
                self.app.processEvents()
                out = Path(os.environ["BURST_QA_DIR"])
                out.mkdir(parents=True, exist_ok=True)
                dialog.grab().save(str(out / "compact-menu.png"))
                dialog.hide()
            return module.QDialog.DialogCode.Accepted
        with patch.object(module.BurstEditDialog, "exec", edit):
            module._controller.edit_button.click()
        self.assertEqual(module._controller.overlay.mode, "timer")
        self.assertEqual(module._controller.overlay.seconds_remaining, 420)
        self.assertEqual(settings.values["review_burst_minutes"], 7)
        self.leave_and_return()
        self.assertFalse(module.is_burst_active())
        module._presence.button.click()
        self.assertEqual(module._controller.overlay.mode, "timer")
        self.assertEqual(module._controller.overlay.seconds_remaining, 420)

    def test_editing_timer_no_change_preserves_deadline_and_switch_to_cards_stops_clock(self):
        module.start_burst()
        controller = module._controller
        controller.configure("timer", 10)
        deadline = controller.deadline
        def keep(dialog):
            self.now.return_value += 13
            return module.QDialog.DialogCode.Accepted
        with patch.object(module.BurstEditDialog, "exec", keep):
            controller.edit_button.click()
        self.assertEqual(controller.deadline, deadline)
        controller.configure("cards", 4)
        self.assertFalse(controller.timer.isActive())
        self.assertEqual(controller.overlay.goal, 4)
        self.assertEqual(controller.overlay.count, 0)
        self.answer()
        self.assertEqual(controller.overlay.count, 1)

    def test_leave_or_hide_cancels_running_countdown(self):
        module.start_burst()
        controller = module._controller
        controller.configure("timer", 1)
        self.leave_and_return()
        self.assertFalse(controller.timer.isActive())
        self.assertFalse(controller.edit_button.isVisible())
        self.assertFalse(module.is_burst_active())
        module._presence.button.click()
        controller = module._controller
        self.assertTrue(controller.timer.isActive())
        module.set_burst_present(False)
        self.assertFalse(controller.timer.isActive())
        self.assertIsNone(module._presence)

    def test_zero_answers_remaining_completes_and_short_clock_formats(self):
        module.start_burst()
        self.answer()
        controller = module._controller
        controller.configure("cards", 0)
        self.settle()
        self.assertTrue(controller.overlay.complete)
        self.assertTrue(controller.confetti.isVisible())
        self.assertEqual(module.clock_text(600), "10:00")
        self.assertEqual(module.clock_text(61), "1:01")
        self.assertEqual(module.clock_text(-1), "0:00")

    def test_timer_expiring_in_unchanged_editor_does_not_restart(self):
        module.start_burst()
        controller = module._controller
        controller.configure("timer", 1)
        def keep(dialog):
            self.now.return_value += 60
            controller.tick()
            return module.QDialog.DialogCode.Accepted
        with patch.object(module.BurstEditDialog, "exec", keep):
            controller.edit_button.click()
        self.assertTrue(controller.overlay.complete)
        self.assertEqual(controller.overlay.seconds_remaining, 0)

    def test_settings_switch_to_timer_sets_default_without_starting(self):
        def configure(dialog):
            choice = dialog.findChild(module.BurstChoice)
            choice.mode.setCurrentIndex(1)
            self.assertEqual(choice.selection(), ("timer", 10))
            choice.amount.setValue(3)
        with patch.object(module.QDialog, "exec", configure):
            module.open_burst_dialog()
        self.assertFalse(module.is_burst_active())
        module._presence.button.click()
        self.assertEqual(module._controller.overlay.mode, "timer")
        self.assertEqual(module._controller.overlay.seconds_remaining, 180)


if __name__ == "__main__":
    unittest.main()
