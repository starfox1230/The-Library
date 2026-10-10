"""Check frozen-package scope, shared instrumentation and local active builds."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
source = ROOT / "baselines/speed_streak_2_05_user_requests_12.ankiaddon"
output = ROOT / "releases/speed_streak_2_05_macos_diagnostic_1.ankiaddon"
provenance = json.loads(output.with_suffix(".provenance.json").read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest() == provenance["source_sha256"]
assert hashlib.sha256(output.read_bytes()).hexdigest() == provenance["package_sha256"]
with zipfile.ZipFile(source) as before, zipfile.ZipFile(output) as after:
    assert after.testzip() is None
    changed = {name for name in after.namelist() if name not in before.namelist() or before.read(name) != after.read(name)}
    assert set(before.namelist()) <= set(after.namelist())
    assert changed == set(provenance["modified_entries"])
    assert changed == {"__init__.py", "build_info.py", "support_dialog.py", "diagnostic_browser.js", "diagnostic_logging.py"}
    assert before.read("manifest.json") == after.read("manifest.json")
    for name in ("diagnostic_logging.py", "diagnostic_browser.js"):
        assert after.read(name) == (ROOT / name).read_bytes()
    for name in after.namelist():
        if name.endswith(".py"):
            compile(after.read(name), name, "exec")
print("Frozen published baseline: five diagnostic entries only; hashes, Python syntax and identity verified.")

for version in ("2.05", "2.07"):
    track = ROOT.parent / ("speed-streak-addon-v" + version)
    archive_path = track / ("speed_streak_v" + version.replace(".", "_") + ".ankiaddon")
    if not (track / "reviewer_overlay.py").exists():
        print("Local feature baseline unavailable:", version)
        continue
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        for target, original in (("__init__.py", "addon_init.py"), ("diagnostic_logging.py", "diagnostic_logging.py"),
                                 ("diagnostic_browser.js", "diagnostic_browser.js")):
            assert (track / target).read_bytes() == (ROOT / original).read_bytes()
            assert archive.read(target) == (ROOT / original).read_bytes()
        for name in ("build_info.py", "support_dialog.py", "reviewer_overlay.py", "web/overlay.js", "web/audio_feedback.js"):
            assert archive.read(name) == (track / name).read_bytes()
        build = {}
        exec(archive.read("build_info.py"), build)
        assert build["BUILD_ID"].endswith("+diagnostics.1")
        assert 'button_text="Copy Support Report"' in archive.read("support_dialog.py").decode()
        assert not any("__pycache__" in name or name.startswith(("tests/", "user_files/")) for name in archive.namelist())
    print("Active local package verified:", build["BUILD_ID"])
