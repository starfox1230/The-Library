# Interventional Radiology Chapter 6 Quiz

Generated from `G:\My Drive\0. Radiology\Core Review Books\IR\6_ Urinary.pdf`.

- Chapter: Urinary.
- Source format: EBSCO-style PDF export with question and answer text interleaved, plus repeated figure captions later in the file.
- Output: 21 scored entries.
- Default answers: empty. User progress is saved locally by the quiz app.

Build notes:

- `build_quiz.py` adapts the prior IR PDF parser for this chapter.
- The parser accepts `This` as a valid question opener so Question 14 is retained.
- Question 5 intentionally has three choices, and Question 21 intentionally has five.
- Images are assigned with explicit `(page_index, image_index)` maps. Repeated answer-section figures are not duplicated when the corresponding inline figure was already extracted.
- A per-question contact sheet was used to verify prompt and explanation image alignment before delivery.
