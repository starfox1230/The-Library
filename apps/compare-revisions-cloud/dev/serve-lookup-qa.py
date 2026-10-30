"""Loopback-only test harness. Synthetic cases, fake identity, no Azure requests."""
from pathlib import Path
import json
import sys
from flask import session
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_app import import_offline_app
m=import_offline_app()
m.summarize_case=lambda case,instructions=None:dict(case,status='unavailable',
    status_message='Local OCR demo: AI analysis is disabled.',revisions=[])
m.app.config['SESSION_COOKIE_SECURE']=False  # Loopback harness only.
fixtures=json.loads((ROOT/'dev/qa-output/grouping-fixtures.json').read_text(encoding='utf-8'))
for c in fixtures:
    for side in ('resident','attending'):
        c[side+'_report']='COMPARISON: EXCLUDE_COMPARISON_875942\nTECHNIQUE: EXCLUDE_TECHNIQUE_875942\n'+c[side+'_report']+'\nSIGNED BY: EXCLUDE_SIGNATURE_875942'
    c['analysis_warnings']=['EXCLUDE_RAW_WARNING_875942']
m.load_ocr_asset=lambda name:(ROOT/'dev/qa-output/ocr-assets'/name).read_bytes()
@m.app.route('/qa')
def qa():
    m.TEMPLATE=(ROOT/'dev/review-template.html').read_text(encoding='utf-8').replace('/* LOOKUP AUTHORING SOURCE */',(ROOT/'dev/lookup.js').read_text(encoding='utf-8'))
    session['comparison_csrf_token']='synthetic-qa-csrf'
    return m.render_template_string(m.TEMPLATE,cases=fixtures,reports_text='EXCLUDE_RAW_INPUT_875942',
        custom_prompt=m.DEFAULT_PROMPT,default_prompt=m.DEFAULT_PROMPT,review_mode='resident',
        combined_view=True,show_report_wording=False,theme='dark',error='',
        csrf_token='synthetic-qa-csrf',username='Synthetic test',synthetic_preview=True)
m.app.run(host='127.0.0.1',port=8766,debug=False)
