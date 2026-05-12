# Neuroradiology Congenital and Developmental Spine Quiz Build Notes

This temporary app turns chapter 12 of `Neuroradiology: A Core Review` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Books/Neuroradiology/12CongenitalandDevelo_NeuroradiologyACoreRe.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

- Questions: PDF pages 1-11, stopping at `ANSWERS AND EXPLANATIONS`
- Answers: PDF pages 11-25

The generated module has 13 scored entries: `1a`, `1b`, `2a`, `2b`, `3a`, `3b`, `4a`, `4b`, and questions 5-9.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty: `const DEFAULT_SELECTED = {};`.
- Image alignment is explicit by `(page, image)`. Do not replace it with nearest-question assignment.
- Several lettered subparts share a source image: q2a/q2b and q4a/q4b.
- q3a and q3b use separate patient images on consecutive pages.
- Answer-side figures are explicitly mapped. Check captions and neighboring answer headers before accepting the mapping, because explanation figures often appear after the answer text starts.

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
