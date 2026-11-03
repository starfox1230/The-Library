"""Real Anki backend regressions; uses disposable collections, never a profile.

Run with Anki's Python, passing --track to select another reviewer source tree.
The small Basic notes are scheduling fixtures, not exported study cards.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock

from anki.collection import Collection
from anki.cards import Card

from time_drain_undo import automatic_queue_change, queue_changes_allowed, is_review_undo

ROOT = Path(__file__).resolve().parents[1]
TRACK = ROOT / "speed-streak-addon-v2.05"


def controller_class(col):
    """Execute the actual queue methods without importing any Qt UI."""
    tree = ast.parse((TRACK / "reviewer_overlay.py").read_text(encoding="utf-8"))
    names = {"_get_next_v3_card_with_time_drain_reordering", "_time_drain_review_last_enabled",
             "_time_drain_timer_override_enabled", "_defer_top_time_drain_card_if_needed",
             "_queued_card_id", "_bury_queued_time_drain_card", "_remember_deferred_time_drain_card",
             "_restore_deferred_time_drain_cards", "_flag_for_queued_card", "_flag_for_card", "on_state_did_undo"}
    nodes = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(nodes) == len(names)
    cls = ast.ClassDef(name="QueueController", bases=[], keywords=[], body=nodes, decorator_list=[])
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), cls], type_ignores=[])
    namespace = dict(Card=Card, mw=SimpleNamespace(col=col), TIME_DRAIN_FETCH_BATCH_SIZES=(32, 128, 512, 2048, 8192, 32768),
                     automatic_queue_change=automatic_queue_change, queue_changes_allowed=queue_changes_allowed,
                     is_review_undo=is_review_undo)
    exec(compile(ast.fix_missing_locations(module), str(TRACK / "reviewer_overlay.py"), "exec"), namespace)
    return namespace["QueueController"]


class QueueUndoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="speed-streak-undo-")
        path = str(Path(self.temp.name) / "collection.anki2")
        self.col = Collection(path)
        model = self.col.models.by_name("Basic")
        self.ids = []
        for i, flag in enumerate((0, 2, 2, 0, 2, 0)):
            note = self.col.new_note(model)
            note["Front"], note["Back"] = f"Undo fixture {i}", "Scheduling test"
            self.col.add_note(note, 1)
            card = note.cards()[0]
            card.due = i + 1
            self.col.update_card(card)
            self.col.set_user_flag_for_cards(flag, [card.id])
            self.ids.append(card.id)
        # Reopen to begin with an empty undo stack, like a fresh Anki session.
        self.col.close()
        self.col = Collection(path)
        self.controller = controller_class(self.col)()
        self.controller.engine = SimpleNamespace(state=SimpleNamespace(time_drain_review_last=True,
                                                time_drain_flag=2, no_undo_mode=False))
        self.controller.special_timer_rules = {}
        self.controller._deferred_time_drain_card_ids = []
        self.controller.sprint_enabled = False
        self.controller._sprint_time_drain_end_phase = False
        self.controller.sprint_tracker = SimpleNamespace(reset=Mock(), undo=Mock(), finish_for_time_drain_review=Mock())
        self.controller._apply_anki_undo_to_speed_streak = Mock()
        self.reviewer = SimpleNamespace(mw=SimpleNamespace(col=self.col), card=None)

    def tearDown(self):
        self.col.close()
        self.temp.cleanup()

    def fetch(self):
        def original(reviewer):
            queue = self.col.sched.get_queued_cards()
            reviewer.card = Card(self.col, backend_card=queue.cards[0].card) if queue.cards else None
            if reviewer.card:
                reviewer.card.start_timer()
        self.controller._get_next_v3_card_with_time_drain_reordering(self.reviewer, original)
        return self.reviewer.card.id if self.reviewer.card else None

    def answer(self):
        self.col.sched.answerCard(self.reviewer.card, 4)

    def test_consecutive_buries_are_one_review_undo(self):
        self.assertEqual(self.fetch(), self.ids[0])
        self.answer()
        step = self.col.undo_status().last_step
        self.assertEqual(self.fetch(), self.ids[3])
        self.assertEqual([self.col.get_card(i).queue for i in self.ids[1:3]], [-2, -2])
        self.assertEqual(self.col.undo_status().last_step, step)
        result = self.col.undo()
        self.assertTrue(is_review_undo(self.col, result))
        for _ in range(3):
            self.assertEqual(self.fetch(), self.ids[0])
            self.assertTrue(self.col.undo_status().redo)
            self.assertFalse(self.controller._restore_deferred_time_drain_cards())
        self.assertEqual([self.col.get_card(i).queue for i in self.ids[1:3]], [0, 0])
        self.assertEqual(self.col.get_card(self.ids[0]).reps, 0)

    def test_repeated_undo_and_new_answer_resume_sorting(self):
        self.fetch(); self.answer(); self.fetch(); self.answer()
        self.assertEqual(self.fetch(), self.ids[5])
        self.col.undo()
        self.assertEqual(self.fetch(), self.ids[3])
        self.col.undo()
        self.assertEqual(self.fetch(), self.ids[0])
        self.answer()
        self.assertFalse(self.col.undo_status().redo)
        self.assertEqual(self.fetch(), self.ids[3])

    def test_undo_does_not_immediately_repeat_automatic_bury(self):
        self.fetch(); self.answer(); self.fetch()
        self.col.undo()
        self.assertEqual(self.fetch(), self.ids[0])
        self.assertTrue(self.col.undo_status().redo)

    def test_redo_preserves_group_and_deferred_restoration(self):
        self.fetch(); self.answer(); self.fetch()
        self.col.undo(); self.fetch()
        self.col.redo()
        self.assertEqual(self.fetch(), self.ids[3])
        self.assertTrue(self.controller._restore_deferred_time_drain_cards())
        self.assertEqual([self.col.get_card(i).queue for i in self.ids[1:3]], [0, 0])
        # Returning to Decks/restoring cards did not add an extra Undo Unbury.
        self.assertEqual(self.col.undo_status().undo, self.col.tr.actions_answer_card())

    def test_undo_at_review_entry_does_not_rebury_or_consume_score(self):
        self.col.sched.bury_cards([self.ids[0]])
        self.col.close()
        # Keep the same controller but replace its collection namespace too.
        self.col = Collection(str(Path(self.temp.name) / "collection.anki2"))
        self.controller = self._rebind_controller()
        self.reviewer.mw.col = self.col
        self.assertEqual(self.fetch(), self.ids[3])
        result = self.col.undo()
        self.controller.on_state_did_undo(result)
        self.controller._apply_anki_undo_to_speed_streak.assert_not_called()
        self.assertEqual(self.fetch(), self.ids[1])
        self.assertTrue(self.col.undo_status().redo)

    def _rebind_controller(self):
        old = self.controller
        new = controller_class(self.col)()
        new.__dict__.update(old.__dict__)
        return new

    def test_restore_leaves_manually_buried_and_suspended_cards_alone(self):
        self.fetch(); self.answer(); self.fetch()
        self.col.sched.bury_cards([self.ids[1]], manual=True)
        self.col.sched.suspend_cards([self.ids[2]])
        self.assertFalse(self.controller._restore_deferred_time_drain_cards())
        self.assertEqual([self.col.get_card(i).queue for i in self.ids[1:3]], [-3, -1])

    def test_disabled_setting_and_all_time_drains_do_not_hide_cards(self):
        self.controller.engine.state.time_drain_review_last = False
        self.assertEqual(self.fetch(), self.ids[0])
        self.assertFalse(self.col.undo_status().undo)
        self.controller.engine.state.time_drain_review_last = True
        for i in self.ids:
            self.col.set_user_flag_for_cards(2, [i])
        before = self.col.undo_status().last_step
        self.assertEqual(self.fetch(), self.ids[0])
        self.assertEqual(self.col.undo_status().last_step, before)

    def test_non_answer_undo_keeps_review_and_sprint_snapshots(self):
        self.fetch(); self.answer(); self.fetch()
        self.controller.sprint_enabled = True
        self.col.set_user_flag_for_cards(1, [self.ids[3]])
        self.controller.on_state_did_undo(self.col.undo())
        self.controller._apply_anki_undo_to_speed_streak.assert_not_called()
        self.controller.sprint_tracker.undo.assert_not_called()
        self.controller.on_state_did_undo(self.col.undo())
        self.controller._apply_anki_undo_to_speed_streak.assert_called_once()
        if "sprint_enabled" in (TRACK / "reviewer_overlay.py").read_text():
            self.controller.sprint_tracker.undo.assert_called_once()

    def test_failed_bury_leaves_undo_and_deferred_list_unchanged(self):
        self.fetch(); self.answer()
        queue = self.col.sched.get_queued_cards()
        before = self.col.undo_status()
        def fail(*args, **kwargs):
            raise RuntimeError("fixture failure")
        self.assertFalse(self.controller._bury_queued_time_drain_card(fail, queue.cards[0]))
        self.assertEqual(self.col.undo_status(), before)
        self.assertEqual(self.controller._deferred_time_drain_card_ids, [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--track", type=Path, default=TRACK)
    args, remaining = parser.parse_known_args()
    TRACK = args.track
    unittest.main(argv=[__file__] + remaining)
