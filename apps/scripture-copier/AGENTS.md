# Scripture Copier App Instructions

These instructions apply to work in `apps/scripture-copier/`, especially when creating the next General Conference tracker app.

## When asked to create a new General Conference tracker

Create a new, separate HTML tracker in this folder by copying the most recent conference tracker and updating it for the new session. Keep the old tracker intact.

Use this naming pattern:

- HTML file: `general_conference_<season>_<year>.html`
- Transcript folder: `GC_Transcripts_<Season>_<Year>/`
- State key: `gc:<season-abbrev>-<year>:state`
- Conference id: `<season-abbrev>-<year>`

Example:

- `general_conference_april_2026.html`
- `GC_Transcripts_April_2026/`
- `gc:apr-2026:state`
- `apr-2026`

## Required app updates

When creating the new tracker, update all of the following:

1. Add the new tracker link to `apps/scripture-copier/index.html`.
2. Add the new tracker card to the root `index.html`.
3. Add the new tracker file to `apps/scripture-copier/folder_structure2.txt`.
4. Create the new transcript folder and transcript files.
5. Update the new tracker's talk list, transcript paths, storage key, conference id, backup filename, and notes filename.

## User preferences to preserve

These are user-specific preferences learned during the April 2026 build and should be treated as defaults unless the user says otherwise:

- Use YouTube links specifically.
- Prefer official individual YouTube talk links from the General Conference channel.
- The user prefers removing non-talk administrative items from the tracker lineup:
  - Solemn Assembly
  - Sustaining of Church officers / general authorities
  - Church Auditing Department Report
- Keep `D. Todd Christofferson` included in the `First Presidency` filter for this app.
- Keep the `Need / All / Seen / Favs` row and the `Filters` dropdown sticky at the top while scrolling.
- Keep a working `Settings` button that offers a link to the local conference summary PDF.
- Keep a `Sum` button for each talk that shows the word-for-word summary from the conference PDF.
- Keep the transcript copy button as a copy symbol and the notes button as a note symbol.
- Unchecking a watched talk must decrease the watch count by 1.

## Transcript source workflow

For talk transcripts:

- Use the official Church General Conference talk pages.
- Read the response stream as UTF-8. Plain `Invoke-WebRequest ... .Content` was not reliable enough for some pages.
- Save each transcript as a plain text file in the new transcript folder.

Important lessons:

- PowerShell URL interpolation for talk slugs needs `$($slug)` inside strings. Without that, some URLs were built incorrectly.
- Reading `RawContentStream` with a UTF-8 `StreamReader` worked better than relying on default decoding.

## Summary PDF workflow

If the user wants summaries from a local General Conference PDF:

1. Look for a PDF in the conference transcript folder, for example:
   - `GC_Transcripts_April_2026/April2026GeneralConferenceEnglishPDFs.pdf`
2. Create a JSON summary file in the same folder, for example:
   - `GC_Transcripts_April_2026/April2026GeneralConferenceSummaries.json`
3. Wire the tracker to load that JSON and show each talk's summary through the `Sum` button.

### What worked

- Ghostscript is available locally and worked for PDF text extraction.
- This command worked to extract page text files:

```powershell
& 'C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe' -q -sDEVICE=txtwrite -o '...\pdftxt-%03d.txt' '...\April2026GeneralConferenceEnglishPDFs.pdf'
```

- The PDF text had to be reconstructed by columns.
- The best parse approach was:
  1. Find column ranges by scanning each line for non-space runs.
  2. Slice each page text into columns.
  3. Detect speaker blocks using the known speaker list from the tracker.
  4. Deduplicate repeated speaker blocks because some extracted page files overlapped.
  5. Map repeated speakers like `Dallin H. Oaks` by occurrence order in the current talk list.

### What did not work well

- `pypdf` was not installed.
- `PyPDF2` was not installed.
- Simple raw text extraction without column parsing produced mixed-together summaries.
- Some Ghostscript text output created duplicate blocks from spread pages.
- PowerShell `Get-Content` could display UTF-8 summary JSON as mojibake even when the file itself was fine. Verify with Python if unsure.

### Summary cleanup notes

The extracted PDF text may contain:

- ligature characters such as `fi`, `fl`, `ff`, `ffi`, `ffl`
- line-wrap hyphenation artifacts
- duplicated spread-page content

When generating the summary JSON:

- preserve the actual wording from the PDF
- clean obvious line-wrap artifacts only as needed
- verify the number of summary entries matches the number of tracker talks

Keep the PDF and final summary JSON. Treat intermediate extraction files like these as temporary:

- `April2026GeneralConferenceEnglishPDFs.txt`
- `pdftxt-001.txt`, `pdftxt-002.txt`, etc.

## Encoding and file-editing lessons

Very important:

- Do not rewrite emoji-heavy HTML files with broad PowerShell text rewrites such as `Set-Content` or `[System.IO.File]::WriteAllText(...)` after loading the file as decoded text. That caused mojibake in `index.html` and in tracker button labels.
- Use `apply_patch` for HTML edits.
- If a file must be restored exactly from `HEAD`, do it in a byte-safe UTF-8 way and then apply a minimal patch.

For the root `index.html` specifically:

- only add the new conference card with a minimal patch
- avoid any full-file rewrite

## UI features that should remain in the conference tracker

Keep these behaviors when cloning the next tracker:

- progress bar
- next-up card
- `Need / All / Seen / Favs`
- collapsible category filters
- sticky filter controls
- transcript copy button
- notes button and modal
- summary button and modal
- settings modal with local PDF link
- backup / restore / notes export controls
- YouTube app deep-link behavior
- watched-count pill with working plus, minus, and manual edit

## Verification checklist

Before finishing the next conference tracker:

1. Confirm the new HTML file exists in `apps/scripture-copier/`.
2. Confirm the new tracker is linked from:
   - `apps/scripture-copier/index.html`
   - root `index.html`
   - `apps/scripture-copier/folder_structure2.txt`
3. Confirm all talks use the intended YouTube links.
4. Confirm transcript file count matches the talk count.
5. If summaries are included, confirm summary JSON entry count matches the talk count.
6. Confirm `node --check` passes for the new tracker script.
7. Confirm the `Settings` button opens a PDF option.
8. Confirm the `Sum` button opens the correct summary.
9. Confirm unchecking a talk reduces the watch count by 1.
10. Confirm sticky filters stay at the top while scrolling.

## Practical command notes

Useful checks:

```powershell
rg -n "youtubeUrl:|transcriptPath:|conferenceId|STORAGE_KEY" apps/scripture-copier/general_conference_*.html
```

```powershell
node --check <temp-extracted-script.js>
```

```powershell
Get-ChildItem -LiteralPath apps/scripture-copier/GC_Transcripts_<Season>_<Year> -File | Measure-Object
```

## Final reminder

When the next request comes in to build a new General Conference tracker, read this file first, follow the same workflow, and avoid repeating the encoding and PDF-extraction mistakes from the April 2026 build.
