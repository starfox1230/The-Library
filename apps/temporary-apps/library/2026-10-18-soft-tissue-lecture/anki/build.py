"""Rebuild panel-first visual diagnosis cards; never alters the Anki note type.

Run from any directory with Python, PyMuPDF, Pillow and genanki available.
All crop coordinates are manually verified against the original PDFs.
"""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import zipfile

import fitz
import genanki
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
APP = HERE.parent
REPO = next(p for p in HERE.parents if (p / 'scripts/build_manifest_apkg.py').is_file())
ASSETS = HERE / 'assets'
QA = HERE / 'qa'
WIDTH = 1000
LIVE = 'https://starfox1230.github.io/The-Library/apps/temporary-apps/library/2026-10-18-soft-tissue-lecture/'

# MRI source xref, page and pixel crop, including the original panel-letter strip.
# Each tuple is (source letter, rectangle, first footer row, sequence label).
# No sequence or contrast status is inferred when the caption does not state it.
MR = {
 1:(5,12,[('a',(0,0,329,330),293,'Axial T1 (SE)'),('b',(0,330,329,648),623,'Axial T1 fat-suppressed (SPGR)')]),
 2:(5,14,[('a',(0,0,375,310),273,'Axial T1 (SE)'),('b',(0,310,375,782),757,'Coronal T1 fat-suppressed, post-contrast (SPGR)'),('c',(388,0,680,782),757,'Lateral radiograph')]),
 3:(6,19,[('a',(0,0,330,448),423,'Coronal T2 fat-suppressed (FSE)'),('b',(342,0,681,448),423,'Coronal T1 fat-suppressed, post-contrast')]),
 4:(6,21,[(None,(0,0,329,359),None,'Coronal T2 (FSE)')]),
 5:(7,26,[(None,(0,0,329,293),None,'Axial T2 fat-suppressed (FSE)')]),
 6:(7,28,[('a',(0,0,329,187),150,'Axial T1 (SE)'),('b',(0,187,329,364),339,'Axial T2 (FSE)')]),
 7:(7,30,[('a',(0,0,329,364),328,'AP radiograph'),('b',(0,364,329,719),694,'Axial T1 fat-suppressed, post-contrast (SPGR)')]),
 8:(7,32,[(None,(0,0,329,216),None,'Coronal T1 (SE)')]),
 9:(8,37,[('a',(0,0,329,338),301,'Axial T1 (SE)'),('b',(0,338,329,660),635,'Axial T2 (FSE)')]),
 10:(9,42,[(None,(0,0,329,252),None,'Lateral radiograph')]),
 11:(9,44,[('a',(0,0,329,494),457,'AP radiograph'),('b',(0,494,329,832),807,'T1 fat-suppressed, post-contrast (SPGR)')]),
 12:(11,52,[('a',(0,0,329,330),293,'Sagittal T2 (FSE), without fat suppression'),('b',(0,330,329,638),613,'Sagittal T2 fat-suppressed (FSE)')]),
 13:(12,57,[('a',(0,0,329,445),409,'Coronal T1 (SE)'),('b',(0,445,329,857),832,'Coronal T1 fat-suppressed, post-contrast (SPGR)')]),
 14:(12,59,[('a',(0,0,330,285),249,'Axial T1 opposed-phase'),('b',(342,0,681,285),249,'Axial T1 fat-suppressed (SPGR)'),('c',(0,285,337,556),531,'Axial T1 fat-suppressed, post-contrast (SPGR)'),('d',(350,285,681,556),531,'Axial subtraction, post-contrast minus pre-contrast')]),
 15:(13,64,[('a',(0,0,328,365),340,'Axial T1 (SE)'),('b',(340,0,671,365),340,'Axial T2 (FSE)'),('c',(683,0,1038,365),340,'Axial T1 fat-suppressed, post-contrast')]),
 16:(14,69,[('a',(0,0,369,318),293,'Axial T2 (FSE)'),('b',(381,0,681,318),293,'Coronal T2* gradient echo')]),
 20:(16,83,[('a',(0,0,333,355),319,'Axial T1 (SE)'),('b',(345,0,681,355),319,'Axial T1 fat-suppressed'),('c',(0,355,340,700),675,'Axial T1 fat-suppressed, post-contrast'),('d',(353,355,681,700),675,'Axial subtraction, post-contrast minus pre-contrast')]),
 21:(17,88,[('a',(0,0,336,363),338,'Axial T2 fat-suppressed'),('b',(348,0,688,363),338,'Axial T1 fat-suppressed, pre-contrast (SPGR)'),('c',(700,0,1038,363),338,'Axial T1 fat-suppressed, post-contrast (SPGR)')]),
}

# CT-paper rectangles on the previously verified 857 x 1109 page coordinate grid.
# The MRI panel in CT figure 5 is an MRI, not a CT; figure 8a starts above 520.
# Lettered crops include the original A/B strips but stop before caption prose.
CT = {
 1:(2,[(None,(56,390,286,879),None,'Coronal CT')]),
 2:(2,[(None,(303,649,533,879),None,'3D CT reconstruction')]),
 3:(2,[(None,(550,610,781,879),None,'CT reconstruction')]),
 4:(3,[(None,(78,102,430,314),None,'Axial CT')]),
 5:(3,[('A',(78,651,430,919),901,'Axial T1 fat-suppressed, post-contrast MRI'),('B',(449,651,802,919),901,'Axial CT')]),
 6:(4,[(None,(56,102,286,331),None,'Coronal CT reconstruction')]),
 7:(4,[(None,(303,102,533,331),None,'Axial CT, bone window')]),
 8:(4,[('A',(56,488,286,718),695,'Sagittal contrast-enhanced CT reconstruction'),('B',(303,538,533,718),695,'3D CT angiography')]),
 9:(5,[(None,(78,102,430,314),None,'Axial CT')]),
 10:(5,[(None,(571,102,801,332),None,'Axial CT')]),
 11:(5,[(None,(78,434,307,888),None,'Coronal CT')]),
 12:(5,[(None,(325,682,554,889),None,'Coronal CT reconstruction')]),
 13:(5,[(None,(571,682,801,889),None,'Axial contrast-enhanced CT')]),
 14:(6,[(None,(56,102,286,331),None,'Axial CT')]),
 15:(6,[(None,(427,102,781,321),None,'Axial CT')]),
 16:(6,[(None,(427,342,781,571),None,'Axial CT')]),
 17:(6,[(None,(550,589,781,859),None,'Coronal CT')]),
 18:(7,[(None,(78,102,307,310),None,'Axial CT')]),
 19:(7,[(None,(325,102,555,310),None,'Coronal CT reconstruction')]),
 20:(7,[(None,(78,472,307,929),None,'3D CT angiography')]),
 21:(7,[(None,(325,472,555,689),None,'Axial CT')]),
}

def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def wrap(text, font, width, draw):
    lines=[]; line=''
    for word in text.split():
        candidate=(line+' '+word).strip()
        if line and draw.textlength(candidate,font=font)>width:
            lines.append(line); line=word
        else: line=candidate
    if line: lines.append(line)
    return lines

def label_image(image, label, band_y, sequence, letter_side='left'):
    """Keep the original letter pixels and write the sequence beside that letter."""
    image=image.convert('RGB')
    native_width=image.width
    factor=WIDTH/native_width
    original_letter=False
    glyph=None
    if label:
        assert band_y is not None and 0<=band_y<image.height
        region=(0,band_y,min(42,native_width),image.height) if letter_side=='left' else (max(0,native_width-38),band_y,native_width,image.height)
        ink=ImageOps.invert(image.crop(region).convert('L')).point(lambda x:255 if x>155 else 0)
        glyph=ink.getbbox()
        assert glyph, f'Original source letter {label} was not found in its strip'
        original_letter=True
        glyph=(glyph[0]+region[0],glyph[1]+band_y,glyph[2]+region[0],glyph[3]+band_y)
    image=image.resize((WIDTH,round(image.height*factor)),Image.Resampling.LANCZOS)
    font=ImageFont.load_default(size=32)
    for font_path in ['C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        if Path(font_path).is_file():
            font=ImageFont.truetype(font_path,32)
            break
    draw=ImageDraw.Draw(image)
    if glyph:
        y=round(glyph[1]*factor)
        if letter_side=='left':
            x=round(glyph[2]*factor)+20; width=WIDTH-x-22
        else:
            x=22; width=round(glyph[0]*factor)-x-20
    else:
        y=image.height+18; x=22; width=WIDTH-44
    lines=wrap(sequence,font,width,draw)
    needed=y+len(lines)*41+14
    if needed>image.height:
        canvas=Image.new('RGB',(WIDTH,needed),'white'); canvas.paste(image,(0,0)); image=canvas; draw=ImageDraw.Draw(image)
    for i,line in enumerate(lines):
        line_x=x if letter_side=='left' or not glyph else x+width-draw.textlength(line,font=font)
        draw.text((line_x,y+i*41),line,font=font,fill='#14242b')
    return image,original_letter

def extract_panels():
    panels=[]
    docs={key:fitz.open(APP/'papers'/file) for key,file in [('ct','ct-soft-tissue-masses.pdf'),('mr','mri-systematic-approach.pdf')]}
    for number,(page,xref,items) in MR.items():
        doc=docs['mr']; pg=doc[page-1]
        pix=fitz.Pixmap(doc,xref)
        if pix.n!=3: pix=fitz.Pixmap(fitz.csRGB,pix)
        original=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        image_info=next(x for x in pg.get_image_info(xrefs=True) if x['xref']==xref)
        image_rect=fitz.Rect(image_info['bbox'])
        for index,(label,box,band,sequence) in enumerate(items,1):
            panel=original.crop(box)
            final,letter_retained=label_image(panel,label,None if band is None else band-box[1],sequence)
            file=f'stlecture_mr_f{number:02}_{label or "single"}_v1.jpg'
            final.save(ASSETS/file,quality=96,subsampling=0)
            source_rect=fitz.Rect(image_rect.x0+box[0]/original.width*image_rect.width,image_rect.y0+box[1]/original.height*image_rect.height,image_rect.x0+box[2]/original.width*image_rect.width,image_rect.y0+box[3]/original.height*image_rect.height)
            hits=[w[4] for w in pg.get_text('words') if source_rect.intersects(fitz.Rect(w[:4]))]
            assert not hits, f'Caption/body text intersects {file}: {hits}'
            panels.append(dict(id=f'mr-{number}-{label or "single"}',sourceFigureId=f'mr-{number}',sourcePanelIndex=index,sourcePanelCount=len(items),sourceLetter=label,sequence=sequence,paper='mr',page=page,xref=xref,sourcePixelCrop=list(box),sourcePdfRect=list(source_rect),file=f'assets/{file}',filename=file,width=final.width,height=final.height,originalLetterRetained=letter_retained,qa=dict(singleSourcePanel=True,noSurroundingPageText=True,extractablePageTextHits=hits,allowedEmbeddedText=['Original panel letter','Scale and original scanner annotations','Added caption-verified sequence label'])))
    for number,(page,items) in CT.items():
        pg=docs['ct'][page-1]
        for index,(label,box,band,sequence) in enumerate(items,1):
            rect=fitz.Rect(box[0]/857*pg.rect.width,box[1]/1109*pg.rect.height,box[2]/857*pg.rect.width,box[3]/1109*pg.rect.height)
            pix=pg.get_pixmap(matrix=fitz.Matrix(4,4),clip=rect,alpha=False)
            original=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
            band_local=None if band is None else round((band-box[1])/(box[3]-box[1])*original.height)
            final,letter_retained=label_image(original,label,band_local,sequence,'right')
            file=f'stlecture_ct_f{number:02}_{label or "single"}_v1.jpg'
            final.save(ASSETS/file,quality=96,subsampling=0)
            panels.append(dict(id=f'ct-{number}-{label or "single"}',sourceFigureId=f'ct-{number}',sourcePanelIndex=index,sourcePanelCount=len(items),sourceLetter=label,sequence=sequence,paper='ct',page=page,sourcePageGrid=[857,1109],sourcePixelCrop=list(box),sourcePdfRect=list(rect),file=f'assets/{file}',filename=file,width=final.width,height=final.height,originalLetterRetained=letter_retained,qa=dict(singleSourcePanel=True,noSurroundingPageText=True,extractablePageTextHits=[],scannedPageManuallyReviewed=True,allowedEmbeddedText=['Original panel letter when present','Added caption-verified modality/sequence label'])))
    return panels,docs

def contact_sheets(panels):
    for start in range(0,len(panels),12):
        group=panels[start:start+12]
        canvas=Image.new('RGB',(1800,((len(group)+3)//4)*570),'#e0e0e0')
        draw=ImageDraw.Draw(canvas)
        for i,p in enumerate(group):
            im=Image.open(HERE/p['file']); im.thumbnail((434,525))
            x=(i%4)*450; y=(i//4)*570
            canvas.paste(im,(x+(450-im.width)//2,y+30))
            draw.text((x+8,y+7),p['id']+' / PDF p'+str(p['page']),font=ImageFont.load_default(size=18),fill='black')
        canvas.save(QA/f'panels-{start//12+1:02}.jpg',quality=94)

def build():
    ASSETS.mkdir(exist_ok=True); QA.mkdir(exist_ok=True)
    config=json.loads((HERE/'cases.json').read_text(encoding='utf-8'))
    panels,docs=extract_panels()
    assert len(panels)==62
    contact_sheets(panels)
    note_manifest=[]; candidates=[]; pages={}
    for case in config['notes']:
        group=sorted([p for p in panels if p['sourceFigureId']==case['figure']],key=lambda p:p['sourcePanelIndex'])
        assert group
        paper=group[0]['paper']; page=group[0]['page']
        page_key=(paper,page)
        if page_key not in pages:
            file=f'stlecture_{paper}_source_page_{page:02}_v1.jpg'
            pix=docs[paper][page-1].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
            Image.frombytes('RGB',(pix.width,pix.height),pix.samples).save(ASSETS/file,quality=94,subsampling=0)
            pages[page_key]=file
        prompt=(case['context']+' ' if case['context'] else '')+'What is the most likely diagnosis?'
        # Candidate text omits the counter; packaging derives it once from media.
        text_html=html.escape(prompt)+'<br><br>{{c1::'+html.escape(case['diagnosis'])+'}}<br><br>'
        counter=f'1/{len(group)}<br>' if len(group)>1 else ''
        image_html='<br>'.join('<img src="'+p['filename']+'">' for p in group)
        text=text_html+counter+image_html
        source_file='ct-soft-tissue-masses.pdf' if paper=='ct' else 'mri-systematic-approach.pdf'
        citation=('Subhawong et al. AJR 2010' if paper=='ct' else 'Wu and Hochman. Radiology 2009')+f', Figure {case["figure"].split("-")[1]}, PDF page {page}.'
        extra=html.escape(case['extra'])+'<br><br>'+html.escape(citation)+'<br><br><img src="'+pages[page_key]+'"><br><a href="'+LIVE+'papers/'+source_file+f'#page={page}">Open source PDF</a>'
        media=[p['filename'] for p in group]+[pages[page_key]]
        note_id='soft-tissue-lecture-v1-'+case['figure']
        note_manifest.append(dict(id=note_id,source_page_id=case['figure'],source_title=citation,deck_name=config['deckName'],note_type_style='saCloze++',fields=dict(Text=text,Extra=extra),tags=[config['batchTag']],guid=genanki.guid_for('soft-tissue-lecture-2026-10-19',case['figure'],'diagnosis-v1'),media_files=[dict(filename=n,local_path='assets/'+n) for n in media]))
        candidates.append(dict(id=note_id,figure=case['figure'],textHtml=text_html,extraText=case['extra'],diagnosis=case['diagnosis'],context=case['context'],frontMedia=[dict(id=p['id'],filename=p['filename'],sequence=p['sequence'],letter=p['sourceLetter']) for p in group],extraMedia=[pages[page_key]],sourcePage=page,paper=paper))
    assert len(note_manifest)==33
    assert sum(len(c['frontMedia']) for c in candidates)==55
    (HERE/'notes.json').write_text(json.dumps(note_manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (HERE/'candidates.json').write_text(json.dumps(candidates,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    receipt={
      'scope':'Direct user-requested PDF visual diagnosis APKG, not Notion or StudyOS event processing',
      'date':'2026-10-19','model':'Current conversation model; exact runtime identity not exposed',
      'instructions':[dict(path=str(p.relative_to(REPO)).replace('\\','/'),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [REPO/'AGENTS.md',REPO/'apps/anki-card-creation-codex-helper/CARD_STYLE_GUIDE.md',REPO/'apps/anki-card-creation-codex-helper/APKG_PACKAGING.md',REPO/'apps/anki-card-creation-codex-helper/VISUAL_STUDY_AND_ANKI_SPEC.md']],
      'userOverrides':['Diagnosis prompts only; no additional arrow or text-fact cards','Every lettered panel separated on the front, with source letter retained and sequence beside it','Only essential, very brief clinical history'],
      'sourceHashes':{key:hashlib.sha256((APP/'papers'/name).read_bytes()).hexdigest() for key,name in [('ct','ct-soft-tissue-masses.pdf'),('mr','mri-systematic-approach.pdf')]},
      'noteCount':33,'frontPanelCount':55,'extractedClinicalPanelCount':62,'sourcePageCount':len(pages),'skipped':config['skipped'],
      'panels':panels
    }
    (HERE/'extraction-manifest.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    # The shared builder resolves assets relative to CWD. Keep portable relative
    # paths in the checked-in manifest and run it from this folder.
    output=HERE/'soft-tissue-visual-diagnosis.apkg'
    subprocess.run([sys.executable,str(REPO/'scripts/build_manifest_apkg.py'),'--manifest','notes.json','--output',output.name],cwd=HERE,check=True)
    render_review(candidates,config)
    verify_package(output,note_manifest,panels)
    print(json.dumps(dict(notes=33,frontPanels=55,extractedPanels=62,sourcePages=len(pages),output=str(output)),indent=2))

def render_review(candidates,config):
    style=(REPO/'apps/radiographics-review/scripts/build_anki_package.py')
    canonical=load_module('lecture_canonical_model',style)
    css=canonical.MODEL.css
    blocks=[]
    for i,c in enumerate(candidates,1):
        # The preview uses the same ordered media and derives the same one counter.
        prompt=(c['context']+' ' if c['context'] else '')+'What is the most likely diagnosis?'
        image_area=(f'<div>1/{len(c["frontMedia"])}</div>' if len(c['frontMedia'])>1 else '')+''.join('<img src="assets/'+m['filename']+'" alt="'+html.escape((m['letter']+'. ' if m['letter'] else '')+m['sequence'])+'">' for m in c['frontMedia'])
        blocks.append(f'<article class="preview" id="{c["figure"]}"><div class="meta">Card {i} of {len(candidates)}</div><div class="card">{html.escape(prompt)}<br><br><span class="hidden-answer">[...]</span><span class="answer cloze" hidden>{html.escape(c["diagnosis"])}</span><br><br>{image_area}</div><button class="reveal">Reveal diagnosis</button><div class="explanation" hidden><p>{html.escape(c["extraText"])}</p><details><summary>Full source page and provenance</summary><p>{c["figure"]} · PDF page {c["sourcePage"]}</p><img loading="lazy" src="assets/{c["extraMedia"][0]}" alt="Full source PDF page"></details></div></article>')
    output='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>Soft Tissue · Anki diagnosis cards</title><style>'''+css+'''
*{box-sizing:border-box;touch-action:manipulation}body{margin:0;background:#171d20;color:#d7dee9;font:16px/1.6 system-ui,sans-serif}header,main{width:min(760px,94vw);margin:auto}header{padding:34px 0 20px}h1{font-size:32px;line-height:1.2}header p{color:#a6b2bb}header a,button{display:inline-block;padding:11px 16px;margin:5px 5px 5px 0;border-radius:8px;background:#ccef8b;color:#17231a!important;font-size:14px;font-weight:600;border:0;cursor:pointer}.preview{border:1px solid #465159;padding:20px 15px;border-radius:14px;margin:24px 0;background:#2f2f31}.meta{font-size:11px;color:#94a4ae;margin-bottom:20px}.card{max-width:700px;margin:auto}.explanation p{font-size:15px;color:#c7d1dc}.explanation>details img{max-width:100%;height:auto}details{margin-top:20px}summary{cursor:pointer;color:#9acbdf}button:focus-visible,a:focus-visible{outline:3px solid #9acbdf;outline-offset:3px}img{height:auto}footer{padding:25px 0;color:#a6b2bb;font-size:12px}a.secondary{background:#26343c;color:#d7dee9!important}.answer[hidden],.explanation[hidden],.hidden-answer[hidden]{display:none}
</style></head><body><header><a class="secondary" href="../index.html">Lecture Lab</a><h1>Visual diagnosis cards.</h1><p>33 focused notes · 55 separate front panels · saCloze++ · Saved Cards</p><a href="soft-tissue-visual-diagnosis.apkg" download>Download Anki package</a><button id="toggle-all">Reveal all answers</button><p>Each panel keeps its original letter, with the sequence alongside it. FSE = fast spin echo; SE = spin echo; SPGR = spoiled gradient echo. Post-contrast and fat suppression are spelled out.</p><details><summary>Selection and skipped figures</summary><p>Only clinical diagnosis cards are included. Three flowcharts and six nonspecific diagnosis examples were omitted. <a class="secondary" href="cases.json">Read the per-figure reasons</a></p></details></header><main>'''+''.join(blocks)+'''<footer>Source figures from the supplied AJR 2010 and Radiology 2009 readings. Source pages appear in each card's Extra field. This preview approximates the canonical card content; Anki client controls remain client-specific.</footer></main><script>
function revealCard(card,on){card.querySelector('.answer').hidden=!on;card.querySelector('.hidden-answer').hidden=on;card.querySelector('.explanation').hidden=!on;card.querySelector('.reveal').textContent=on?'Hide diagnosis':'Reveal diagnosis';}
document.addEventListener('click',e=>{if(e.target.classList.contains('reveal')){const card=e.target.closest('.preview');revealCard(card,card.querySelector('.answer').hidden);}});
document.querySelector('#toggle-all').addEventListener('click',e=>{const on=e.target.textContent==='Reveal all answers';document.querySelectorAll('.preview').forEach(card=>revealCard(card,on));e.target.textContent=on?'Hide all answers':'Reveal all answers';});
document.addEventListener('dblclick',e=>e.preventDefault());
</script></body></html>'''
    (HERE/'review.html').write_text(output,encoding='utf-8')

def verify_package(output,notes,panels):
    canonical=load_module('lecture_verify_model',REPO/'apps/radiographics-review/scripts/build_anki_package.py').MODEL
    refs=set()
    for n in notes:
        text=n['fields']['Text']; extra=n['fields']['Extra']
        assert len(re.findall(r'\{\{c1::[^{}]+\}\}',text))==1
        assert len(re.findall(r'\{\{c\d+::',text))==1
        assert 'What is the most likely diagnosis?' in text
        front=re.findall(r'<img src="([^"]+)">',text)
        assert front
        assert text.count(f'1/{len(front)}<br>')==(1 if len(front)>1 else 0)
        assert all((ASSETS/file).is_file() for file in front)
        assert all('http' not in file and 'source_page' not in file for file in front)
        assert 'source_page' in extra and '<img ' in extra
        assert n['deck_name']=='Saved Cards' and n['note_type_style']=='saCloze++'
        assert re.fullmatch(r'#AnkiChat::2026\.10\.19_[A-Za-z0-9_]+',n['tags'][0])
        refs.update(re.findall(r'<img src="([^"]+)">',text+extra))
    assert len({n['guid'] for n in notes})==len(notes)
    for figure in {p['sourceFigureId'] for p in panels}:
        group=[p for p in panels if p['sourceFigureId']==figure]
        assert sorted(p['sourcePanelIndex'] for p in group)==list(range(1,len(group)+1))
        assert all(p['sourcePanelCount']==len(group) for p in group)
    assert all(p['qa']['singleSourcePanel'] and p['qa']['noSurroundingPageText'] for p in panels)
    assert all(not p['sourceLetter'] or p['originalLetterRetained'] for p in panels)
    with zipfile.ZipFile(output) as z:
        media=json.loads(z.read('media'))
        assert set(media.values())==refs
        assert all(len(z.read(key))>0 for key in media)
        con=sqlite3.connect(':memory:')
        try:
            con.deserialize(z.read('collection.anki2'))
            assert con.execute('select count(*) from notes').fetchone()[0]==33
            assert con.execute('select count(*) from cards').fetchone()[0]==33
            models=json.loads(con.execute('select models from col').fetchone()[0]); model=next(iter(models.values()))
            assert len(models)==1 and model['name']=='saCloze++' and int(model['id'])==canonical.model_id
            assert [f['name'] for f in model['flds']]==['Text','Extra']
            assert model['css']==canonical.css
            assert model['tmpls'][0]['qfmt']==canonical.templates[0]['qfmt']
            assert model['tmpls'][0]['afmt']==canonical.templates[0]['afmt']
            decks=json.loads(con.execute('select decks from col').fetchone()[0])
            assert [d['name'] for d in decks.values() if d['name']!='Default']==['Saved Cards']
            exported=dict(con.execute('select guid,flds from notes').fetchall())
            assert all(exported[n['guid']]==n['fields']['Text']+'\x1f'+n['fields']['Extra'] for n in notes)
        finally:
            con.close()
    (HERE/'validation.json').write_text(json.dumps(dict(status='passed',notes=33,cards=33,frontImages=55,packagedMedia=len(refs),extractedPanels=62,modelName=canonical.name,modelId=canonical.model_id,fields=['Text','Extra'],deck='Saved Cards',oneClozePerNote=True,oneImagePerLine=True,sourcePagesInExtra=True,originalLettersRetained=True,canonicalTemplatesAndCssExact=True,liveAnkiImportPerformed=False),indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': build()
