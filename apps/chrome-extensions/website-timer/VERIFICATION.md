# Website Timer and extension-library verification

Verified October 24, 2026.

- 17 dependency-free logic/service-worker tests passed.
- Actual Manifest V3 loading tested in an isolated Chromium 140 profile, with local Facebook and Rotten Tomatoes fixtures.
- Verified red timer injection on both supported sites.
- Verified settings opened as a browser tab, immediate cutoff enforcement for open tabs, persistent main-frame redirects on a new Facebook subdomain navigation, and access restoration after disabling the cutoff.
- No extension or page runtime errors during the browser check.
- Inspected screenshots of the timer, compact settings, break page, and extension catalog at desktop and 390px mobile width. Catalog has six registered extensions and no horizontal overflow.
- Ran the shared PowerShell installer against a temporary directory for all six registry entries.
- Synced Website Timer and Screen Capture Transcriber Link into the permanent home.
- Moved three existing installed extensions into the permanent home and verified manifest hashes through both their new directories and the compatibility junctions at the original Chrome installation paths. RadPrimer already used the permanent home.
- Existing installed extension versions/configuration were preserved during organization.
- User's regular Chrome profile was not modified. Website Timer has been tested in the isolated browser; first-time Load unpacked is still required in regular Chrome.

Commands:

```text
node apps/chrome-extensions/website-timer/tests/timer.test.cjs
node apps/chrome-extensions/website-timer/tests/browser-smoke.cjs
powershell -NoProfile -ExecutionPolicy Bypass -File apps/chrome-extensions/sync-extensions.ps1 -Slug website-timer
git diff --check
```

Browser smoke uses Playwright. In this environment, PLAYWRIGHT_MODULE pointed to the bundled package and TIMER_TEST_BROWSER to the already installed Chromium binary. Test profiles/screenshots stayed in the OS temporary folder and were not committed.
