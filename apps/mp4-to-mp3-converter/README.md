# MP4 to MP3 Converter

This is a local-only Windows desktop utility. It does not run in the browser.

## What it does

- Prompts you to choose an `.mp4` as soon as it opens.
- Extracts the first audio stream to a high-quality `.mp3`.
- Saves the output in the same folder as the source video.
- Shows live conversion progress in the window, including percent complete when duration data is available.
- If `filename.mp3` already exists, it creates `filename (1).mp3`, `filename (2).mp3`, and so on.

## Run it

Double-click:

- `Start MP4 to MP3 Converter.vbs`

Or from PowerShell in this folder:

```powershell
.\run.bat
```

## Drag a file in from the command line

You can also pass a file directly:

```powershell
.\run.bat "C:\path\to\video.mp4"
```

That path uses the same conversion logic as the GUI, which is useful for testing and automation.

If you want to call the PowerShell script directly instead of the batch wrapper, use:

```powershell
.\run.ps1 "C:\path\to\video.mp4"
```

## Dependency

This app expects `ffmpeg` to be available on `PATH`.
