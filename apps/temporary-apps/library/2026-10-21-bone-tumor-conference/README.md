# Bone tumor conference review

October 22, 2026 case-conference preparation, based on the assigned Helms bone tumor chapters, González-Huete et al. RSNA educational exhibit, and Caracciolo et al. ACR Bone-RADS paper.

- [Library entry](https://starfox1230.github.io/The-Library/apps/temporary-apps/library/2026-10-21-bone-tumor-conference/index.html)
- [Private complete reading room](https://bone-tumor-conference-oct22.glut4.chatgpt.site)

The public page contains the interface and 200 original consolidated study points. The complete source reader and figure atlas are hosted in the owner-private reading room. Original textbook pages, publisher slides, and source images are deliberately absent from this public repository.

## Use

Night mode is the default. Use the top-bar Day/Night toggle to switch; the browser remembers the preference separately from study progress.

Check a point to remove it from **To study**. **Show all** and **Completed** bring it back. **Key point / Favorite**, **Review**, and notes are independent of completion. **Your flags** collects saved material and links it back to its context. The source reader separately tracks whole pages and individual passages; checked passages can be hidden. Image captions can be hidden for rehearsal, although text printed inside a source image remains visible.

Annotations stay in localStorage in the current browser and origin. There is no automatic cross-device sync. Export/import transfers progress and keeps the newest saved version of each whole item. Export from both devices before combining concurrent edits. No API keys, external writes, or analytics are used.

## Source coverage

| Source | Reader pages/slides | Atlas entries |
| --- | ---: | ---: |
| Fundamentals of Skeletal Radiology, 6th ed., chapter 2 | 16 | 41 numbered figures |
| Chapter 3 | 25 | 48 numbered figures |
| Chapter 4 | 20 | 40 numbered figures |
| ACR paper plus update cover and May 2024 correction | 17 | 10 numbered figures, using corrected Figure 9 |
| RSNA educational exhibit | 59 | 59 complete slides, retaining grouped panels and diagrams |
| Total | 137 | 198 |

The ACR e-only report DOCX files are linked from the original paper but not downloaded separately. Their report template is reproduced in the assigned RSNA exhibit on slides 47–48 and is available in the reader.

The original ACR Figure 9 remains visible on original source page 13, labeled superseded. The atlas uses the correction on source page 17. RSNA slides 6, 16, and 53 have explanatory source warnings. A few source heuristics are intentionally framed as practical discriminators rather than universal clinical rules. The original case tables are retained for comparison with the narrative ACR definitions.

Chapter 3's supplied PDF ends at printed page 73, although its metadata lists the chapter range as 49–74; whether page 74 is blank was not independently established. The review includes all 25 supplied PDF pages.

## Rebuild private source material

`build_sources.py` accepts local chapter PDFs and the ACR and RSNA PDFs, and writes the **private** `corpus.json` and assets. Requires PyMuPDF and Pillow. The RSNA PDF was rendered from the original 59-slide PPTX using PowerPoint. Do not commit its generated output here.

```powershell
python build_sources.py --chapters 'PATH_TO_CHAPTER_FOLDER' --acr 'ACR.pdf' --rsna 'RSNA.pdf' --output 'PRIVATE_SITE/dist'
python validate.py --private 'PRIVATE_SITE/dist'
```

The generator removes the personally identifying ClinicalKey download footer from reader images and text; source metadata credits Elsevier. Every figure retains a full-page context link. Multi-row panels are grouped using caption boundaries, followed by visual contact-sheet QA. Full original page images remain the authority for tables, reading order, and image relationships.

## Validation

`validate.py` checks source coverage, all figure numbers, local assets, reference targets, unique IDs, the corrected ACR graphic, and exclusion of source assets from the public directory. Browser QA covers check-off hiding, persistence, flags, reader passage hiding, source warnings, image favorites, dialogs, export/import, and desktop/mobile layout.
