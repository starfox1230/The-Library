# Ultrasound Vascular Quiz Build Notes

This temporary app turns chapter 9 of `Core Review Ultrasound reattempt.pdf` into a self-contained HTML quiz.

## Source PDF

```text
G:/My Drive/0. Radiology/Core Review Ultrasound reattempt.pdf
```

## Page Ranges

- Questions 1-54: PDF pages 432-486
- Answers 1-54: PDF pages 486-514
- Chapter 10 starts on PDF page 515

The generated module has 63 scored entries because several questions have lettered subparts.

## Extraction Notes

- Images are converted to browser-safe JPG during extraction.
- Default answers are intentionally empty: `const DEFAULT_SELECTED = {};`.
- q13 has three answer choices in the source text.
- Subparts without separate figures inherit the parent figure when they ask follow-up management, artifact, or interpretation questions for the same case.
- q54's question image is on the same PDF page where the answers begin, so that page must remain in both the question and answer ranges.
