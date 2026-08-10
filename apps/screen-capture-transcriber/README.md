# Screen Capture Transcriber

A Windows-first personal recorder for study videos and lectures. It records a selected
screen region plus the audio Windows is sending to the active output device, creates a
separate transcription-ready MP3, and can send the audio to OpenAI for transcription.
Anatomy study mode also captures timestamped stills, provides
a native-resolution arrow/drawing editor, builds a clickable video review, and can
package labeled structures as `saCloze++` Anki cards.

## The fast workflow

1. Select the area to record.
2. Confirm the system-audio row shows the expected output, such as `TOSHIBA-TV`.
3. Press **Start Recording** or `F8`.
4. For anatomy, press `.` or the camera icon on the recording boundary. The app pauses
   the player and recorder together, then opens the paused frame for arrows, drawing,
   and an optional label.
5. For a non-visual concept you want to remember, press `Backspace`. The app captures
   the source-video timestamp, pauses video and recording together, and focuses a
   learning-note editor with nearby transcript context. Save or cancel to resume.
6. Press **Save & Resume**. Recording restarts and the app replays a normal click at the
   same player location, so paused study time is omitted from the final recording.
7. Press `F8` to finish.
8. Open **Session Review**, or choose a transcription model and press **Transcribe**.
9. Copy the transcript alone or the transcript with clearly labeled learning notes.

Recording never requires an API key or internet connection. Transcription is separate
and resumable, so a failed API request cannot destroy the local recording.

## Past Sessions

Press **Past Sessions** at the top of the app to search and sort previous recordings.
The library shows each session's date, title, duration, anatomy-capture count,
learning-note count,
total on-disk size, transcript availability, and processing state. The selected
session's size is repeated in the detail panel, and the footer shows the combined
size of the currently visible sessions.

The detail panel provides direct actions:

- **Review Session** opens the video, timestamped learning notes, anatomy gallery,
  and transcript together.
- **Edit Anatomy Screenshots** opens the non-destructive post-session editor.
- **Copy Codex Anki Prompt** copies a complete local-file-aware build request and
  saves the same prompt as `codex-anki-prompt.txt` in the session folder.
- **Play Recording** opens the final video without opening File Explorer.
- **Open Transcript** opens the saved Markdown transcript directly.
- The learning-notes panel supports timestamp-ordered review, editing, deletion,
  individual copying, and opening the final recording at the associated moment.
- **Copy Transcript** preserves the original transcript-only behavior.
- **Copy Transcript + Notes** appends a clearly labeled `User Learning Notes` section;
  user text is never presented as spoken transcript.
- **Load in Main Window** restores the session title, region, anatomy list,
  transcript, duration, and model in the recorder UI.
- **Open Folder in Explorer** remains available when raw files are needed, but is not
  required for normal review.
- **Delete Session…** asks for explicit confirmation, then permanently deletes the
  entire session folder, including its video, audio, transcript, screenshots, edits,
  review page, metadata, and local APKG. Cards that were already imported into Anki
  remain in Anki's separate collection and media folder.

The anatomy review page remembers video position in browser local storage, so reopening
the same review continues where it was last stopped. Loading is intentionally
read-only: starting a recording afterward creates a new session rather than silently
overwriting the old final video or invalidating its transcript.

Review thumbnails always fit their cards and use a viewport-limited height, so an entire
capture remains visible even when the source screenshot is large. Clicking a thumbnail
still seeks the video to that timestamp. Its separate **Expand** button opens a
full-window, aspect-ratio-preserving view; clicking anywhere or pressing `Esc` closes it.
Accepted post-session screenshot edits immediately regenerate the review page and its
Anki-card badges. If the review is already open, returning to its browser tab checks for
the regenerated page and reloads it while preserving the saved video position.

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
- `anatomy-review.html` is the combined session review; learning notes and anatomy
  images jump the video to their associated recording timestamps.
- The optional `.apkg` uses the repository's canonical `saCloze++` note model, `Text`
  and `Extra` fields, the `Saved Cards` deck, and a dated `#AnkiChat` tag.
- `session.json` preserves region, device, segments, anatomy captures,
  stable timestamped learning-note objects, state, estimates, and warnings.
- `transcript.md` is the copy-friendly timestamped transcript.
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

## Browser-linked Medality and YouTube mode

The bundled private Chrome extension is the preferred path for Medality and also
detects YouTube. It does not require the Chrome Web Store:

1. Start the desktop app.
2. Open `chrome://extensions`.
3. Enable **Developer mode** and choose **Load unpacked**.
4. Select the app's `chrome-extension` folder.
5. Reload any Medality or YouTube lesson that was already open.

When several supported videos are open, use the **Browser video** selector in the
desktop app to choose the exact tab. Starting a recording locks that tab as the source.
Other Medality and YouTube tabs cannot consume play/pause commands, pause the recorder,
replace the title, or contribute a transcript to that session.

Medality uses a Vimeo video element inside a `player.vimeo.com` frame. The extension
reads the real element's `currentTime`, `duration`, `paused`, `seeking`, and
`playbackRate` values. This also detects Medality's stale-speed condition in which a
new lesson retains a saved 2× preference but actually starts at 1×. When a linked
recording begins, the app applies that saved rate to the real video before playing.

In linked mode:

- starting the recorder arms the capture before the extension plays the lesson;
- a webpage pause stops the active recording segment;
- a webpage play while paused is briefly intercepted until the recorder is armed;
- seeking and playback-rate changes close one source-time span and open another;
- screenshot, `.`, boundary pause, resume, and stop use direct video commands
  instead of approximated mouse clicks;
- anatomy captures retain the source-video timestamp;
- `Backspace` captures an intentional learning note at the current source timestamp,
  including immediately after using the video seek/scrubber control;
  `Ctrl+Enter` saves it from the note editor,
- the note editor's **-** and **+** controls resize both the note and nearby
  transcript text, and the selected size is remembered across app restarts,
  unless focus is already in a webpage text field; `Ctrl+Backspace` is untouched;
- finalization builds a newest-take-wins timeline, so rewatching 03:35–03:50 replaces
  only that source interval instead of adding a duplicate passage;
- unwatched source intervals are preserved as an explicit gap list and coverage
  percentage in `session.json`.

When Medality provides its transcript drawer, the extension temporarily opens it if
needed, imports its timestamp/text cue pairs, and returns the drawer to its prior state.
YouTube's built-in transcript panel is handled the same way. The selected source
transcript is saved as `transcript.md` and `transcript.json` and becomes the default
text shown in the app. No OpenAI request is needed. After recording, the transcription
button reads **Replace with AI Transcript** so an API-generated version remains
available as an explicit override.

Raw segments remain non-destructive. The clean `recording.mkv`, `recording.mp4`, and
`audio.mp3` are rebuilt from the chosen source-time intervals, while the original
segment files remain available for recovery.

The extension communicates only with the desktop app's loopback endpoint at
`127.0.0.1:43129`. It sends playback metadata—not cookies, credentials, lesson media,
or page contents.

If no supported player heartbeat is available when Start Recording is pressed, the
app clearly labels the session **Fallback** and explains whether the extension was
missing or the current player was unsupported. It then opens the existing
play/pause-point selector and retains the previous workflow.

## Anatomy pause and annotation

A three-pixel cyan-blue, click-through border traces the exact selected recording area
for the entire time capture is active. It is painted as one continuous square-cornered
rectangle matching the region-selection outline, while the interior remains completely
unobstructed. Windows capture exclusion prevents the outline from being burned into the
saved video.

A compact icon-only control panel hugs the upper-right perimeter with crisp vector
camera, pause/resume, and stop icons. Its physical size follows the selected monitor's
Windows display scaling so the complete tray remains visible instead of clipping.
While paused, the boundary changes from blue to amber and the pause icon becomes play.
Pausing closes the current media segment cleanly; resuming starts the next segment, so
paused time is omitted from the final joined recording. The topmost boundary remains
visible while paused or while another window is in front, and the panel uses the same
capture exclusion as the outline.

Before each new recording, the app covers the selected area and asks for one stable
play/pause point. Click the middle of the video surface when the player supports
click-anywhere toggling; this is more reliable than a control that hides until hover.
The setup click is blocked from the webpage, a yellow marker confirms the chosen point,
and **Use This Point** starts the synchronized workflow.

The recorder starts its segment before clicking the selected point to play. Pause,
anatomy screenshot, `.`, stop, and resume all reuse that same point.
For a pause or screenshot, the player is clicked first and the recording segment is
then closed; for resume, the new recording segment starts before the player is clicked.

While actively recording, `.` is a global shortcut for the same action as the border's
camera button: it pauses the selected player, closes the current recording segment, and
opens the screenshot editor. The shortcut is disabled as soon as recording pauses, so
inside the screenshot editor `.` retains its motion-crop behavior.

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
transcript, every annotated screenshot, the canonical card-style and packaging guides,
and the canonical `saCloze++` model builder. It clearly separates intentional visual
captures from intentional non-visual learning notes. Visual targets retain this layout:

```html
What is indicated by the <span style="color: #FFAA00;">yellow arrow</span>?<br><br>{{c1::ANSWER}}<br><br><img src="ANNOTATED_IMAGE_BASENAME.png">
```

The requested visual answer is the capture name. Every timestamped learning note must
also yield a text-first non-visual `saCloze++` candidate for the point the user selected;
the copied prompt embeds the full timestamped transcript as well as the note timestamp
and nearby context. The full transcript is supporting context, not permission to mine
unrelated facts.
The prompt requires `Saved Cards`, fields named `Text` and `Extra`, the canonical dated
tag, stable GUIDs based on capture indices or note IDs, packaged local media, a
machine-readable manifest, and validation before Codex reports the APKG as ready. It
also requires Codex to return clickable links for both the APKG and its containing
folder instead of a bare path. A durable copy is saved beside the recording.

## Long recordings

OpenAI file uploads are limited to 25 MB. The app keeps normal lecture audio compact,
and automatically divides any oversized transcription section into overlapping
20-minute requests.
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
bar, the current request, and elapsed time. The Transcribe button and top
status indicator also remain in a busy state until the result is saved.

Every successful API response is written immediately under
`transcription/chapter-NNN/response-NNN.txt` before the app performs later merging or
formatting. If local post-processing fails after every request has already returned,
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
- [GPT Transcribe](https://developers.openai.com/api/docs/models/gpt-transcribe)
- [Microsoft WASAPI loopback recording](https://learn.microsoft.com/en-us/windows/win32/coreaudio/loopback-recording)
- [PyAudioWPatch WASAPI loopback](https://github.com/s0d3s/PyAudioWPatch)
- [FFmpeg gdigrab options](https://ffmpeg.org/doxygen/7.1/gdigrab_8c.html)
