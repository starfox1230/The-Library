# Screen Capture Transcriber

A Windows-first personal recorder for study videos and lectures. It records a selected
screen region plus the audio Windows is sending to the active output device, creates a
separate transcription-ready MP3, stores chapter markers, and can send the audio to
OpenAI for transcription. Anatomy study mode also captures timestamped stills, provides
a native-resolution arrow/drawing editor, builds a clickable video review, and can
package labeled structures as `saCloze++` Anki cards.

## The fast workflow

1. Select an area, or use the primary screen.
2. Confirm the system-audio row shows the expected output, such as `TOSHIBA-TV`.
3. Press **Start Recording** or `F8`.
4. Press **Add Chapter** or `F9` whenever the topic changes.
5. For anatomy, Ctrl+left-click the video player. That click pauses the player and the
   recorder, then opens the paused frame for arrows, drawing, and an optional label.
6. Press **Save & Resume**. Recording restarts and the app replays a normal click at the
   same player location, so paused study time is omitted from the final recording.
7. Press `F8` to finish.
8. Open **Anatomy Review**, or choose a transcription model and press **Transcribe**.
9. Press **Copy All** to move the Markdown transcript into ChatGPT or another workflow.

Recording never requires an API key or internet connection. Transcription is separate
and resumable, so a failed API request cannot destroy the local recording.

## Past Sessions

Press **Past Sessions** at the top of the app to search and sort previous recordings.
The library shows each session's date, title, duration, anatomy-capture count,
transcript availability, and processing state.

The detail panel provides direct actions:

- **Review Anatomy** opens the timestamped image gallery and video.
- **Edit Anatomy Screenshots** opens the non-destructive post-session editor.
- **Copy Codex Anki Prompt** copies a complete local-file-aware build request and
  saves the same prompt as `codex-anki-prompt.txt` in the session folder.
- **Play Recording** opens the final video without opening File Explorer.
- **Open Transcript** opens the saved Markdown transcript directly.
- **Load in Main Window** restores the session title, region, chapters, anatomy list,
  transcript, duration, and model in the recorder UI.
- **Open Folder in Explorer** remains available when raw files are needed, but is not
  required for normal review.

The anatomy review page remembers video position in browser local storage, so reopening
the same review continues where it was last stopped. Loading is intentionally
read-only: starting a recording afterward creates a new session rather than silently
overwriting the old final video or invalidating its transcript.

## Setup

Open PowerShell in this folder:

```powershell
cd C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\screen-capture-transcriber
.\setup.ps1
```

The setup script creates an isolated `.venv`, installs the Windows WASAPI/Qt/OpenAI
dependencies, and creates `.env` from `.env.example`.

FFmpeg is also required. The app automatically finds FFmpeg installed by WinGet on this
machine. On a different Windows installation, use:

```powershell
winget install Gyan.FFmpeg
```

or set `FFMPEG_PATH` in `.env`.

## Add the OpenAI API key

Recording works without a key. To enable transcription, edit:

```text
C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\screen-capture-transcriber\.env
```

and set:

```dotenv
OPENAI_API_KEY=your_real_key_here
```

The `.env` file is ignored by Git.

## Run

```powershell
.\run.ps1
```

For a quiet double-click launch, use `Start Screen Capture Transcriber.vbs`.
The app and its Windows shortcut use `assets/app-icon.ico`.

## Files created

Every capture gets its own folder under `recordings`:

```text
2026-07-24_14-30-00_Lecture-name/
  session.json
  segments/
    segment-001-screen.mp4
    segment-001-audio.wav
    segment-001.mkv
    segment-001.mp3
    segment-002-...
  anatomy/
    capture-001-original.png
    capture-001-annotated.png
    capture-001-edit.json
  recording.mkv
  recording.mp4
  audio.mp3
  anatomy-review.html
  anki-notes.json
  Lecture-name-anatomy.apkg
  transcript.md
  transcript.json
  transcription/
```

- `recording.mkv` is the combined video and system audio.
- `recording.mp4` is the browser-friendly copy used by anatomy review.
- `audio.mp3` is mono 16 kHz audio optimized for transcription and easy listening.
- `anatomy-review.html` contains a gallery whose images jump the video to their exact
  recording timestamps.
- The optional `.apkg` uses the repository's canonical `saCloze++` note model, `Text`
  and `Extra` fields, the `Saved Cards` deck, and a dated `#AnkiChat` tag.
- `session.json` preserves region, device, segments, chapters, anatomy captures, state,
  estimates, and warnings.
- `transcript.md` is the copy-friendly chaptered transcript.
- Raw capture files are retained so a failed post-processing step can be recovered.

## Audio-device behavior

The first audio entry is **Follow Windows default**. At the start of every recording,
the app asks WASAPI for the current default output and opens its loopback device. That
means a Toshiba HDMI television is selected when Windows is currently playing through
that television, while headphones or speakers are selected on later recordings when
they become the default.

The live meter confirms that actual output samples are reaching the recorder. If you
change or unplug the output in the middle of this MVP's recording, stop the capture,
press **Refresh**, and start a new recording. Automatic mid-recording endpoint stitching
is intentionally left for the reliability phase rather than silently risking missing
audio.

Each resumed anatomy segment reopens the selected output. When **Follow Windows
default** is selected, an output change made while the annotation editor is open is
picked up on Resume.

## Anatomy pause and annotation

A thin red, click-through border remains visible just outside the selected recording
area for the entire time capture is active. Because the strips sit outside the selected
pixels, they identify the boundary without being burned into the recorded image.

Ctrl+left-click is intentionally passive: the original click still reaches the web
page or desktop player, while the recorder notices it globally. Click the normal
play/pause surface inside the selected capture area. Avoid using it on hyperlinks,
because some sites assign a special meaning to Ctrl+click.

`F10` is the universal fallback for players that do not respond normally to a modified
click. Pause that player with its own control, press `F10`, annotate, then press its
play control after the recorder resumes.

The editor defaults to the same `#FFAA00` yellow-orange used by Anki Pocket Knife. Pen
strokes are smoothed, arrows use rounded geometry, and all marks remain as drawing
commands until Save; the final PNG is rendered once at the source frame's native
resolution instead of repeatedly resampling a screenshot.

The annotation window is built once in the background when the app starts. On an
anatomy pause, the exact last frame is extracted before segment audio/video conversion
begins, then inserted into that existing window. On the current full-resolution test
capture, frame extraction plus editor loading measured approximately 0.43 seconds.

Fast annotation shortcuts:

- `Enter`: save the annotation, resume recording, and replay the source-player click.
- `Ctrl+Backspace`: discard the annotation and resume.
- `.`: enter motion-crop mode; press `.` again to apply.
- `Backspace` while cropping: cancel the current crop operation.

In motion-crop mode, moving the mouse upward expands the crop vertically, downward
shrinks it vertically, right expands it horizontally, and left shrinks it horizontally.
Holding `Ctrl` while moving preserves the crop dimensions and moves the whole crop in
the same direction. The pointer is hidden and continuously recentered in this mode, so
the edge of the monitor never limits further movement; the crop rectangle itself remains
clamped to the source image. The regular **Crop** button instead provides conventional
draggable corners, sides, and interior movement.

The untouched source frame, crop rectangle, and vector drawing commands are all stored
separately. **Clear Drawing** removes every arrow/pen stroke while preserving the base
image, and **Reset Crop** returns to the full original frame.

For a screenshot-only capture, clear the Anki checkbox or leave the structure blank.
For a structure card, add a label and keep the checkbox enabled. The resulting prompt
is “What is indicated by the yellow arrow?” with the answer as a cloze and
the annotated image on the front.

## Editing screenshots after recording

Open **Past Sessions → Edit Anatomy Screenshots**, or load a session and press
**Edit Anatomy Screenshots** beneath its anatomy list. Select any capture to:

- change its capture name or structure label;
- add, undo, or completely clear arrows and pen strokes;
- crop using the standard or motion controls;
- reset the crop to the original frame;
- enable or disable its Anki card.

Saving regenerates the annotated PNG, anatomy review page, notes manifest, and—when
applicable—the `saCloze++` APKG. Older captures created before edit metadata existed
retain their existing flattened drawing when opened. The app saves that legacy image
as a preserved layer, so renaming or cropping does not remove its arrows. Press
**Clear Drawing** only when you explicitly want to return to the untouched source
frame and redraw from scratch.

## Copying an Anki build prompt for Codex

Press **Copy Codex Anki Prompt** beneath the current anatomy list or from
**Past Sessions**. The copied prompt includes absolute paths to the session manifest,
every annotated screenshot, the canonical card-style and packaging guides, and the
canonical `saCloze++` model builder. It asks Codex to make one card for each labeled
capture marked for Anki with this `Text` layout:

```html
What is indicated by the <span style="color: #FFAA00;">yellow arrow</span>?<br><br>{{c1::ANSWER}}<br><br><img src="ANNOTATED_IMAGE_BASENAME.png">
```

The requested answer is the capture name. The prompt also requires `Saved Cards`,
fields named `Text` and `Extra`, the canonical dated tag, stable GUIDs, packaged local
media, a machine-readable manifest, and validation before Codex reports the APKG as
ready. A durable copy is saved beside the recording so it can be reused later even
after the clipboard changes.

## Chapters and long recordings

Chapter markers are timestamps in `session.json`; the video is not destructively cut.
You can double-click chapter titles to rename them. During transcription, the app
extracts each chapter independently, so the resulting Markdown keeps exact manual
chapter boundaries.

OpenAI file uploads are limited to 25 MB. The app keeps normal lecture audio compact,
and automatically divides any chapter over 24 MB into overlapping 20-minute requests.
It passes preceding transcript context and removes repeated overlap when combining the
parts.

## Cost display

Before transcription, the UI estimates cost from recording duration:

- GPT-4o mini Transcribe: approximately `$0.003/minute`
- GPT-4o Transcribe and diarization: approximately `$0.006/minute`
- Whisper: `$0.006/minute`

GPT-4o transcription is actually token-billed, so its preflight number is explicitly an
estimate. When the API returns usage counts, the app calculates and stores the actual
token cost in `session.json` and `transcript.json`.

## Transcription progress and recovery

While a request is running, the Transcript panel shows a prominent animated progress
bar, the current chapter/request, and elapsed time. The Transcribe button and top
status indicator also remain in a busy state until the result is saved.

Every successful API response is written immediately under
`transcription/chapter-NNN/response-NNN.txt` before the app performs later merging or
formatting. If local post-processing fails after every chapter has already returned,
the app automatically reconstructs `transcript.md` and `transcript.json` without
sending or charging for another API request and records the original issue in
`transcription-recovery.txt`. A real failure creates `transcription-error.txt` with
the model, exception, and traceback for diagnosis.

## Current intentional limits

- Windows only.
- A selected region must remain on one monitor.
- The app follows the output that is default when each recording segment starts; it
  does not reconnect in the middle of a playing segment after an HDMI/Bluetooth switch.
- Screen and WASAPI audio are captured independently and synchronized from monotonic
  start times during per-segment post-processing. Study pauses are removed by joining
  complete segments. This is suitable for lectures and study material, but should be
  validated before frame-accurate production use.
- Protected/DRM video may intentionally block screen or loopback capture.
- The app does not record the microphone; it records system output only.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## API references

- [OpenAI speech-to-text guide](https://developers.openai.com/api/docs/guides/speech-to-text)
- [GPT-4o mini Transcribe](https://developers.openai.com/api/docs/models/gpt-4o-mini-transcribe)
- [GPT-4o Transcribe](https://developers.openai.com/api/docs/models/gpt-4o-transcribe)
- [Microsoft WASAPI loopback recording](https://learn.microsoft.com/en-us/windows/win32/coreaudio/loopback-recording)
- [PyAudioWPatch WASAPI loopback](https://github.com/s0d3s/PyAudioWPatch)
- [FFmpeg gdigrab options](https://ffmpeg.org/doxygen/7.1/gdigrab_8c.html)
