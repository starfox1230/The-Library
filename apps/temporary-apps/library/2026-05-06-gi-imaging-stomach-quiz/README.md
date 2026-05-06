# Gastrointestinal Imaging Stomach Quiz Build Notes

This temporary app turns chapter 2 of `Core Review - Gastrointestinal Imaging .pdf` into a self-contained HTML quiz.

## Source PDF

```text
G:/My Drive/0. Radiology/Core Review - Gastrointestinal Imaging .pdf
```

## Page Ranges

- Questions 1-26: PDF pages 113-155
- Answers 1-26: PDF pages 156-180
- Questions 27-29: PDF pages 181-184
- Answers 27-29: PDF pages 185-187
- Chapter 3 starts on PDF page 188

The generated module has 39 scored entries because q12 and q13 are matching questions split into four single-answer subquestions each.

## Extraction Notes

- Images are converted to browser-safe JPG during extraction because this PDF may expose JPEG 2000 assets.
- Default answers are intentionally empty: `const DEFAULT_SELECTED = {};`.
- q12 is split into `12a` through `12d` for Patients 1-4.
- q13 is split into `13a` through `13d` for Examples 1-4.
- q29 has three answer choices in the source text.
