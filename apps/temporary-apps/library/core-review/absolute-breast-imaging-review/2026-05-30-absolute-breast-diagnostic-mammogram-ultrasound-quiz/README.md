# Absolute Breast Imaging Review Chapter 4 Quiz

Generated from `G:\My Drive\0. Radiology\Core Review Books\Breast Imaging\Off Brand\Absolute Breast Imaging Review.pdf`.

- Chapter: Diagnostic Mammogram and Ultrasound.
- Question pages: PDF pages 131-168.
- Answer pages: PDF pages 168-198.
- Output: 81 scored entries, including lettered subquestions through question 33.
- Default answers: empty. User progress is saved locally by the quiz app.

Build notes:

- `build_quiz.py` parses question stems, answer choices, answers, and explanations from the PDF text layer, then injects them into the shared quiz template.
- Question and explanation images are assigned with explicit page/image maps. Do not rely on page proximity alone for this chapter because some question figures and answer figures share the same PDF page.
- A per-question contact sheet was used to audit image alignment. Two high-risk corrections were made during review: the PDF page 147 ultrasound belongs to question 14a-c rather than question 13d, and the PDF page 168 circled mammogram image belongs to answer explanation 1a rather than question 33.
- Text cleanup includes dehyphenation and correction of the observed OCR artifact `t1his` to `this`.
