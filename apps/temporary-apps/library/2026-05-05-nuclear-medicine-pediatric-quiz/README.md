# Nuclear Medicine Pediatric Nuclear Medicine Quiz Build Notes

This temporary app turns chapter 10 of `Core Review Nuclear Medicine.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Nuclear Medicine.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 10 is split in the source PDF:

- Questions 1a-12: PDF pages 362-371
- Answers 1a-12: PDF pages 371-380
- Questions 13-20: PDF pages 381-384
- Answers 13-20: PDF pages 384-386
- Chapter 11 starts on PDF page 387

The generated module has 22 scored entries because source questions 1 and 9 have lettered subparts.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty for this chapter: `const DEFAULT_SELECTED = {};`.
- q3's reflux image is on PDF page 363, which also contains q1b answer choices and q2 text, so it must be manually mapped to q3.
- q13's answer starts on the same page as q20's stem and choices before the answer section heading; include PDF page 384 in the second answer range.
- Lettered follow-up subparts such as q1b and q9b inherit the parent `a` image when they refer to the same study.

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
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-05-nuclear-medicine-pediatric-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
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
