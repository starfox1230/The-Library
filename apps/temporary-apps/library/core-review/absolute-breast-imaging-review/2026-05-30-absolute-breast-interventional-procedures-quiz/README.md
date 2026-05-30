# Absolute Breast Imaging Review Chapter 6 Quiz

Generated from `G:\My Drive\0. Radiology\Core Review Books\Breast Imaging\Off Brand\Absolute Breast Imaging Review.pdf`.

- Chapter: Interventional Procedures.
- Question pages: PDF pages 249-265.
- Answer pages: PDF pages 265-276.
- Output: 29 scored entries, including lettered subquestions.
- Default answers: empty. User progress is saved locally by the quiz app.

Build notes:

- `build_quiz.py` parses question stems, answer choices, answers, and explanations from the PDF text layer, then injects them into the shared quiz template.
- Question and explanation images are assigned with explicit `(page_index, image_index)` maps.
- PDF page 265 is a mixed page: it contains question 12a/12b and then the answer section begins. The ultrasound image on that page is mapped to question 12a/12b, not to the answer explanation.
- Parser cleanup corrects observed OCR artifacts including `targete.d` and `imageguided`.
- A per-question contact sheet was used to verify prompt and explanation image alignment before delivery.
