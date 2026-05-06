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
- Default answers are seeded from the highlighted choices in the source PDF for this chapter.
- q2 and q32 have answer choices embedded as figure panels, so the generator supplies generic `Case A-E` and `Case A-D` options.
- q34b is a matching anatomy-label question. The generator splits it into `34bA` through `34bH`, sharing the source images and using the numbered anatomy labels as answer choices.
- Image alignment was manually mapped because image pages frequently sit between the stem and choices.
- For future GI chapters, do not rely on nearest-question page adjacency. Generate a contact sheet of all extracted question images, then compare every image-bearing PDF page against the page's text flow. If a page contains answer choices for one question and a new stem below, decide whether the image belongs to the previous stem, the current choices, or the next stem. Use per-image overrides when one PDF page contains unrelated figures.
- After rebuilding, print every question number with its image paths and skim for shifted filenames, especially around multi-page cases, lettered subparts, and pages where figures sit above answer choices. Also verify that subparts sharing a stem inherit the correct parent image and that explanation-side figures remain in `explanationImages`.

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
