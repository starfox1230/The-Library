# Brain CT search-pattern game

A quiet CT viewer with 70 case-specific checkpoints across ten phases adapted from Andrew Dixon's [brain CT search-pattern lecture](https://www.youtube.com/watch?v=u3NPBiYDqwA&t=120s). Includes one public-domain, source-reported negative adult CT with separate brain and bone reconstructions, genuine HU windowing, axial/sagittal/coronal reformats, practice hints, timed runs and local personal bests.

## Run

From the repository root:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765/apps/search-pattern/brain-ct-game/ in a current Chromium browser. No build, account, backend or external runtime dependencies. Serve over localhost or HTTPS (Web Crypto requires a secure context). The first load downloads about 32 MB and expands two signed 16-bit volumes in memory.

## Play

Choose Practice or Timed and press Start. Scroll through the image, then click the current phase's anatomical checkpoints. Both sides must be checked. The next phase opens automatically. Practice offers Show hint and Locate for the selected checkpoint. Timed mode hides hints; pausing or leaving the tab changes that attempt to practice. Restart returns to ready.

- A / S / C: planes; arrow keys and slice slider: slices.
- Brain / Subdural / Bone: window presets; W/L fields or right-drag: custom windowing.
- View: zoom, three planes, crosshairs, reset. Middle-drag pans; Shift-click recentres without scoring.
- Checklist collapses to maximize the scan. Touch users can tap and use the sliders and numeric fields.

## Case and annotation limitations

The [PCIR catalog](https://www.pcir.org/researchers/54879843_20060101.html) records the result as “None”; this is not an independent clinical normality certification. Checkpoint regions received author visual review, not clinical expert validation. They are selected landmark patches and short slice intervals, not complete organ segmentations. Correct anatomy outside a patch may not score. Start with practice to learn the accepted regions. The scan includes the superior maxillary sinuses, not their full inferior extent. See [attribution](cases/normal-head/ATTRIBUTION.md), [case review](qa/case-review.md) and [checkpoint review](qa/checkpoint-review.md).

## Validation and editing

From this directory:

```powershell
node --test tests/*.test.mjs
$env:PYTHONPATH = (Get-Location).Path
python -m unittest discover -s tests -p test_prepare_case.py
python tools/author_checkpoints.py
python tools/render_checkpoint_qa.py
```

Preparation dependencies are pinned in `requirements-data.txt`; none are needed by the browser. `tools/prepare_case.py` reads DICOM series, applies rescale slope/intercept, normalizes physical orientation and writes X-fastest signed 16-bit HU. Original identifiers and archives are not distributed. Keep the source acquisition and conversion provenance in the case review.

After editing annotations, inspect all changed outlines and slice endpoints, update the checkpoint version in both manifests and checkpoints, rerun the tests and a practice run. Scores are isolated by case and checkpoint version. Clinical review should precede use as an assessment tool. This app records clicks, not completeness of diagnostic interpretation.
