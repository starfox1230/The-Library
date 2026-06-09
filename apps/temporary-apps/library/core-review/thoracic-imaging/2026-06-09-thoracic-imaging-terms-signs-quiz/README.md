# Thoracic Imaging: A Core Review Chapter 3 Quiz

Generated from `G:\My Drive\0. Radiology\Thoracic Imaging_ A Core Review.epub`.

- Chapter: Terms and Signs.
- Source XHTML files: `OEBPS/xhtml/Hobbs9781975126223-ch003.xhtml` and `OEBPS/xhtml/Hobbs9781975126223-ch003e.xhtml`.
- Output: 32 scored entries, including lettered subquestions.
- Default answers: empty. User progress is saved locally by the quiz app.

Build notes:

- `build_quiz.py` reads the EPUB directly with Python `zipfile` and parses the chapter XHTML with `lxml`.
- The EPUB could not be fully extracted because of a bad CRC in an unrelated chapter 13 image, so the build reads only chapter 3 XHTML and referenced chapter 3 image assets.
- Images are copied from each question or explanation block's DOM position, preserving the EPUB's question-to-image mapping.
- Two answer-section images are present and are attached as explanation images to Q11b, matching the Hampton hump / pulmonary infarct explanation.
- Some multipart answer explanations are stored by the EPUB only under the final subpart. The generator hydrates short letter-only explanations with the shared related explanation so the quiz does not show only a bare answer letter.
- A per-question contact sheet was used to verify prompt and explanation image alignment before delivery.
