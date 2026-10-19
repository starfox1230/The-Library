# Liver MRI study workspace

Public page: https://starfox1230.github.io/The-Library/apps/medality-study/

Contains the 38-video **Malignant Liver Lesions on MRI** course index read from the logged-in Medality course outline on October 18, 2026. Catalog durations may differ by rounding. The public data contains original study-focus prompts, not transcript-derived summaries or full transcripts.

Users capture transcripts from accessible Medality lesson pages, then select and copy any combination in the workspace. Transcript text and personal notes are stored in this browser's `localStorage`; neither is uploaded to GitHub or sent to an external service. Export JSON backups to move between devices. The workspace does not transcribe audio, bulk-crawl a course, bypass access restrictions, or change course progress.

## Use

1. Install or update the extension from **Download extension v1.1**. Extract first, then load the folder containing `manifest.json` at `chrome://extensions`. For an existing installation, replace its files in place, click Reload, then refresh Medality and this workspace.
2. On Medality use **Copy transcript** or **Save transcript** beside the lesson title. The extension can open the existing transcript panel when asked; if it cannot find transcript rows, it explains that text is unavailable. It uses observed timestamped `[data-item]` transcript rows, not the whole page's text.
3. In the hosted workspace choose **Import extension captures**. Alternatively export saved transcripts from the extension popup and import the JSON file.
4. Select individual lessons, all shown lessons, none, or the LI-RADS first-pass subset. The preview shows exactly what will be copied. Transcript-only, notes-only, combined, timestamped and optional study-prompt formats are available. Missing transcripts are counted and omitted from transcript output.

## Extension

The `extension/` folder is **Medality Remember Speed v1.1.0**. It retains 2x default speed enforcement with selectable speeds and an off switch. The official Vimeo Player SDK 2.30.4 and its MIT license are bundled.

- `storage`: local playback preferences and individually keyed transcript captures.
- `clipboardWrite`: user-triggered copy button and copy shortcut.
- Content scripts on HTTPS Medality/MRI Online pages; a separate bridge script only on this exact GitHub Pages app path.
- The bridge reads saved transcript captures only after a matching page request; speed preferences and other stored data are not exposed.
- Shortcut: Ctrl+Shift+Y / Command+Shift+Y. If another extension already uses it, assign it at `chrome://extensions/shortcuts`.
- Transcript capture does not auto-advance lessons, auto-save every page, complete lessons, or play videos.

## Development

Buildless HTML/CSS/JavaScript served by the repository's existing GitHub Pages workflow. No Sites registration or separate hosting account is needed for the user-requested repository deployment.

Run `npm ci` and `npm test` in this folder. Tests use synthetic transcript text and mock Chrome/player APIs. Package the `extension` folder as `downloads/medality-study-extension.zip` after edits. Do not commit personal captures, authentication details, installed dependencies or browser profiles.

Live Medality row structure was inspected. Automated verification covers transcript parsing, copy/save actions, absence handling, imports, preservation of notes, packet selection, timestamp formatting, source filtering and the extension-to-workspace bridge. End-to-end testing of an installed extension requires the user's installation/reload; a hosted-page test alone does not establish that an extension is installed.
