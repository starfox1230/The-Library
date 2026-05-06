#!/usr/bin/env python3
"""Validate temporary app registration in landing pages.

Checks:
1) Every app folder under apps/temporary-apps/library/*/index.html is listed in
   apps/temporary-apps/index.html (TEMP_APPS -> path field).
2) Root landing page index.html links to apps/temporary-apps/index.html.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMP_INDEX = REPO_ROOT / "apps" / "temporary-apps" / "index.html"
ROOT_INDEX = REPO_ROOT / "index.html"
TEMP_LIBRARY = REPO_ROOT / "apps" / "temporary-apps" / "library"

PATH_PATTERN = re.compile(r'path:\s*"([^"]+)"')


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def collect_library_paths() -> set[str]:
    if not TEMP_LIBRARY.exists():
        return set()

    paths: set[str] = set()
    for index_file in TEMP_LIBRARY.glob("**/index.html"):
        relative = index_file.relative_to(REPO_ROOT / "apps" / "temporary-apps")
        paths.add(relative.as_posix())
    return paths


def collect_registered_paths() -> set[str]:
    html = TEMP_INDEX.read_text(encoding="utf-8")
    return set(PATH_PATTERN.findall(html))


def main() -> None:
    if not TEMP_INDEX.exists():
        fail("Missing apps/temporary-apps/index.html")
    if not ROOT_INDEX.exists():
        fail("Missing root index.html")

    library_paths = collect_library_paths()
    registered_paths = collect_registered_paths()

    missing_in_temp_index = sorted(library_paths - registered_paths)
    stale_entries = sorted(registered_paths - library_paths)

    if missing_in_temp_index:
        fail(
            "Found library apps not registered in apps/temporary-apps/index.html: "
            + ", ".join(missing_in_temp_index)
        )

    if stale_entries:
        fail(
            "Found TEMP_APPS entries without matching folder index.html: "
            + ", ".join(stale_entries)
        )

    root_index_html = ROOT_INDEX.read_text(encoding="utf-8")
    if 'href="apps/temporary-apps/index.html"' not in root_index_html:
        fail("Root index.html is missing a Temporary Apps Library link")

    print("OK: Temporary apps library and landing-page links are in sync.")


if __name__ == "__main__":
    main()
