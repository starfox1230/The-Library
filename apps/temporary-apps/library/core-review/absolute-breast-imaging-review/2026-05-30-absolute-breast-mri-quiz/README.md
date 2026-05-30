# Absolute Breast Imaging Review Chapter 5 Quiz

Generated from `G:\My Drive\0. Radiology\Core Review Books\Breast Imaging\Off Brand\Absolute Breast Imaging Review.pdf`.

- Chapter: Breast MRI.
- Question pages: PDF pages 202-225.
- Answer pages: PDF pages 226-247.
- Output: 50 scored entries, including lettered subquestions.
- Default answers: empty. User progress is saved locally by the quiz app.

Build notes:

- `build_quiz.py` parses question stems, answer choices, answers, and explanations from the PDF text layer, then injects them into the shared quiz template.
- Question and explanation images are assigned with explicit `(page_index, image_index)` maps. This chapter has many pages with two unrelated figures, so image-level mapping is required.
- Parser cleanup handles the line break in question 27 where `age 16` can be misread as a duplicate question 16.
- Answer 20b is printed in the source answer key without a visible answer-letter prefix; it is normalized to answer `B` (`Inflamed cyst`) in the generator.
- A per-question contact sheet was used to verify prompt and explanation image alignment before delivery.
