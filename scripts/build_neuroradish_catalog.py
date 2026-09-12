"""Build a current, categorized catalog of the NeuroRadish YouTube channel.

The script intentionally keeps the source inventory (YouTube metadata) separate
from the study-oriented classification fields so that the catalog can be
refreshed without losing the organization logic.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from yt_dlp import YoutubeDL


CHANNEL_ID = "UCnTMr6JCu3V1ghhlz3vcBcQ"
CHANNEL_URL = "https://www.youtube.com/@neuroradish"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "exports" / "neuroradish"


def seconds_to_hms(value):
    if value is None:
        return ""
    seconds = int(round(float(value)))
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


def number_from_title(pattern: str, title: str, default=0):
    match = re.search(pattern, title, re.I)
    return int(match.group(1)) if match else default


def classify(title: str, duration: float | None):
    clean = re.sub(r"\s+", " ", title.replace("#shorts", "").strip())
    lower = clean.lower()

    # Primary track, then the logical study sequence within that track.
    if re.search(r"board review.*?\bcase\s+\d+\b", lower):
        domain = "Board review — brain"
        if "head/neck" in lower:
            domain = "Board review — head & neck"
            domain_order = 3
        elif "pediatric" in lower:
            domain = "Board review — pediatric"
            domain_order = 4
        elif "spine" in lower:
            domain = "Board review — spine"
            domain_order = 2
        else:
            domain_order = 1
        case_number = number_from_title(r"case\s+(\d+)", lower)
        return {
            "track": "Board Review Cases",
            "category": domain,
            "subcategory": "Numbered case series",
            "format": "Long-form case review",
            "order_key": (20, domain_order, case_number, clean.lower()),
            "series_number": case_number,
        }

    if "board review case list" in lower:
        return {
            "track": "Board Review Cases",
            "category": "Board review — index",
            "subcategory": "Case navigation",
            "format": "Long-form orientation",
            "order_key": (29, 0, 0, clean.lower()),
            "series_number": "",
        }

    if "buzzword" in lower and "core exam" in lower:
        case_number = number_from_title(r"#?\s*(\d+)\s*$", clean)
        return {
            "track": "Core Exam / Buzzword Cases",
            "category": "Buzzword Neuro Core Exam",
            "subcategory": "Individual rapid case",
            "format": "Short case review",
            "order_key": (30, 0, case_number, clean.lower()),
            "series_number": case_number,
        }

    if "rapid" in lower and "board review" in lower:
        if "neuroanatomy" in lower:
            if "sagittal" in lower:
                anatomy_order = 1
            elif "coronal" in lower:
                anatomy_order = 2
            elif "axial" in lower:
                anatomy_order = 3
            elif "skull base" in lower:
                anatomy_order = 4
            else:
                anatomy_order = 5
            return {
                "track": "Rapid Review Compilations",
                "category": "Neuroanatomy rapid review",
                "subcategory": "Cross-sectional anatomy",
                "format": "Rapid compilation",
                "order_key": (41, anatomy_order, 0, clean.lower()),
                "series_number": "",
            }
        if "intraventricular" in lower:
            compilation_order = 1
        elif "tsc" in lower:
            compilation_order = 2
        elif "nf1" in lower:
            compilation_order = 3
        else:
            compilation_order = 4
        first_case = number_from_title(r"cases?\s+(\d+)", lower)
        return {
            "track": "Rapid Review Compilations",
            "category": "Rapid board review — case compilations",
            "subcategory": "Themed or sequential compilation",
            "format": "Rapid compilation",
            "order_key": (40, compilation_order, first_case, clean.lower()),
            "series_number": first_case or "",
        }

    if "rapid" in lower and "board review" in lower:
        first_case = number_from_title(r"cases?\s+(\d+)", lower)
        return {
            "track": "Rapid Review Compilations",
            "category": "Rapid board review — case compilations",
            "subcategory": "Themed or sequential compilation",
            "format": "Rapid compilation",
            "order_key": (40, 4, first_case, clean.lower()),
            "series_number": first_case or "",
        }

    if "multiple choice" in lower and "sign" in lower:
        return {
            "track": "Neuroradiology Signs",
            "category": "Sign review — multiple choice",
            "subcategory": "Named imaging sign identification",
            "format": "Long-form quiz",
            "order_key": (50, 0, 0, clean.lower()),
            "series_number": "",
        }

    if "sign" in lower:
        is_short = "#shorts" in title.lower() or (
            duration is not None and duration <= 180
        )
        return {
            "track": "Neuroradiology Signs",
            "category": "Sign shorts" if is_short else "Sign explanations",
            "subcategory": "Named imaging sign",
            "format": "Short" if is_short else "Short-form teaching",
            "order_key": (60 if is_short else 50, 0, 0, clean.lower()),
            "series_number": "",
        }

    if "mri physics" in lower:
        part = number_from_title(r"part\s+(\d+)", lower)
        return {
            "track": "Foundations & Approach",
            "category": "Clinical MRI physics",
            "subcategory": "Three-part foundation series",
            "format": "Long-form lecture",
            "order_key": (10, 1, part, clean.lower()),
            "series_number": part,
        }

    if "temporal bone" in lower:
        part = number_from_title(r"part\s+(\d+)", lower)
        return {
            "track": "Foundations & Approach",
            "category": "CT temporal bone",
            "subcategory": "Step-by-step interpretation",
            "format": "Long-form tutorial",
            "order_key": (10, 8, part, clean.lower()),
            "series_number": part,
        }

    if "mass lesion crossing corpus callosum" in lower:
        order = 6
        category = "Differential diagnosis tutorials"
        subcategory = "Mass lesion differential"
    elif "dwi" in lower or "restricted diffusion" in lower:
        order = 3
        category = "MRI interpretation fundamentals"
        subcategory = "Diffusion-weighted imaging"
    elif "brain mri" in lower:
        order = 2
        category = "MRI interpretation fundamentals"
        subcategory = "Systematic brain MRI approach"
    elif "mass effect" in lower or "brain herniation" in lower:
        order = 4
        category = "MRI interpretation fundamentals"
        subcategory = "Mass effect and herniation"
    elif "neuroanatomy" in lower or "limbic system" in lower or "hypothalamus" in lower:
        order = 5
        category = "Neuroanatomy foundations"
        subcategory = "Anatomy and pathways"
    elif "posterior fossa" in lower:
        order = 7
        category = "Pediatric neuroradiology foundations"
        subcategory = "Posterior fossa malformations"
    else:
        order = 9
        category = "Other teaching"
        subcategory = "Unclassified teaching video"

    return {
        "track": "Foundations & Approach",
        "category": category,
        "subcategory": subcategory,
        "format": "Long-form tutorial",
        "order_key": (10, order, 0, clean.lower()),
        "series_number": "",
    }


def fetch_entries():
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "ignoreerrors": True,
    }
    with YoutubeDL(options) as ydl:
        entries = []
        seen = set()
        for suffix in ("/videos", "/shorts"):
            playlist = ydl.extract_info(CHANNEL_URL + suffix, download=False)
            for entry in playlist.get("entries") or []:
                if not entry or not entry.get("id") or entry["id"] in seen:
                    continue
                seen.add(entry["id"])
                entries.append(entry)
    return entries


def normalized(entry):
    title = entry.get("title") or "(untitled)"
    duration = entry.get("duration")
    classification = classify(title, duration)
    upload_date = entry.get("upload_date") or ""
    if upload_date and len(upload_date) == 8:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    return {
        "video_id": entry["id"],
        "title": title,
        "url": f"https://www.youtube.com/watch?v={entry['id']}",
        "upload_date": upload_date,
        "duration_seconds": int(round(duration)) if duration is not None else "",
        "duration": seconds_to_hms(duration),
        "views": entry.get("view_count") if entry.get("view_count") is not None else "",
        "description": (entry.get("description") or "").strip(),
        "series_number": classification.pop("series_number"),
        **classification,
    }


def write_outputs(rows):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = [
        "catalog_order", "track", "category", "subcategory", "format",
        "title", "series_number", "duration", "upload_date", "views",
        "video_id", "url", "description",
    ]
    for index, row in enumerate(rows, 1):
        row["catalog_order"] = index

    with (OUTPUT_DIR / "neuroradish_video_catalog.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    with (OUTPUT_DIR / "neuroradish_video_catalog.json").open("w", encoding="utf-8") as handle:
        json.dump({
            "source": {
                "channel": CHANNEL_URL,
                "channel_id": CHANNEL_ID,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "video_count": len(rows),
            },
            "videos": rows,
        }, handle, ensure_ascii=False, indent=2)

    grouped = defaultdict(list)
    for row in rows:
        grouped[row["track"]].append(row)

    lines = [
        "# NeuroRadish YouTube Video Catalog",
        "",
        f"Source: [{CHANNEL_URL}]({CHANNEL_URL})  ",
        f"Retrieved: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"Inventory: **{len(rows)} videos** (including Shorts)",
        "",
        "This is a study-oriented reordering of the channel inventory. The original YouTube title, upload date, duration, stable video ID, and direct link are preserved in the CSV/JSON exports. Classification is based on the title and available duration; it is intentionally broad where the channel title does not expose the individual diagnosis.",
        "",
        "## Catalog map",
        "",
        "1. Foundations & Approach — start here for MRI physics, systematic interpretation, anatomy, and focused tutorials.",
        "2. Board Review Cases — numbered Brain, Spine, Pediatric, and Head/Neck cases, ordered from Case 1 upward within each domain.",
        "3. Core Exam / Buzzword Cases — individual rapid core-exam cases, ordered numerically.",
        "4. Rapid Review Compilations — grouped board-review and neuroanatomy compilations.",
        "5. Neuroradiology Signs — the multiple-choice sign review followed by sign Shorts alphabetically.",
        "",
    ]
    for track in ("Foundations & Approach", "Board Review Cases", "Core Exam / Buzzword Cases", "Rapid Review Compilations", "Neuroradiology Signs"):
        lines.extend([f"## {track}", ""])
        current_category = None
        for row in grouped.get(track, []):
            if row["category"] != current_category:
                current_category = row["category"]
                lines.extend([f"### {current_category}", ""])
            lines.append(f"{row['catalog_order']}. [{row['title']}]({row['url']}) — {row['duration'] or 'duration unavailable'}; {row['format']}")
        lines.append("")

    lines.extend([
        "## Notes",
        "",
        "- The source inventory is a point-in-time snapshot; YouTube metadata and availability can change.",
        "- “Short” is assigned when the title explicitly includes `#shorts` or the sign video is at most three minutes; YouTube’s Shorts eligibility and display rules can change.",
        "- The numbered Board Review series and Buzzword series are ordered by case number, not by upload date, because that is the most useful study sequence.",
        "- The CSV is the easiest file to sort/filter; the JSON preserves descriptions and machine-readable metadata for the next stage.",
    ])
    (OUTPUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows = [normalized(entry) for entry in fetch_entries()]
    rows.sort(key=lambda row: row["order_key"])
    write_outputs(rows)
    print(json.dumps({
        "count": len(rows),
        "tracks": Counter(row["track"] for row in rows),
        "output_dir": str(OUTPUT_DIR),
    }, indent=2))


if __name__ == "__main__":
    main()
