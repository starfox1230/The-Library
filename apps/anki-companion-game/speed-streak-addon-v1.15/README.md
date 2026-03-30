# Speed Streak v1.15

This folder contains the Speed Streak v1.15 version of the project packaged as an Anki add-on.

It does not modify the original standalone files in the parent folder.

## Changelog

### v1.15 (from v1.14)

- Rebuilt Speed Streak as a native Anki add-on, removing the old dependency on the external browser page, AnkiConnect, and AutoHotkey.
- Added two display modes: an inline side pane and a separate external compatibility window. The external window is generally the recommended option because it renders more smoothly and plays better with add-ons like AnkiHub and AMBOSS.
- Added a new `Brick Layout` view as the built-in ultra-low-resource mode alongside the original `Sphere/Satellites` view.
- Added a full `Haptic/Audio Feedback` settings section with per-event audio and haptic customization, audio previews, audio uploads, and persistent uploaded-file ordering.
- Packaged audio now ships in trimmed form so the built-in sounds start faster.
- Added a `Shortcuts` settings section with a configurable pause shortcut, plus a new `Longest Streak` stat in the stats view.
- Reworked the sidebar controls and settings layout, including symbol-based quick toggles for layout, display mode, haptics, and sound.

## What it does

- Lets you choose between an inline left pane and a compatibility floating window at launch
- Tracks streaks and timers natively
- Includes both the original `Sphere/Satellites` view and a new battery-friendly `Brick Layout` mode
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
4. In the folder that opens, create a new folder named `speed_streak_v1_15`.
5. Copy the contents of this project folder into that new folder.
6. Start Anki again.

If the add-on loads successfully, the review screen will show Speed Streak in the display mode you choose at launch.
`v1.15` adds a new `Brick Layout` visual mode that is designed to minimize CPU/GPU activity while still giving you satisfying progress chunking.

### Faster install on Windows

You can also run:

```powershell
.\install_to_anki.ps1
```

from this folder, and it will copy the add-on into Anki's default `addons21` directory for you.
The installer preserves the installed add-on's `user_files` folder so Review Later cohort history survives updates.

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

## First run

- On first launch, pick either `Inline Side Pane` or `External Window`.
- `External Window` is recommended, especially if you use add-ons like AMBOSS or AnkiHub.
- The default visual mode is `Sphere/Satellites`. `Brick Layout` is the built-in ultra-low-resource alternative.
- Open a deck and start reviewing.
- The overlay arms itself on the first question card.
- Show the answer normally.
- Rate the card normally with buttons or keys.
- In Settings, `Sphere/Satellites` keeps the old orbit view and `Brick Layout` gives the new ultra-low-resource visualization.
- Press your configured pause shortcut to pause or resume the timer. The default is `P`.
- If you have a compatible controller connected, rumble should fire on reveal, rating, skip, reset, and timeout. Windows uses native XInput. Non-Windows platforms use the embedded browser's gamepad haptics support when available.

## Updating after changes

The simplest reliable workflow is:

1. Close Anki completely.
2. Run `.\install_to_anki.ps1` again from this folder.
3. Start Anki again.

Anki add-ons are loaded at startup, so a full quit and reopen is the easiest way to reload changes.
The installed add-on's `user_files` folder is preserved during updates, so Review Later cohort history survives reinstalls.

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

- `speed_streak_v1_15.ankiaddon`

To build the package on macOS:

```sh
./build_ankiaddon.sh
```

The packaging script excludes:

- `__pycache__`
- `user_files`
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
- The overlay keeps the orb on the left and pushes the review card to the right.
