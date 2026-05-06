# Breast Diagnostic Imaging Quiz Build Notes

This temporary app turns chapter 3 of `Breast Imaging: A Core Review, 2e.epub` into a self-contained HTML quiz.

## Source

The browser/EBSCO PDF export for this chapter is capped at 100 pages and stops before the answer explanations. The complete source used here is the local EPUB:

```text
G:/My Drive/0. Radiology/Core Review Books/Breast Imaging_ A Core Review, 2e.epub
```

Chapter 3 is:

```text
OEBPS/ch003.xhtml
```

Do not commit the EPUB or the unpacked `epub_src/` directory. `build_quiz.py` can unpack the EPUB locally when needed.

## Extraction Notes

- The EPUB chapter contains both `QUESTIONS` and `ANSWERS AND EXPLANATIONS`.
- Question IDs are in `span.colnum`.
- This chapter uses `num2` and `Questbnum2` classes for three-digit question IDs, so future parsers must include those classes in addition to `num`, `num1`, `Questbnum`, and `Questbnum1`.
- Subquestion IDs such as `3a`, `3b`, `100a`, and `100b` are preserved as separate scored entries.
- Images are copied from EPUB `<img>` references into `assets/`.
- Explanation-side images are copied into `explanationImages`.

## Special Cases Found

- The source has a matching question at `67`: `Answer 1-B, 2-A, 3-D`. The generator splits this into `67-1`, `67-2`, and `67-3` so each part is independently answerable and scored.
- The source labels the answer for question `100b` as `100c`. Since there is no `100c` question, `build_quiz.py` maps that explanation back to `100b`.
- The generated quiz has 151 scored entries because lettered subquestions and split matching parts are counted separately. This is expected for the module format, even if the source's top-level numbered questions end at 112.

## Future Workflow

1. Prefer the complete EPUB when an EBSCO PDF export is capped or missing answer pages.
2. Use `toc.ncx` or `nav.xhtml` to map the EBSCO section/navPoint to the chapter XHTML file.
3. Parse XHTML structurally with `lxml`, not regex over raw HTML.
4. Preserve source subquestion IDs instead of collapsing them into parent numbers.
5. Split matching-style questions into independent entries when the answer key uses formats like `1-B, 2-A`.
6. Clean obvious extraction problems:
   - add missing spaces where words were spliced together
   - remove random page numbers inserted inside stems or explanations
   - remove repeated headers, footers, copyright notices, and access notices
7. Validate:
   - missing answer keys
   - questions with fewer than two choices
   - questions whose source text says image/table but no image/table was captured
   - subquestions and matching questions with unusual answer format
   - explanation-side figures that need to be included in `explanationImages`
8. Register the app in `apps/temporary-apps/index.html`.
9. Run:

```powershell
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-04-28-breast-diagnostic-imaging-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
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
