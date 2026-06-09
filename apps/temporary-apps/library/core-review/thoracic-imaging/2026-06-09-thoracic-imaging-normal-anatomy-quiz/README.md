# Thoracic Imaging: A Core Review Chapter 2 Quiz

Generated from `G:\My Drive\0. Radiology\Thoracic Imaging_ A Core Review.epub`.

- Chapter: Normal Anatomy.
- Source XHTML files: `OEBPS/xhtml/Hobbs9781975126223-ch002.xhtml` and `OEBPS/xhtml/Hobbs9781975126223-ch002e.xhtml`.
- Output: 33 scored entries, including lettered subquestions.
- Default answers: empty. User progress is saved locally by the quiz app.

Build notes:

- `build_quiz.py` reads the EPUB directly with Python `zipfile` and parses the chapter XHTML with `lxml`.
- The EPUB could not be fully extracted because of a bad CRC in an unrelated chapter 13 image, so the build reads only chapter 2 XHTML and referenced chapter 2 image assets.
- Images are copied from each question block's DOM position, preserving the EPUB's question-to-image mapping.
- The chapter has no separate explanation-side images in the answer blocks; all extracted images are prompt-side.
- Some multipart answer explanations are stored by the EPUB only under the final subpart. The generator hydrates short letter-only explanations with the shared related explanation so the quiz does not show only `b.` or `c.`.
- A per-question contact sheet was used to verify prompt image alignment before delivery.
