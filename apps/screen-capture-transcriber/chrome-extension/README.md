# Screen Capture Transcriber Link

This is a private, unpacked Manifest V3 Chrome extension for the local Screen
Capture Transcriber. It is specialized for Medality's embedded Vimeo player and
also detects standard YouTube video elements.

## Install locally

1. Start Screen Capture Transcriber.
2. Open `chrome://extensions` in Chrome.
3. Enable **Developer mode**.
4. Choose **Load unpacked**.
5. Select this `chrome-extension` folder.
6. Reload any already-open Medality and YouTube lessons once.

The extension does not need the Chrome Web Store. It exchanges small playback-state
messages with `http://127.0.0.1:43129`; media, credentials, cookies, and lesson
content are not sent through the bridge.

The extension reads the active video element's current source time, duration, actual
playback rate, play/pause state, and seek events. On Medality it also imports the
site-provided timestamped transcript, temporarily opening and restoring the transcript
drawer when necessary. YouTube's built-in timestamped transcript is imported in the
same way. The desktop app scopes playback commands, events, titles, and transcripts to
one selected Chrome tab, so other open video tabs cannot interfere. It accepts local
play, pause, and speed commands only from the desktop recorder's loopback bridge.
While linked recording is active, an unmodified
`Backspace` outside text-entry controls sends the current player timestamp to the
desktop learning-note workflow; `Ctrl+Backspace` and Backspace inside editable fields
are left untouched.
