# MSK Image Bank

The MSK Image Bank is a native PySide6 desktop curation tool for the 50 visually memorable MSK diagnoses in the starter list. It is deliberately small and fast: choose a diagnosis, open the XR/CT/MRI searches in your existing Chrome, then paste screenshots or drop image files/URLs anywhere in the matching modality panel.

## Run locally on Windows

From PowerShell in this folder, install the one UI dependency once:

```powershell
py -m pip install -r .\requirements.txt
```

Then launch it:

```powershell
py .\run_app.py
```

Or double-click/run:

```powershell
.\launch.ps1
```

The launcher opens a native Python window. It does not open Chrome automatically or reposition windows. Clicking a Google Images button opens a new tab in the existing Chrome installation/profile; the app does not attempt split-screen or monitor positioning.

## Workflow

- Click **Google Images** for any modality. **Open all searches** opens XR, CT, and MRI together in Chrome.
- Click anywhere in a modality panel before pressing `Ctrl/Cmd+V` so the screenshot lands in the intended column. Dragging a local image or a browser image/URL anywhere inside that same panel highlights the whole panel and adds the resolved image there.
- The `‹/›` button collapses the left diagnosis panel when you want more room. The three modality panels stay visible and flex to the available width, with text wrapping and no left-to-right scrollbar.
- Each modality accepts multiple images. Add a caption/source note, favorite individual images, or favorite the entire pathology.
- Images always fit their preview without cropping. Click an image preview to open a full-screen viewer; click anywhere or press `Esc` to close it. Right-click a thumbnail or fullscreen image to copy it. **Remove** is available on every image; there is no extra Open button.
- **Copy favorites** copies favorite metadata to the clipboard. **Export** creates a ZIP containing `favorites.json` plus the actual favorite image files. **Import** restores that ZIP later.

Images and metadata are stored under `%LOCALAPPDATA%\MSK Image Bank` (normally `C:\Users\<you>\AppData\Local\MSK Image Bank`). Nothing is uploaded to this repository or to a server. Export periodically for backup.

The findings are concise educational report-style prompts, editable for personal use; they are not a substitute for clinical reference material.
