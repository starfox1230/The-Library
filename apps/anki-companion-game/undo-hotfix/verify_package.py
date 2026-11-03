"""Validate the public hotfix's narrow scope, syntax, build ID and provenance."""
import ast
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
source = ROOT.parent / "diagnostics/baselines/speed_streak_2_05_user_requests_12.ankiaddon"
output = ROOT / "releases/speed_streak_2_05_time_drain_undo_1.ankiaddon"
with zipfile.ZipFile(source) as archive:
    before = {n: archive.read(n) for n in archive.namelist() if not n.endswith("/")}
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
    after = {n: archive.read(n) for n in archive.namelist() if not n.endswith("/")}
assert set(after) - set(before) == {"time_drain_undo.py"}
assert not (set(before) - set(after))
changed = {n for n in before if before[n] != after[n]}
assert changed == {"build_info.py", "reviewer_overlay.py"}, changed
for name in changed | {"time_drain_undo.py"}:
    ast.parse(after[name].decode("utf-8"), filename=name)
assert after["time_drain_undo.py"] == (ROOT / "time_drain_undo.py").read_text(encoding="utf-8").encode()
assert b"2.05-user-requests.12+time-drain-undo.1" in after["build_info.py"]
provenance = json.loads(output.with_suffix(".provenance.json").read_text())
assert provenance["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
assert provenance["package_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
print(f"Verified {len(after)} archive entries: only reviewer integration, build ID and the new undo helper changed.")
