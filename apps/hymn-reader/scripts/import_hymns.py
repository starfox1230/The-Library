#!/usr/bin/env python3
"""Extract the two text-only hymn collections into data/hymns.js.

The source exports use h4 elements for verses and p elements for both refrains
and non-lyric notes. Repeated pre-Info paragraphs are refrains. The small set of
one-off refrains is audited below so that explanatory notes never enter lyrics.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


SUPPORTED_TAGS = {"h2", "h3", "h4", "p"}
HEADING_PATTERN = re.compile(r"^(\d+)\.\s*(.+)$")

# These hymn numbers contain genuine lyric paragraphs that occur only once or
# vary slightly between repetitions. All other unique paragraphs are notes.
ONE_OFF_LYRIC_PARAGRAPH_NUMBERS = {
    "home": {1009, 1020, 1021, 1024, 1030, 1053, 1209},
    "classic": {221, 258},
}

# These are one-off notes inside hymns that also have one-off lyric paragraphs.
NOTE_PREFIXES_IN_MIXED_HYMNS = {
    "*Alternate text for baptism day:",
    "“Alleluia” means “praise the Lord.”",
}

# Every source number expected to contain a unique explanatory/performance note.
# An unfamiliar unique paragraph fails the import so it can be reviewed.
AUDITED_NOTE_NUMBERS = {
    "home": {
        1001, 1003, 1005, 1007, 1010, 1016, 1017, 1023, 1031, 1032,
        1033, 1034, 1035, 1039, 1040, 1045, 1053, 1055, 1060, 1202, 1204,
        1207, 1209, 1210,
    },
    "classic": {180, 195, 302, 320},
}


@dataclass
class Element:
    tag: str
    text: str


@dataclass
class SourceHymn:
    number: int
    title: str
    elements: list[Element] = field(default_factory=list)


class HymnHtmlCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current_tag: str | None = None
        self.current_parts: list[str] = []
        self.elements: list[Element] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SUPPORTED_TAGS:
            self.current_tag = tag
            self.current_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag != self.current_tag:
            return
        text = re.sub(r"\s+", " ", "".join(self.current_parts)).strip()
        self.elements.append(Element(tag, text))
        self.current_tag = None
        self.current_parts = []

    def handle_data(self, data: str) -> None:
        if self.current_tag:
            self.current_parts.append(data)


def parse_source(path: Path) -> list[SourceHymn]:
    parser = HymnHtmlCollector()
    parser.feed(path.read_text(encoding="utf-8"))

    hymns: list[SourceHymn] = []
    current: SourceHymn | None = None
    for element in parser.elements:
        if element.tag == "h3":
            if current:
                hymns.append(current)
            heading = HEADING_PATTERN.fullmatch(element.text)
            if not heading:
                raise ValueError(f"Unrecognized hymn heading in {path.name}: {element.text!r}")
            current = SourceHymn(number=int(heading.group(1)), title=heading.group(2))
        elif current:
            current.elements.append(element)

    if current:
        hymns.append(current)
    if not hymns:
        raise ValueError(f"No hymns found in {path}")
    return hymns


def lyric_blocks(hymn: SourceHymn, collection: str) -> tuple[list[str], list[str]]:
    candidates: list[Element] = []
    for element in hymn.elements:
        if element.tag == "p" and element.text.casefold() == "info":
            break
        if element.tag in {"h4", "p"} and element.text:
            candidates.append(element)

    paragraph_counts = Counter(element.text for element in candidates if element.tag == "p")
    included: list[str] = []
    omitted: list[str] = []

    for element in candidates:
        if element.tag == "h4":
            included.append(element.text)
            continue

        is_repeated = paragraph_counts[element.text] > 1
        is_mixed_note = any(element.text.startswith(prefix) for prefix in NOTE_PREFIXES_IN_MIXED_HYMNS)
        is_audited_one_off_lyric = hymn.number in ONE_OFF_LYRIC_PARAGRAPH_NUMBERS[collection]

        if is_repeated or (is_audited_one_off_lyric and not is_mixed_note):
            included.append(element.text)
        else:
            if hymn.number not in AUDITED_NOTE_NUMBERS[collection]:
                raise ValueError(
                    f"Unreviewed unique paragraph in {collection} hymn {hymn.number}: {element.text!r}"
                )
            omitted.append(element.text)

    if not included:
        raise ValueError(f"No lyrics retained for {collection} hymn {hymn.number}")
    return included, omitted


def build_records(classic_path: Path, home_path: Path) -> tuple[list[dict[str, object]], list[tuple[str, int, str]]]:
    records: list[dict[str, object]] = []
    omitted_notes: list[tuple[str, int, str]] = []

    for collection, path in (("classic", classic_path), ("home", home_path)):
        for hymn in parse_source(path):
            blocks, omitted = lyric_blocks(hymn, collection)
            records.append({
                "number": hymn.number,
                "title": hymn.title,
                "lyrics": "\n\n".join(blocks),
            })
            omitted_notes.extend((collection, hymn.number, note) for note in omitted)

    records.sort(key=lambda hymn: int(hymn["number"]))
    numbers = [int(hymn["number"]) for hymn in records]
    duplicates = [number for number, count in Counter(numbers).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate hymn numbers across collections: {duplicates}")
    return records, omitted_notes


def validate_records(records: list[dict[str, object]], expected_count: int) -> None:
    if len(records) != expected_count:
        raise ValueError(f"Expected {expected_count} records, extracted {len(records)}")

    forbidden_fragments = (
        "\nInfo\n",
        "Text:",
        "Music:",
        "All rights reserved",
        "About this hymn",
        "For sacrament,",
        "When played on organ,",
        "May be sung without accompaniment",
    )
    for record in records:
        if set(record) != {"number", "title", "lyrics"}:
            raise ValueError(f"Unexpected fields in hymn {record.get('number')}")
        if not all(str(record[field]).strip() for field in ("number", "title", "lyrics")):
            raise ValueError(f"Blank required field in hymn {record.get('number')}")
        lyrics = str(record["lyrics"])
        found = [fragment for fragment in forbidden_fragments if fragment in lyrics]
        if found:
            raise ValueError(f"Non-lyric text in hymn {record['number']}: {found}")
        if "<" in lyrics or ">" in lyrics:
            raise ValueError(f"HTML markup remains in hymn {record['number']}")


def write_javascript(records: list[dict[str, object]], output_path: Path) -> None:
    payload = json.dumps(records, ensure_ascii=False, indent=2)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "// Generated by scripts/import_hymns.py. Records contain only number, title, and lyrics.\n"
        f"window.HYMN_DATA = {payload};\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--classic", type=Path, required=True)
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=410)
    args = parser.parse_args()

    records, omitted_notes = build_records(args.classic, args.home)
    validate_records(records, args.expected_count)
    write_javascript(records, args.output)

    classic_count = sum(int(record["number"]) < 1000 for record in records)
    home_count = len(records) - classic_count
    print(f"Wrote {len(records)} hymns ({classic_count} classic, {home_count} home and church).")
    print(f"Omitted {len(omitted_notes)} audited non-lyric notes.")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
