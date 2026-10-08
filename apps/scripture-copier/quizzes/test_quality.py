import copy
import json
import unittest
import tempfile
from pathlib import Path
from quality import bank_hash, REVIEW_CHECKS, validate_quality
from export_quizduel import build_exports
from validate import validate

class PublicationGates(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).parent / '2026-10-07.json').read_text(encoding='utf-8'))

    def test_reviewed_bank_passes(self):
        validate_quality(self.doc)

    def test_reused_pool_is_rejected(self):
        questions = self.doc['levels']['kid']
        questions[1]['options'] = copy.deepcopy(questions[0]['options'])
        with self.assertRaisesRegex(ValueError, 'reused answer choice'):
            validate_quality(self.doc)

    def test_question_cannot_give_away_answer(self):
        q = self.doc['levels']['kid'][0]
        answer = next(o['text'] for o in q['options'] if o['id'] == q['correctOptionId'])
        q['question'] = f'The answer is {answer}. What must the people pay?'
        with self.assertRaisesRegex(ValueError, 'stem contains'):
            validate_quality(self.doc)

    def test_oversized_choice_is_rejected(self):
        self.doc['levels']['kid'][0]['options'][0]['text'] += ' with many additional explanations and exceptions to make this option obviously different'
        with self.assertRaisesRegex(ValueError, 'unequal word counts'):
            validate_quality(self.doc)

    def test_predictably_long_key_is_rejected(self):
        for i,q in enumerate(self.doc['levels']['kid']):
            for o in q['options']:
                o['text'] = f'Choice {i} {o["id"]}' + (' extra' if o['id'] == q['correctOptionId'] else '')
        with self.assertRaisesRegex(ValueError, 'length predicts'):
            validate_quality(self.doc)

    def test_predictably_short_key_is_rejected(self):
        for i,q in enumerate(self.doc['levels']['kid']):
            for o in q['options']:
                o['text'] = f'Choice {i} {o["id"]}' + ('' if o['id'] == q['correctOptionId'] else ' extra')
        with self.assertRaisesRegex(ValueError, 'length predicts'):
            validate_quality(self.doc)

    def test_edited_bank_requires_new_review(self):
        self.doc['levels']['kid'][0]['explanation'] += ' Changed.'
        with self.assertRaisesRegex(ValueError, 'stale content-bound'):
            validate_quality(self.doc)

    def test_answer_positions_are_checked(self):
        for q in self.doc['levels']['kid']:
            key = next(o for o in q['options'] if o['id'] == q['correctOptionId'])
            q['options'].remove(key); q['options'].insert(0,key)
        with self.assertRaisesRegex(ValueError, 'unbalanced stored'):
            validate_quality(self.doc)

    def test_future_scripture_books_use_their_own_paths(self):
        date = '2026-10-19'
        self.doc['date'] = date
        for questions in self.doc['levels'].values():
            for q in questions:
                q['id'] = q['id'].replace('2026-10-07', date)
                q['date'] = date
                q['source'] = {'reference': 'Jeremiah 1:1', 'url': 'https://www.churchofjesuschrist.org/study/scriptures/ot/jer/1.1?lang=eng'}
        self.doc['qualityReview'] = {'questionSha256': bank_hash(self.doc), 'checks': REVIEW_CHECKS}
        self.doc['quizDuel'] = build_exports(self.doc)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / f'{date}.json'
            path.write_text(json.dumps(self.doc), encoding='utf-8')
            self.assertEqual(validate(path, {date: [('Jeremiah', 1, 1)]}), 30)

if __name__ == '__main__':
    unittest.main()
