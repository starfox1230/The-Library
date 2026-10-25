#!/usr/bin/env python3
"""Generate an app-scoped pre-cache list from local runtime assets and imports."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = re.compile(r"(?:from\s*|import\s*)[\"'](\./[^\"']+)[\"']")


def main():
    files = {"./", "./index.html", "./styles.css", "./manifest.webmanifest", "./vendor/pixi-8.22.0.min.js", "./assets/catalog.json", "./assets/sources.json"}
    pending = [ROOT / "app.js"]
    while pending:
        source = pending.pop()
        rel = "./" + source.relative_to(ROOT).as_posix()
        if rel in files:
            continue
        files.add(rel)
        for request in MODULE.findall(source.read_text(encoding="utf-8")):
            target = (source.parent / request[2:]).resolve()
            if target.exists(): pending.append(target)
            else: raise SystemExit(f"Missing imported module: {request} in {source}")
    catalog = json.loads((ROOT / "assets/catalog.json").read_text(encoding="utf-8"))
    for pack in catalog["packs"].values():
        files.update(item["src"] for item in pack["frames"].values())
    files.update(f"./{p.relative_to(ROOT).as_posix()}" for p in (ROOT / "icons").glob("*.png"))
    files.add("./icons/source.svg")
    ordered = sorted(files)
    (ROOT / "precache-manifest.js").write_text("self.QUIET_HARBOR_ASSETS = " + json.dumps(ordered, indent=2) + ";\n", encoding="utf-8")
    print(f"Generated a scoped offline list for {len(ordered)} files.")


if __name__ == "__main__": main()
