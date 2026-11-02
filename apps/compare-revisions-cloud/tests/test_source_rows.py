"""Bounded pixel-only evidence and dual titles in offline exports; no external calls."""
import base64
import json
import re
import struct
import unittest
import zlib
import test_export as export_helpers
from test_app import pasted_case


def chunk(kind, body):
    return struct.pack('>I', len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)


def png(width=4,height=2,metadata=False,pixels=None):
    header=struct.pack('>IIBBBBB',width,height,8,6,0,0,0)
    body=pixels if pixels is not None else (b'\0'+b'\xff'*width*4)*height
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)
    if metadata:data+=chunk(b'tEXt',b'Comment\0PRIVATE_METADATA')
    data+=chunk(b'IDAT',zlib.compress(body))+chunk(b'IEND',b'')
    return 'data:image/png;base64,'+base64.b64encode(data).decode()


class SourceRowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        export_helpers.ExportTests.setUpClass();cls.m=export_helpers.ExportTests.m

    record=export_helpers.ExportTests.record

    def test_pixel_images_survive_joins_but_metadata_and_extra_fields_do_not(self):
        row=dict(case_number=68,accession='CT000001234',confirmed=True,source_row=png(metadata=True),full_screenshot='PRIVATE_FULL_IMAGE')
        out=self.m.confirmed_lookup([row,row])
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]['accession'],'CT000001234')
        self.assertNotIn(b'PRIVATE_METADATA',base64.b64decode(out[0]['source_row'].split(',')[1]))
        self.assertNotIn('full_screenshot',out[0])
        self.assertEqual(out[0]['source_row'],self.m.safe_source_row(out[0]['source_row']))

    def test_invalid_images_fail_without_rendering_or_unbounded_decompression(self):
        for image in ['https://invalid/image.png','data:image/svg+xml;base64,PHN2Zz4=',png(width=1201),png(height=121),png(pixels=b'\0'*10000),png()[:-5]+'!!!!!']:
            with self.subTest(prefix=image[:25]),self.assertRaises(ValueError):self.m.safe_source_row(image)

    def test_filtered_export_keeps_only_selected_source_crops_and_both_safe_titles(self):
        c=self.record();c.update(title_resident='Resident memory cue',title_attending='Final interpretation cue')
        with self.m.app.test_client() as client:
            client.get('/')
            with client.session_transaction() as s:s['comparison_csrf_token']='test-csrf'
            result=client.post('/export-review',json={'cases':[c],'lookup':[
                dict(case_number=68,accession='CT000001234',confirmed=True,source_row=png()),
                dict(case_number=999,accession='UNSELECTED',confirmed=True,source_row=png(width=5))]},headers={'X-CSRF-Token':'test-csrf'})
        self.assertEqual(result.status_code,200)
        html=result.text
        self.assertIn('Resident memory cue',html);self.assertIn('Final interpretation cue',html)
        self.assertIn('id="mode-attending"',html);self.assertNotIn('UNSELECTED',html)
        lookup=json.loads(re.search(r'<script id="lookup-data" type="application/json">(.*?)</script>',html,re.S)[1])
        self.assertEqual([r['case_number'] for r in lookup],[68])
        self.assertEqual(lookup[0]['source_row'],png())

    def test_each_title_is_filtered_for_excluded_report_context(self):
        c=self.record();c.update(title_resident='COMPARISON_SECRET_123',title_attending='SIGNATURE_SECRET_123')
        out=self.m.export_review_cases([c])[0]
        self.assertNotIn('SECRET',str(out))

    def test_normal_form_preserves_source_images_outside_analysis_cases(self):
        row=dict(case_number=68,accession='CT000001234',confirmed=True,source_row=png())
        with self.m.app.test_client() as client:
            client.get('/')
            with client.session_transaction() as s:s['comparison_csrf_token']='test-csrf'
            result=client.post('/',data={'csrf_token':'test-csrf','reports_text':pasted_case(68),
                'lookup_json':json.dumps([row])})
        self.assertEqual(result.status_code,200)
        lookup=json.loads(re.search(r'<script id="lookup-data" type="application/json">(.*?)</script>',result.text,re.S)[1])
        cases=json.loads(re.search(r'<script id="review-data" type="application/json">(.*?)</script>',result.text,re.S)[1])
        self.assertEqual(lookup,[row])
        self.assertNotIn('source_row',json.dumps(cases))

    def test_analysis_keeps_incomplete_flagged_and_conflicting_rows_editable(self):
        rows = [
            dict(case_number=68, accession='CT000001234', confirmed=True, source_row=png()),
            dict(case_number=69, accession='CT000001235', caseIssue='Case number may be incomplete', source_row=png()),
            dict(case_number=70, accession='OT000001236', accessionIssue='Check accession length'),
            dict(case_number=71, accession='CT000001237'),
            dict(case_number=71, accession='CT000001238'),
            dict(case_number=None, accession='CT000001239'),
            dict(case_number=72, accession=''),
        ]
        with self.m.app.test_client() as client:
            client.get('/')
            with client.session_transaction() as s:s['comparison_csrf_token']='test-csrf'
            result=client.post('/',data={'csrf_token':'test-csrf','reports_text':pasted_case(68)+pasted_case(69),
                'lookup_json':json.dumps(rows)})
        self.assertEqual(result.status_code,200)
        lookup=json.loads(re.search(r'<script id="lookup-data" type="application/json">(.*?)</script>',result.text,re.S)[1])
        cases=json.loads(re.search(r'<script id="review-data" type="application/json">(.*?)</script>',result.text,re.S)[1])
        self.assertEqual(len(lookup),len(rows))
        self.assertEqual(lookup[1]['caseIssue'],'Case number may be incomplete')
        self.assertEqual(lookup[2]['accessionIssue'],'Check accession length')
        self.assertEqual(lookup[1]['source_row'],png())
        self.assertEqual([r['accession'] for r in lookup[3:5]],['CT000001237','CT000001238'])
        self.assertIsNone(lookup[5]['case_number'])
        self.assertEqual(lookup[6]['accession'],'')
        self.assertTrue(cases,'lookup warnings must not prevent report preparation')
        self.assertNotIn('CT000001234',json.dumps(cases))
        self.assertNotIn('source_row',json.dumps(cases))

    def test_lookup_draft_bounds_and_allowlist_still_apply(self):
        out=self.m.lookup_draft([dict(case_number='68',accession='CT000001234',
            caseIssue='x'*200,source_row=png(metadata=True),full_screenshot='PRIVATE_FULL_IMAGE')])[0]
        self.assertIsNone(out['case_number'])
        self.assertEqual(len(out['caseIssue']),160)
        self.assertNotIn('full_screenshot',out)
        self.assertNotIn(b'PRIVATE_METADATA',base64.b64decode(out['source_row'].split(',')[1]))
        for rows in ({},[None],[dict(accession=123)],[dict(accession='x'*129)],[{}]*1001):
            with self.subTest(rows=str(rows)[:30]),self.assertRaises(ValueError):self.m.lookup_draft(rows)


if __name__=='__main__':unittest.main()
