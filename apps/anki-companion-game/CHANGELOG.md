# Speed Streak Changelog

This changelog tracks the versioned Speed Streak add-on folders in this repository.

It is written as a repository-level record so the older frozen version folders can stay unchanged.

## `speed-streak-addon`

Base Speed Streak release line before the numbered version forks.

- Added the core Speed Streak review experience with streaks, score, timers, orbiting satellites, haptics, Review Later, and Time Drain workflows.
- Added orb and satellite color customization, including saved custom palettes and theme-specific default color sets.
- Added optional timer coloring that can follow the selected orb palette, plus timer preview controls and brightness adjustment.
- Improved the settings and preview experience for orb/timer customization.
- Added automatic Review Later Manager refresh on open and on focus regain.
- Fixed Review Later timestamp tracking so cards keep stable add times instead of all collapsing to the newest flagged time.
- Hardened parts of the Mac/load path around missing web assets and Windows-specific assumptions.

## `speed-streak-addon-v1.1`

First preserved development fork after the base add-on line.

- Split the project into its own install/build identity so development could continue without overwriting the original installed add-on.
- Fixed undo behavior so Speed Streak state rolls back with Anki review undo instead of leaving streak/satellite state behind.
- Improved runtime resilience when web assets are missing by softening some asset-loading failures instead of crashing immediately.
- Continued Review Later timestamp stabilization work so per-card add times remain persistent.

## `speed-streak-addon-v1.11`

Hook- and asset-focused compatibility pass.

- Reworked major reviewer integration away from direct monkey-patching toward official Anki hooks where possible.
- Registered exported web assets through Anki instead of relying only on manual disk reads.
- Kept embedded web asset fallbacks for resilience if packaged installs are missing `web/` files.
- Added an `Orb Animation` setting so users can disable the animated orb/satellites and keep a simpler streak-number display.
- Reduced web asset maintenance redundancy by generating `web_assets.py` from the real `web/` sources during install/build.

## `speed-streak-addon-v1.12`

Display-mode and windowing release.

- Added first-launch display mode choice between `Inline Left Pane` and `Compatibility Window`.
- Added a floating compatibility window mode so Speed Streak can run beside Anki without taking over the reviewer layout.
- Saved and restored floating window geometry.
- Fixed the display-mode chooser loop so it does not reopen endlessly in review.
- Added a native top-menu entry in Anki: `Speed Streak -> Settings`.
- Added `Speed Streak -> Review Later Manager` in the native top menu.
- Made the floating compatibility window behave more like a passive companion window by returning focus to Anki after interaction.
- Improved the native settings window:
  - wider default size
  - reusable top-level window behavior
  - safer scroll-wheel behavior so scrolling the page does not accidentally change timer/dropdown values

## `speed-streak-addon-v1.13`

Mac-focused compatibility cleanup.

- Improved inline/floating mode switching on Mac by tagging and recognizing the inline wrapper more reliably.
- Cleaned up stale inline containers when switching to the external compatibility window.
- Adjusted native top-menu action roles so macOS is less likely to hide or relocate menu items like `Settings`.
- Reworked settings combo-box popups to use an explicitly styled list view so dropdown options remain readable on macOS.
- Continued compatibility cleanup around reviewer layout ownership and cross-platform UI behavior.

## `speed-streak-addon-v1.14`

Performance and energy-use reduction pass.

- Added `Classic`, `Low Resource`, and `Ultra Low Resource` render modes so users can choose between smoother visuals and lighter timer/orbit behavior.
- Refined the reduced-resource modes so `Ultra Low Resource` uses the simplest half-second timer stepping and stationary/no-flare satellite presentation.
- Reworked the timer display pipeline so the sidebar timer and top card timer share the same countdown model instead of each computing their own time independently.
- Replaced a chunk of the heavier timer rerender behavior with lighter timer-only update logic aimed at reducing stutter and keeping the two timer surfaces better synchronized.
- Continued trimming repeated UI work by caching no-op DOM/style writes and keeping structural rerenders more event-driven.
- Throttled card background probing in the top card timer script so it does not keep re-checking the same background continuously.
- Improved native settings UX substantially:
  - reorganized settings into clearer `Display Style` and `Performance` sections
  - linked the duplicated `Vibration Only Mode` toggles
  - redesigned the settings window layout and styling for a more polished look
  - left-justified controls and fixed width/overflow issues that made the window harder to use
- Updated flag selectors to use Anki's actual runtime flag colors instead of approximate guessed colors.
- Added `meta.json` self-healing/bootstrap during config writes and local install flows so settings saves do not fail when the installed add-on folder is missing that file.

## `speed-streak-addon-v1.15`

Native add-on packaging and feature expansion release.

- Rebuilt Speed Streak as a native Anki add-on, removing the old dependency on the external browser page, AnkiConnect, and AutoHotkey.
- Added inline and external display modes, plus the new `Brick Layout` ultra-low-resource visual mode.
- Added per-event audio and haptic customization, audio uploads, configurable pause shortcuts, and longest-streak stats.

## `speed-streak-addon-v1.16`

Comparison build for the external-window layout experiment.

- Preserved the `Brick Layout` visual mode while restoring the review-only external-window layout persistence experiment for side-by-side testing against `v1.15`.

## `speed-streak-addon-v1.17`

Review Later deck-page button release.

- Added a new Review Later Manager toggle that enables or disables a Speed Streak deck-page button showing how many cards were added to Review Later today.
- Made that deck-page button stay hidden when today's count is zero and open the Review Later Manager when clicked.
- Scoped the new deck-page button wiring to Speed Streak-specific config keys and JS messages so it does not clash with Pocket Knife.
