"""Offline regression checks for the cloud report reviewer.

All reports are synthetic. Azure responses and identity login are substituted;
these tests exercise local parsing, validation and application guards, not the
external provider's authentication or clinical model accuracy.
"""

from __future__ import annotations

import copy
import functools
import importlib.util
import json
import re
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
import flask  # Load before patch.dict(sys.modules); retain one Flask/Werkzeug identity.


APP_PATH = Path(__file__).resolve().parents[1] / "main.py"
TENANT_ID = "44784e6c-ffc6-4a36-8fd8-b99d8edc9109"


def report(findings="Clear lungs.", impression="No acute abnormality.", *, context="Synthetic chest study"):
    return f"EXAM: {context}\nINDICATION: Synthetic test only.\nFINDINGS:\n{findings}\nIMPRESSION:\n{impression}"


def pasted_case(number, resident=None, attending=None):
    if resident is None:
        resident = report()
    if attending is None:
        attending = report()
    return f"Case {number}\nAttending Report:\n{attending}\nResident Report:\n{resident}\n"


class OfflineAuth:
    """Provide an authenticated identity context without contacting Microsoft."""

    def __init__(self, **kwargs):
        self.user = {"tid": TENANT_ID, "name": "Synthetic tester"}

    def login_required(self, view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            from flask import abort
            if self.user is None:
                abort(401)
            return view(*args, context={"user": self.user}, **kwargs)
        return wrapped


def import_offline_app():
    identity_module = types.ModuleType("identity.flask")
    identity_module.Auth = OfflineAuth
    identity_package = types.ModuleType("identity")
    identity_package.flask = identity_module
    settings = {
        "AUTHORITY": f"https://login.microsoftonline.com/{TENANT_ID}",
        "CLIENT_ID": "synthetic-client-id",
        "CLIENT_SECRET": "synthetic-not-a-credential",
        "REDIRECT_URI": "https://synthetic.example/redirect",
        "AZURE_OPENAI_API_KEY": "synthetic-not-an-api-key",
        "AZURE_OPENAI_ENDPOINT": "https://synthetic.example/",
        "AZURE_OPENAI_API_VERSION": "synthetic-test-version",
        "MODEL_ID": "synthetic-deployment",
    }
    spec = importlib.util.spec_from_file_location("reviewer_under_test", APP_PATH)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(os.environ, settings), patch.dict(sys.modules, {
        "identity": identity_package, "identity.flask": identity_module,
    }), patch("socket.socket.connect", side_effect=AssertionError("Network prohibited in offline tests")):
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    module.app.config.update(TESTING=True, SECRET_KEY="synthetic-test-session-key")
    return module


class ReviewerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = import_offline_app()

    def setUp(self):
        self.network_guard = patch("socket.socket.connect", side_effect=AssertionError("Network prohibited in offline tests"))
        self.network_guard.start()
        self.addCleanup(self.network_guard.stop)
        self.module.auth.user = {"tid": TENANT_ID, "name": "Synthetic tester"}

    def pair(self, resident=None, attending=None):
        return self.module.prepare_cases(pasted_case(1, resident, attending))[0]

    def payload(self, *items):
        return {"exam_label": "CXR", "title": "Synthetic comparison", "revisions": list(items), "warnings": []}

    def revision(self, **changes):
        item = {
            "importance": "minor", "action": "added", "resident_summary": "Not documented",
            "attending_summary": "Enteric tube in stomach",
            "resident_quote": "", "attending_quote": "Enteric tube terminates in the stomach.",
            "reason": "Device statement added.", "resident_section": "", "attending_section": "a0",
            "major_evidence_side": "none", "major_evidence_section": "", "major_evidence_quote": "",
        }
        item.update(changes)
        return item

    def device_pair(self):
        return self.pair(report(), report("Clear lungs. Enteric tube terminates in the stomach."))

    def test_sections_keep_clinical_text_and_exclude_context_and_later_footer(self):
        text = "INDICATION: Secret context sentinel.\nTECHNIQUE: Technique sentinel.\nFINDINGS:\nClear lungs.\nIMPRESSION:\nNo acute abnormality.\nCOMMUNICATION: Footer sentinel."
        parsed = self.module.parse_sections(text)
        self.assertTrue(parsed["recognized"])
        self.assertIn("Clear lungs.", parsed["clinical_text"])
        self.assertIn("No acute abnormality.", parsed["clinical_text"])
        for excluded in ("Secret context sentinel", "Technique sentinel", "Footer sentinel"):
            self.assertNotIn(excluded, parsed["clinical_text"])

    def test_alternate_combined_and_conclusion_only_headings(self):
        for heading, expected in [
            ("FINDINGS / IMPRESSION:", "combined"),
            ("Findings and Conclusion:", "combined"),
            ("FINDING/CONCLUSION:", "combined"),
            ("CONCLUSION:", "impression"),
            ("Impressions:", "impression"),
        ]:
            with self.subTest(heading=heading):
                parsed = self.module.parse_sections(f"EXAM: Synthetic\n{heading}\nNo acute abnormality.")
                self.assertTrue(parsed["recognized"])
                self.assertEqual(parsed["sections"][0]["kind"], expected)

    def test_heading_words_inside_sentences_do_not_split_section(self):
        parsed = self.module.parse_sections(report("These findings include a stable cyst. Impression of adjacent cortex is unchanged."))
        self.assertEqual([s["kind"] for s in parsed["sections"]], ["findings", "impression"])

    def test_headingless_pair_is_not_silently_no_change(self):
        case = self.pair("No acute finding.", "Hemorrhage with mass effect.")
        self.assertEqual(case["status"], "needs_sections")

    def test_full_context_preserved_but_not_in_clinical_diff(self):
        case = self.pair(report(context="Resident context sentinel"), report(context="Attending context sentinel"))
        self.assertIn("Resident context sentinel", case["resident_report"])
        self.assertIn("Attending context sentinel", case["attending_report"])
        self.assertNotIn("context sentinel", str(case["clinical_diff"]))

    def test_identical_nearby_noncontiguous_pairs_group_with_original_numbers(self):
        cases = self.module.prepare_cases(pasted_case(25) + pasted_case(26, report("Different lungs."), report("Different lungs.")) + pasted_case(27))
        self.assertEqual([c["source_numbers"] for c in cases], [[25, 27], [26]])
        self.assertEqual(cases[0]['case_label'], '25, 27')
        self.assertEqual(len({c['id'] for c in cases}), 2)

    def test_identical_contiguous_pairs_group_and_keep_next_number(self):
        cases = self.module.prepare_cases(pasted_case(25) + pasted_case(26) + pasted_case(27) + pasted_case(28, report("Different."), report("Different.")))
        self.assertEqual([c["source_numbers"] for c in cases], [[25, 26, 27], [28]])
        self.assertEqual([c['case_label'] for c in cases], ['25–27', '28'])

    def test_exact_gap_boundary_uses_source_numbers_not_remaining_record_positions(self):
        for gap in (1, 2, 3, 4, 100):
            with self.subTest(gap=gap):
                cases = self.module.prepare_cases(pasted_case(68) + pasted_case(68 + gap))
                expected = [[68, 68 + gap]] if gap <= 3 else [[68], [68 + gap]]
                self.assertEqual([c['source_numbers'] for c in cases], expected)

    def test_six_adjacent_and_spaced_matching_members_chain_from_previous_match(self):
        for numbers in (list(range(68, 74)), [68, 71, 74, 77, 80, 83]):
            with self.subTest(numbers=numbers):
                cases = self.module.prepare_cases(''.join(pasted_case(n) for n in numbers))
                self.assertEqual([c['source_numbers'] for c in cases], [numbers])
                self.assertEqual(cases[0]['resident_report'], report())
                self.assertEqual(cases[0]['attending_report'], report())

    def test_gap_of_four_starts_a_new_group_that_later_matches_can_join(self):
        cases = self.module.prepare_cases(''.join(pasted_case(n) for n in [68, 69, 73, 74]))
        self.assertEqual([c['source_numbers'] for c in cases], [[68, 69], [73, 74]])

    def test_both_sides_must_match_and_need_not_match_each_other(self):
        resident, attending = report('Small effusion.'), report('Moderate effusion.')
        cases = self.module.prepare_cases(pasted_case(68, resident, attending) + pasted_case(69, resident, attending)
            + pasted_case(70, report('Large effusion.'), attending) + pasted_case(71, resident, report('No effusion.')))
        self.assertEqual([c['source_numbers'] for c in cases], [[68, 69], [70], [71]])

    def test_context_attestation_case_punctuation_and_whitespace_differences_prevent_grouping(self):
        original = report() + '\nSigned by: Synthetic attending'
        alternatives = [original.replace('Synthetic test only.', 'Other indication.'),
            original.replace('EXAM:', 'EXAM: Other context\nCOMPARISON: Prior study\nORIGINAL EXAM:'),
            original.replace('Synthetic attending', 'Other attending'),
            original.replace('Clear lungs.', 'Clear  lungs.'), original.replace('Clear lungs.', 'CLEAR LUNGS.'),
            original.replace('Clear lungs.', 'Clear lungs!')]
        for side in ('resident', 'attending'):
            for changed in alternatives:
                with self.subTest(side=side, changed=changed):
                    second = (changed, original) if side == 'resident' else (original, changed)
                    cases = self.module.prepare_cases(pasted_case(68, original, original) + pasted_case(69, *second))
                    self.assertEqual([c['source_numbers'] for c in cases], [[68], [69]])

    def test_known_attestation_removal_for_clinical_scope_does_not_affect_group_identity(self):
        attestation = 'As the attending physician, I have personally reviewed the images, interpreted and/or supervised the study or procedure, and agree with the wording of the above report.'
        cases = self.module.prepare_cases(pasted_case(68) + pasted_case(69, report(), report() + '\n' + attestation))
        self.assertEqual([c['source_numbers'] for c in cases], [[68], [69]])
        self.assertNotIn(attestation, self.module.parse_sections(cases[1]['attending_report'])['clinical_text'])

    def test_platform_line_endings_and_outer_import_whitespace_do_not_prevent_grouping(self):
        cases = self.module.prepare_cases(pasted_case(68, report().replace('\n', '\r\n'), report().replace('\n', '\r'))
            + pasted_case(69, ' \n' + report() + '\n ', '\n' + report() + '\n'))
        self.assertEqual([c['source_numbers'] for c in cases], [[68, 69]])

    def test_nonascending_input_is_preserved_without_grouping(self):
        for numbers in ([69, 68], [68, 70, 69, 71]):
            with self.subTest(numbers=numbers):
                cases = self.module.prepare_cases(''.join(pasted_case(n) for n in numbers))
                self.assertEqual([c['source_numbers'] for c in cases], [[n] for n in numbers])

    def test_incomplete_members_stay_separate_without_losing_source_gaps(self):
        cases = self.module.prepare_cases(pasted_case(68) + pasted_case(69, report(), '')
            + pasted_case(70, report(), '') + pasted_case(71) + pasted_case(75))
        self.assertEqual([c['source_numbers'] for c in cases], [[68, 71], [69], [70], [75]])
        self.assertTrue(all(c['status'] != 'queued' for c in cases[1:3]))

    def test_grouping_does_not_mutate_original_parsed_records(self):
        records = self.module.parse_cases(pasted_case(68) + pasted_case(69))
        original = copy.deepcopy(records)
        self.module.group_nearby_identical_pairs(records)
        self.assertEqual(records, original)

    def test_duplicate_identity_includes_full_context_and_both_reports(self):
        cases = self.module.prepare_cases(pasted_case(1) + pasted_case(2, report(context="Different indication"), report()) + pasted_case(3, report(), report(context="Different indication")))
        self.assertEqual(len(cases), 3)

    def test_source_order_not_numeric_sort_order(self):
        cases = self.module.prepare_cases(pasted_case(9) + pasted_case(3, report("Other."), report("Other.")))
        self.assertEqual([c["source_numbers"] for c in cases], [[9], [3]])

    def test_empty_attending_retains_case_and_excludes_analysis_queue(self):
        cases = self.module.prepare_cases(pasted_case(9) + pasted_case(10, report(), "") + pasted_case(11, report("Other."), report("Other.")))
        pending = next(c for c in cases if c["source_numbers"] == [10])
        self.assertNotEqual(pending["status"], "queued")
        self.assertEqual(cases[-1]["source_numbers"], [11])

    def test_long_report_is_preserved_without_context_cutoff(self):
        long_findings = "Stable synthetic observation. " * 1800
        full = report(long_findings, "No acute abnormality.")
        case = self.pair(full, full)
        self.assertIn(long_findings, case["resident_report"])
        self.assertIn("No acute abnormality.", self.module.parse_sections(full)["clinical_text"])

    def test_html_in_reports_cannot_become_active_diff_markup(self):
        case = self.pair(report("<script>synthetic()</script>"), report("Clear lungs."))
        # Diff data must remain lossless; safety is enforced at HTML/DOM rendering.
        self.assertIn("<script>", str(case["clinical_diff"]))
        with self.module.app.app_context():
            rendered = self.module.render_template_string(self.module.TEMPLATE,
                cases=[case], reports_text='', custom_prompt=self.module.DEFAULT_PROMPT,
                default_prompt=self.module.DEFAULT_PROMPT, combined_view=False, csrf_token='test',
                error='', username='', synthetic_preview=True)
        self.assertNotIn('<script>synthetic()</script>', rendered)
        self.assertIn('\\u003cscript\\u003e', rendered)

    def test_valid_quote_is_retained(self):
        result = self.module.validate_analysis(self.payload(self.revision()), self.device_pair())
        self.assertEqual(len(result["revisions"]), 1)
        self.assertEqual(result["revisions"][0]["attending_quote"], "Enteric tube terminates in the stomach.")

    def test_summary_schema_requires_two_endpoints_not_free_form_summary(self):
        schema = self.module.RADIOLOGY_SUMMARY_TOOL[0]['parameters']['properties']['revisions']['items']
        for field in ('resident_summary', 'attending_summary'):
            self.assertIn(field, schema['required'])
        self.assertNotIn('summary', schema['properties'])
        self.assertIn('FIXED RESIDENT / ATTENDING ORDER', self.module.DEFAULT_PROMPT)

    def test_added_summary_uses_documentation_marker_and_server_generated_arrow(self):
        item = self.revision(resident_summary='No tube present', attending_summary='  Enteric tube in stomach  ')
        result = self.module.validate_analysis(self.payload(item), self.device_pair())
        revision = result['revisions'][0]
        self.assertEqual(revision['resident_summary'], 'Not documented')
        self.assertEqual(revision['attending_summary'], 'Enteric tube in stomach')
        self.assertEqual(revision['summary'], 'Not documented → Enteric tube in stomach')
        self.assertEqual(revision['resident_quote'], '')
        self.assertEqual({link['side'] for link in revision['source_links']}, {'attending'})

    def test_removal_without_attending_evidence_does_not_become_explicit_negative(self):
        pair = self.pair(report('Small effusion.'), report('Clear lungs.'))
        item = self.revision(action='removed', resident_summary='Small effusion', attending_summary='No effusion',
            resident_quote='Small effusion.', resident_section='r0', attending_quote='', attending_section='')
        result = self.module.validate_analysis(self.payload(item), pair)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['revisions'][0]['summary'], 'Small effusion → Not retained in attending report')

    def test_explicit_negative_and_existing_context_keep_their_supported_endpoints(self):
        for action, before, after in (
            ('changed', 'Right pneumothorax.', 'No pneumothorax.'),
            ('added', 'Diverticulitis without perforation.', 'Diverticulitis with perforation.'),
            ('description', 'Simple cyst.', 'Simple cyst measures 1.2 cm.'),
        ):
            with self.subTest(action=action):
                item = self.revision(action=action, resident_summary=before, attending_summary=after,
                    resident_quote=before, resident_section='r0', attending_quote=after, attending_section='a0')
                result = self.module.validate_analysis(self.payload(item), self.pair(report(before), report(after)))
                self.assertEqual(result['revisions'][0]['summary'], before + ' → ' + after)

    def test_emphasis_uses_one_direct_phrase_even_if_model_writes_it_differently(self):
        pair = self.pair(report('Small right pneumothorax.'), report('Small right pneumothorax.', 'Small right pneumothorax.'))
        item = self.revision(action='emphasis', importance='wording',
            resident_summary='Small right pneumothorax', attending_summary='Same pneumothorax in Impression',
            resident_quote='Small right pneumothorax.', resident_section='r0',
            attending_quote='Small right pneumothorax.', attending_section='a1')
        result = self.module.validate_analysis(self.payload(item), pair)
        self.assertEqual(result['status'], 'complete')
        revision = result['revisions'][0]
        self.assertEqual(revision['summary'], 'Small right pneumothorax → Added to Impression; finding unchanged')
        self.assertEqual(revision['importance'], 'wording')
        self.assertEqual(revision['attending_quote'], 'Small right pneumothorax.')
        self.assertIn(self.module.IMPRESSION_EMPHASIS_SUMMARY, self.module.DEFAULT_PROMPT)

    def test_exported_prompt_is_exact_and_explains_decision_order(self):
        exported = (APP_PATH.parent / 'ANALYSIS_PROMPT.md').read_text(encoding='utf-8')
        self.assertEqual(exported, self.module.DEFAULT_PROMPT)
        self.assertIn('DECISION ORDER', exported)
        self.assertIn('Impression mention proves major', exported)

    def test_invalid_endpoint_never_silently_falls_back_to_free_form_summary(self):
        malformed = []
        for value in ('', '  ', 'Before → after', 'Before -> after', 'Before => after', 'First\nsecond'):
            for field in ('resident_summary', 'attending_summary'):
                malformed.append(self.revision(**{field: value}))
        legacy = self.revision()
        legacy.pop('resident_summary')
        legacy['summary'] = 'Added tube'
        malformed.append(legacy)
        for item in malformed:
            with self.subTest(item=item):
                result = self.module.validate_analysis(self.payload(self.revision(), item), self.device_pair())
                self.assertEqual(result['status'], 'partial')
                self.assertEqual(len(result['revisions']), 1)
                self.assertTrue(result['analysis_warnings'])

    def test_fabricated_quote_marks_partial_never_no_change(self):
        result = self.module.validate_analysis(self.payload(self.revision(attending_quote="Invented hemorrhage.")), self.device_pair())
        self.assertEqual(result["status"], "partial")
        self.assertTrue(result["analysis_warnings"])
        self.assertEqual(result["revisions"], [])

    def test_context_quote_is_not_valid_clinical_evidence(self):
        case = self.device_pair()
        result = self.module.validate_analysis(self.payload(self.revision(attending_quote="Synthetic test only.")), case)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["revisions"], [])

    def test_wrong_section_quote_is_rejected_even_when_present_elsewhere(self):
        item = self.revision(attending_quote="No acute abnormality.", attending_section="a0")
        result = self.module.validate_analysis(self.payload(item), self.device_pair())
        self.assertEqual(result["status"], "partial")
        self.assertFalse(result["revisions"])

    def test_body_only_major_is_review_not_false_perfect_case(self):
        item = self.revision(importance="major", major_evidence_side="attending", major_evidence_section="a0", major_evidence_quote="Enteric tube terminates in the stomach.")
        result = self.module.validate_analysis(self.payload(item), self.device_pair())
        self.assertEqual(result["status"], "partial")
        self.assertEqual(len(result["revisions"]), 1)
        self.assertEqual(result["revisions"][0]["importance"], "review")
        self.assertTrue(result["analysis_warnings"])

    def test_resident_impression_supports_major_removal(self):
        resident = report("Pneumothorax.", "Pneumothorax.")
        attending = report("No pneumothorax.", "No pneumothorax.")
        item = self.revision(importance="major", action="removed", resident_summary="Pneumothorax", attending_summary="No pneumothorax", resident_quote="Pneumothorax.", resident_section="r1", attending_quote="No pneumothorax.", attending_section="a1", major_evidence_side="resident", major_evidence_section="r1", major_evidence_quote="Pneumothorax.")
        result = self.module.validate_analysis(self.payload(item), self.pair(resident, attending))
        self.assertEqual(result["revisions"][0]["importance"], "major")

    def test_emphasis_and_description_never_count_as_major_or_minor(self):
        for action in ("emphasis", "description"):
            with self.subTest(action=action):
                result = self.module.validate_analysis(self.payload(self.revision(action=action, importance="minor", resident_quote="Clear lungs.", resident_section="r0")), self.device_pair())
                self.assertEqual(result["revisions"][0]["importance"], "wording")

    def test_mixed_invalid_and_valid_items_preserve_valid_feedback(self):
        result = self.module.validate_analysis(self.payload(self.revision(), self.revision(attending_quote="Invented hemorrhage.")), self.device_pair())
        self.assertEqual(result["status"], "partial")
        self.assertEqual(len(result["revisions"]), 1)

    def test_malformed_revisions_cannot_become_successful_empty_summary(self):
        for bad in (None, "not a list", {"major": "wrong shape"}):
            with self.subTest(bad=bad):
                payload = self.payload()
                payload["revisions"] = bad
                try:
                    result = self.module.validate_analysis(payload, self.device_pair())
                except ValueError:
                    continue
                self.assertIn(result["status"], ("partial", "error"))

    def client_with_csrf(self):
        client = self.module.app.test_client()
        with client.session_transaction() as session:
            session["comparison_csrf_token"] = "synthetic-csrf"
        return client

    def test_wrong_tenant_is_rejected(self):
        self.module.auth.user = {"tid": "wrong-tenant"}
        self.assertEqual(self.module.app.test_client().get("/").status_code, 403)

    def test_missing_login_does_not_reach_review(self):
        self.module.auth.user = None
        self.assertEqual(self.module.app.test_client().get("/").status_code, 401)

    def test_post_and_analyze_require_csrf(self):
        client = self.client_with_csrf()
        for path in ("/", "/analyze"):
            with self.subTest(path=path):
                self.assertEqual(client.post(path, json={}).status_code, 400)

    def test_initial_post_does_not_call_azure(self):
        client = self.client_with_csrf()
        with patch.object(self.module, "get_azure_client", side_effect=AssertionError("Initial form must not call Azure")):
            response = client.post("/", data={"csrf_token": "synthetic-csrf", "reports_text": pasted_case(1)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        self.assertIn(b'"status": "queued"', response.data)

    def test_retired_echo_route_is_absent(self):
        self.assertNotIn("/echo", {str(rule) for rule in self.module.app.url_map.iter_rules()})

    def fake_client(self, payload=None, status='completed'):
        from unittest.mock import MagicMock
        client = MagicMock()
        client.responses.create.return_value = types.SimpleNamespace(status=status, output=[
            types.SimpleNamespace(type='function_call', name='summarize_radiology_report',
                                  arguments=json.dumps(payload if payload is not None else self.payload()))])
        return client

    def test_call_sends_full_context_strict_schema_and_no_storage(self):
        client = self.fake_client()
        case = self.pair()
        with patch.object(self.module, 'get_azure_client', return_value=client):
            result = self.module.summarize_case(case, 'Prefer concise phrasing')
        self.assertEqual(result['status'], 'complete')
        kwargs = client.responses.create.call_args.kwargs
        self.assertFalse(kwargs['store'])
        self.assertFalse(kwargs['parallel_tool_calls'])
        self.assertTrue(kwargs['tools'][0]['strict'])
        self.assertEqual(kwargs['model'], 'synthetic-deployment')
        content = json.loads(kwargs['input'][1]['content'])
        self.assertEqual(content['resident']['full_report'], case['resident_report'])
        self.assertTrue(content['resident']['eligible_sections'])
        self.assertNotIn('additional_guidance', content)
        self.assertEqual(kwargs['input'][0], {'role':'system', 'content':'Prefer concise phrasing'})
        self.assertEqual(client.responses.create.call_count, 1)

    def test_truncated_response_is_not_graded(self):
        with patch.object(self.module, 'get_azure_client', return_value=self.fake_client(status='incomplete')):
            result = self.module.summarize_case(self.pair())
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['revisions'], [])

    def test_malformed_json_is_recoverable_without_leaking_error(self):
        client = self.fake_client()
        client.responses.create.return_value.output[0].arguments = '{private_source_sentinel'
        with patch.object(self.module, 'get_azure_client', return_value=client), self.assertLogs(self.module.logger, level='WARNING') as logs:
            result = self.module.summarize_case(self.pair())
        self.assertEqual(result['status'], 'error')
        self.assertNotIn('private_source_sentinel', str(result) + str(logs.output))

    def test_unfinished_capture_never_calls_ai(self):
        case = self.module.prepare_cases(pasted_case(1, report(), ''))[0]
        with patch.object(self.module, 'get_azure_client', side_effect=AssertionError('No call expected')):
            self.assertNotEqual(self.module.summarize_case(case)['status'], 'complete')

    def test_extractor_placeholder_never_calls_ai(self):
        text = 'Case 10\nCapture status: POSSIBLY AWAITING ATTENDING — NOT ANALYZED.\nAttending Report:\n[NO ATTENDING TEXT CAPTURED — NOT A REPORT]\nResident Report:\n' + report()
        self.assertEqual(self.module.prepare_cases(text)[0]['status'], 'pending')

    def test_case_number_collision_and_malformed_pair_rejected(self):
        for text in (pasted_case(1) + pasted_case(1), 'Case 1\nResident Report: only one', 'unexpected data\n'+pasted_case(1)):
            with self.subTest(text=text[:25]), self.assertRaises(ValueError):
                self.module.prepare_cases(text)

    def test_added_major_needs_attending_impression(self):
        pair = self.pair(report('Pneumothorax.', 'Pneumothorax.'), report('Pneumothorax.', 'No acute abnormality.'))
        item = self.revision(importance='major', attending_quote='Pneumothorax.',
            major_evidence_side='resident', major_evidence_section='r1', major_evidence_quote='Pneumothorax.')
        self.assertEqual(self.module.validate_analysis(self.payload(item), pair)['revisions'][0]['importance'], 'review')

    def test_long_diff_reconstructs_both_inputs_exactly(self):
        before = ('Original synthetic line 123.4 mm.\n' * 2500) + '\nResident end.'
        after = ('Rewritten synthetic line 567.8 mm.\n' * 2500) + '\nAttending end.'
        parts, _ = self.module.build_text_diff(before, after)
        self.assertEqual(''.join(t for k,t in parts if k != 'insert'), before)
        self.assertEqual(''.join(t for k,t in parts if k != 'delete'), after)

    def test_analyze_endpoint_auth_csrf_and_success(self):
        client = self.client_with_csrf()
        body = dict(id='g1', resident_report=report(), attending_report=report(), custom_prompt=self.module.DEFAULT_PROMPT)
        with patch.object(self.module, 'get_azure_client', return_value=self.fake_client()):
            response = client.post('/analyze', json=body, headers={'X-CSRF-Token':'synthetic-csrf'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'complete')
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_input_limits_are_explicit_without_truncation(self):
        full = report('x' * 120001)
        case = self.pair(full, report())
        self.assertEqual(case['status'], 'error')
        self.assertEqual(case['resident_report'], full)

    def test_template_remains_in_sync(self):
        template = (APP_PATH.parent / 'dev/review-template.html').read_text(encoding='utf-8')
        template = template.replace('/* LOOKUP AUTHORING SOURCE */',
            (APP_PATH.parent / 'dev/lookup.js').read_text(encoding='utf-8'))
        self.assertEqual(self.module.TEMPLATE, template)

    def test_text_change_percent_uses_both_versions_and_ignores_context(self):
        same = self.pair(report(context='Resident context'), report(context='Different attending context'))
        self.assertEqual(same['text_change_percent'], 0.0)
        self.assertFalse(same['text_change_approximate'])
        pair = self.pair(report('Small effusion.'), report('Moderate effusion.'))
        parts = pair['clinical_diff']
        changed = sum(len(p['text']) for p in parts if p['kind'] != 'equal')
        total = sum(len(p['text']) * (2 if p['kind'] == 'equal' else 1) for p in parts)
        self.assertEqual(pair['text_change_percent'], round(100 * changed / total, 1))
        self.assertGreater(pair['text_change_percent'], 0)
        self.assertLessEqual(pair['text_change_percent'], 100)

    def test_text_change_percent_full_replacement_and_coarse_notice(self):
        with patch.object(self.module, 'build_text_diff', return_value=([('delete', 'AAAA'), ('insert', 'BBBB')], True)):
            pair = self.pair()
        self.assertEqual(pair['text_change_percent'], 100.0)
        self.assertTrue(pair['text_change_approximate'])

    def test_text_change_percent_unavailable_is_not_zero(self):
        for pair in (self.pair(report(), ''), self.pair('No clinical headings', report()),
                     self.pair(report('x' * 120001), report())):
            self.assertIsNone(pair['text_change_percent'])

    def test_text_change_percent_does_not_depend_on_ai_availability(self):
        pair = self.pair(report('Small effusion.'), report('Moderate effusion.'))
        expected = pair['text_change_percent']
        failed = self.module._analysis_error(pair, 'Synthetic failure')
        self.assertEqual(failed['text_change_percent'], expected)

    def test_editor_contains_full_default_instructions(self):
        from html import unescape
        response = self.client_with_csrf().get('/')
        editor = re.search(r'<textarea id="custom-prompt"[^>]*>(.*?)</textarea>', response.text, re.S).group(1)
        self.assertEqual(unescape(editor), self.module.DEFAULT_PROMPT)
        self.assertLess(len(editor), self.module.MAX_PROMPT_CHARACTERS)

    def test_paired_view_defaults_on_and_explicit_single_view_survives_submission(self):
        client = self.client_with_csrf()
        for path in ('/', '/main', '/main2'):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertRegex(response.text, r'<div id="cr-app"[^>]*class="dual-view"')
                self.assertIn('id="combined-view" checked', response.text)
                self.assertIn('name="combined_view" value="1"', response.text)
        response = client.post('/', data={'csrf_token':'synthetic-csrf',
            'reports_text':pasted_case(1), 'combined_view':'0'})
        self.assertNotRegex(response.text, r'<div id="cr-app"[^>]*class="dual-view"')
        self.assertNotIn('id="combined-view" checked', response.text)
        self.assertIn('name="combined_view" value="0"', response.text)

    def test_report_wording_preference_defaults_visible_and_survives_submission(self):
        client = self.client_with_csrf()
        self.assertIn('name="show_report_wording" value="1"', client.get('/').text)
        for submitted, expected in (('0', '0'), ('1', '1'), ('invalid', '1')):
            response = client.post('/', data={'csrf_token':'synthetic-csrf',
                'reports_text':pasted_case(1), 'show_report_wording':submitted})
            self.assertIn('name="show_report_wording" value="'+expected+'"', response.text)

    def test_edited_prompt_is_preserved_and_view_preference_survives_post(self):
        from html import unescape
        prompt = '  Compare using my replacement rubric.\n<fictional instructions>  '
        response = self.client_with_csrf().post('/', data={'csrf_token':'synthetic-csrf',
            'reports_text':pasted_case(1), 'custom_prompt':prompt, 'combined_view':'1'})
        editor = re.search(r'<textarea id="custom-prompt"[^>]*>(.*?)</textarea>', response.text, re.S).group(1)
        self.assertEqual(unescape(editor), prompt)
        self.assertRegex(response.text, r'<div id="cr-app"[^>]*class="dual-view"')
        self.assertIn('id="combined-view" checked', response.text)

    def test_empty_and_oversized_prompts_rejected_before_api_call(self):
        client = self.client_with_csrf()
        with patch.object(self.module, 'get_azure_client', side_effect=AssertionError('No call expected')):
            for prompt in ('', '  \n  ', 'x' * (self.module.MAX_PROMPT_CHARACTERS + 1)):
                with self.subTest(length=len(prompt)):
                    response = client.post('/analyze', json=dict(id='g1',resident_report=report(),
                        attending_report=report(),custom_prompt=prompt),headers={'X-CSRF-Token':'synthetic-csrf'})
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(self.module.summarize_case(self.pair(),prompt)['status'], 'error')
                    response = client.post('/',data={'csrf_token':'synthetic-csrf',
                        'reports_text':pasted_case(1),'custom_prompt':prompt})
                    self.assertIn('id="analysis-error"',response.text)
                    self.assertNotIn('"status": "queued"',response.text)

    def test_default_call_uses_visible_default_without_hidden_guidance(self):
        client = self.fake_client()
        with patch.object(self.module, 'get_azure_client',return_value=client):
            self.module.summarize_case(self.pair())
        instructions = client.responses.create.call_args.kwargs['input']
        self.assertEqual(instructions[0]['content'],self.module.DEFAULT_PROMPT)
        self.assertEqual(len(instructions),2)
        self.assertEqual(set(json.loads(instructions[1]['content'])),{'resident','attending'})

    def test_prompt_above_old_supplement_limit_is_sent_without_truncation(self):
        prompt = 'Replacement prompt\n' + ('x' * 9000)
        client = self.fake_client()
        with patch.object(self.module, 'get_azure_client',return_value=client):
            response = self.client_with_csrf().post('/analyze',json=dict(id='g1',resident_report=report(),
                attending_report=report(),custom_prompt=prompt),headers={'X-CSRF-Token':'synthetic-csrf'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(client.responses.create.call_args.kwargs['input'][0]['content'],prompt)


if __name__ == "__main__":
    unittest.main()
