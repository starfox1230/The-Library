# Interventional Radiology Fundamentals Quiz Build Notes

This temporary app turns chapter 1 of `Vascular and Interventional Radiology: A Core Review` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Books/IR/1_ Fundamentals of Interventional Radiology.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Extraction Notes

- This is an EBSCO-style PDF export, not the usual separated `QUESTIONS` and `ANSWERS AND EXPLANATIONS` layout.
- Questions and answer explanations appear inline through PDF page 44; the later `ANSWERS AND EXPLANATIONS` section repeats answer text.
- The generator stops when it reaches the repeated answer section.
- Small 32x32/10x16 EBSCO UI icons are filtered out during image extraction.
- Image alignment is explicit by `(page, image)`. Keep using contact sheets because several pages contain companion figures immediately before the next question.
- q15, q26, and q30 required manual image-map cleanup after contact-sheet review.
- q8, q10, q11, and q31 intentionally have three answer choices; q13 intentionally has five.

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
