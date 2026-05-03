# Nuclear Medicine Endocrine System Quiz Build Notes

This temporary app turns chapter 2 of `Core Review Nuclear Medicine.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Nuclear Medicine.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 2 is split in the source PDF:

- Questions 1-36: PDF pages 32-51
- Answers 1-36: PDF pages 52-73
- Questions 37-50: PDF pages 74-80
- Answers 37-50: PDF pages 80-84
- Chapter 3 starts on PDF page 85

The source includes lettered subquestions `7a`, `7b`, `34a`, and `34b`, so the generated module has 52 scored entries.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default text extraction merges stems into answer choices because the PDF prints question numbers in a left column and content in a right column.
- Preserve lettered source IDs rather than renumbering them.
- Questions 5 and 46 use image/diagram answer choices. The generator assigns generic `Image A` through `Image D` choices when no text choices are present.
- Question 25's answer label is split across two layout lines in the source; the generator patches that answer from the surrounding page text.
- Image extraction uses `pypdf` page images and manually checked page-to-question maps.

## Future Workflow

1. Inspect the PDF page ranges and chapter boundaries first.
2. Try layout-mode extraction before writing custom text heuristics.
3. Preserve source subquestion IDs.
4. Validate:
   - missing answer keys
   - questions with fewer than two choices
   - image-choice questions that need generic `Image A/B/C/D` options
   - questions whose source text says image/table but no image/table was captured
   - explanation-side figures that need to be included in `explanationImages`
5. Register the app in `apps/temporary-apps/index.html`.
6. Run:

```powershell
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-03-nuclear-medicine-endocrine-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
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
