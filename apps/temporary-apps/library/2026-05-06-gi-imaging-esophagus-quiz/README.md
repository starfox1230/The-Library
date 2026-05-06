# Gastrointestinal Imaging Pharynx and Esophagus Quiz Build Notes

This temporary app turns chapter 1 of `Core Review - Gastrointestinal Imaging .pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review - Gastrointestinal Imaging .pdf
```

Do not commit the PDF.

## Page Ranges

- Questions 1-29: PDF pages 11-55
- Answers 1-29: PDF pages 56-93
- Questions 30-35: PDF pages 94-109
- Answers 30-35: PDF pages 109-112

The generated module has 52 scored entries because several source questions have lettered subparts, and matching question 34b is split into eight single-answer subquestions.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty: `const DEFAULT_SELECTED = {};`.
- q2 and q32 have answer choices embedded as figure panels, so the generator supplies generic `Case A-E` and `Case A-D` options.
- q34b is a matching anatomy-label question. The generator splits it into `34bA` through `34bH`, sharing the source images and using the numbered anatomy labels as answer choices.
- Image alignment was manually mapped because image pages frequently sit between the stem and choices.

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
