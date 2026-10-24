# Custom Chrome extension home

Read README.md and registry.json before creating or updating a custom Chrome extension.

- Sterling's permanent, unpacked installation home is `C:\Users\sterl\Documents\Chrome Extensions`. Keep one descriptive, stable subfolder per extension, with manifest.json directly inside.
- New source belongs in `apps/chrome-extensions/<slug>/extension/`. Existing apps can keep their current source paths; register them here instead of duplicating source.
- Add every extension to registry.json and confirm it appears on index.html.
- Run `powershell -NoProfile -ExecutionPolicy Bypass -File apps/chrome-extensions/sync-extensions.ps1 -Slug <slug>` after changes and verification, so the permanent local folder receives the finished files. There is no download, extraction, or build step.
- Keep folder names stable. Update in place, then tell the user to click Reload in chrome://extensions and refresh affected pages. First-time installations still require Developer mode > Load unpacked.
- Do not remove/reinstall an existing extension to reorganize it: the ID and local data can change. Keep existing compatibility junctions when relocating previously loaded folders. Do not edit Chrome profile preferences or copy browser storage into source control.
- Preserve user configuration and secrets. Never commit profile data, captured content, .env files, or local helper credentials.
- Run `node apps/chrome-extensions/website-timer/tests/timer.test.cjs` for timer changes. Test its page UI and actual extension loading when a test browser is available.
- Commit and push scoped completed changes. Give the extension-library webpage and repository source link; an unpacked extension itself is not a hosted webpage or Web Store listing.
