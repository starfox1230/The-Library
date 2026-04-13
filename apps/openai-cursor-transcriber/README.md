# OpenAI Cursor Transcriber

A small Windows desktop app that stays local on your computer, listens for a global hotkey, records up to 60 seconds from your microphone, sends the audio to OpenAI's transcription API, copies the result to your clipboard, and shows a cursor-following transcript tag until you paste.

## What it does

- Press `F3` once to start recording.
- Recording starts immediately, and the loading indicator stays up only until the microphone actually starts delivering audio. By default there is no extra artificial delay.
- After that, the recording badge appears near your cursor with the 60-second countdown.
- Press `F3` again to stop.
- The app sends the recording to OpenAI using `gpt-4o-transcribe`.
- The full transcript is copied to your clipboard.
- A preview bubble stays next to your cursor until you paste with `Ctrl+V`, `Ctrl+Shift+V`, or `Shift+Insert`.
- Press `Shift+F3` to quit the app.
- The app also shows a tray icon in the Windows notification area, so you can confirm it is running and quit it from the caret menu.

## Desktop stack

The overlay uses `PySide6` instead of `tkinter`, because this machine's Python install does not include a usable Tcl/Tk runtime. Qt packages its own UI runtime, which makes this desktop utility much more reliable on Windows here.

## Setup

From this folder:

```powershell
cd C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\openai-cursor-transcriber
.\setup.bat
```

That script creates a local `.venv`, installs dependencies, and copies `.env.example` to `.env` the first time.

## Where to put your API key

Put it in:

[`C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\openai-cursor-transcriber\.env`](C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\openai-cursor-transcriber\.env)

Use this format:

```dotenv
OPENAI_API_KEY=your_real_api_key_here
```

You can also change the hotkeys in the same file:

```dotenv
TOGGLE_HOTKEY=<f3>
EXIT_HOTKEY=<shift>+<f3>
PASTE_HOTKEYS=<ctrl>+v,<ctrl>+<shift>+v,<shift>+<insert>,<ctrl>+c
RECORDING_READY_DELAY_MS=0
```

The built-in app hotkeys live in `.env`. If you create a Windows desktop shortcut and give that shortcut its own keyboard shortcut, that is a separate Windows setting stored on the `.lnk` file, not in `.env`.

## Run it

```powershell
.\run.bat
```

`run.ps1` prefers `pythonw.exe`, so the app can run quietly in the background without leaving a console window open.

For the simplest double-click launch, use [`Start Cursor Transcriber.vbs`](C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\openai-cursor-transcriber\Start Cursor Transcriber.vbs). That starts the app hidden in the background.
Launching it again now will not start a second competing copy of the app. Instead, it shows a small "already running" message and exits.
When it is running, you should also see a small tray icon under the Windows notification-area caret, with a menu for status, shortcuts, and quit.

To open your Windows Startup folder, press `Win + R`, type `shell:startup`, and press Enter.
The full path is:

```text
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

## Notes

- The overlay shows a wrapped preview, while the full transcript goes to the clipboard.
- Right-click context-menu paste is not intercepted, so the cursor tag clears automatically only for the configured keyboard shortcuts such as `Ctrl+V`, `Shift+Insert`, or `Ctrl+C`.
- If Windows blocks microphone access, enable microphone permission in Windows Settings.
- Logs are written to [`C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\openai-cursor-transcriber\runtime\app.log`](C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\openai-cursor-transcriber\runtime\app.log).

## OpenAI references

- [Speech to text guide](https://developers.openai.com/api/docs/guides/speech-to-text)
- [GPT-4o Transcribe model](https://developers.openai.com/api/docs/models/gpt-4o-transcribe)
