"""Build a reproducible, inspectable ZIP for Chrome's Load unpacked flow."""
from pathlib import Path
import json
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
assert manifest["manifest_version"] == 3
assert manifest["content_scripts"][0]["matches"] == ["https://ankiweb.net/*", "https://ankiuser.net/*"]
assert not manifest.get("permissions") and not manifest.get("host_permissions")
files = ["manifest.json", "README.md", *manifest["content_scripts"][0]["js"],
         *manifest["content_scripts"][0].get("css", [])]
output = root / "dist" / "ankiweb-enhancer-milestone-3.zip"
output.parent.mkdir(exist_ok=True)
with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
    for name in sorted(files):
        entry = ZipInfo(f"ankiweb-enhancer/{name}", date_time=(2026, 10, 9, 0, 0, 0))
        entry.compress_type = ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, (root / name).read_bytes())
with ZipFile(output) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist()) == len(files)
print(output)
