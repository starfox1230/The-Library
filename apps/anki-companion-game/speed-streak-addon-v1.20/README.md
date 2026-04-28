# Speed Streak v1.20

This folder contains the Speed Streak v1.20 version of the project packaged as an Anki add-on.

It does not modify the original standalone files in the parent folder.

<p><strong>High-yield recent changes since v1.16</strong></p>
<ul>
  <li>Added an optional <strong>Review Later deck-page button</strong> showing how many cards were added to Review Later today</li>
  <li>Added an experimental <strong>WebGL satellite renderer</strong> for the Sphere view</li>
  <li>Added <strong>window position presets</strong> for the External Window mode</li>
  <li>Added a <strong>Review Time Drains Last</strong> option so future Time Drain repeats can move behind the rest of the current session</li>
  <li>Removed the temporary testing control for manually setting the streak/satellite count</li>
</ul>

## Changelog

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
- Sends controller rumble on Windows through XInput and uses a browser gamepad fallback on non-Windows platforms when available
- Removes the need for the external browser page, AnkiConnect, and AutoHotkey

## Folder layout

- `__init__.py`: add-on entrypoint and Anki hook wiring
- `game_state.py`: native Python game engine
- `haptics.py`: native Windows XInput rumble support
- `reviewer_overlay.py`: reviewer integration and JS bridge
- `web/overlay.css`: injected overlay styles
- `web/overlay.js`: injected overlay UI, animations, and browser-side haptics fallback

## Installation

Anki loads add-ons from the `addons21` folder in your Anki profile, not from arbitrary project folders.

To install this manually:

1. Open Anki.
2. Go to `Tools -> Add-ons -> View Files`.
3. Close Anki.
4. In the folder that opens, create a new folder named `speed_streak_v1_20`.
5. Copy the contents of this project folder into that new folder.
6. Start Anki again.

If the add-on loads successfully, the review screen will show Speed Streak in the display mode you choose at launch.
`v1.20` keeps the `Brick Layout` visual mode, the optional deck-page Review Later count button, and the WebGL sphere renderer.

### Faster install on Windows

You can also run:

```powershell
.\install_to_anki.ps1
```

from this folder, and it will copy the add-on into Anki's default `addons21` directory for you.
Speed Streak keeps its mutable data in the current Anki profile's `addons-data/speed_streak` folder. The installer still preserves a legacy `user_files` folder so older installs can migrate forward safely.

### Trim packaged audio on Windows

If you later add raw source packs back into an `Audio` folder, you can generate a trimmed `Audio_trimmed` folder with:

```powershell
.\trim_audio_to_trimmed.ps1
```

The script trims only leading silence and writes the processed results into `Audio_trimmed` with the same subfolder structure. This repo currently ships the packaged audio in trimmed form.

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
- The overlay arms itself on the first question card.
- Show the answer normally.
- Rate the card normally with buttons or keys.
- In Settings, `Sphere/Satellites` keeps the old orbit view and `Brick Layout` gives the new ultra-low-resource visualization.
- In Settings, enable the Review Later deck-page button if you want a deck-page count for cards added to Review Later today.
- In the Time Drain panel, enable `Review Time Drains Last` if you want future Time Drain repeats to move behind the rest of the current session.
- Press your configured pause shortcut to pause or resume the timer. The default is `P`.
- If you have a compatible controller connected, rumble should fire on reveal, rating, skip, reset, and timeout. Windows uses native XInput. Non-Windows platforms use the embedded browser's gamepad haptics support when available.

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

- `speed_streak_v1_20.ankiaddon`

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
- Controller rumble depends on either native XInput support on Windows or browser gamepad haptics support on non-Windows platforms, and may not work with every controller or driver stack.
- The inline overlay keeps Speed Streak on the left and pushes the review card to the right.
- The external window can store reusable position presets for common Anki layouts.
