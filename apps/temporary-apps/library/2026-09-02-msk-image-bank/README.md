# MSK Image Bank

The MSK Image Bank is a local-first curation tool for the 50 visually memorable MSK diagnoses in the starter list. It is deliberately small and fast: choose a diagnosis, open the XR/CT/MRI searches, then paste screenshots or drop image files/URLs into the matching column.

## Run locally on Windows

From PowerShell in this folder:

```powershell
py .\run_app.py
```

Or double-click/run:

```powershell
.\launch.ps1
```

The launcher serves the app at `http://127.0.0.1:8765` and opens Chrome. Keep the PowerShell window open while using it. No packages or virtual environment are required; it uses Python’s standard library.

## Workflow

- Click **Google images** or **Radiopaedia** for any modality. **Open 3 searches** opens XR, CT, and MRI together.
- Click a modality’s drop zone before pressing `Ctrl/Cmd+V` so the screenshot lands in the intended column. Clicking the zone also opens a file picker; drag-and-drop works too.
- Each modality accepts multiple images. Add a caption/source note, favorite individual images, or favorite the entire pathology.
- **Copy favorites** copies a JSON backup to the clipboard. **Export** downloads the same backup, including pasted image data. **Import** restores it later on this device or another browser.

Images are stored in the browser’s IndexedDB and metadata in local browser storage. Nothing is uploaded to this repository or to a server. Clearing browser site data can remove the collection, so export periodically.

The findings are concise educational report-style prompts, editable for personal use; they are not a substitute for clinical reference material.
