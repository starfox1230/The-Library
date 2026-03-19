# Speed Streak

This folder contains the Speed Streak version of the project packaged as an Anki add-on.

It does not modify the original standalone files in the parent folder.

## What it does

- Embeds the Speed Streak left-side orbit directly in Anki's review screen
- Tracks streaks and timers natively
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
4. In the folder that opens, create a new folder named `speed_streak`.
5. Copy the contents of this project folder into that new folder.
6. Start Anki again.

If the add-on loads successfully, the review screen will show the Speed Streak orbit on the left side of the review screen.

### Faster install on Windows

You can also run:

```powershell
.\install_to_anki.ps1
```

from this folder, and it will copy the add-on into Anki's default `addons21` directory for you.
The installer preserves the installed add-on's `user_files` folder so Review Later cohort history survives updates.

### Faster install on macOS

You can also run:

```sh
./install_to_anki.sh
```

from this folder, and it will copy the add-on into the default macOS `addons21` directory for you while preserving `user_files`.

## First run

- Open a deck and start reviewing.
- The overlay arms itself on the first question card.
- Show the answer normally.
- Rate the card normally with buttons or keys.
- Press `P` to pause or resume the timer.
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

- `speed_streak.ankiaddon`

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
