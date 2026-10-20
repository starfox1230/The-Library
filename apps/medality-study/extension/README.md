# Medality Remember Speed v1.2

Keeps your preferred video speed (2x by default) and adds transcript copy/save controls.

## Install or update

- Extract the ZIP to a permanent folder.
- At `chrome://extensions`, enable Developer mode and use **Load unpacked** to select the folder containing `manifest.json`.
- If already installed, replace the files in the existing extension folder, then click that extension's **Reload** button. If Chrome asks for the added clipboard/site permission, review it there.
- Refresh both your Medality lesson and the study workspace after updating.
- Pin the extension through Chrome's puzzle-piece menu for access to speed preferences and JSON export.

## Transcript workflow

1. Open a lesson. The new toolbar appears beside the title.
2. **Copy transcript** copies the available transcript with its title and source URL. **Ctrl+Shift+Y** does the same (Command+Shift+Y on Mac). If the shortcut is already assigned, change it at `chrome://extensions/shortcuts`.
3. **Save transcript** stores that lesson's transcript locally in extension storage. Re-saving the same URL updates the existing capture.
4. Open https://starfox1230.github.io/The-Library/apps/medality-study/ and click **Import extension captures**.
5. Select one, several, all shown, or none; preview and copy the combined packet. JSON export/import is also available from the popup.

The copy/save action can open the site's existing Transcript panel. If no supported transcript is available, it reports that instead of copying unrelated page text. Captions may contain transcription errors; the extension preserves the available wording.

## Scope and privacy

- Runs on HTTPS Medality/MRI Online pages and their subdomains.
- A separate bridge runs only on the exact The-Library Medality study workspace path. It shares saved captures with that page after a user import request.
- Captures and preferences are stored locally. The public app stores imported transcripts and notes in this browser's localStorage; it does not upload them to GitHub.
- Permissions: `storage` and `clipboardWrite`. No cookies, browsing-history, download, all-sites, or Vimeo-wide permission.
- No course crawling, automatic captures, auto-advancing, progress changes, stream extraction, or audio transcription.
- Disabling automatic speed leaves the current video's rate as it is. To update or remove the extension, use `chrome://extensions`.

## Verification

23 automated checks passed: 13 speed checks and 10 transcript/workspace checks, using synthetic text and simulated Chrome/player APIs. The live Medality transcript DOM was inspected. The workspace's selection, preview, clipboard copy, and clear-selection behavior were tested in Chrome. Installation/reload and the actual Medality-to-hosted-page transfer still require a live installed-extension check.

Official Vimeo Player SDK 2.30.4 is bundled. See `vendor/VIMEO-LICENSE.md` and https://github.com/vimeo/player.js.

## Video download button

**Download video** opens a visible video-download link supplied by the current lesson, when one exists. If the lesson offers no download, the toolbar says so. This does not extract Vimeo streams or bypass disabled downloads. No additional permissions are needed. After updating the unpacked extension, click Reload at chrome://extensions and refresh the lesson.
