#!/usr/bin/env python3
"""Generate Core Study Organizer video metadata from the playlist tracker.

The playlist tracker remains the canonical list of Radiology Tutorials videos.
This script maps the 104 transcript-backed study sections to playlist entries
8 through 111 and writes a compact companion catalog for static consumers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "apps" / "youtube-radiology-physics" / "index.html"
MANIFEST = ROOT / "apps" / "core-studying" / "YT Physics" / "index.json"
OUTPUT = ROOT / "apps" / "core-studying" / "YT Physics" / "sources.json"


def extract_tracker_videos(html: str) -> list[dict]:
    match = re.search(
        r"const videos = (\[.*?\]);\s*const DEFAULT_SERIES_ORDER",
        html,
        flags=re.DOTALL,
    )
    if not match:
        raise RuntimeError("Could not locate the tracker video array.")
    return json.loads(match.group(1))


def flatten_manifest(manifest: dict) -> list[tuple[str, dict]]:
    sections: list[tuple[str, dict]] = []
    for chapter in manifest.values():
        source = chapter.get("sections", chapter)
        for key, value in source.items():
            if key == "title" or not isinstance(value, dict) or "file" not in value:
                continue
            sections.append((key, value))
    return sections


def main() -> None:
    videos = extract_tracker_videos(TRACKER.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sections = flatten_manifest(manifest)

    transcript_videos = videos[7:]
    if len(transcript_videos) != len(sections):
        raise RuntimeError(
            "Tracker/transcript mismatch: "
            f"{len(transcript_videos)} mapped videos for {len(sections)} sections."
        )

    mapped: dict[str, dict] = {}
    for (section_key, section), video in zip(sections, transcript_videos, strict=True):
        mapped[section_key] = {
            "title": section["title"],
            "file": section["file"],
            "videoId": video["videoId"],
            "youtubeUrl": video["youtubeUrl"],
            "duration": video["duration"],
            "durationSeconds": sum(
                int(part) * (60 ** index)
                for index, part in enumerate(reversed(video["duration"].split(":")))
            ),
            "playlistIndex": video["playlistIndex"],
            "series": video["series"],
        }

    payload = {
        "generatedFrom": "apps/youtube-radiology-physics/index.html",
        "mapping": "Playlist entries 8-111 map in manifest order to YT Physics sections.",
        "sectionCount": len(mapped),
        "sections": mapped,
    }
    OUTPUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(mapped)} section sources to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
