# Nuclear Medicine Head and Neck Quiz Build Notes

This temporary app turns chapter 4 of `Core Review Nuclear Medicine.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Nuclear Medicine.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 4 is split in the source PDF:

- Questions 1-15: PDF pages 153-164
- Answers 1-15: PDF pages 164-173
- Questions 16-24: PDF pages 174-179
- Answers 16-24: PDF pages 180-183
- Chapter 5 starts on PDF page 184

The generated module has 25 scored entries because source question 9 is split into `9a` and `9b`.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty for this chapter: `const DEFAULT_SELECTED = {};`.
- Question 23 has three answer choices in the source PDF. This is an expected exception, not a parser failure.
- PDF page 158 contains two different question images. The first image belongs to q8 and the second image belongs to q9a, so the generator uses an image-specific split map instead of page-level mapping for that page.
- Question-side and answer-side figures are mapped manually after checking a contact sheet. Do not trust automatic page adjacency for this PDF.

## Future Workflow

1. Inspect PDF page ranges and chapter boundaries first.
2. Generate a question-page contact sheet before finalizing image mappings.
3. Map images by question ID, not just by nearby page. If a single page has multiple unrelated images, add per-image overrides like the q8/q9a split in this generator.
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
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-05-nuclear-medicine-head-neck-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
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
