# Hand Arthropathy Distribution Lab

Interactive select-all-that-apply quiz built from the six user-supplied labeled hand-distribution diagrams on [Radiopaedia](https://radiopaedia.org/cases/hand-arthropathies-distribution-diagram-1#image-49954625).

## Build

```powershell
python build_assets.py
python build_quiz.py
```

`build_assets.py` creates `assets/blank-hand.png` by recovering unannotated grayscale pixels across the six variants and emits one transparent blue overlay per target region. `questions.json` is the authored bank; `_template.html` contains the renderer.

## Scope note

The answer key is intentionally diagram-specific. It teaches the distribution relationships shown in the supplied source image and is not a complete clinical differential or diagnostic decision aid. Original labeled images remain in `assets/` for provenance, with attribution linked in the app.
