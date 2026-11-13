# Breast Rotation Command Center

Personal study index and flexible preparation plan. Entry point: `index.html`.

Published route: https://starfox1230.github.io/The-Library/apps/core-studying/breast-rotation-command-center/

## Inventory checked November 12, 2026

- Core Radiology chapter 5: 12 registered text sections; local 76-page breast PDF with bookmarked subsections.
- Crack the Core chapter 14: 18 registered text sections and local mammography/MRI/male breast PDF extracts.
- Brant and Helms: registered breast text and local chapter PDF.
- Absolute Breast Imaging Review: complete 451-page local PDF with 12 chapters; seven existing quiz apps contain 360 scored entries. Chapters 8–12 have no organized quiz apps in the audited repository.
- Breast Imaging: A Core Review, 2e: local complete EPUB, five local PDF chapter exports, and apps for chapters 1 and 3 (66 + 151 = 217 entries). The alternate chapter 1 app contains the same 66 entries and is not additional coverage. Chapters 2, 4 and 5 have no organized quiz apps in the audited repository.
- Total: 577 entries across nine distinct chapter banks, 643 including the alternate regulatory version. This counts lettered subquestions separately and does not imply user completion.
- Medality breast catalog: 29 unique courses, deduplicated across modality groupings. Durations and DICOM counts came from the signed-in catalog. Outlines were inspected for screening fundamentals, diagnostic fundamentals, management fundamentals, US biopsy and stereo/tomo biopsy. Playback and account-wide completion were not tested. The inspected current course pages showed a content review date of October 29, 2026; this does not guarantee every lesson uses v2025 terminology.
- Local breast rotation folder also contains audio, BI-RADS review slides/PDF, ACR's v2025 change document, and fibroepithelial lesion/journal club materials. Filenames and availability were inventoried; audio and older presentations were not fully reviewed for completeness or accuracy.

## Source boundaries

`inventory.json` records verified paths, question-bank counts, textbook section links, current PDF outline metadata, and lexical review flags. Full source books and rotation audio remain local/on mounted Google Drive; no new textbook PDFs or EPUBs are added to the site.

The inventory searches the repository, Documents/Downloads/Desktop by relevant radiology filenames, and `G:/My Drive/0. Radiology`, including its breast rotation and Core Review folders. It is not a claim to have searched every disk, cloud account, or course on the internet.

The Core Review diagnostic PDF is a truncated 100-page export. Its existing quiz correctly uses the complete EPUB. The EPUB contains questions, answers and images for the three unbuilt chapters. Prefer that source for future builds. Do not treat a PDF's final page as proof of complete chapter coverage: exports sometimes include the next chapter's opening page.

Absolute chapter ranges on the hub use **1-based PDF viewer pages from the current file outline**, not printed page numbers. For example, chapter 7 begins at viewer page 276 / printed page 269. Some existing quiz READMEs describe printed pages as PDF pages. Locate visible question/answer headings afresh before extracting; do not reuse those ranges blindly. This task did not regenerate, edit or certify the existing quiz banks.

Lexical flags search stems, choices and explanations for a small explicit list of older terms. They are leads for contextual review, not a BI-RADS migration or correctness test. In particular, mammographic margin changes must not be generalized to ultrasound, and the ordinary word “focus” is not always an obsolete lexicon category.

## Study design

The default seven-session plan assumes 30–45 minutes daily because the rotation start date and final schedule were not supplied. The 14-day plan splits each session into learning and retrieval; the weekend plan groups work into three blocks. All modes cover selected core activities rather than complete courses. Individual reading speed and case difficulty may require carrying work into the rotation.

Four on-service tracks support screening, diagnostics, procedures and MRI/cancer workup. Exact clinical technique, medication decisions, follow-up processes and departmental implementation of v2025 remain service-specific learning targets.

## Current public references

The page links directly to ACR's BI-RADS resource page, its free v2025 change PDF and mammography, ultrasound, MRI and CEM summary forms. Those documents were accessed from the official ACR page on the audit date. FDA MQSA information and ACR symptom-workup publications are linked alongside older teaching resources. The full manual's images, FAQs and complete guidance are not reproduced.

## Local behavior and maintenance

- Serve over HTTP(S); JSON fetching does not support opening `index.html` as a `file:` URL.
- Checklist, pace and optional rotation start date use `breast-rotation-prep-v1` in browser localStorage. Export/import JSON moves this progress between browsers. Progress does not sync to Medality, Anki or individual quiz apps.
- Local source paths are copyable because web pages cannot reliably open Windows files. Paste the exact path into File Explorer. Mounted Google Drive must be available.
- To update the inventory, compare the registered book manifests, organized `questions.json` banks and their READMEs, source book TOCs and local files. Refresh `inventory.json` and `courses.json`, update the audit date, and recheck every changed link. Do not infer completion from presence.
- Source changes do not require changes to `books.json`; this app consumes existing registered material and does not add a book corpus.
- Validate with `node --check apps/core-studying/breast-rotation-command-center/app.js`, `python scripts/verify_core_studying_books.py`, local link checks and browser QA.
