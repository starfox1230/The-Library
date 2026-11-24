from unittest import TestCase
from unittest.mock import patch
import importlib
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import ModuleType

package = ModuleType("speed_lab_fixture")
package.__path__ = [str(Path(__file__).resolve().parents[1])]
sys.modules[package.__name__] = package
game = importlib.import_module(package.__name__ + ".game_state")
lab_module = importlib.import_module(package.__name__ + ".suggestion_lab")


class LabTests(TestCase):
    def setUp(self):
        self.clock = 1000000
        clock_patch = patch.object(game, "now_epoch_ms", lambda: self.clock)
        clock_patch.start()
        self.addCleanup(clock_patch.stop)
        self.engine = game.CompanionGameEngine()

    def question(self):
        self.engine.sync_on_question(card_id="1", deck_name="Practice", is_free=False)

    def test_shared_balance_on_real_reviewer_paths_and_undo(self):
        e = self.engine
        e.set_bank_trial(True)
        self.question()
        self.clock += 5000
        e.sync_visible_answer_surface(card_id="1", deck_name="Practice", timer_policy={})
        self.assertEqual(e.state.phase_limit_ms, 115000)
        self.clock += 5000
        snapshot = e.capture_review_undo_snapshot()
        e.on_rate(3)
        e.commit_review_undo_snapshot(snapshot)
        e.sync_visible_question_surface(card_id="2", deck_name="Practice", timer_policy={})
        self.assertEqual(e.state.phase_limit_ms, 122000)
        self.assertTrue(e.undo_last_review())
        self.assertEqual(e.state.phase_limit_ms, 115000)
        self.assertEqual(e._phase_elapsed_ms(), 5000)
        e.set_bank_trial(False)
        self.assertEqual(e.state.phase_limit_ms, e.state.review_limit_ms)

    def test_bank_pause_and_expiry_and_free_card(self):
        e = self.engine
        e.set_bank_trial(True)
        e.sync_on_question(card_id="1", deck_name="Practice")
        e.on_answer_shown()
        e.on_rate(3)
        self.assertEqual(e.state.lab_bank_ms, 120000)
        self.clock += 3000
        e.toggle_pause()
        self.clock += 7000
        e.toggle_pause()
        self.assertEqual(e._phase_elapsed_ms(), 3000)
        self.clock += 118000
        self.assertEqual(e.check_timeout(), "timeout")
        self.assertEqual(e.state.streak, 0)
        self.assertEqual(e.state.phase_limit_ms, 120000)

    def test_saved_metric_ignores_free_and_untimed_sides_and_is_undoable(self):
        e = self.engine
        e.trial_saved = True
        e.state.question_limit_ms = e.state.review_limit_ms = 10000
        self.question()
        self.clock += 2000
        e.sync_visible_answer_surface(card_id="1", deck_name="Practice", timer_policy={})
        self.clock += 2000
        snapshot = e.capture_review_undo_snapshot()
        e.on_rate(3)
        e.commit_review_undo_snapshot(snapshot)
        self.assertEqual(e.state.lab_saved_ms, 16000)
        e.undo_last_review()
        self.assertEqual(e.state.lab_saved_ms, 0)
        e.sync_on_question(card_id="3", deck_name="Practice", is_free=True)
        e.on_answer_shown()
        e.on_rate(4)
        self.assertEqual(e.state.lab_saved_ms, 0)

    def test_legacy_penalty_retains_streak_and_restarts_each_deadline(self):
        e = self.engine
        e.trial_penalty = True
        e.state.gameplay_mode = game.GAMEPLAY_MODE_LEGACY
        self.question()
        e.state.score, e.state.streak = 3, 5
        for score in [2, 1, 0, 0]:
            self.clock += e.state.phase_limit_ms + 1
            self.assertEqual(e.check_timeout(), "point-penalty")
            self.assertEqual((e.state.score, e.state.streak), (score, 5))
            self.assertIsNone(e.check_timeout())

    def test_picks_persist_without_public_activation(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            lab = lab_module.SuggestionLab(root, True)
            lab.data.update(trying=["touch"], decisions={"touch": "Skip", "race": "Keep"})
            lab.save()
            lab = lab_module.SuggestionLab(root, True)
            self.assertTrue(lab.active("touch"))
            self.assertFalse(lab.active("race"))
            self.assertEqual(lab.verdict("touch"), "Skip")
            self.assertIn("Keep\n• Race", lab.summary())
            self.assertFalse(lab_module.SuggestionLab(root, False).active("touch"))

