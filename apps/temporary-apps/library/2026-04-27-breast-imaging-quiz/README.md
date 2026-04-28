# Breast Imaging Regulatory Quiz Build Notes

This temporary app turns chapter 1 of `Breast Imaging: A Core Review, 2e.epub` into a self-contained HTML quiz.

## Source EPUB

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Books/Breast Imaging_ A Core Review, 2e.epub
```

Do not commit the EPUB or the unpacked `epub_src/` directory. `build_quiz.py` can unpack the EPUB locally when needed.

## EPUB Extraction Notes

Unlike the prior PDF workflow, this EPUB is structured XHTML:

- `META-INF/container.xml` points to `OEBPS/package.opf`.
- `OEBPS/toc.ncx` and `OEBPS/nav.xhtml` identify chapter files.
- Chapter 1 is `OEBPS/ch001.xhtml`.
- Question IDs are in `span.colnum`, including subquestion IDs like `7a`, `7b`, `12a`, and `12b`.
- Questions and answers are separated by headings: `QUESTIONS` and `ANSWERS AND EXPLANATIONS`.
- Question images are regular `<img src="images/...">` elements near the question.
- Explanation-side images and tables may appear in the answer section and should be attached to `explanationImages` or included in explanation text.

The current generator uses `lxml.html` rather than PDF libraries. It walks XHTML siblings, detects question starts by paragraph classes such as `num`, `num1`, `Questbnum`, and `Questbnum1`, and copies referenced EPUB images into `assets/`.

## Special Cases Found

- Question 2 is a matching-style item with no answer-choice `<ol>` in the XHTML. The generator adds fallback choices:
  - `A. BI-RADS 2`
  - `B. BI-RADS 4`
- Many questions have five choices. This is source-faithful for this EPUB and should not be treated as a parser failure.
- Some subquestions are separate quiz entries because the source labels them separately, for example `7a` and `7b`.

## Future EPUB Workflow

1. Unpack the EPUB or let `build_quiz.py` unpack it locally.
2. Read `META-INF/container.xml` to locate the OPF.
3. Read `toc.ncx` or `nav.xhtml` to identify the chapter XHTML file.
4. Parse XHTML structurally with `lxml`, not regex over raw HTML.
5. Use `span.colnum` values as stable question IDs.
6. Preserve subquestion IDs instead of forcing numeric-only IDs.
7. Copy `<img>` assets into the app `assets/` folder.
8. Convert tables into readable text when they are part of a question or explanation.
9. Validate:
   - missing answer keys
   - questions with fewer than two choices
   - questions whose source text says image/table but no image/table was captured
   - subquestions and matching questions with unusual answer format
10. Register the app in `apps/temporary-apps/index.html`.
11. Run:

```powershell
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-04-27-breast-imaging-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
```

## Required UI Behavior

Keep the same behavior as the prior PDF quiz apps:

- night mode by default
- Tutor and Quiz modes
- saved local state with JSON import/export
- collapsible question navigation
- click/tap image lightbox
- one-question-at-a-time review
- `Copy Question Text`
- `Copy Screenshot` rich HTML clipboard pack for Anki-style paste
