from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import zipfile

try:
    import zstandard as zstd
except ImportError as exc:  # pragma: no cover - dependency guard
    raise SystemExit(
        "Missing dependency: zstandard\n\n"
        "Install it with:\n"
        "  py -m pip install --user zstandard\n"
    ) from exc


IMAGE_RE = re.compile(r"<img\s+src=", re.IGNORECASE)
CLOZE_RE = re.compile(r"\{\{c\d+::", re.IGNORECASE)
MOST_LIKELY_DX_RE = re.compile(r"\bmost likely diagnosis\?", re.IGNORECASE)
CLINICAL_STEM_RE = re.compile(
    r"\b(year-old|year old|man with|woman with|patient with)\b",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract a recent-style snapshot from an Anki backup .colpkg. "
            "Useful for tracking note-type mix, image usage, and sample card wording."
        )
    )
    parser.add_argument(
        "--profile",
        default="Default",
        help="Anki profile name under %%APPDATA%%\\Anki2 (default: Default).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="How many recent notes to analyze (default: 200).",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=12,
        help="How many recent notes to include in the output sample (default: 12).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write JSON output. Prints to stdout if omitted.",
    )
    return parser.parse_args()


def backups_dir_for_profile(profile: str) -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is not set.")
    return Path(appdata) / "Anki2" / profile / "backups"


def latest_backup_path(profile: str) -> Path:
    backup_dir = backups_dir_for_profile(profile)
    backups = sorted(
        backup_dir.glob("backup-*.colpkg"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not backups:
        raise FileNotFoundError(f"No backups found in {backup_dir}")
    return backups[0]


def decompress_backup_database(colpkg_path: Path) -> Path:
    temp_dir = Path(tempfile.gettempdir()) / "anki_recent_style_snapshot"
    temp_dir.mkdir(parents=True, exist_ok=True)
    db_path = temp_dir / f"{colpkg_path.stem}.sqlite3"

    with zipfile.ZipFile(colpkg_path, "r") as archive:
        if "collection.anki21b" not in archive.namelist():
            raise RuntimeError(
                f"{colpkg_path.name} does not contain collection.anki21b."
            )
        compressed = archive.read("collection.anki21b")

    dctx = zstd.ZstdDecompressor()
    with io.BytesIO(compressed) as source, open(db_path, "wb") as target:
        dctx.copy_stream(source, target)

    return db_path


def _unicase(a: str | None, b: str | None) -> int:
    a_folded = "" if a is None else str(a).casefold()
    b_folded = "" if b is None else str(b).casefold()
    return (a_folded > b_folded) - (a_folded < b_folded)


def open_collection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.create_collation("unicase", _unicase)
    connection.row_factory = sqlite3.Row
    return connection


def _split_fields(raw_fields: str) -> list[str]:
    return str(raw_fields or "").split("\x1f")


def _sample_field_text(raw_html: str, *, limit: int = 280) -> str:
    text = str(raw_html or "").replace("\n", " ").strip()
    return text if len(text) <= limit else f"{text[:limit]}..."


def build_snapshot(connection: sqlite3.Connection, *, limit: int, sample_size: int) -> dict[str, object]:
    cursor = connection.cursor()
    recent_rows = cursor.execute(
        """
        SELECT
            n.id,
            n.tags,
            n.sfld,
            n.flds,
            nt.name AS notetype,
            GROUP_CONCAT(DISTINCT d.name) AS decks
        FROM (
            SELECT *
            FROM notes
            ORDER BY id DESC
            LIMIT ?
        ) n
        JOIN notetypes nt ON nt.id = n.mid
        LEFT JOIN cards c ON c.nid = n.id
        LEFT JOIN decks d ON d.id = c.did
        GROUP BY n.id, n.tags, n.sfld, n.flds, nt.name
        ORDER BY n.id DESC
        """,
        (int(limit),),
    ).fetchall()

    summary: dict[str, object] = {
        "recent_notes": len(recent_rows),
        "by_notetype": {},
        "with_images": 0,
        "text_only": 0,
        "most_likely_diagnosis": 0,
        "clinical_stem": 0,
        "extra_nonempty": 0,
        "avg_images_per_note": 0.0,
        "avg_clozes_per_note": 0.0,
        "max_images": 0,
        "max_clozes": 0,
    }

    by_notetype: dict[str, int] = {}
    total_images = 0
    total_clozes = 0
    samples: list[dict[str, object]] = []

    for row in recent_rows:
        fields = _split_fields(row["flds"])
        text_field = fields[0] if fields else ""
        extra_field = fields[1] if len(fields) > 1 else ""
        image_count = len(IMAGE_RE.findall(row["flds"] or ""))
        cloze_count = len(CLOZE_RE.findall(row["flds"] or ""))
        notetype = str(row["notetype"] or "Unknown")

        by_notetype[notetype] = by_notetype.get(notetype, 0) + 1
        total_images += image_count
        total_clozes += cloze_count
        summary["max_images"] = max(int(summary["max_images"]), image_count)
        summary["max_clozes"] = max(int(summary["max_clozes"]), cloze_count)

        if image_count > 0:
            summary["with_images"] = int(summary["with_images"]) + 1
        else:
            summary["text_only"] = int(summary["text_only"]) + 1

        if extra_field.strip():
            summary["extra_nonempty"] = int(summary["extra_nonempty"]) + 1

        sfld = str(row["sfld"] or "")
        if MOST_LIKELY_DX_RE.search(sfld):
            summary["most_likely_diagnosis"] = int(summary["most_likely_diagnosis"]) + 1
        if CLINICAL_STEM_RE.search(sfld):
            summary["clinical_stem"] = int(summary["clinical_stem"]) + 1

        if len(samples) < sample_size:
            samples.append(
                {
                    "id": int(row["id"]),
                    "notetype": notetype,
                    "decks": [] if row["decks"] is None else str(row["decks"]).split(","),
                    "tags": str(row["tags"] or "").split(),
                    "image_count": image_count,
                    "cloze_count": cloze_count,
                    "text": _sample_field_text(text_field),
                    "extra": _sample_field_text(extra_field),
                }
            )

    note_count = max(len(recent_rows), 1)
    summary["avg_images_per_note"] = round(total_images / note_count, 2)
    summary["avg_clozes_per_note"] = round(total_clozes / note_count, 2)
    summary["by_notetype"] = dict(sorted(by_notetype.items(), key=lambda item: (-item[1], item[0].casefold())))

    return {
        "summary": summary,
        "samples": samples,
    }


def main() -> int:
    args = parse_args()
    backup_path = latest_backup_path(args.profile)
    db_path = decompress_backup_database(backup_path)

    with open_collection(db_path) as connection:
        snapshot = build_snapshot(
            connection,
            limit=max(int(args.limit), 1),
            sample_size=max(int(args.sample_size), 1),
        )

    payload = {
        "profile": args.profile,
        "backup_path": str(backup_path),
        "db_path": str(db_path),
        **snapshot,
    }

    output_text = json.dumps(payload, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_text, encoding="utf-8")
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
