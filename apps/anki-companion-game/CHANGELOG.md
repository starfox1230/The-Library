# Speed Streak Changelog

This changelog tracks the versioned Speed Streak add-on folders in this repository.

It is written as a repository-level record so the older frozen version folders can stay unchanged.

## `speed-streak-addon-v1.33`

Consolidated interaction and layout release.

- Created from the frozen `speed-streak-addon-v1.32` folder without modifying v1.32.
- Moves the hover-revealed No Pause, No Undo, and Boost shortcut controls below the charge earn meter so bolts no longer move before a click lands.
- Makes every filled bolt, empty bolt, and gap open Charge Bank Capacity, while the progress bar and `Next charge` text open Cards Required to Earn a Charge.
- Replaces the separate Orbit, Crystal, and Brick buttons with one bottom-left selector using purpose-drawn inline SVG icons.
- Adds snapped resource levels and descriptions for Full/Balanced/Ultra Orbit, Animated/Still Crystal, and the fixed ultra-light Brick mode.
- Opens the visual selector when the center visualization is clicked and collapses it when the pointer leaves the selector/sidebar.
- Replaces the window-preset glyph with a recognizable window-layout icon and lets Default or saved setups be marked to apply automatically on external-mode entry.
- Adds a persisted arrow below Settings in inline mode for moving the pane between the left and right sides of the review card.

## `speed-streak-addon-v1.32`

Time Boost gameplay release.

- Created from the frozen `speed-streak-addon-v1.31` folder.
- Keeps the existing points and multiplier system as the default `Legacy Points` gameplay mode.
- Adds opt-in `Time Boost` mode with configurable starting charges, bank capacity, cards-per-charge accrual, and seconds added per boost.
- Adds a responsive lightning-bolt charge bank and compact configurable shortcut keycap, with a fraction fallback in narrow panels.
- Integrates charges with run reset, optional restart restoration, settings persistence, and Anki review undo.
- Adds independent `No Pause mode` for blocking deliberate pauses while retaining safety pauses outside the active review surface.
- Adds `No Undo mode`, interactive focus-rule toggles above the charge bank, and an option to hide those toggles while inactive.
- Hardens Time Boost shortcut ownership against conflicts introduced by other review shortcuts or add-ons.
- Extends Developer Preferences with the requested Time Boost test preset: No Pause/No Undo on, visible focus toggles, 10-second boosts, three-charge capacity, one starting charge, one charge per 10 cards, and backtick as the Boost shortcut.
- Rebinds shortcut edits immediately in Review and fixes the No Undo guard incorrectly replacing a configured `U` pause/unpause binding.
- Moves focus-rule toggles and the shortcut keycap into a single expanding charge-bank hover/focus row; it occupies normal layout space instead of overlapping the timer, and clicking the keycap opens and focuses its native shortcut setting.
- Restores mouse input on the charge-bank hover target so the expanding controls actually appear in the otherwise click-through sidebar.
- Clears pointer-created button focus after activation so the row collapses when the mouse leaves the charge area.
- Matches the shortcut keycap to the focus-toggle height and removes its upward offset so it is no longer clipped.
- Makes the charge bank and earn-progress area open Settings directly at the Time Boost configuration controls while clearing their mouse-created focus on activation.
- Changes the standard Use Time Boost shortcut default from `B` to `R`; Developer Preferences continues to use its backtick testing override.
- Adds visible No Undo feedback for the platform Undo shortcut (`Ctrl+Z` on Windows) instead of leaving the disabled command silent.

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

## `speed-streak-addon-v1.20`

WebGL sphere renderer release.

- Added an experimental WebGL satellite renderer for the sphere view.
- Kept the native add-on packaging, Review Later deck-page button, and external-window positioning behavior from earlier versions.

## `speed-streak-addon-v1.21`

Steam Controller 2026 PC haptics compatibility pass.

- Created from `speed-streak-addon-v1.20`.
- Improved Windows rumble dispatch by detecting connected XInput controller slots instead of assuming slot 0.
- Sends haptic patterns to every connected XInput slot so Steam Input virtual Xbox controllers continue to receive rumble when Steam assigns them to a nonzero slot.
- Added an optional, UI-free Steamworks flat-API bridge that can use `steam_api64.dll` if supplied later for native Steam Input haptics.

## `speed-streak-addon-v1.22`

Haptics testing workbench release.

- Created from `speed-streak-addon-v1.21`.
- Added nested Audio and Haptics panels inside the Haptic/Audio Feedback settings section so haptics can be tuned without scrolling past every audio control.
- Added a saved controller type selector for Standard/Xbox-style and Steam Controller/Steam Input tuning.
- Added a Haptics Lab with grouped one-click test patterns, including timeout-focused and Steam Controller-focused experiments.
- Made the Steam Controller profile default `Again` to `Sync Tap` and `Timeout` to a repeated `Rising Alarm`.

## `speed-streak-addon-v1.24`

Pause-screen key guard release.

- Created from `speed-streak-addon-v1.23`.
- Added an optional Shortcuts setting that blocks Anki's normal review `Space`, `Enter`, and `1`-`4` answer/reveal keys while Speed Streak is paused.
- Guards Anki's show-answer and answer-card paths directly while paused, and disables/captures bottom-bar Show Answer and ease-button clicks.
- Keeps that setting off by default for normal users and on by default when the hidden developer preset is enabled from Settings with `Ctrl+Shift+W`.
