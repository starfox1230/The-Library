# Medality Remember Speed v1.4

Keeps your preferred video speed (2x by default), saves watched transcripts at 90%, and gives you a selectable recent-lecture inbox.

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
- No course crawling, auto-advancing, progress changes, or audio transcription.
- Disabling automatic speed leaves the current video's rate as it is. To update or remove the extension, use `chrome://extensions`.

## Verification

Automated JavaScript and Python checks cover the download, transcript, watched-history, and speed workflows. They cover speed, transcripts, workspace, download controls, helper errors, and sender/URL validation. The helper successfully downloaded and merged the live Morphologic Cirrhosis lecture; FFprobe confirmed both audio and video. The updated button still requires an extension reload and live installed-extension test.

Official Vimeo Player SDK 2.30.4 is bundled. See `vendor/VIMEO-LICENSE.md` and https://github.com/vimeo/player.js.

## Video downloads for offline study

Version 1.3 adds **Download video** to the lesson toolbar. It downloads the current Vimeo lecture's available video and audio streams and merges them into an MP4 in `Downloads/Medality`. It reports progress and completion. It does not advance lessons or download an entire course.

Chrome needs a small local helper to merge the streams. Requires Python, yt-dlp (`python -m pip install yt-dlp`), and FFmpeg (`winget install Gyan.FFmpeg`). Double-click `helper/Start.cmd` in the installed extension folder and leave its window open while downloading. On first launch it creates a local pairing token; reload the extension at `chrome://extensions` and refresh the lesson once. Later launches retain that token. Close the helper window when finished. No Windows startup entry is installed.

The extension gains access only to `http://127.0.0.1:18764/*` for the helper. The helper listens only on loopback and authenticates requests with the generated token. No cookies are read or exported. It accepts only Medality lesson URLs and Vimeo player video IDs, handles one download at a time, and reports unavailable or protected streams as errors. Downloaded files and pairing tokens must never be committed to GitHub. Transfer the MP4 to your phone using your preferred file-transfer method.

## Automatic watched library (v1.4)

- Enabled by default, separately from the playback-speed preference. Switch it off in the popup or Recently watched page.
- At 90% playback position, record the lesson title, URL, course, and first watch time; save the available transcript. Seeking past 90% counts. Replays do not create duplicate entries or change the original ordering.
- Only the active lesson is captured. No backfill of past browsing, course crawling, or changing Medality completion status. Does not pause, seek, or change the video. If transcript text is not already in the DOM, it may briefly open the site's Transcript panel, restoring Cases when it was active and you have not interacted during capture.
- Missing transcript still leaves a watched entry. Use Save transcript to retry later. Storage errors are shown in the toolbar.
- Open Recently watched from the lesson toolbar or extension popup. Select individual lectures, latest five, all shown, or none. Copy includes only selected available transcripts, sorted by first watch time (earliest first), with titles and source URLs. Missing transcripts are counted.
- Extension page uses Chrome local storage directly and updates live without importing. The public recent.html page requests the same library through the scoped bridge and keeps a local browser copy; no capture text is committed or uploaded to GitHub.
- Export full library backup before uninstalling the extension. Import that JSON on a phone at the public Recently watched page. Phone transfer is manual; the URL alone contains no transcripts.
- Transcript saving and review do not need the video download helper or a server.
