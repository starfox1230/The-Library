# Website Timer

A buildless Manifest V3 extension for Facebook (including mobile/subdomains) and Rotten Tomatoes. Its red strip sits at the upper right of supported pages and shows active time for **this visit** and **today**. Click **Limits** to open settings.

## Install

The prepared folder is `C:\Users\sterl\Documents\Chrome Extensions\Website Timer`. In `chrome://extensions`, enable Developer mode, click Load unpacked, and select that folder. Refresh existing Facebook and Rotten Tomatoes tabs.

After source changes, run the parent library's sync-extensions.ps1 with `-Slug website-timer`, click Reload in Chrome, and refresh the sites. No build, download, extraction, or Web Store listing.

## Counting and limits

- Only the selected tab in the focused Chrome window counts. Switching tabs/windows, minimizing Chrome, locking the computer, or becoming idle for 60 seconds pauses counting.
- Heartbeats use background timestamps, not a page-provided duration. Missing heartbeats are capped at 2.5 seconds so sleep/background suspension is not charged. Normal display granularity is one second.
- A visit is active time in a tab on the same site. Refreshing or following links within the site preserves it; leaving the site, closing the tab, reloading the extension, or restarting Chrome clears it. Switching tabs pauses and resumes it.
- Daily totals survive browser restarts and reset at **the computer's local midnight**. Daylight-saving changes use local calendar boundaries. Each site has its own total.
- Both limits start **off**. Enable a daily minute budget (1–1440 minutes), a time-of-day cutoff, or both, separately per site. Cutoffs block from that time until midnight; these are not overnight schedule ranges.
- Reaching a limit redirects existing tabs to a break page and installs a persistent main-frame redirect rule for that site and its subdomains. It blocks refreshing/opening another page too. Settings apply immediately; midnight/cutoffs also reconcile with a 30-second Chrome alarm when no site is sending heartbeats. Chrome can delay alarms while sleeping.
- The break page offers settings, The Library, and a return link. Changing limits can restore access; this is a personal focus aid, and uninstalling/disabling it also stops enforcement.

## Privacy and permissions

Everything is stored in this Chrome profile. No network service, analytics, browsing history, URL log, or credential is collected. Content scripts and host permissions cover only facebook.com and rottentomatoes.com. The worker checks the actual selected tab/window and validates message senders. Only the extension settings page may change limits.

Permissions: storage (daily totals/settings and temporary visit state), idle (pause on idle/lock), alarms (cutoff/midnight reconciliation), declarativeNetRequestWithHostAccess (site block redirects). No tabs/history/cookie permission or all-sites access.

## Verification

Run `node apps/chrome-extensions/website-timer/tests/timer.test.cjs`. Tests cover time boundaries, daily limits/cutoffs, host matching, focus changes, duplicate tabs, browser sleep, worker restart, and message authorization. Browser smoke verification covers actual Manifest V3 loading, timer injection, settings, and blocking using local fixtures.

Chrome references: [Load unpacked](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world#load-unpacked), [idle](https://developer.chrome.com/docs/extensions/reference/api/idle), [declarative rules](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest).

Optional browser check: run `node apps/chrome-extensions/website-timer/tests/browser-smoke.cjs` with Playwright installed. `PLAYWRIGHT_MODULE` can point to a bundled Playwright module and `TIMER_TEST_BROWSER` to a Chromium binary that supports unpacked extensions. `TIMER_QA_OUTPUT` selects a screenshot directory; otherwise screenshots go into the temporary test profile. The test uses isolated browser storage and local website fixtures, without touching the user's Chrome profile or accounts.
