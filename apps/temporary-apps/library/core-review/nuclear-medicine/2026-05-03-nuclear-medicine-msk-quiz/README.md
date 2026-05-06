# Nuclear Medicine Musculoskeletal System Quiz Build Notes

This temporary app turns chapter 3 of `Core Review Nuclear Medicine.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Nuclear Medicine.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 3 is split in the source PDF:

- Questions 1-27: PDF pages 85-114
- Answers 1-27: PDF pages 114-133
- Questions 28-45: PDF pages 134-144
- Answers 28-45: PDF pages 144-152
- Chapter 4 starts on PDF page 153

The generated module has 45 scored entries.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default text extraction merges stems and choices because this PDF prints question numbers in a left column.
- Page 144 contains question 45's answer choices and then the second answer section; the parser stops question parsing when it sees `ANSWERS AND EXPLANATIONS`.
- Question 15's answer label is split across layout lines in the source; the generator patches that answer from the surrounding page text.
- Question 42 is an image-choice question without text choices, so the generator assigns generic `Image A` through `Image D` choices.
- Image extraction uses `pypdf` page images and manually checked page-to-question maps.

## Future Workflow

1. Inspect PDF page ranges and chapter boundaries first.
2. Prefer layout-mode extraction before custom text heuristics.
3. Preserve source question IDs.
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
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-03-nuclear-medicine-msk-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
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
