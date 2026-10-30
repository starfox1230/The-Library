"""Experimental render/compare benchmark; never a production OCR validator.

Requires developer-only Pillow and NumPy, not additions to Cloud Run requirements.
Rows JSON: {"rows": [{"text": "TEST000001", "bbox": [x0,y0,x1,y1]}]}.
Use verified truth, with full text-cell boxes excluding table borders. Keep real
images, truth, fitted models and output outside Git. Stdout contains aggregates.
Fit on one image; use --model for subsequent images without refitting thresholds.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def ink_crop(gray):
    gray = np.asarray(gray, dtype=float)
    background = max(1, float(np.quantile(gray, .85)))
    ink = np.clip((background-gray)/background, 0, 1)
    y, x = np.nonzero(ink > .45)
    if not len(x):
        raise ValueError('Text cell contains no detectable dark text.')
    return ink[y.min():y.max()+1, x.min():x.max()+1]


@lru_cache(maxsize=32768)
def render(text, font_path, size):
    font = ImageFont.truetype(font_path, size)
    box = font.getbbox(text)
    canvas = Image.new('L', (max(1, box[2]-box[0])+8, box[3]-box[1]+8), 255)
    ImageDraw.Draw(canvas).text((4-box[0], 4-box[1]), text, font=font, fill=0)
    return ink_crop(canvas)


def mismatch(target, text, model):
    template = render(text, model['font'], model['size'])
    width = max(1, round(template.shape[1]*model['x_scale']))
    height = model['height']
    template = np.array(Image.fromarray((template*255).astype('uint8')).resize(
        (width, height), Image.Resampling.BILINEAR), dtype=float)/255
    # A fixed scale preserves the width signal for insertions/deletions. Only
    # small translations are allowed; do not stretch each candidate to fit.
    h = max(target.shape[0], height)+2
    w = max(target.shape[1], width)+2
    source = np.zeros((h, w));source[1:1+target.shape[0], 1:1+target.shape[1]]=target
    best = 1.0
    for dy in range(3):
        for dx in range(3):
            overlay = np.zeros((h, w));overlay[dy:dy+height, dx:dx+width]=template
            # Symmetric: measure both uncovered source ink and excess overlay
            # ink. One-sided coverage could miss an extra or substituted stroke.
            error = np.abs(source-overlay).sum(axis=0)
            union = np.maximum(source, overlay).sum(axis=0)
            score = error.sum()/max(1e-9, union.sum())
            if model.get('metric') == 'local':
                # A wrong digit can be diluted by ten correct characters.
                # Also test the worst glyph-width neighborhood, without
                # requiring character boxes from the primary recognizer.
                kernel = np.ones(6)
                errors = np.convolve(error, kernel, mode='valid')
                unions = np.convolve(union, kernel, mode='valid')
                valid = unions > 2
                local = float(np.max(errors[valid]/unions[valid])) if valid.any() else 0
                score = .5*score+.5*local
            best = min(best, float(score))
    return best


def mutations(text):
    seen = {text}
    for i, char in enumerate(text):
        alphabet = '0123456789' if char.isdigit() else 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        variants = [('substitution', text[:i]+c+text[i+1:]) for c in alphabet if c != char]
        variants += [('deletion', text[:i]+text[i+1:]),
                     ('insertion', text[:i]+char+text[i:])]
        if i+1 < len(text):
            variants.append(('transposition', text[:i]+text[i+1]+char+text[i+2:]))
        for kind, candidate in variants:
            if candidate not in seen:
                seen.add(candidate)
                yield kind, candidate


def evaluate(targets, rows, model):
    correct = [mismatch(a, r['text'], model) for a, r in zip(targets, rows)]
    altered = []
    for target, row in zip(targets, rows):
        altered.extend((kind, mismatch(target, text, model)) for kind, text in mutations(row['text']))
    threshold = model['threshold']
    by_kind = {}
    for kind in sorted(set(k for k, _ in altered)):
        scores = [s for k, s in altered if k == kind]
        by_kind[kind] = {'tested': len(scores), 'detected': sum(s > threshold for s in scores)}
    # Exploratory upper bound for this scalar score if the threshold were
    # retuned on the evaluation data. Never use it as the frozen result.
    c = np.sort(correct);a = np.sort([s for _, s in altered])
    thresholds = np.unique(np.concatenate((c, a)))
    specificity = np.searchsorted(c, thresholds, side='right')/len(c)
    sensitivity = 1-np.searchsorted(a, thresholds, side='right')/len(a)
    best = int(np.argmax(np.minimum(specificity, sensitivity)))
    return {
        'correct_strings': len(correct),
        'correct_accepted': sum(s <= threshold for s in correct),
        'specificity': sum(s <= threshold for s in correct)/len(correct),
        'altered_strings': len(altered),
        'altered_detected': sum(s > threshold for _, s in altered),
        'sensitivity': sum(s > threshold for _, s in altered)/len(altered),
        'by_mutation': by_kind,
        'best_joint_if_retuned_on_this_image': {
            'specificity': float(specificity[best]), 'sensitivity': float(sensitivity[best]),
            'threshold': float(thresholds[best]), 'posthoc_not_a_validation_result': True},
        'score_ranges': {'correct': [min(correct), max(correct)],
                         'altered': [min(s for _, s in altered), max(s for _, s in altered)]},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--rows', type=Path, required=True)
    parser.add_argument('--font', type=Path, action='append')
    parser.add_argument('--model', type=Path, help='Frozen model from a calibration image.')
    parser.add_argument('--model-out', type=Path)
    parser.add_argument('--metric', choices=('global', 'local'), default='global')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    source = Image.open(args.image).convert('L')
    rows = json.loads(args.rows.read_text(encoding='utf-8'))['rows']
    if not rows or any(not isinstance(r['text'], str) or not r['text'] for r in rows):
        raise ValueError('Provide nonempty, manually verified text rows.')
    targets = [ink_crop(source.crop(tuple(map(int, r['bbox'])))) for r in rows]
    if args.model:
        model = json.loads(args.model.read_text(encoding='utf-8'))
    else:
        if not args.font:
            parser.error('Provide --font candidates or a frozen --model.')
        choices = []
        for path in args.font:
            for size in (12, 16, 20):
                glyphs = [render(r['text'], str(path), size) for r in rows]
                model = {'font': str(path), 'size': size, 'metric': args.metric,
                         'height': int(np.median([a.shape[0] for a in targets])),
                         'x_scale': float(np.median([a.shape[1]/g.shape[1] for a, g in zip(targets, glyphs)]))}
                scores = [mismatch(a, r['text'], model) for a, r in zip(targets, rows)]
                choices.append((float(np.mean(scores)), model, scores))
        _, model, scores = min(choices, key=lambda choice: choice[0])
        # Accept all correct calibration rows. This is in-sample calibration,
        # not an independently established specificity or confidence bound.
        model['threshold'] = max(scores)+1e-9
        if args.model_out:
            args.model_out.write_text(json.dumps(model, indent=2), encoding='utf-8')
    metrics = evaluate(targets, rows, model)
    metrics['model_fitted_on_this_image'] = not bool(args.model)
    metrics['interpretation'] = ('Exploratory string-level tests; mutations from one row are correlated. '
                                 'Not clinical validation, independent patient samples, or a general accuracy claim.')
    args.out.write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print(json.dumps(metrics))


if __name__ == '__main__':
    main()
