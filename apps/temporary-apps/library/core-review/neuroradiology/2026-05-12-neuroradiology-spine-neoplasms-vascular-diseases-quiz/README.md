# Neuroradiology Spine Neoplasms and Vascular Diseases Quiz Build Notes

This temporary app turns chapter 11 of `Neuroradiology: A Core Review` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Books/Neuroradiology/11SpineNeoplasmsSpine_NeuroradiologyACoreRe.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

- Questions: PDF pages 1-25, stopping at `ANSWERS AND EXPLANATIONS`
- Answers: PDF pages 25-59

The generated module has 35 scored entries because many source questions have lettered subparts, including q10a-c and q19a-b.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty: `const DEFAULT_SELECTED = {};`.
- Image alignment is explicit by `(page, image)`. Do not replace it with nearest-question assignment.
- q19 has several image-only pages before its answer choices; all q19 images are shared by q19a and q19b.
- q2 is text-only and intentionally has no question image.
- q3 has a transition sentence after q3a option D (`An MRI with contrast was performed...`) that belongs with q3b, not q3a's answer choices. Keep the explicit cleanup in `normalize_options`.
- Answer-side figures are also explicitly mapped. Keep checking captions against neighboring answer headers because explanation images frequently appear on pages after the answer text begins.

## Required UI Behavior

Keep the same behavior as the prior quiz apps:

- night mode by default
- Tutor and Quiz modes
- saved local state with JSON import/export
- collapsible question navigation
- click/tap image lightbox
- one-question-at-a-time review
- `Copy Question Text`
- `Copy Screenshot` rich HTML clipboard pack for Anki-style paste
