"""Mode and prompt selection checks using synthetic reports and mocked Azure."""
import json
import re
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch

import test_app as helpers
from test_app import pasted_case, report


class ModeTests(unittest.TestCase):
    # Share established offline helpers, without inheriting unrelated test cases.
    setUp = helpers.ReviewerTests.setUp
    pair = helpers.ReviewerTests.pair
    payload = helpers.ReviewerTests.payload
    fake_client = helpers.ReviewerTests.fake_client
    client_with_csrf = helpers.ReviewerTests.client_with_csrf

    @classmethod
    def setUpClass(cls):
        cls.module = helpers.import_offline_app()

    def test_mode_prompts_differ_only_in_title_rule_and_exports_are_exact(self):
        m = self.module
        self.assertEqual(m.DEFAULT_PROMPT.count(m.RESIDENT_TITLE_RULE), 1)
        self.assertNotEqual(m.DEFAULT_PROMPT, m.ATTENDING_PROMPT)
        self.assertEqual(m.ATTENDING_PROMPT.replace(m.ATTENDING_TITLE_RULE, m.RESIDENT_TITLE_RULE, 1), m.DEFAULT_PROMPT)
        root = Path(__file__).resolve().parents[1]
        self.assertEqual((root/'ANALYSIS_PROMPT.md').read_text(encoding='utf-8'), m.DEFAULT_PROMPT)
        self.assertEqual((root/'ATTENDING_ANALYSIS_PROMPT.md').read_text(encoding='utf-8'), m.ATTENDING_PROMPT)

    def test_fresh_visit_defaults_resident_and_toggle_precedes_input(self):
        response = self.client_with_csrf().get('/')
        self.assertRegex(response.text, r'id="mode-resident"[^>]*checked')
        self.assertNotRegex(response.text, r'id="mode-attending"[^>]*checked')
        self.assertLess(response.text.index('id="mode-attending"'), response.text.index('id="input-disclosure"'))

    def test_attending_form_default_survives_submission_and_group_membership(self):
        response = self.client_with_csrf().post('/', data={'csrf_token':'synthetic-csrf',
            'review_mode':'attending', 'reports_text':pasted_case(68)+pasted_case(69)})
        self.assertEqual(response.status_code, 200)
        self.assertRegex(response.text, r'id="mode-attending"[^>]*checked')
        editor = re.search(r'<textarea id="custom-prompt"[^>]*>(.*?)</textarea>', response.text, re.S).group(1)
        self.assertEqual(unescape(editor), self.module.ATTENDING_PROMPT)
        cases = json.loads(re.search(r'<script id="review-data" type="application/json">(.*?)</script>', response.text, re.S).group(1))
        self.assertEqual([c['source_numbers'] for c in cases], [[68,69]])
        self.assertEqual(cases[0]['review_mode'], 'attending')

    def test_attending_form_preserves_edited_instructions_and_invalid_prompt_choice(self):
        client = self.client_with_csrf()
        for prompt in (' My attending instructions.\n<synthetic> ', ''):
            response = client.post('/', data={'csrf_token':'synthetic-csrf','review_mode':'attending',
                'reports_text':pasted_case(1),'custom_prompt':prompt})
            editor = re.search(r'<textarea id="custom-prompt"[^>]*>(.*?)</textarea>', response.text, re.S).group(1)
            self.assertEqual(unescape(editor), prompt)
            self.assertRegex(response.text, r'id="mode-attending"[^>]*checked')
            if not prompt:
                self.assertIn('Analysis instructions cannot be empty', response.text)
                self.assertNotIn('"status": "queued"', response.text)

    def test_attending_default_reaches_model_once_without_extra_guidance(self):
        case = self.pair(); case['review_mode'] = 'attending'
        client = self.fake_client()
        with patch.object(self.module, 'get_azure_client', return_value=client):
            result = self.module.summarize_case(case)
        self.assertEqual(client.responses.create.call_count, 1)
        self.assertEqual(client.responses.create.call_args.kwargs['input'][0]['content'], self.module.ATTENDING_PROMPT)
        self.assertEqual(result['review_mode'], 'attending')

    def test_attending_single_request_sends_exact_edited_prompt(self):
        client = self.fake_client(); prompt = 'My edited attending instructions.'
        with patch.object(self.module, 'get_azure_client', return_value=client):
            response = self.client_with_csrf().post('/analyze', json=dict(id='g1', review_mode='attending',
                resident_report=report(), attending_report=report(), custom_prompt=prompt),
                headers={'X-CSRF-Token':'synthetic-csrf'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['review_mode'], 'attending')
        self.assertEqual(client.responses.create.call_args.kwargs['input'][0]['content'], prompt)

    def test_attending_batch_keeps_mode_and_one_request_per_review_entry(self):
        client = self.fake_client()
        records = [dict(id=f'g{i}', resident_report=report(), attending_report=report()) for i in (1,2)]
        with patch.object(self.module, 'get_azure_client', return_value=client):
            response = self.client_with_csrf().post('/analyze-batch', json=dict(cases=records,
                review_mode='attending', custom_prompt=self.module.ATTENDING_PROMPT),
                headers={'X-CSRF-Token':'synthetic-csrf'})
            events = list(map(json.loads, response.data.splitlines()))
        self.assertEqual(client.responses.create.call_count, 2)
        self.assertTrue(all(e['result']['review_mode']=='attending' for e in events if e['type']=='case'))
        self.assertTrue(all(c.kwargs['input'][0]['content']==self.module.ATTENDING_PROMPT for c in client.responses.create.call_args_list))

    def test_invalid_modes_are_rejected_before_model_calls(self):
        client = self.client_with_csrf()
        with patch.object(self.module, 'get_azure_client', side_effect=AssertionError('No provider access')):
            for mode in ('', 'administrator', None, [], {}, True):
                with self.subTest(mode=mode):
                    record = dict(id='g1', resident_report=report(), attending_report=report())
                    response = client.post('/analyze', json=dict(record, review_mode=mode, custom_prompt=self.module.DEFAULT_PROMPT), headers={'X-CSRF-Token':'synthetic-csrf'})
                    self.assertEqual(response.status_code, 400)
                    response = client.post('/analyze-batch', json=dict(cases=[record], review_mode=mode, custom_prompt=self.module.DEFAULT_PROMPT), headers={'X-CSRF-Token':'synthetic-csrf'})
                    self.assertEqual(response.status_code, 400)
            response = client.post('/', data={'csrf_token':'synthetic-csrf','review_mode':'administrator','reports_text':pasted_case(1)})
            self.assertIn('Choose Resident or Attending mode', response.text)
            self.assertNotIn('"status": "queued"', response.text)
