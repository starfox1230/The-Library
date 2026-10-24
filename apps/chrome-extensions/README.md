# Chrome Extension Library

Permanent local home: **C:\Users\sterl\Documents\Chrome Extensions**

[Open the extension library](https://starfox1230.github.io/The-Library/apps/chrome-extensions/)

Every extension has one stable, already unpacked folder with manifest.json directly inside. Future extension work must register its source in registry.json and sync the finished files into this home. This policy also lives in the root AGENTS.md and Sterling's global Codex instructions.

## First installation

Open `chrome://extensions`, turn on **Developer mode**, click **Load unpacked**, and select the extension's folder inside this home. For Website Timer, select `C:\Users\sterl\Documents\Chrome Extensions\Website Timer`. Refresh any pages that were already open.

Chrome requires this one-time Load unpacked step; creating a folder does not automatically install it. No ZIP download or extraction is needed.

## Updates

From any checkout of The Library, sync a finished extension:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\apps\chrome-extensions\sync-extensions.ps1" -Slug website-timer
```

Use another registry slug for that extension, or `-Slug all` to update all registered extensions to the versions in that checkout. The script copies source files in place, leaves unrelated files alone, and preserves registered local configuration such as Medality's helper-config.js. Use a current checkout to avoid downgrading an extension.

Then click **Reload** on the extension's card in `chrome://extensions` and refresh its website tabs. Folder names stay stable, preserving the extension ID and Chrome's separately stored settings.

## Existing installations

On October 24, 2026, Sterling's installed custom extensions were inventoried from Chrome's unpacked extension paths. RadPrimer already used this home. Next Up, AnkiWeb Enhancer, and Medality Remember Speed were moved here **with their currently installed files preserved**, and directory junctions at their previous paths keep Chrome's existing installations pointing to the new folders. There is no need to remove/reinstall them or re-enter settings. Keep the compatibility links; do not load a second copy of these extensions. The available repository source can be newer than the preserved installed version.

Website Timer and Screen Capture Transcriber Link are prepared here for first-time loading. Chrome's managed/Web Store extensions and its dictation connector are outside this custom-extension library.

Personal captures, Chrome storage, and credentials are not copied into this repository.
