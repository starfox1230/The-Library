"""Build the PRIVATE source corpus; never commit the generated corpus or assets.

Usage: python build_sources.py --chapters DIR --acr FILE --output PRIVATE_DIST
Requires PyMuPDF and Pillow. Full pages preserve every panel and table. Figure crops
are conveniences with an always-available complete source-page fallback.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


def clean(text):
    text = text.replace('\u200b', '').replace('\u00ad', '')
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    return re.sub(r'\s+', ' ', text).strip()


def render(page, rect, dest, scale=2):
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
    Image.frombytes('RGB', (pix.width, pix.height), pix.samples).save(dest, quality=89, optimize=True)


def generate(chapters, acr, output, rsna=None):
    output.mkdir(parents=True, exist_ok=True)
    assets = output / 'assets'
    assets.mkdir(exist_ok=True)
    files = [
        ('helms2', next(chapters.glob('*Chapter 2*.pdf')), 'Imaging Features of Bone Tumors', 'https://drive.google.com/file/d/1uPXC1o329tX-9FLDpPiEJ0qZbvlWqIjn/view', 33),
        ('helms3', next(chapters.glob('*Chapter 3*.pdf')), 'Bone Tumors Radiologists Should Know', 'https://drive.google.com/file/d/16RgomRmQ6EfO4nyPl2wz6M8WwVqyKjaX/view', 49),
        ('helms4', next(chapters.glob('*Chapter 4*.pdf')), 'Bone Tumor Mimics', 'https://drive.google.com/file/d/1CPccD0FewXAjjOP2bcanpqyBJ78wEuIR/view', 75),
        ('acr', acr, 'ACR Bone-RADS paper & Figure 9 correction', 'https://www.jacr.org/article/S1546-1440(23)00595-1/fulltext', 1044),
    ]
    corpus = {'version': 1, 'sources': [], 'figures': [], 'coverage': {}}
    crop_audit = []
    for sid, path, title, url, printed in files:
        doc = fitz.open(path)
        source = {'id': sid, 'title': title, 'url': url, 'description': 'Fundamentals of Skeletal Radiology, 6th edition. Copyright Elsevier. Personal study copy.' if sid.startswith('helms') else '2023 consensus guideline and May 2024 Figure 9 erratum. E-only report templates remain linked from the original article.', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'pages': []}
        for pi, page in enumerate(doc):
            page_id = f'{sid}-p{pi+1}'
            # ClinicalKey's personal download footer contains the user's email.
            # Keep the textbook content, credit the publication in source metadata.
            content_rect = fitz.Rect(0, 0, page.rect.width, 648) if sid.startswith('helms') else page.rect
            render(page, content_rect, assets / f'{page_id}.jpg')
            blocks = []
            image_rects = []
            captions = []
            for block in page.get_text('dict')['blocks']:
                rect = fitz.Rect(block['bbox'])
                if block['type'] == 1:
                    if rect.width > 20 and rect.height > 20:
                        image_rects.append(rect)
                    continue
                raw = '\n'.join(''.join(s['text'] for s in line['spans']) for line in block['lines'])
                text = clean(raw)
                if not text or rect.y0 < 43 or rect.y1 > content_rect.y1 - (0 if sid.startswith('helms') else 22):
                    continue
                if any(x in text for x in ['Downloaded for Sterling', 'Elsevier on July', 'For personal use only']):
                    continue
                # Skip running headers/footers but retain section headings.
                if sid == 'acr' and (text.startswith('Journal of the American College') or text.startswith('Clinical Practice Management') or re.match(r'^Volume \d+', text)):
                    continue
                label = re.match(r'^(?:FIG\.|Fig\.|Figure)\s*(\d+(?:\.\d+)?)\b[.\s]*', text)
                if label:
                    captions.append((label.group(1), text, rect))
                if len(text) > 2 and not re.fullmatch(r'[A-Z ]{1,8}|\d+', text):
                    blocks.append((rect, text))
            # Read two columns in sequence, not across the gutter. Wide blocks retain
            # their position as separators (figures, tables and full-width captions).
            wide = [(r, t) for r, t in blocks if r.width > page.rect.width * .62]
            boundaries = sorted({0, content_rect.y1, *[r.y0 for r, t in wide], *[r.y1 for r, t in wide]})
            ordered = []
            used = set()
            for lo, hi in zip(boundaries, boundaries[1:]):
                current = [(j, r, t) for j, (r, t) in enumerate(blocks) if j not in used and lo <= r.y0 < hi]
                current.sort(key=lambda b: (0 if b[1].width > page.rect.width * .62 else 1 if b[1].x0 < page.rect.width / 2 else 2, b[1].y0))
                for j, r, t in current:
                    ordered.append({'id': f'{page_id}-b{len(ordered)+1}', 'text': t})
                    used.add(j)
            for j, (r, t) in enumerate(blocks):
                if j not in used:
                    ordered.append({'id': f'{page_id}-b{len(ordered)+1}', 'text': t})
            entry = {'id': page_id, 'source': sid, 'page': pi+1, 'printed': str(printed+pi) if sid != 'acr' or pi < 15 else 'Update cover' if pi == 15 else '700 (erratum)', 'image': f'assets/{page_id}.jpg', 'text': '\n\n'.join(b['text'] for b in ordered), 'blocks': ordered, 'figures': []}
            if sid == 'acr' and pi == 12:
                entry['warning'] = 'The original Figure 9 scoring graphic on this page was superseded by the May 2024 erratum. Use PDF page 17 / Corrected Fig. 9: margin 1 + periosteal reaction 4 + all other features 0 = 5 points, Bone-RADS 3. A soft tissue mass contributes 4 points.'
            for number, caption, cr in captions:
                fid = f'{sid}-fig{number}'
                if sid == 'acr' and pi == 16:
                    fid = 'acr-fig9-corrected'
                elif sid == 'acr' and number == '9':
                    # Preserve original page but the gallery uses the corrected figure.
                    continue
                if any(f['id'] == fid for f in corpus['figures']):
                    # A continued figure gets its own gallery entry, keeping all panels.
                    fid += f'-continued-p{pi+1}'
                # Include every row of a multi-panel figure. Selecting only the
                # closest image to a caption silently drops upper A/B panels.
                barriers = [r.y1 for num, txt, r in captions if r.y1 < cr.y0 and max(0, min(r.x1, cr.x1)-max(r.x0, cr.x0)) / min(r.width, cr.width) > .35]
                lower_limit = max(barriers, default=43)
                eligible = []
                for ir in image_rects:
                    overlap = max(0, min(ir.x1, cr.x1)-max(ir.x0, cr.x0))
                    gap = cr.y0-ir.y1
                    if gap >= -5 and ir.y0 >= lower_limit and overlap / min(ir.width, cr.width) > .35:
                        eligible.append((gap, ir))
                crop = None
                if eligible:
                    for gap, ir in eligible:
                        crop = fitz.Rect(ir) if crop is None else crop | ir
                if crop is None:
                    crop = content_rect
                    fallback = True
                else:
                    crop = (crop + (-3, -3, 3, 3)) & content_rect
                    fallback = False
                render(page, crop, assets / f'{fid}.jpg', 2.4)
                fig = {'id': fid, 'source': sid, 'page': pi+1, 'label': ('Corrected ' if 'corrected' in fid else '') + ('Fig. ' if sid == 'acr' else 'Figure ') + number, 'title': caption.split('. ', 2)[-1].split('.')[0][:100], 'caption': caption, 'image': f'assets/{fid}.jpg', 'contextImage': entry['image'], 'fullPageFallback': fallback}
                if sid == 'acr' and number == '8':
                    continuation = [clean(b[4]) for b in doc[12].get_text('blocks') if b[1] > 670 and b[1] < 725 and 'giving 3 points' in b[4]]
                    fig['caption'] += ' ' + ' '.join(continuation)
                corpus['figures'].append(fig)
                entry['figures'].append(fid)
                crop_audit.append({'id': fid, 'page': pi+1, 'box': list(crop), 'caption': caption, 'fallback': fallback})
            source['pages'].append(entry)
        corpus['sources'].append(source)
        corpus['coverage'][sid] = {'pages': len(source['pages']), 'figures': sum(f['source'] == sid for f in corpus['figures'])}
    rsna_source = {'id': 'rsna', 'title': 'RSNA: Radiographic Evaluation of Bone Tumors', 'url': 'https://pubs.rsna.org/do/10.1148/rg.230048.pres/full/', 'description': 'González-Huete et al., RadioGraphics 2023. Assigned educational exhibit. Each gallery entry preserves the whole slide and all panels, labels and diagrams.', 'pages': []}
    if rsna:
        deck = fitz.open(rsna)
        rsna_source['sha256'] = hashlib.sha256(rsna.read_bytes()).hexdigest()
        for si, slide in enumerate(deck):
            pid = f'rsna-p{si+1}'
            render(slide, slide.rect, assets/f'{pid}.jpg', 1.8)
            texts = [(b[1], b[0], clean(b[4])) for b in slide.get_text('blocks') if clean(b[4])]
            texts.sort()
            paragraphs = [{'id': f'{pid}-b{i+1}', 'text': t} for i, (y,x,t) in enumerate(texts)]
            text = '\n\n'.join(b['text'] for b in paragraphs)
            title = texts[0][2][:150] if texts else f'Slide {si+1}'
            fid = f'rsna-slide{si+1}'
            entry = {'id': pid, 'source': 'rsna', 'page': si+1, 'printed': str(si+1), 'image': f'assets/{pid}.jpg', 'text': text, 'blocks': paragraphs, 'figures': [fid]}
            warnings = {
                6: 'The source age table appears to list chondroblastoma among malignant lesions in older patients. Chondroblastoma is generally benign and favors younger patients; the corresponding common adult cartilage malignancy is chondrosarcoma.',
                16: 'The source describes a well-defined lesion but labels it original Lodwick IC. Describe the border in words and distinguish original IC from modified grade II; do not memorize this caption label as a universal rule.',
                53: 'This source osteoid osteoma case uses IB margin 3 + solid periosteal reaction 2 = 5 points, category 3. ACR also discusses classic recognizable osteoid osteoma as a benign example. Score observed features and distinguish an example from a fixed score for a diagnosis.',
            }
            if si+1 in warnings:
                entry['warning'] = warnings[si+1]
            # Full-slide images retain vector diagrams, captions and grouped panels.
            # Case rehearsal cannot hide labels that are embedded in these slides.
            fig = {'id': fid, 'source': 'rsna', 'page': si+1, 'label': f'Slide {si+1}', 'title': title, 'caption': text, 'image': entry['image'], 'contextImage': entry['image'], 'fullPageFallback': True, 'embeddedLabels': True}
            corpus['figures'].append(fig)
            rsna_source['pages'].append(entry)
        corpus['coverage']['rsna'] = {'pages': len(deck), 'figures': len(deck), 'grouping': 'All panels and diagrams grouped by original slide'}
    else:
        rsna_source['status'] = 'pending'
    corpus['sources'].append(rsna_source)
    corpus['coverageNotes'] = [
        'Complete assigned readings: textbook chapters 2–4, ACR article and Figure 9 correction, and RSNA exhibit.',
        'RSNA atlas entries preserve all panels and diagrams grouped by original slide. Some labels are embedded in the source images.',
        'The ACR report templates are reproduced on RSNA slides 47–48. The e-only DOCX appendices are linked from the original paper, not separately downloaded.',
    ]
    source_order = {s['id']: i for i,s in enumerate(corpus['sources'])}
    corpus['figures'].sort(key=lambda f: (source_order[f['source']], [int(n) for n in re.findall(r'\d+', f['label'])]))
    (output / 'corpus.json').write_text(json.dumps(corpus, ensure_ascii=False), encoding='utf-8')
    (output.parent / 'crop-audit.json').write_text(json.dumps(crop_audit, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(corpus['coverage']))
    print('Total figures:', len(corpus['figures']), 'text blocks:', sum(len(p['blocks']) for s in corpus['sources'] for p in s['pages']))
    # Contact sheets support crop/caption visual QA without opening 139 files.
    for start in range(0, len(corpus['figures']), 30):
        subset = corpus['figures'][start:start+30]
        sheet = Image.new('RGB', (1200, 6*230), '#eee9df')
        draw = ImageDraw.Draw(sheet)
        for i, f in enumerate(subset):
            image = Image.open(output/f['image']); image.thumbnail((230, 192))
            x, y = (i % 5)*240, (i//5)*230
            sheet.paste(image, (x+(240-image.width)//2, y))
            draw.text((x+6, y+196), f['id'], fill='black')
        sheet.save(output.parent/f'figure-qa-{start//30+1}.jpg', quality=90)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--chapters', type=Path, required=True)
    parser.add_argument('--acr', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rsna', type=Path)
    args = parser.parse_args()
    generate(args.chapters, args.acr, args.output, args.rsna)
