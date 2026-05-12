# Neuroradiology Spine Infection, Inflammation, and Demyelination Quiz Build Notes

This temporary app turns chapter 10 of `Neuroradiology: A Core Review` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Books/Neuroradiology/10SpineInfectionInfla_NeuroradiologyACoreRe.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

- Questions: PDF pages 1-18, stopping at `ANSWERS AND EXPLANATIONS`
- Answers: PDF pages 18-41

The generated module has 28 scored entries because source questions 1 through 13 have lettered subparts, while questions 14 and 15 are single-answer questions.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty: `const DEFAULT_SELECTED = {};`.
- The source PDF sometimes places the image above the question text that follows in text extraction. Image mapping is explicit by `(page, image)` and should be checked against a contact sheet before future edits.
- q1 and q2 both have transition sentences after the first subpart's option D that introduce the next MRI image. Keep those transition sentences with q1b/q2b, not inside q1a/q2a answer choices.
- Bare subpart headings such as `5b` are handled as question starts, with the next extracted line becoming the stem.
- Answer-side figures also use explicit mappings. Check captions against neighboring answer headers because captions can appear before the next answer begins.

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
