"""Render the actual app with entirely fictional, prewritten review results.

No credentials, API calls, patient data, or production authentication changes.
Run this with the app's test dependencies installed. Outputs stay in ignored QA.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_app import import_offline_app, pasted_case, report


def fixtures(app):
    # A deliberately dense synthetic CT CAP: exact quotes make every shown item
    # inspectable against full reports. These are illustrative, not model results.
    observations = [
        ('BOWEL', 'Acute sigmoid diverticulitis without perforation.', 'Acute sigmoid diverticulitis with focal perforation and adjacent extraluminal gas.'),
        ('SUPPORT DEVICES', 'Enteric tube terminates in the stomach.', 'Enteric tube enters the right mainstem bronchus; immediate repositioning advised.'),
        ('CHEST WALL', 'No acute chest wall finding.', 'Nondisplaced left seventh rib fracture. Unchanged ballistic fragments in the left upper chest wall.'),
        ('KIDNEYS', 'Simple left renal cyst.', 'Simple right renal cyst.'),
        ('LUNGS', 'A 5 mm solid right upper lobe pulmonary nodule.', 'A 5 mm solid right upper lobe pulmonary nodule. Consider follow-up CT in 12 months if high risk.'),
        ('LIVER', 'Small simple hepatic cyst.', 'Simple hepatic cyst measures 1.2 cm.'),
        ('PLEURA', 'Small bilateral pleural effusions.', 'Small bilateral pleural effusions.'),
        ('BOWEL DETAIL', 'Stranding all the way around the sigmoid colon.', 'Circumferential perisigmoid stranding.'),
        ('VASCULATURE', 'Mild scattered aortic calcification.', 'Mild scattered atherosclerotic aortic calcification.'),
        ('SPINE', 'Multilevel degenerative disc disease.', 'Multilevel degenerative disc disease, greatest at L4-L5.'),
    ]
    stable = {
        'MEDIASTINUM': 'The heart is normal in size. There is no pericardial effusion. No enlarged mediastinal or hilar lymph nodes are identified. The thoracic aorta is normal in caliber. The included thyroid is homogeneous. The esophagus is not dilated. No mediastinal collection is identified.',
        'AIRWAYS': 'The trachea and proximal bronchi are patent apart from the separately described support device. There is no focal obstructing endobronchial lesion. Mild dependent linear atelectatic opacity is present at both lung bases. No lobar airspace consolidation is identified. Respiratory motion slightly limits assessment of the lung bases.',
        'BILIARY SYSTEM': 'The gallbladder is nondistended. No pericholecystic fluid or radiopaque gallstone is identified. There is no intrahepatic or extrahepatic biliary ductal dilation. No focal abnormality is identified in the porta hepatis. The portal and hepatic veins are patent on the supplied portal venous phase images.',
        'PANCREAS': 'The pancreas is homogeneous in enhancement. There is no pancreatic ductal dilation, peripancreatic fluid collection, or focal pancreatic lesion. The adjacent splenic vein is patent. No inflammatory change is identified around the pancreatic tail. No focal abnormality is identified along the expected course of the common bile duct.',
        'SPLEEN AND ADRENALS': 'The spleen is normal in size and homogeneous in enhancement. There is no perisplenic fluid. The adrenal glands are normal in configuration without a discrete nodule. No retroperitoneal hematoma is identified. The included diaphragmatic crura are symmetric. No focal lesion is identified in the splenic hilum.',
        'URINARY TRACT': 'Both kidneys enhance symmetrically. There is no hydronephrosis, hydroureter, or obstructing urinary tract calculus. No perinephric collection is identified. The urinary bladder is partially distended and otherwise unremarkable. The ureters are not dilated. No focal abnormality is identified at either ureterovesical junction.',
        'SMALL BOWEL': 'The stomach is mildly distended with fluid. The small bowel loops are nondilated. No transition point, small bowel wall thickening, or pneumatosis is identified. The appendix is normal in caliber. The inflammatory changes involving the sigmoid colon are described separately. No additional focus of bowel inflammation is identified.',
        'RETROPERITONEUM': 'No enlarged retroperitoneal lymph nodes are identified. The abdominal aorta is normal in caliber. The major visceral arteries are patent within the limitations of a portal venous phase examination. There is no retroperitoneal fluid collection. The iliac vessels are normal in caliber. No focal filling defect is identified in the included venous structures.',
        'PELVIS': 'The pelvic sidewalls are symmetric. There is no pelvic lymphadenopathy. No discrete adnexal or other pelvic mass is identified. A small amount of reactive pelvic fluid is present adjacent to the sigmoid inflammatory process. The pelvic musculature is symmetric. No acute abnormality is identified in the included sacroiliac joints.',
        'SOFT TISSUES': 'The abdominal wall is intact. No drainable subcutaneous collection is identified. Mild dependent soft tissue edema is present. No inguinal hernia containing bowel is identified. The paraspinal muscles are symmetric. No additional focal soft tissue abnormality is identified in the field of view.',
    }
    rf = '\n\n'.join(f'{name}: {before}' for name,before,after in observations)
    af = '\n\n'.join(f'{name}: {after}' for name,before,after in observations)
    normal = '\n\n'.join(f'{name}: {text}' for name,text in stable.items())
    ri = 'Acute sigmoid diverticulitis without perforation.\nEnteric tube terminates in the stomach.\nA 5 mm solid right upper lobe pulmonary nodule.'
    ai = 'Acute sigmoid diverticulitis with focal perforation and adjacent extraluminal gas.\nEnteric tube enters the right mainstem bronchus; immediate repositioning advised.\nNondisplaced left seventh rib fracture.\nA 5 mm solid right upper lobe pulmonary nodule. Consider follow-up CT in 12 months if high risk.\nSmall bilateral pleural effusions.'
    resident = report(rf + '\n\n' + normal, ri, context='CT chest, abdomen and pelvis with IV contrast')
    attending = report(af + '\n\n' + normal, ai, context='CT chest, abdomen and pelvis with IV contrast')
    first = app.prepare_cases(pasted_case(12, resident, attending))[0]

    def item(importance, action, before, after, rq, aq, rs='r0', ats='a0', reason='The same finding is described with additional detail.'):
        return dict(importance=importance, action=action, resident_summary=before, attending_summary=after, resident_quote=rq, attending_quote=aq,
            resident_section=rs if rq else '', attending_section=ats if aq else '', reason=reason,
            major_evidence_side='attending' if importance=='major' else 'none',
            major_evidence_section='a1' if importance=='major' else '',
            major_evidence_quote=aq if importance=='major' else '')
    revisions = [
        item('major','added','Diverticulitis without perforation','Diverticulitis with focal perforation',observations[0][1],observations[0][2],reason='The new complication changes the acute interpretation; the underlying diverticulitis was already reported.'),
        item('major','changed','Enteric tube in stomach','Enteric tube in right mainstem bronchus',observations[1][1],observations[1][2],reason='The revised position is accompanied by an immediate repositioning recommendation.'),
        item('minor','added','Not documented','Nondisplaced left seventh rib fracture','','Nondisplaced left seventh rib fracture.',reason='An uncomplicated fracture is newly reported.'),
        item('minor','added','Not documented','Unchanged left chest wall ballistic fragments','','Unchanged ballistic fragments in the left upper chest wall.',reason='A stable incidental finding is newly documented.'),
        item('minor','changed','Simple left renal cyst','Simple right renal cyst',observations[3][1],observations[3][2],reason='Laterality changes a clinical assertion even though the cyst remains simple.'),
        item('minor','added','Not documented','Conditional 12-month nodule follow-up','','Consider follow-up CT in 12 months if high risk.',reason='A nonurgent recommendation is added; actionability alone does not make it major.'),
        item('wording','description','Small simple hepatic cyst','Simple hepatic cyst, 1.2 cm',observations[5][1],observations[5][2]),
        item('wording','emphasis','Small bilateral pleural effusions','Added to Impression; finding unchanged',observations[6][1],observations[6][2],ats='a1',reason='The resident already documented the same effusions in Findings; the attending also included them in Impression.'),
        item('wording','description','Stranding all around sigmoid colon','Circumferential perisigmoid stranding',observations[7][1],observations[7][2]),
        item('wording','description','Mild aortic calcification','Mild atherosclerotic aortic calcification',observations[8][1],observations[8][2]),
        item('wording','description','Multilevel disc degeneration','Disc degeneration greatest at L4-L5',observations[9][1],observations[9][2]),
    ]
    first = app.validate_analysis(dict(exam_label='CT CAP',title='Diverticulitis with pleural effusions',revisions=revisions,warnings=[]), first)
    assert first['status']=='complete', first['analysis_warnings']
    cases = [first]
    def add(n,r,a,payload):
        case = app.prepare_cases(pasted_case(n,r,a))[0]
        case = app.validate_analysis(payload,case)
        assert case['status']=='complete',case['analysis_warnings']
        cases.append(case)
    r=report('Small right pneumothorax.','No acute abnormality.',context='Chest radiograph')
    a=report('Small right pneumothorax.','Small right pneumothorax.',context='Chest radiograph')
    add(13,r,a,dict(exam_label='CXR',title='Small right pneumothorax',warnings=[],revisions=[item('wording','emphasis','Small right pneumothorax','Added to Impression; finding unchanged','Small right pneumothorax.','Small right pneumothorax.',ats='a1',reason='The resident already documented the pneumothorax in Findings; the attending also included it in Impression.')] ))
    r=report('Right pneumothorax.','Right pneumothorax.',context='Chest radiograph')
    a=report('No pneumothorax.','No pneumothorax.',context='Chest radiograph')
    change=item('major','changed','Right pneumothorax','No pneumothorax','Right pneumothorax.','No pneumothorax.',rs='r1',ats='a1',reason='The important resident call is explicitly negated; this is a reversal, not a missed pneumothorax.')
    change.update(major_evidence_side='resident',major_evidence_section='r1',major_evidence_quote='Right pneumothorax.')
    add(14,r,a,dict(exam_label='CXR',title='Pneumothorax call',warnings=[],revisions=[change]))
    r=report('Perforated diverticulitis with a multiloculated perisigmoid collection.','Perforated diverticulitis with a multiloculated perisigmoid collection.',context='CT abdomen and pelvis')
    a=report('Perforated diverticulitis with a multiloculated perisigmoid abscess.','Perforated diverticulitis with a multiloculated perisigmoid abscess.',context='CT abdomen and pelvis')
    add(15,r,a,dict(exam_label='CT AP',title='Perforated diverticulitis with collection',warnings=[],revisions=[item('wording','description','Multiloculated perisigmoid collection','Multiloculated perisigmoid abscess','a multiloculated perisigmoid collection','a multiloculated perisigmoid abscess')]))
    # A single normal study for the layout fixture. Duplicate-identity regression
    # cases live in test_app.py; matching templates cannot prove linked studies.
    normal=app.prepare_cases(pasted_case(16,report(context='XR elbow and forearm'),report(context='XR elbow and forearm')))[0]
    cases.append(app.validate_analysis(dict(exam_label='XR upper extremity',title='No acute injury',revisions=[],warnings=[]),normal))
    cases.append(app.prepare_cases(pasted_case(19,report(),''))[0])
    add(20,report(),report(),dict(exam_label='CXR',title='No acute finding',revisions=[],warnings=[]))
    failure=app.prepare_cases(pasted_case(21,report('Small effusion.'),report('Moderate effusion.')))[0]
    cases.append(app._analysis_error(failure,'AI did not finish this case. The full reports and text changes remain available.'))
    for i,c in enumerate(cases):
        c['id']=f'g{i+1}'
    return cases


if __name__ == '__main__':
    app=import_offline_app()
    cases=fixtures(app)
    output=ROOT/'dev/qa-output'
    output.mkdir(exist_ok=True)
    with app.app.app_context():
        html=app.render_template_string(app.TEMPLATE,cases=cases,reports_text='',custom_prompt=app.DEFAULT_PROMPT,
            default_prompt=app.DEFAULT_PROMPT,combined_view=True,
            error='',csrf_token='synthetic-preview',username='',synthetic_preview=True)
    (output/'preview.html').write_text(html,encoding='utf-8')
    (output/'fixtures.json').write_text(json.dumps(cases,ensure_ascii=False),encoding='utf-8')
    # Repeated evidence and overlapping quotations stress source-link navigation.
    repeated_r=report('🧪 marker. Small effusion. Stable comparison. Small effusion.', 'Small effusion.')
    repeated_a=report('🧪 marker. Moderate effusion. Stable comparison. Moderate effusion.', 'Moderate effusion.')
    repeated=app.prepare_cases(pasted_case(1,repeated_r,repeated_a))[0]
    def repeated_revision(rq,aq,rs='r0',ats='a0'):
        return dict(importance='minor',action='changed',resident_summary='Small effusion',attending_summary='Moderate effusion',reason='Synthetic test.',
            resident_quote=rq,attending_quote=aq,resident_section=rs,attending_section=ats,
            major_evidence_side='none',major_evidence_section='',major_evidence_quote='')
    repeated=app.validate_analysis(dict(exam_label='CXR',title='Repeated synthetic effusion wording',warnings=[],revisions=[
        repeated_revision('Small effusion.','Moderate effusion.'),
        repeated_revision('🧪 marker. Small effusion. Stable comparison. Small effusion.',
                          '🧪 marker. Moderate effusion. Stable comparison. Moderate effusion.'),
        repeated_revision('Small effusion.','Moderate effusion.','r1','a1'),
    ]),repeated)
    (output/'link-fixture.json').write_text(json.dumps([repeated],ensure_ascii=False),encoding='utf-8')
    # Import real synthetic source rows to exercise the new grouping pipeline.
    gr, ga = report('Small effusion.', context='Synthetic chest study'), report('Moderate effusion.', context='Synthetic chest study')
    knee, wrist = report(context='Synthetic knee study'), report(context='Synthetic wrist study')
    grouped = app.prepare_cases(pasted_case(68, gr, ga) + pasted_case(69, gr, ga)
        + pasted_case(70, knee, knee) + pasted_case(71, wrist, wrist)
        + pasted_case(74, wrist, wrist) + pasted_case(78, wrist, wrist))
    grouped_results = []
    for i, case in enumerate(grouped):
        revisions = [dict(importance='minor', action='changed', resident_summary='Small effusion',
            attending_summary='Moderate effusion', reason='Synthetic report change.',
            resident_quote='Small effusion.', attending_quote='Moderate effusion.',
            resident_section='r0', attending_section='a0', major_evidence_side='none',
            major_evidence_section='', major_evidence_quote='')] if i == 0 else []
        grouped_results.append(app.validate_analysis(dict(exam_label='Synthetic exam',
            title='Synthetic effusion' if i == 0 else 'No acute finding', warnings=[], revisions=revisions), case))
    with app.app.app_context():
        grouped_html = app.render_template_string(app.TEMPLATE, cases=grouped_results, reports_text='',
            custom_prompt=app.DEFAULT_PROMPT, default_prompt=app.DEFAULT_PROMPT, combined_view=True,
            error='', csrf_token='synthetic-preview', username='', synthetic_preview=True)
    (output/'grouping-preview.html').write_text(grouped_html, encoding='utf-8')
    (output/'grouping-fixtures.json').write_text(json.dumps(grouped_results, ensure_ascii=False), encoding='utf-8')
    # Mode-specific defaults and titles, rendered without a provider or sign-in.
    mode_attending = dict(grouped_results[0], review_mode='attending', title='Moderate effusion')
    mode_resident = dict(grouped_results[0], review_mode='resident', title='Small effusion')
    mode_queue = [dict(grouped[0], review_mode='attending')]
    with app.app.app_context():
        for name, mode, values, synthetic in [('mode-empty', 'resident', [], True),
                ('mode-queued', 'attending', mode_queue, False),
                ('mode-attending', 'attending', [mode_attending], True)]:
            mode_html = app.render_template_string(app.TEMPLATE, cases=values, reports_text='',
                custom_prompt=app.REVIEW_PROMPTS[mode], default_prompt=app.REVIEW_PROMPTS[mode],
                review_mode=mode, combined_view=True, error='', csrf_token='synthetic-preview',
                username='', synthetic_preview=synthetic)
            (output/(name+'.html')).write_text(mode_html, encoding='utf-8')
    (output/'mode-fixtures.json').write_text(json.dumps(dict(attending=mode_attending,
        resident=mode_resident, reports_text=pasted_case(68,gr,ga)+pasted_case(69,gr,ga)),
        ensure_ascii=False), encoding='utf-8')
    print(f'Synthetic production-template preview: {output / "preview.html"}')
    print(f'Complex report: {len(cases[0]["resident_report"].split())} words, {len(cases[0]["revisions"])} distinct revisions.')
