# Absolute Breast Imaging Review Chapter 7 Quiz

Generated from `G:\My Drive\0. Radiology\Core Review Books\Breast Imaging\Off Brand\Absolute Breast Imaging Review.pdf`.

- Chapter: Pathology.
- Question pages: PDF pages 270-288.
- Answer pages: PDF pages 288-299.
- Output: 45 scored entries, including lettered subquestions.
- Default answers: empty. User progress is saved locally by the quiz app.

Build notes:

- `build_quiz.py` parses question stems, answer choices, answers, and explanations from the PDF text layer, then injects them into the shared quiz template.
- Question and explanation images are assigned with explicit `(page_index, image_index)` maps.
- PDF page 288 is a mixed page containing the end of Question 23 and the beginning of the answer section.
- Answers 2 and 4 use combination-answer formatting without a period after the letter. Question 9b prints only the answer text, which is matched to choice C.
- Questions 10b and 23b intentionally have six choices, and Question 16c intentionally has three.
- PDF page 279 stores the lower Question 15 images before the upper Question 14 image in its extraction order; the explicit map corrects that inversion.
- A per-question contact sheet was used to verify prompt and explanation image alignment before delivery.
