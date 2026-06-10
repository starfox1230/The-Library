# Interventional Radiology Chapter 5 Quiz

Generated from `G:\My Drive\0. Radiology\Core Review Books\IR\5_ Gastrointestinal.pdf`.

- Chapter: Gastrointestinal.
- Source format: EBSCO-style PDF export with question and answer text interleaved, plus repeated figure captions later in the file.
- Output: 45 scored entries.
- Default answers: empty. User progress is saved locally by the quiz app.

Build notes:

- `build_quiz.py` adapts the prior IR PDF parser for this chapter.
- The parser accepts `Immediately` as a valid question opener; otherwise questions 26 and 29 are missed.
- Four source questions intentionally have three choices: 15, 28, 29, and 32.
- Images are assigned with explicit `(page_index, image_index)` maps. Prompt-side cue-word questions were checked after mapping, and Q5/Q8/Q26 image indices were corrected during audit.
- A per-question contact sheet was used to verify prompt and explanation image alignment before delivery.
