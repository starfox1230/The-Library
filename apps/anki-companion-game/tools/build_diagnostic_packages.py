"""Apply identical observational logging to source tracks or a frozen archive.

No gameplay/render/audio/haptic implementation is edited. Frozen packages have
an explicit build ID and a sidecar provenance manifest with original SHA256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "diagnostics"
MODULES = {"__init__.py": "addon_init.py", "diagnostic_logging.py": "diagnostic_logging.py",
           "diagnostic_browser.js": "diagnostic_browser.js"}


def support_source(source):
    source = source.replace('button.setMinimumWidth(148)',
                            'button.setMinimumWidth(180 if button_text == "Copy Support Report" else 148)')
    if 'button_text="Copy Support Report"' in source:
        return source
    anchor = "        root.addStretch(1)"
    assert source.count(anchor) == 1
    card = '''        from .diagnostic_logging import copy_support_report
        root.addWidget(
            _action_card(
                self,
                icon="↗",
                icon_color="#7fb0ff",
                title="Anki closed unexpectedly?",
                detail="Copy recent diagnostic events, including the previous Anki session. "
                       "The report contains technical events, not card content. Nothing is sent automatically.",
                button_text="Copy Support Report",
                callback=copy_support_report,
            )
        )
'''
    source = source.replace(anchor, card + anchor)
    return source.replace("self.resize(650, 400)", "self.resize(650, 520)")


def update_track(directory):
    for target, original in MODULES.items():
        (directory / target).write_bytes((SHARED / original).read_bytes())
    path = directory / "support_dialog.py"
    path.write_text(support_source(path.read_text(encoding="utf-8")), encoding="utf-8")
    info = directory / "build_info.py"
    namespace = {}
    exec(info.read_text(encoding="utf-8"), namespace)
    build = namespace["BUILD_ID"]
    original_source = info.read_text(encoding="utf-8")
    if "+diagnostics.1" not in build:
        info.write_text(original_source.rstrip() + '\nBUILD_ID += "+diagnostics.1"\n', encoding="utf-8")
        build += "+diagnostics.1"
    print(directory.name, build)


def package_track(directory):
    excludes = {"tests", "user_files", "__pycache__", ".pytest_cache", ".ankiaddon-build", ".build-poc", ".build-release"}
    excluded_files = {"install_to_anki.ps1", "install_to_anki.sh", "build_ankiaddon.ps1", "build_ankiaddon.sh",
                      "generate_web_assets.py", "apply_event_wav_fade.ps1", "trim_audio_to_trimmed.ps1",
                      "SpeedStreakHaptics-diagnostic.json"}
    identity = json.loads((directory / "manifest.json").read_text())["package"]
    output = directory / (identity + ".ankiaddon")
    temporary = directory / (identity + ".diagnostic-build.zip")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob("*")):
            relative = path.relative_to(directory)
            if not path.is_file() or any(part in excludes or part.startswith(".edge") for part in relative.parts):
                continue
            if path.name in excluded_files or path.suffix in {".ankiaddon", ".zip", ".pyc", ".sqlite3"}:
                continue
            archive.write(path, relative.as_posix())
    temporary.replace(output)
    print("Built", output)


def frozen(source, output, build):
    before = {}
    with zipfile.ZipFile(source) as archive:
        assert archive.testzip() is None
        before = {entry.filename: archive.read(entry) for entry in archive.infolist() if not entry.is_dir()}
    namespace = {}
    exec(before["build_info.py"].decode(), namespace)
    original_build = namespace["BUILD_ID"]
    after = dict(before)
    after.update({target: (SHARED / original).read_bytes() for target, original in MODULES.items()})
    after["build_info.py"] = ('BUILD_ID = ' + json.dumps(build) + '\n').encode()
    after["support_dialog.py"] = support_source(before["support_dialog.py"].decode()).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(after.items()):
            archive.writestr(name, data)
    changed = sorted(name for name, data in after.items() if before.get(name) != data)
    assert set(changed) <= {"__init__.py", "diagnostic_logging.py", "diagnostic_browser.js", "build_info.py", "support_dialog.py"}
    provenance = dict(base_build=original_build, build=build, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                      package_sha256=hashlib.sha256(output.read_bytes()).hexdigest(), modified_entries=changed,
                      purpose="Observational logging only; no proposed crash fix or new features.")
    output.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(output, json.dumps(provenance))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracks", nargs="*", choices=["2.05", "2.06", "2.07"], default=[])
    parser.add_argument("--frozen", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--build")
    parser.add_argument("--package-tracks", action="store_true")
    args = parser.parse_args()
    for version in args.tracks:
        directory = ROOT / ("speed-streak-addon-v" + version)
        update_track(directory)
        if args.package_tracks:
            package_track(directory)
    if args.frozen:
        if not args.output or not args.build:
            parser.error("--frozen requires --output and --build")
        frozen(args.frozen, args.output, args.build)
