"""Package only reviewed runtime files, never captures, dependencies or test fixtures."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json

ROOT = Path(__file__).resolve().parents[1]
FILES = ["manifest.json", "core.js", "db.js", "background.js", "capture.js", "content.js", "library.html", "library.css", "library.js"]
manifest = json.loads((ROOT / "extension/manifest.json").read_text(encoding="utf-8"))
output = ROOT / "downloads/radprimer-case-library.zip"
output.parent.mkdir(exist_ok=True)
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for name in FILES:
        archive.write(ROOT / "extension" / name, name)
with ZipFile(output) as archive:
    assert sorted(archive.namelist()) == sorted(FILES)
    assert archive.testzip() is None
print(f"Built {output.name} v{manifest['version']} ({output.stat().st_size:,} bytes; {len(FILES)} runtime files)")
