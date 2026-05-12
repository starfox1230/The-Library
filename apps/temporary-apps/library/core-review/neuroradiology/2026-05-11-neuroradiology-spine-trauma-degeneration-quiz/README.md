# Neuroradiology Spine Trauma and Degeneration Quiz Build Notes

This temporary app turns chapter 9 of `Neuroradiology: A Core Review` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Books/Neuroradiology/9SpineTraumaandDegene_NeuroradiologyACoreRe.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

- Questions: PDF pages 1-14, stopping at `ANSWERS AND EXPLANATIONS`
- Answers: PDF pages 14-38

The generated module has 24 scored entries because source questions 1, 2, 4, 6, 7, 11, 12, and 13 have lettered subparts.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty: `const DEFAULT_SELECTED = {};`.
- The source PDF continues answer-choice lettering across subparts on some pages. The generator normalizes each subquestion back to `A-D` so answer keys from the explanation section match the quiz choices.
- Image alignment uses explicit `(page, image)` mappings. Do not replace this with nearest-question page assignment.
- Before future edits, regenerate a contact sheet of all page images. In this chapter, PDF page 3 extracts q4's MRI before q3's radiograph, and PDF page 5 contains separate images for q6 and q7.
- q6a/q6b and q7a/q7b are adjacent image pairs and are easy to invert. q6 is the bilateral C2 pedicle/Hangman injury and q7 is the C1/Jefferson burst injury; verify both question and answer images against those diagnoses.
- Answer-side figures also use explicit mappings. Check captions against the following answer header; captions often appear immediately before the next answer.

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
