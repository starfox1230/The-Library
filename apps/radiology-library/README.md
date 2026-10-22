# Radiology Library

A permanent, link-only directory in `The-Library`, outside the temporary-apps area.

[Open the directory](https://starfox1230.github.io/The-Library/apps/radiology-library/index.html) · [Read the full linked inventory and teaching coverage](INVENTORY.md)

Resources can have multiple types and subjects. Expand categories, group by type or subject, search descriptions, or select **Teaches a subject**, **Particularly helpful**, or **My saved links**. Counts represent unique resources; category counts overlap. Individual chapters and modules are included, so the resource count is not an app count.

The catalog contains links and short editorial descriptions. It does not contain copies of the apps, their content banks, study records, or credentials. Existing tools keep their original locations and access settings. Source-only Python/desktop tools are labeled as requiring setup. Private Sites still require the owner's sign-in.

## Inventory basis

Snapshot taken on 2026-10-22:

- Enumerated all 48 accessible GitHub repositories and all eight owned Sites (the Sites list had no next cursor).
- Inspected the complete, non-truncated `The-Library` Git tree (32,018 entries), permanent app page sources, temporary resource titles, and organized Core Review/MRI video quiz paths.
- Inspected relevant standalone repository trees and source files; checked GitHub Pages configuration before choosing public app links. Server apps with no usable static entry link to source.
- Inspected `Learning-App-Hub` tutor sources, the Educational Emporium tree and overlapping radiology paths, plus the AI for Radiology Site source.
- Reviewed published version provenance for Radiology Study OS v89, AI for Radiology v1, Call Exam Studio v8, and Bone Tumor Conference v4. Individual private study records and the complete case inventories were not inspected.
- Grouped previous Core Review routes and Educational Emporium counterparts as alternate links. Redirected neuro/spine image galleries point to their current viewer. Distinct alternate implementations remain separately labeled.
- Read the dynamically loaded neuro/spine and liver outlines, the 42-figure/eight-lesson soft-tissue bank, and the 200-point bone-tumor guide to describe their topic ranges.
- Excluded unrelated family, scripture, finance, gaming, and household projects. General Anki and review tools are included where they support the radiology study workflow.

“Teaches a subject” means a focused lesson, concept explanation, or guided teaching tool. An empty review shell, tracker, or question bank is labeled by its actual function. In particular, `MRI-Physics` is currently a transcript organizer, `Bone-Age` is a report generator, and `Body-CaseStacks` is a progress tracker.

“Particularly helpful” is a reasoned suggestion based on explicit scope, explanatory structure, visual interaction, active recall, or consolidated study routes. It does not claim measured effectiveness, clinical validation, or that every app was run successfully. Subject teaching has its own view; recommended organization and recall tools are also included in the helpful view.

## Maintaining the directory

Edit `catalog.json`, the canonical catalog. Give each creation a stable ID, primary existing URL, specific scope, one or more types/subjects, access/setup status, provenance URL, and evidence note. Use `related` for previous routes or versions. Add `recommendation` only when there is a clear reason, and set `teaches` only for a subject lesson.

Run from the repository root:

```sh
python scripts/build_radiology_library.py
node --check apps/radiology-library/app.js
```

The builder validates links and fields, then regenerates `catalog.js` and `INVENTORY.md`. The browser uses `catalog.js`, so filtering also works when the page is opened locally. Its catalog download produces JSON. Update the date and audit notes after a new inventory pass. This is a snapshot, not an automatic discovery service.

Saved-link stars use only the browser's local storage. URL query parameters preserve the current view, search, subject/type filters, and grouping, so filtered views can be bookmarked.

## Verification

All 243 checked public app and alternate-route entry links returned HTTP 200. This establishes link availability, not full functionality of the original apps. Private Sites retain their access controls; source-only/server tools were not run.

The directory was exercised in Chromium at desktop and mobile sizes, including 320, 390, and 768 pixels wide. Checks covered expandable categories, unique resource counts, subject-teaching and helpful views, combined search/subject/type filters, grouping, saved links across reload, removal and empty states, bookmarkable filter URLs, catalog download, and browser errors. No horizontal overflow or JavaScript errors were observed.
