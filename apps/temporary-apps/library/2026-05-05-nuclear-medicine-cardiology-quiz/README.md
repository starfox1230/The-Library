# Nuclear Medicine Cardiology Quiz Build Notes

This temporary app turns chapter 5 of `Core Review Nuclear Medicine.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Nuclear Medicine.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 5 is split in the source PDF:

- Questions 1-23: PDF pages 184-200
- Answers 1-23: PDF pages 201-218
- Questions 24-31: PDF pages 219-223
- Answers 24-31: PDF pages 223-226
- Chapter 6 starts on PDF page 227

The generated module has 33 scored entries because source questions 8 and 10 are split into `8a`/`8b` and `10a`/`10b`.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty for this chapter: `const DEFAULT_SELECTED = {};`.
- Several pages contain the end of one question and the image for the next question. The generator uses `question_image_targets` for per-image mapping on mixed pages rather than relying on page-level mapping.
- In particular, PDF page 188 has separate images for q10a and q11; PDF page 219 has separate ECG strips for q24 and q25; and PDF page 221 belongs to q27 while q28's raw-data image starts on PDF page 222.
- Question-side and answer-side figures are mapped manually after checking a contact sheet. Do not trust automatic page adjacency for this PDF.

## Future Workflow

1. Inspect PDF page ranges and chapter boundaries first.
2. Generate a question-page contact sheet before finalizing image mappings.
3. Map images by question ID and image index when a page includes multiple unrelated figures.
4. Validate:
   - missing answer keys
   - questions with fewer than four choices, while documenting true source exceptions
   - question stems that reference an image but have no image attached
   - neighboring questions that accidentally received each other's images
   - explanation-side figures that need to be included in `explanationImages`
5. Register the app in `apps/temporary-apps/index.html`.
6. Run:

```powershell
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-05-nuclear-medicine-cardiology-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
```

## Required UI Behavior

Keep the same behavior as the prior quiz apps:

- night mode by default
- Tutor and Quiz modes
- saved local state with JSON import/export
- collapsible question navigation
- click/tap image lightbox
- one-question-at-a-time review
- `Copy Question Text`
- `Copy Screenshot` rich HTML clipboard pack for Anki-style paste
