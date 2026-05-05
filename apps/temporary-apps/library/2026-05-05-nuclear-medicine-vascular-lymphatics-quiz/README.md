# Nuclear Medicine Vascular and Lymphatics Quiz Build Notes

This temporary app turns chapter 6 of `Core Review Nuclear Medicine.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Nuclear Medicine.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 6 is contained in one short question section:

- Questions 1-20: PDF pages 227-236
- Answers 1-20: PDF pages 236-245
- Chapter 7 starts on PDF page 246

The generated module has 20 scored entries.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty for this chapter: `const DEFAULT_SELECTED = {};`.
- The text line `99m sulfur colloid...` in q2 can be falsely detected as a question ID unless the parser restricts lettered question suffixes to `a`/`b`.
- Question 5 is an image-choice/site-selection question. The source choices are embedded in the diagram, so the generator assigns generic `Site A` through `Site D` choices.
- The question-side image map was manually checked with a contact sheet:
  - q1: PDF page 227
  - q5: PDF page 228
  - q6: PDF page 229
  - q8: PDF page 230
  - q9: PDF page 231
  - q10: PDF page 232
  - q11: PDF page 233
  - q14: PDF page 234
  - q15: PDF page 235

## Future Workflow

1. Inspect PDF page ranges and chapter boundaries first.
2. Generate a question-page contact sheet before finalizing image mappings.
3. Watch for radiotracer names like `99m` being misread as question numbers.
4. Validate:
   - missing answer keys
   - questions with fewer than four choices, while documenting true source exceptions
   - image-choice questions requiring generic `Image` or `Site` options
   - question stems that reference an image but have no image attached
   - explanation-side figures that need to be included in `explanationImages`
5. Register the app in `apps/temporary-apps/index.html`.
6. Run:

```powershell
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-05-nuclear-medicine-vascular-lymphatics-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
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
