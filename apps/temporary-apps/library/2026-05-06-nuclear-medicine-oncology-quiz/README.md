# Nuclear Medicine Oncology Quiz Build Notes

This temporary app turns chapter 11 of `Core Review Nuclear Medicine.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Nuclear Medicine.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 11 is split in the source PDF:

- Questions 1-33: PDF pages 387-407
- Answers 1-33: PDF pages 408-426
- Questions 34-37: PDF pages 427-428
- Answers 34-37: PDF pages 428-429
- Chapter 12 starts on PDF page 430

The generated module has 37 scored entries.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty for this chapter: `const DEFAULT_SELECTED = {};`.
- q37's choices and question image are on PDF page 428 before the answer section; keep that page in both the second question range and the second answer range.
- Many oncology figures appear on continuation pages or on pages shared with another question. Keep the explicit image map in `extract_images()` and do not rely only on question-number page starts.
- q33 has three choices in the source text; this is a true source exception rather than an extraction failure.

## Future Workflow

1. Inspect PDF page ranges and chapter boundaries first.
2. Generate a question-page contact sheet before finalizing image mappings.
3. Check pages that contain answer choices for one question and the stem for a later question.
4. Validate:
   - missing answer keys, especially when answers start on a mixed question/answer page
   - lettered subparts that should share parent images
   - questions with fewer than four choices, while documenting true source exceptions
   - question stems that reference an image but have no image attached
   - explanation-side figures that need to be included in `explanationImages`
5. Register the app in `apps/temporary-apps/index.html`.
6. Run:

```powershell
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-06-nuclear-medicine-oncology-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
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
