# Drawing image copy safety

In the Anki note editor, right-click an image and choose **Draw on Image**.
Use **Ctrl+C** or **Copy & Close** when finished. Both save a recovery PNG,
copy the complete annotated image, and check the clipboard before closing.
The original image and note are unchanged; paste the copied image where needed.

The copy includes both native image data and PNG data. Temporary clipboard
failures are retried up to six times. A failed or incomplete copy keeps the
drawing window open, shows an error, and lets you try again. Repeated Ctrl+C
presses cannot start overlapping copies. The dialog does not write to the
clipboard again after closing.

**Recovery Copies** opens the add-on's `user_files/annotated_images` folder.
Every copy attempt saves a uniquely named PNG there before accessing the
clipboard. These files survive reinstalls and are kept until you delete them.
If a recovery file cannot be written and verified, the drawing stays open.
A later clipboard change by another application cannot be prevented; use the
recovery PNG if the copied image is subsequently replaced.

Close Anki, then reinstall from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-pocket-knife\install_to_anki.ps1"
```

Restart Anki to load the updated code.

Regression tests use real PyQt6 rendering with simulated clipboard contention,
missing formats, wrong pixels, clipboard replacement, and storage failures.
They do not modify your system clipboard. Run with a Python containing PyQt6:

```powershell
& "$env:LOCALAPPDATA\AnkiProgramFiles\.venv\Scripts\python.exe" tests/test_draw_on_image_copy.py
```
