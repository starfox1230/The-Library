# Speed Streak v1.34

This folder contains Speed Streak v1.34, built directly from v1.33 without modifying the frozen v1.33 folder.

It does not modify the original standalone files in the parent folder.

<p><strong>High-yield recent changes since v1.16</strong></p>
<ul>
  <li>Added an optional <strong>Review Later deck-page button</strong> showing how many cards were added to Review Later today</li>
  <li>Added an experimental <strong>WebGL satellite renderer</strong> for the Sphere view</li>
  <li>Added <strong>window position presets</strong> for the External Window mode</li>
  <li>Added a <strong>Review Time Drains Last</strong> option so future Time Drain repeats can move behind the rest of the current session</li>
  <li>Restored a hidden developer-only control for manually setting the streak/satellite count</li>
</ul>

## Changelog

### v1.34 (from v1.33)

- Adds configurable Crystal Reactor color styles while preserving the existing Ice Crystal appearance as the default.
- Adds Answer Colors, which gives every earned crystal the configured Hard, Good, or Easy rating color with automatically shaded facets.
- Adds Central Orb Color, which creates a coordinated monochrome crystal formation from the configured central-orb color.

### v1.33 (from v1.32)

- Adds an opt-in `Time Boost` gameplay mode alongside the default `Legacy Points` mode.
- Keeps the streak and visual growth in Time Boost mode while replacing score and multiplier with a capped charge bank.
- Starts Time Boost runs with one charge by default, earns another every five timed cards, and caps the bank at three charges; all three values are configurable.
- Shows the charge bank as filled and theme-muted lightning-bolt slots, with an automatic compact fraction fallback when the panel is too narrow for every slot.
- Replaces the former full-width `BOOST` button with a compact keycap showing the configurable shortcut. The keycap appears in the charge-bank hover row and opens directly to its shortcut setting when clicked; pressing that keyboard key spends a charge.
- Prevents boosts on free, untimed, paused, already-expired, or inactive phases so a charge cannot revive a streak after timeout resolution.
- Persists charge configuration and, when run restoration is enabled, charge progress and usage. Normal Anki undo restores the bank and earn meter unless No Undo mode is active.
- Adds an independent `No Pause mode` that blocks manual pauses while retaining safety pauses when Anki leaves Review or opens Settings.
- Adds `No Undo mode`, which clears Anki's undo history during a committed review run, plus compact No Pause/No Undo toggles below the charge earn meter.
- Collapses the No Pause/No Undo controls and shortcut keycap until the charge area is hovered or keyboard-focused. The single control row expands below `Next charge` so the bolts stay still and remain easy to click. A Gameplay option controls whether inactive focus-mode toggles are included; active toggles are always included.
- Opens Charge Bank Capacity when any bolt, empty bolt, or gap in the bank is clicked. Clicking the earn bar or `Next charge` text instead opens and selects Cards Required to Earn a Charge.
- Gives blocked platform Undo commands such as `Ctrl+Z` the same visible No Undo feedback as the review-screen `U` shortcut.
- Claims the configured Time Boost review shortcut after Anki and other add-ons finish building the shortcut list, preventing later shortcut registrations from silently stealing it.
- Expands Developer Preferences into a ready-to-test Time Boost preset: Time Boost mode, No Pause, No Undo, visible inactive focus toggles, 10 seconds per charge, a three-charge bank, one starting charge, a charge every 10 completed cards, and the backtick key for Boost.
- Applies single-key shortcut edits immediately during an active review and prevents the No Undo guard from taking a key assigned to Speed Streak pause, unpause, or Boost.
- Leaves the complete score/multiplier system available as the default legacy option.
- Keeps the WebGL card timer on one uninterrupted animation loop during normal countdown updates, while still resynchronizing safely for pause, resume, Time Boost, phase changes, resizing, and hiding.
- Gives the circular sidebar timer the same persistent, deadline-based WebGL animation behavior instead of cancelling and rebuilding its frame loop at every text update.
- Updates the Time Boost charge bank only when its charge data or available width changes, and skips repeated inline-pane visibility/layout work when the requested state is already applied.
- Caches sidebar WebGL canvas dimensions and viewport state, using resize notifications to update Orbit, Crystal Reactor, and timer rendering only when their canvas size actually changes.

### v1.31 (from v1.30)

- Makes both sides of the first card untimed by default each time the user enters Review, without resetting the existing streak or score.
- Adds a General Timers toggle for disabling that free first card.
- Adds an `Answer timer can end streak` toggle that remains on by default; when off, answer timeout still alerts the user but preserves the streak.

### v1.30 (from v1.28)

- Consolidates Orbit, Crystal Reactor, and Brick Streak into one bottom-left SVG visual selector.
- Adds a snapped resource-usage slider with Full/Balanced/Ultra Orbit levels, Animated/Still Crystal levels, a fixed Brick mode, descriptions, and relative load estimates.
- Clicking the center visualization opens the same selector, and leaving the selector or sidebar collapses it.
- Keeps the selector icon-only and responsive, wraps all explanatory copy within narrow panes, and adds a generous invisible hover bridge so the selector stays open while the pointer travels to it.
- Wraps long window-preset names instead of truncating them and disables incidental text selection throughout the gameplay pane.
- Starts at streak zero with only the number, so every visible crystal component represents an earned streak card.
- Preserves the preferred **golden-angle rosette** exactly through streak 50, including its original crystal size, placement, and sheen.
- After streak 50, gives each set of 50 cards a spacious concentric growth era, turning late streaks into a layered crystal mandala instead of one packed mass.
- Keeps the newest late-streak component slightly larger and lightly haloed so each addition remains perceptible in the 400-1000 range.
- Gives every 10 cards a lock-in pulse, every 50 cards a stronger double-ring era ignition, and 100/250/500/1000 milestones the full reactor celebration.
- Adds one connected, multi-facet crystal component for every successful card, using a fixed ice/cyan/lavender sheen rather than answer-rating colors.
- Retains the original individual golden-angle placement inside every growth era instead of creating spokes, branches, or local snowflakes.
- Uses era-aware camera framing so new layers expand the formation while remaining on-screen through streak 1000.
- Removes the rotating containment rings and named tier word so the growing crystal remains the visual focus.
- Pulses the reactor on each answer and fractures the full assembly when time expires.
- Keeps the smooth full-frame behavior of v1.28 rather than the v1.29 frame-throttling experiment.
- Reuses the proven satellite renderer's WebGL canvas, context, and compatible dynamic point pipeline so selecting the star does not request a fragile second graphics context.
- Leaves the streak number visible if WebGL is unavailable instead of showing an unearned starter crystal.

### v1.28 (from v1.27)

- Rebuilds the Settings visual system from the ground up without changing its hierarchy, saved options, or actions.
- Uses custom-painted solid surfaces and filled action buttons instead of relying on nested Qt stylesheet inheritance, producing deterministic Windows and macOS rendering.
- Keeps collapsible section headings deliberately unfilled and visually distinct from every clickable action button.
- Retains the Settings dialog in memory after first use so subsequent opens are effectively immediate.

### v1.27 (from v1.26)

- Adds opt-in note type-specific timer rules under Timers > Special Timers.
- Loads note types from the current Anki collection into a searchable multi-select picker.
- Lets one rule apply the same exact question and answer timers to multiple note types.
- Prevents Enter from closing the Settings window.
- Stops saving tag timer rules on every keystroke; tag edits now apply through the adjacent `Save Tag` button or Enter in that tag field.

### v1.26 (from v1.25)

- Renames the pause protection setting to `Lock answering while paused` so its purpose is immediately clear.
- Places the toggle directly after `Pause Shortcut Mode` in the Shortcuts section, before the individual shortcut fields.
- Clarifies that the safety lock prevents both keyboard answering and clicks on Show Answer or the ease buttons.
- Keeps the safety lock disabled by default for normal users while preserving an existing user's saved choice during upgrades.
- Enables the safety lock when the hidden developer preferences preset is activated with `Ctrl+Shift+W` while Settings is focused; later manual changes remain saved across Settings closes, Anki restarts, and add-on updates.
- Uses `Ctrl+Shift+W` to toggle the hidden developer preferences while Settings is focused.
- Adds a developer-only control at the top of Settings for setting the current streak and satellite count from 0 to 5000, including precise 129/130/131 transition testing.
- Removes the automatic switch to Ultra Low Resource at 130 satellites; Speed Streak now keeps using the renderer selected by the user at every streak size.

### v1.25 (from v1.24)

- Moves the Review Later deck-page button toggle to the top-right of the Review Later Manager header.
- Colors the deck-page toggle blue when enabled and red when disabled.
- Adds `Download HTML Review` next to `Open All in Browser`, exporting the visible Review Later cards as a static HTML review file without per-card Browser or Review Later toggle buttons.
- Rewrites relative media references in the downloaded HTML to local Anki collection media `file:///` URLs so images remain available from the exported file on the same machine.

### v1.24 (from v1.23)

- Adds an optional Shortcuts setting, `Block answer keys while paused`, that blocks Anki's normal review `Space`, `Enter`, and `1`-`4` keys while the Speed Streak pause screen is active.
- Guards Anki's actual show-answer and answer-card methods while paused, and disables/captures the bottom-bar Show Answer and ease buttons so mouse clicks cannot answer through the pause screen.
- Keeps the pause key guard off by default for normal users, but turns it on automatically in the hidden developer preset toggled with `Ctrl+Shift+W` from Settings.

### v1.23 (from v1.22)

- Creates a new active development snapshot so v1.22 can remain frozen.
- Marks the historical v2.0 comparison build as an old branch and treats it as a conflicting install.
- Improves inline side-pane collapse behavior so a hidden Speed Streak pane does not leave unnecessary blank review space.
- Adds a Display Style toggle to fully disable the side panel while keeping the top card timer and haptics.
- Adds opt-in absolute Special Timers for AnKing one-by-one cards, native typed-answer cards, and multiple exact-tag rules.
- Adds compatibility-safe card flag access for newer Anki versions.
- Adds an automatic low-resource safeguard for large sphere/satellite streaks.
- Keeps the developer review preset hidden from normal settings. While the Settings dialog is focused, `Ctrl+Shift+W` toggles it and briefly shows its on/off state.
- Clarifies special-card timing with phase-specific labels, `None` for no added time, and disabled time fields unless Extra time is selected.
- Lazily builds audio event controls, haptic event controls, the haptics test lab, and each special-card timing subsection when first expanded.
- Rebuilds active reviewer shortcuts immediately after shortcut or developer-preset changes, without requiring users to leave and reopen the deck.
- Uses explicit settings-dialog palettes and control-state colors so nested headings, text fields, buttons, dropdowns, selections, and disabled controls retain readable contrast on macOS and Windows.
- Replaces additive special-card timing with absolute per-phase timers nested under Timers. Typed-answer, AnKing one-by-one, and multiple exact-tag rules can independently make the question or answer phase untimed; overlapping rules use the longest time per phase, with Untimed taking precedence.
- Uses indented phase controls for each special timer rule and simple six-digit numeric seconds fields with no stepper arrows or in-field unit suffixes.
- Adds an opt-in Time Drain flag timer rule. When enabled, flagged cards use exact special timers instead of the Time Drain warning or review-last queue behavior.
- Keeps special-rule question and answer options hidden until that rule's Enable toggle is turned on.
- Batches collapsible-section and conditional-control layout changes into a single paint pass, avoiding brief overlaps or jumps when settings panels open and close.
- Preserves the settings scrollbar's exact pixel position during content-height changes and prevents section headings from triggering Qt's automatic focus scrolling.
- Keeps `UNTIMED` fully visible above timer graphics in both the top card timer and side-panel timer.
- Uses a dedicated unclipped foreground layer for the side-panel `UNTIMED` label and disables the timer canvas while that state is active.
- Matches AnKing selective one-by-one values per cloze card, so a field such as `1,3` affects only cloze cards 1 and 3 while nonnumeric enabled values such as `y` affect all clozes on that note.
- Labels AnKing timing as “Before one-by-one starts” and “While revealing items,” with a prominent autoflip explanation directly above the controls.
- Preserves Anki's `meta.json` configuration during local Windows and macOS reinstall workflows; AnkiWeb updates retain configuration under the stable add-on ID.
- Avoids declaring the live AnkiWeb ID as a self-conflict, while local installers still remove obsolete or duplicate Speed Streak folders explicitly.

### v1.22 (from v1.21)

- Adds nested Audio and Haptics panels inside the Haptic/Audio Feedback settings section.
- Adds a saved controller type selector for `Standard / Xbox-style controller` and `Steam Controller / Steam Input`.
- Adds a Haptics Lab with one-click test buttons for a larger vibration pattern library, including timeout-focused and Steam Controller-focused experiments.
- Makes the Steam Controller profile default `Again` to `Sync Tap` and `Timeout` to a repeated `Rising Alarm`.
- Keeps existing per-event haptic assignments and defaults unchanged unless you pick a different pattern.

### v1.21 (from v1.20)

- Improves PC controller haptics for Steam Input and the Steam Controller 2026 compatibility path without adding UI.
- Detects connected XInput slots and sends rumble to each connected slot, so Steam's virtual Xbox controller does not have to occupy slot 0.
- Keeps native Windows XInput rumble as the default path for existing Xbox-style controllers.
- Adds a dormant Steamworks flat-API bridge that can use `steam_api64.dll` from the add-on folder, `steamworks/`, `steam_haptics/`, or the `SPEED_STREAK_STEAM_API64` environment variable if a future Steam Input runtime is supplied.
- Converts packaged feedback audio from OGG to MP3 for better cross-platform playback, especially on macOS.

### v1.20 (from v1.17)
- Adds an experimental WebGL satellite renderer for the sphere view.

### v1.17 (from v1.16)

- Added a new Review Later Manager toggle that controls whether Speed Streak shows a deck-page button with today's Review Later count.
- Added the optional deck-page Review Later button itself, which stays hidden at zero and opens the Review Later Manager when clicked.
- Kept the deck-page button implementation namespaced to Speed Streak so it can live beside Pocket Knife without sharing handlers or message IDs.

### v1.16 (from v1.15)

- Comparison build that restores the review-only external-window layout persistence experiment so it can be tested side-by-side against `v1.15`.

### v1.15 (from v1.14)

- Rebuilt Speed Streak as a native Anki add-on, removing the old dependency on the external browser page, AnkiConnect, and AutoHotkey.
- Added two display modes: an inline side pane and a separate external compatibility window. The external window is generally the recommended option because it renders more smoothly and plays better with add-ons like AnkiHub and AMBOSS.
- Added a new `Brick Layout` view as the built-in ultra-low-resource mode alongside the original `Sphere/Satellites` view.
- Added a full `Haptic/Audio Feedback` settings section with per-event audio and haptic customization, audio previews, audio uploads, and persistent uploaded-file ordering.
- Packaged audio now ships in trimmed form so the built-in sounds start faster.
- Added a `Shortcuts` settings section with a configurable pause shortcut, plus a new `Longest Streak` stat in the stats view.
- Reworked the sidebar controls and settings layout, including symbol-based quick toggles for layout, display mode, haptics, and sound.

## What it does

- Lets you choose between an inline side pane and a compatibility floating window at launch
- Tracks streaks and timers natively
- Includes both the original `Sphere/Satellites` view and the battery-friendly `Brick Layout` mode
- Uses the WebGL renderer by default for the Sphere view, with reduced-resource render modes still available
- Adds optional Review Later deck-page status and Time Drain review-order controls
- Saves and reapplies external-window position presets
- Sends controller rumble on Windows through connected XInput slots, with an optional Steamworks bridge when supplied, and uses a browser gamepad fallback when native rumble is unavailable
- Removes the need for the external browser page, AnkiConnect, and AutoHotkey

## Folder layout

- `__init__.py`: add-on entrypoint and Anki hook wiring
- `game_state.py`: native Python game engine
- `haptics.py`: native Windows XInput rumble support plus optional Steamworks bridge detection
- `reviewer_overlay.py`: reviewer integration and JS bridge
- `web/overlay.css`: injected overlay styles
- `web/overlay.js`: injected overlay UI, animations, and browser-side haptics fallback

## Installation

Anki loads add-ons from the `addons21` folder in your Anki profile, not from arbitrary project folders.

To install this manually:

1. Open Anki.
2. Go to `Tools -> Add-ons -> View Files`.
3. Close Anki.
4. In the folder that opens, create a new folder named `speed_streak_v1_34`.
5. Copy the contents of this project folder into that new folder.
6. Start Anki again.

If the add-on loads successfully, the review screen will show Speed Streak in the display mode you choose at launch.
`v1.34` keeps the v1.33 Sphere, Brick, and Crystal Reactor visuals while adding Crystal Reactor color styles.

### Faster install on Windows

You can also run:

```powershell
.\install_to_anki.ps1
```

from this folder, and it will copy the add-on into Anki's default `addons21` directory for you.
The Windows installer removes previous Speed Streak version folders and AnkiWeb `1237336370`, so v1.34 replaces them on the next Anki restart. Speed Streak keeps its mutable data in the current Anki profile's `addons-data/speed_streak` folder. The installer still preserves a legacy `user_files` folder so older installs can migrate forward safely.

### Trim packaged audio on Windows

If you later add raw source packs back into an `Audio` folder, you can generate a trimmed `Audio_trimmed` folder with:

```powershell
.\trim_audio_to_trimmed.ps1
```

The script trims only leading silence and writes the processed results into `Audio_trimmed` with the same subfolder structure. It writes MP3 files by default for cross-platform playback; pass `-OutputExtension .ogg` or another supported extension if you need a different format. This repo currently ships the packaged audio in trimmed MP3 form.

### Faster install on macOS

You can also run:

```sh
./install_to_anki.sh
```

from this folder, and it will copy the add-on into the default macOS `addons21` directory for you while preserving `user_files`.
That legacy preserve step is only for migration compatibility. Live Speed Streak data is stored in the current profile's `addons-data/speed_streak` folder.

## First run

- On first launch, pick either `Inline Side Pane` or `External Window`.
- `External Window` is recommended, especially if you use add-ons like AMBOSS or AnkiHub.
- The default visual mode is `Sphere/Satellites` using the WebGL renderer. `Brick Layout` is the built-in ultra-low-resource alternative.
- Open a deck and start reviewing.
- By default, both sides of the first card are untimed each time you enter Review.
- Show the answer normally.
- Rate the card normally with buttons or keys.
- In Settings, `Sphere/Satellites` keeps the old orbit view and `Brick Layout` gives the new ultra-low-resource visualization.
- In Settings, enable the Review Later deck-page button if you want a deck-page count for cards added to Review Later today.
- In the Time Drain panel, enable `Review Time Drains Last` if you want future Time Drain repeats to move behind the rest of the current session.
- Press your configured pause shortcut to pause or resume the timer. The default is `P`.
- In Time Boost mode, press the configured boost shortcut (default `R`) to spend one charge and add time.
- Enable `No Pause mode` to reject deliberate pause commands; Anki navigation and Settings still use safety pauses.
- In Shortcuts, use `Lock answering while paused` to choose whether the pause screen blocks answer keys and answer-button clicks.
- If you have a compatible controller connected, rumble should fire on reveal, rating, skip, reset, and timeout. Windows uses native XInput across connected controller slots and can use an optional Steamworks bridge if supplied. Non-Windows platforms use the embedded browser's gamepad haptics support when available.

## Updating after changes

The simplest reliable workflow is:

1. Close Anki completely.
2. Run `.\install_to_anki.ps1` again from this folder.
3. Start Anki again.

Anki add-ons are loaded at startup, so a full quit and reopen is the easiest way to reload changes.
Live Speed Streak data now lives in the current Anki profile's `addons-data/speed_streak` folder. The legacy `user_files` folder is still preserved during installs so older data can migrate forward safely.

## Publishing On AnkiWeb

AnkiWeb accepts add-ons as `.ankiaddon` zip archives.

This folder now includes:

- `manifest.json` for direct file installs outside AnkiWeb
- `build_ankiaddon.ps1` to create a clean upload package
- `build_ankiaddon.sh` to create a clean upload package on macOS/Linux

To build the package on Windows:

```powershell
.\build_ankiaddon.ps1
```

That creates:

- `speed_streak_v1_34.ankiaddon`

To build the package on macOS:

```sh
./build_ankiaddon.sh
```

The packaging script excludes:

- `__pycache__`
- legacy `user_files`
- the local install/build helper scripts

After building:

1. Go to `https://ankiweb.net/shared/addons/`
2. Sign in
3. Use the Upload button
4. Upload the generated `.ankiaddon` file
5. Fill in the add-on title, description, and supported Anki versions

AnkiWeb expects the archive contents to have files like `__init__.py` at the root of the archive, not wrapped in an extra top-level folder.

## Notes

- This add-on is designed for Windows haptics first.
- Controller rumble depends on either native XInput support on Windows, the optional Steamworks bridge when supplied, or browser gamepad haptics support when native rumble is unavailable. It should work with Steam Input virtual Xbox slots even when the controller is not assigned to XInput user 0.
- The inline overlay can sit on either side of the review card; use the arrow below Settings to move it left or right.
- The external window can store reusable position presets for common Anki layouts, and any setup can be marked to apply automatically whenever external mode opens.
