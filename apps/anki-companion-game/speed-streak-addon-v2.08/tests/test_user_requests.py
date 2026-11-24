import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
import ast
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'requests_' + ROOT.name.replace('-', '_').replace('.', '_')
package = ModuleType(PACKAGE); package.__path__ = [str(ROOT)]; sys.modules[PACKAGE] = package
game = importlib.import_module(PACKAGE + '.game_state')
prefs = importlib.import_module(PACKAGE + '.request_preferences')


class RequestBehaviorTests(unittest.TestCase):
    def test_real_policy_combines_decks_tags_and_untimed(self):
        tree = ast.parse((ROOT / 'reviewer_overlay.py').read_text(encoding='utf-8'))
        controller = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ReviewerOverlayController')
        wanted = {'_normalize_special_timer_rules', '_normalize_special_timer_rule', '_timer_policy_for_card', '_timer_policy_candidate'}
        namespace = {'Any': Any, 'deck_rules': prefs.deck_rules, 'matches_deck': prefs.matches_deck, 'TIMER_POLICY_NORMAL': 'normal'}
        methods = ast.Module(body=[node for node in controller.body if isinstance(node, ast.FunctionDef) and node.name in wanted], type_ignores=[])
        exec(compile(methods, str(ROOT/'reviewer_overlay.py'), 'exec'), namespace)
        cls = type('Policy', (), {key: namespace[key] for key in wanted})
        instance = cls()
        instance.engine = self.engine()
        decks = SimpleNamespace(get=lambda deck_id, default=False: {1: {'name':'Law'}, 2: {'name':'Law::Cases'}}.get(deck_id))
        namespace['mw'] = SimpleNamespace(col=SimpleNamespace(decks=decks))
        instance._note_for_card = lambda card: None
        instance._note_tags = lambda note: ['slow']
        instance._flag_for_card = lambda card: 0
        instance._is_anking_one_by_one_card = lambda card, note: False
        instance._is_typed_answer_card = lambda card: False
        instance.special_timer_rules = instance._normalize_special_timer_rules({
            'decks_enabled': True, 'decks': [{'deck_ids': [1, '1', None], 'enabled': True, 'question_seconds': 20, 'answer_seconds': 25}],
            'tags_enabled': True, 'tags': [{'tag':'slow', 'enabled':True, 'question_seconds':30, 'answer_untimed':True}],
        }, general_question_seconds=12, general_answer_seconds=8)
        self.assertEqual(instance.special_timer_rules['decks'][0]['deck_ids'], [1])
        result = instance._timer_policy_for_card(SimpleNamespace(did=2, odid=0))
        self.assertEqual(result['question_limit_ms'], 30000)
        self.assertEqual(result['answer_limit_ms'], 0)
        instance.special_timer_rules['tags_enabled'] = False
        result = instance._timer_policy_for_card(SimpleNamespace(did=9, odid=2))
        self.assertEqual(result['question_limit_ms'], 20000)
        instance.special_timer_rules['decks_enabled'] = False
        self.assertEqual(instance._timer_policy_for_card(SimpleNamespace(did=2, odid=0)), {})

    def engine(self):
        engine = game.CompanionGameEngine()
        engine.state.enabled = True
        engine.state.synced = True
        engine.state.boost_charges = 0
        return engine

    def test_default_and_selected_boost_ratings(self):
        for enabled in ([1, 2, 3, 4], [2, 3, 4], [3], []):
            for rating in (1, 2, 3, 4):
                engine = self.engine()
                engine.update_time_limits(question_seconds=12, answer_seconds=8, boost_earning_ratings=enabled)
                engine.begin_question_phase(is_free=False)
                engine.on_answer_shown()
                engine.on_rate(rating)
                self.assertEqual(engine.state.boost_charge_progress, int(rating in enabled))

    def test_boost_full_bank_and_threshold(self):
        engine = self.engine(); engine.state.cards_per_boost_charge = 1
        engine.state.boost_earning_ratings = [3]
        for rating, expected in [(1, 0), (3, 1)]:
            engine.begin_question_phase(is_free=False); engine.on_answer_shown(); engine.on_rate(rating)
            self.assertEqual(engine.state.boost_charges, expected)
        engine.state.boost_charges = engine.state.max_boost_charges
        engine.begin_question_phase(is_free=False); engine.on_answer_shown(); engine.on_rate(3)
        self.assertEqual(engine.state.boost_charge_progress, 0)

    def test_undo_restores_boost_progress_and_keeps_preferences(self):
        engine = self.engine(); engine.state.cards_per_boost_charge = 1
        engine.begin_question_phase(is_free=False); engine.on_answer_shown()
        snapshot = engine.capture_review_undo_snapshot()
        engine.on_rate(3); engine.commit_review_undo_snapshot(snapshot)
        self.assertEqual(engine.state.boost_charges, 1)
        engine.state.boost_earning_ratings = [3]
        engine.state.timer_number_mode = 'seconds'
        self.assertTrue(engine.undo_last_review())
        self.assertEqual(engine.state.boost_charges, 0)
        self.assertEqual(engine.state.boost_charge_progress, 0)
        self.assertEqual(engine.state.boost_earning_ratings, [3])
        self.assertEqual(engine.state.timer_number_mode, 'seconds')

    def test_answer_pause_keeps_rating_available_and_next_question_timed(self):
        engine = self.engine(); engine.state.no_pause_mode = True
        engine.update_time_limits(question_seconds=12, answer_seconds=8, pause_answer_timer=True)
        engine.begin_question_phase(is_free=False)
        self.assertEqual(engine.state.phase_limit_ms, 12000)
        engine.on_answer_shown()
        engine.state.phase_start_epoch_ms -= 120000
        self.assertEqual(engine.state.phase_limit_ms, 0)
        self.assertIsNone(engine.check_timeout())
        self.assertFalse(engine.state.paused)
        self.assertTrue(engine.export()['answerTimerPaused'])
        self.assertEqual(engine.on_rate(3), 'good')
        engine.begin_question_phase(is_free=False)
        self.assertEqual(engine.state.phase_limit_ms, 12000)
        self.assertFalse(engine.export()['answerTimerPaused'])

    def test_enabling_answer_pause_during_settings_clears_blocking_pause(self):
        engine = self.engine()
        engine.begin_question_phase(is_free=False)
        engine.on_answer_shown()
        self.assertEqual(engine.toggle_pause(count_in_stats=False), 'pause')
        self.assertTrue(engine.state.paused)
        engine.update_time_limits(question_seconds=12, answer_seconds=8, pause_answer_timer=True)
        self.assertEqual(engine.state.phase_limit_ms, 0)
        self.assertFalse(engine.state.paused)
        self.assertEqual(engine.state.paused_remaining_ms, 0)
        self.assertEqual(engine.state.phase_base_limit_ms, 0)
        self.assertFalse(engine.export()['paused'])
        self.assertEqual(engine.on_rate(3), 'good')
        engine.begin_question_phase(is_free=False)
        self.assertEqual(engine.state.phase_limit_ms, 12000)

    def test_side_timer_visibility_is_presentation_only(self):
        engine = self.engine()
        self.assertTrue(engine.state.show_side_panel_timer)
        engine.update_time_limits(question_seconds=12, answer_seconds=8, show_side_panel_timer=False)
        engine.begin_question_phase(is_free=False)
        self.assertEqual(engine.state.phase_limit_ms, 12000)
        self.assertFalse(engine.export()['showSidePanelTimer'])
        self.assertTrue(engine.state.show_card_timer)
        preferences = engine._capture_user_preferences()
        engine.reset_settings_to_defaults()
        self.assertTrue(engine.state.show_side_panel_timer)
        engine._restore_user_preferences(preferences)
        self.assertFalse(engine.state.show_side_panel_timer)

    def test_request_preferences_round_trip_and_reset(self):
        engine = self.engine()
        engine.update_time_limits(question_seconds=12, answer_seconds=8, pause_answer_timer=True,
                                  timer_number_mode_value='hidden', card_timer_number_mode_value='seconds', boost_earning_ratings=[])
        snapshot = engine._capture_user_preferences()
        engine.reset_settings_to_defaults()
        self.assertEqual(engine.state.boost_earning_ratings, [1, 2, 3, 4])
        self.assertEqual(engine.state.timer_number_mode, 'decimal')
        self.assertEqual(engine.state.card_timer_number_mode, 'decimal')
        self.assertFalse(engine.state.pause_answer_timer)
        engine._restore_user_preferences(snapshot)
        self.assertEqual(engine.state.boost_earning_ratings, [])
        self.assertEqual(engine.export()['timerNumberMode'], 'hidden')
        self.assertEqual(engine.export()['cardTimerNumberMode'], 'seconds')
        self.assertTrue(engine.state.pause_answer_timer)

    def test_deck_ids_subdecks_renames_filtered_and_deleted(self):
        names = {1: {'name': 'Law'}, 2: {'name': 'Law::Cases'}, 3: {'name': 'Lawyer'}, 9: {'name': 'Filtered'}}
        decks = SimpleNamespace(get=lambda deck_id, default=False: names.get(deck_id))
        rule = {'deck_ids': [1], 'include_subdecks': True}
        self.assertTrue(prefs.matches_deck(rule, SimpleNamespace(did=2, odid=0), decks))
        self.assertTrue(prefs.matches_deck(rule, SimpleNamespace(did=9, odid=2), decks))
        self.assertFalse(prefs.matches_deck(rule, SimpleNamespace(did=3, odid=0), decks))
        rule['include_subdecks'] = False
        self.assertFalse(prefs.matches_deck(rule, SimpleNamespace(did=2, odid=0), decks))
        names[1]['name'] = 'Renamed'
        self.assertTrue(prefs.matches_deck(rule, SimpleNamespace(did=1, odid=0), decks))
        rule.update(deck_ids=[999], include_subdecks=True)
        self.assertFalse(prefs.matches_deck(rule, SimpleNamespace(did=2, odid=0), decks))


if __name__ == '__main__':
    unittest.main()
