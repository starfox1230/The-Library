"""Clinical-only exports and exact, confirmed accession mappings. Synthetic only."""
import unittest
import json
import re
from unittest.mock import patch
from test_app import import_offline_app, report, pasted_case


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = import_offline_app()

    def record(self):
        m = self.m
        r = report('Clear lungs.', 'No acute abnormality.', context='SOURCE_CONTEXT_SECRET')
        r = r.replace('INDICATION: Synthetic test only.',
            'INDICATION: INDICATION_SECRET_123\nCOMPARISON: COMPARISON_SECRET_123\nTECHNIQUE: TECHNIQUE_SECRET_123')
        r += '\nATTESTATION: ATTESTATION_SECRET_123\nSIGNED BY: SIGNATURE_SECRET_123'
        c = m.prepare_cases(pasted_case(68, r, r))[0]
        c.update(title='Clear lungs', exam_label='CXR', status='complete', revisions=[],
            analysis_warnings=['RAW_WARNING_SECRET'], status_message='RAW_ERROR_SECRET',
            source_numbers=[68, 69], unknown={'secret': 'UNKNOWN_SECRET'})
        return c

    def test_full_document_excludes_context_inputs_and_live_runtime(self):
        m = self.m
        with m.app.test_client() as client:
            client.get('/')
            with client.session_transaction() as session:
                session['comparison_csrf_token'] = 'synthetic-csrf'
            result = client.post('/export-review', json={'cases':[self.record()],
                'lookup':[{'case_number':68,'accession':'000068001','confirmed':True},
                          {'case_number':999,'accession':'UNRELATED_SECRET','confirmed':True}]},
                headers={'X-CSRF-Token':'synthetic-csrf'})
        self.assertEqual(result.status_code, 200)
        html = result.get_data(as_text=True)
        for marker in ['SOURCE_CONTEXT_SECRET', 'INDICATION_SECRET', 'COMPARISON_SECRET',
                'TECHNIQUE_SECRET', 'ATTESTATION_SECRET', 'SIGNATURE_SECRET', 'RAW_WARNING_SECRET',
                'RAW_ERROR_SECRET', 'UNKNOWN_SECRET', 'UNRELATED_SECRET', 'id="report-text"',
                'id="custom-prompt"', 'id="lookup-panel"', 'csrf_token', '/analyze-batch',
                'createWorker', '/ocr-assets/', 'review-prompts']:
            self.assertNotIn(marker, html)
        self.assertIn('<meta name="compare-revisions-export" content="offline-v1">', html)
        self.assertIn('Contains PHI.', html)
        self.assertIn('000068001', html)
        self.assertIn('Clear lungs.', html)
        self.assertIn('Clinical reports', html)
        self.assertNotIn('Synthetic preview · illustrative results',html)
        self.assertIn('clinical-review.html', result.headers['Content-Disposition'])

    def test_normal_page_has_no_offline_reader_marker(self):
        with self.m.app.test_client() as client:
            html=client.get('/').get_data(as_text=True)
        self.assertNotIn('<meta name="compare-revisions-export"', html)

    def test_export_rebuilds_clinical_offsets_and_rejects_context_quotes(self):
        m = self.m
        c = self.record()
        c['revisions'] = [dict(importance='wording', action='description',
            resident_summary='Clear lungs', attending_summary='Clear lungs', reason='Same clinical assertion.',
            resident_section='r0', attending_section='a0', resident_quote='Clear lungs.',
            attending_quote='Clear lungs.', major_evidence_side='none', major_evidence_section='', major_evidence_quote='',
            source_links=[{'side':'resident', 'start':999999, 'end':9999999}])]
        exported = m.export_review_cases([c])[0]
        self.assertEqual(exported['revisions'][0]['source_links'][0]['start'], len('FINDINGS:\n'))
        self.assertNotIn('SECRET', str(exported))
        c['revisions'][0]['resident_quote']='ATTESTATION_SECRET_123'
        self.assertEqual(m.export_review_cases([c])[0]['revisions'], [])

    def test_export_drops_generated_context_and_unstructured_failures(self):
        c = self.record()
        c['title'] = 'COMPARISON_SECRET_123'
        out = self.m.export_review_cases([c])[0]
        self.assertEqual(out['title'], 'Clinical report review')
        c['revisions']=[None]
        self.assertEqual(self.m.export_review_cases([c])[0]['status'],'partial')
        for status in ['error','pending','needs_sections']:
            c['status']=status
            self.assertNotIn('SECRET', str(self.m.export_review_cases([c])))
        c['status']='processing'
        with self.assertRaises(ValueError):self.m.export_review_cases([c])

    def test_headingless_report_is_omitted_not_exported_as_a_fallback(self):
        c = self.record();c['resident_report']='UNSTRUCTURED_SECRET'
        exported=self.m.export_review_cases([c])[0]
        self.assertEqual(exported['resident_report'],'')
        self.assertEqual(exported['status'],'unavailable')

    def test_markup_in_clinical_text_is_serialized_as_data(self):
        m=self.m
        c=self.record()
        c['resident_report']=c['attending_report']='FINDINGS:\nLiteral </script><img src=x onerror=alert(1)> text.\nIMPRESSION:\nUnchanged.'
        records=m.export_review_cases([c])
        with m.app.app_context():
            html=m.render_template_string(m.TEMPLATE,cases=records,exported_review=True,lookup_rows=[],
                combined_view=True,theme='dark',show_report_wording=False,review_mode='resident',synthetic_preview=True)
        self.assertNotIn('</script><img',html)
        self.assertIn('\\u003c/script\\u003e',html)

    def test_lookup_strict_confirmation_conflicts_leading_zeros_and_duplicates(self):
        good={'case_number':68,'accession':'000012345','confirmed':True}
        self.assertEqual(self.m.confirmed_lookup([good,good]),[good])
        for bad in [dict(good,confirmed=False),dict(good,case_number='68'),dict(good,accession=12345),
                dict(good,accession='12 345'),dict(good,case_number=True)]:
            with self.assertRaises(ValueError):self.m.confirmed_lookup([bad])
        with self.assertRaises(ValueError):self.m.confirmed_lookup([good,dict(good,accession='99999')])

    def test_source_numbers_cannot_collide_between_entries(self):
        with self.assertRaises(ValueError):self.m.export_review_cases([self.record(),self.record()])

    def test_export_requires_session_and_csrf(self):
        with self.m.app.test_client() as client:
            self.assertEqual(client.post('/export-review',json={'cases':[self.record()]}).status_code,400)

    def test_confirmed_lookup_survives_analyze_form_submission(self):
        m=self.m
        lookup=[{'case_number':68,'accession':'000068001','confirmed':True}]
        with m.app.test_client() as client:
            client.get('/')
            with client.session_transaction() as session:token=session['comparison_csrf_token']
            response=client.post('/',data={'csrf_token':token,'reports_text':pasted_case(68),
                'custom_prompt':m.DEFAULT_PROMPT,'lookup_json':json.dumps(lookup)})
        html=response.get_data(as_text=True)
        self.assertEqual(response.status_code,200)
        stored=re.search(r'<script id="lookup-data" type="application/json">(.*?)</script>',html,re.S)
        self.assertEqual(json.loads(stored.group(1)),lookup)

    def test_ocr_asset_integrity_unknown_paths_and_no_arbitrary_proxy(self):
        m=self.m
        with m.app.test_client() as client:
            self.assertEqual(client.get('/ocr-assets/not-allowed.js').status_code,404)
        m.load_ocr_asset.cache_clear()
        from io import BytesIO
        with patch.object(m,'urlopen',return_value=BytesIO(b'wrong public asset')):
            with self.assertRaises(ValueError):m.load_ocr_asset('tesseract.min.js')


if __name__=='__main__': unittest.main()
