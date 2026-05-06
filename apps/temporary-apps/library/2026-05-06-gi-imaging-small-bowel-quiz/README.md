# Gastrointestinal Imaging Small Bowel Quiz Build Notes

This temporary app turns chapter 3 of `Core Review - Gastrointestinal Imaging .pdf` into a self-contained HTML quiz.

## Source PDF

```text
G:/My Drive/0. Radiology/Core Review - Gastrointestinal Imaging .pdf
```

## Page Ranges

- Questions 1-37: PDF pages 188-238
- Answers 1-37: PDF pages 239-276
- Questions 38-48: PDF pages 277-285
- Answers 38-48: PDF pages 285-291
- Chapter 4 starts on PDF page 292

The generated module has 75 scored entries because several questions have lettered subparts and matching prompts are split into single-answer subquestions.

## Extraction Notes

- Images are converted to browser-safe JPG during extraction.
- Default answers are intentionally empty: `const DEFAULT_SELECTED = {};`.
- q1 is a seven-patient matching prompt split into `1a` through `1g`.
- q14 is a four-defect matching prompt split into `14a` through `14d`.
- q46 is a four-patient imaging-choice matching prompt split into `46a` through `46d`.
- q48 is an extended matching prompt split into `48a` through `48d`.
- q19 is a figure/case-set question with source option C embedded in the supplied images; the generator supplies a generic Case C option.
- q44 and q45 share a PDF page with two unrelated images and require per-image mapping.
