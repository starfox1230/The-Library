"""Apply the focused Time Drain undo fix to a source tree or frozen package."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "undo-hotfix" / "time_drain_undo.py"
SUFFIX = "+time-drain-undo.1"


def patch_reviewer(source: str) -> str:
    source = source.replace("\r\n", "\n")
    # Keep the frequent non-review timer path free of collection queries when
    # there are no deferred cards. Also normalizes previews made by this tool.
    source = source.replace('''    def _restore_deferred_time_drain_cards(self) -> bool:
        if not queue_changes_allowed(getattr(mw, "col", None)):
            return False
        if not self._deferred_time_drain_card_ids:
            return False
''', '''    def _restore_deferred_time_drain_cards(self) -> bool:
        if not self._deferred_time_drain_card_ids:
            return False
        if not queue_changes_allowed(getattr(mw, "col", None)):
            return False
''')
    marker = "from .time_drain_undo import automatic_queue_change, queue_changes_allowed, is_review_undo\n"
    if marker in source:
        return source
    source = source.replace("from __future__ import annotations\n", "from __future__ import annotations\n\n" + marker, 1)
    anchor = "    def _get_next_v3_card_with_time_drain_reordering(self, reviewer: Reviewer, original: Any) -> None:\n"
    assert source.count(anchor) == 1
    source = source.replace(anchor, anchor + '''        # Undo must be allowed to present restored cards without re-burying
        # them. Redo remains available until the next deliberate collection edit.
        if not queue_changes_allowed(getattr(mw, "col", None)):
            original(reviewer)
            return

''', 1)
    # Keep each track's queue selection, Sprint Time and visuals unchanged.
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    bury = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_bury_queued_time_drain_card")
    start = next(n for n in bury.body if isinstance(n, ast.Try)).lineno - 1
    end = bury.end_lineno
    lines[start:end] = ['        with automatic_queue_change(getattr(mw, "col", None)) as allowed:\n',
                        '            if not allowed:\n', '                return False\n'] + ["    " + line if line.strip() else line for line in lines[start:end]]
    source = "".join(lines)
    anchor = "    def _restore_deferred_time_drain_cards(self) -> bool:\n        if not self._deferred_time_drain_card_ids:\n            return False\n"
    assert source.count(anchor) == 1
    source = source.replace(anchor, anchor + '''        if not queue_changes_allowed(getattr(mw, "col", None)):
            return False
''', 1)
    old = '''                unbury_cards([card_id])
                restored = True
'''
    new = '''                # Undo may already have restored this card. Never unbury a
                # card subsequently buried manually or suspended by the user.
                if mw.col.get_card(card_id).queue != -2:
                    continue
                with automatic_queue_change(mw.col) as allowed:
                    if not allowed:
                        self._remember_deferred_time_drain_card(card_id)
                        continue
                    unbury_cards([card_id])
                    restored = True
'''
    assert source.count(old) == 1
    source = source.replace(old, new, 1)
    # Non-answer undos must not consume a review snapshot or Sprint Time undo.
    tree = ast.parse(source)
    undo = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "on_state_did_undo")
    guard = undo.body[0]
    assert isinstance(guard, ast.If) and "no_undo_mode" in ast.unparse(guard.test)
    lines = source.splitlines(keepends=True)
    lines[guard.end_lineno:guard.end_lineno] = ['        if not is_review_undo(getattr(mw, "col", None), changes):\n', '            return\n']
    result = "".join(lines)
    ast.parse(result)
    return result


def build_label(data: bytes) -> bytes:
    namespace = {}
    exec(data.decode("utf-8"), namespace)
    build = namespace["BUILD_ID"]
    if SUFFIX not in build:
        build += SUFFIX
    return ("BUILD_ID = " + json.dumps(build) + "\n").encode()


def patch_directory(directory: Path) -> None:
    reviewer = directory / "reviewer_overlay.py"
    reviewer.write_text(patch_reviewer(reviewer.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    (directory / "time_drain_undo.py").write_text(HELPER.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    build = directory / "build_info.py"
    build.write_bytes(build_label(build.read_bytes()))
    print("Patched", directory)


def patch_package(source: Path, output: Path) -> None:
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    with zipfile.ZipFile(source) as archive:
        assert archive.testzip() is None
        before = {n: archive.read(n) for n in archive.namelist() if not n.endswith("/")}
    after = dict(before)
    after["reviewer_overlay.py"] = patch_reviewer(before["reviewer_overlay.py"].decode("utf-8")).encode()
    after["build_info.py"] = build_label(before["build_info.py"])
    after["time_drain_undo.py"] = HELPER.read_text(encoding="utf-8").encode()
    changed = sorted(n for n in after if before.get(n) != after[n])
    assert set(changed) <= {"reviewer_overlay.py", "build_info.py", "time_drain_undo.py"}
    if not changed and source.resolve() == output.resolve():
        print("Already patched", output)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".undo-build.zip")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(after.items()):
            archive.writestr(name, data)
    temporary.replace(output)
    provenance = dict(source_sha256=source_hash,
                      package_sha256=hashlib.sha256(output.read_bytes()).hexdigest(), modified_entries=changed,
                      purpose="Time Drain undo fix only; all other archive entries are byte-identical.")
    output.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print("Built", output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.directory:
        patch_directory(args.directory)
    if args.package:
        if not args.output:
            parser.error("--package requires --output")
        patch_package(args.package, args.output)
