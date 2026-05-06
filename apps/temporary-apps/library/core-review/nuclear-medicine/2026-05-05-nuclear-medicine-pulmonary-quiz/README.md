# Nuclear Medicine Pulmonary System Quiz Build Notes

This temporary app turns chapter 7 of `Core Review Nuclear Medicine.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Nuclear Medicine.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 7 is contained in one question section:

- Questions 1-22: PDF pages 246-263
- Answers 1-22: PDF pages 263-280
- Chapter 8 starts on PDF page 281

The generated module has 22 scored entries.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty for this chapter: `const DEFAULT_SELECTED = {};`.
- PDF page 247 is a mixed page: it contains answer choices for q4 and the stem for q5. The image belongs to q4, not q5.
- PDF page 248 contains q5's image and answer choices before q6 starts.
- q12 uses both the V/Q image and the chest radiograph from the following page.
- Explanation-side figures were extracted for questions 2, 4, 5, 6, 9, 10, 11, 13, 15, 16, 18, and 19.

## Future Workflow

1. Inspect PDF page ranges and chapter boundaries first.
2. Generate a question-page contact sheet before finalizing image mappings.
3. Map mixed pages manually when a page has prior answer choices above a new question stem.
4. Validate:
   - missing answer keys
   - questions with fewer than four choices, while documenting true source exceptions
   - question stems that reference an image but have no image attached
   - questions that require multiple related images across adjacent pages
   - explanation-side figures that need to be included in `explanationImages`
5. Register the app in `apps/temporary-apps/index.html`.
6. Run:

```powershell
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-05-nuclear-medicine-pulmonary-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
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
