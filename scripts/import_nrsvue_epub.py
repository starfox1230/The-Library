#!/usr/bin/env python3
"""Import NRSVue Bible text from an EPUB into Scripture Copier JSON files."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path


OT_BOOKS = [
    "genesis", "exodus", "leviticus", "numbers", "deuteronomy", "joshua",
    "judges", "ruth", "1samuel", "2samuel", "1kings", "2kings",
    "1chronicles", "2chronicles", "ezra", "nehemiah", "esther", "job",
    "psalms", "proverbs", "ecclesiastes", "songofsolomon", "isaiah",
    "jeremiah", "lamentations", "ezekiel", "daniel", "hosea", "joel",
    "amos", "obadiah", "jonah", "micah", "nahum", "habakkuk", "zephaniah",
    "haggai", "zechariah", "malachi",
]

HEADING_CLASSES = {
    "ah1", "ahaft1", "bh", "bhaft", "bhaft1", "bk1", "bk2", "bk3", "bk4",
    "chaft", "cs", "ct", "ctfm",
}


class VerseParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.verses: dict[tuple[int, int, int], list[str]] = defaultdict(list)
        self.current: tuple[int, int, int] | None = None
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = set((attr.get("class") or "").split())
        if classes & HEADING_CLASSES:
            self.current = None
        if tag == "a" and "fnref" in classes:
            self.skip_depth += 1
            return
        verse_id = attr.get("id") or ""
        match = re.fullmatch(r"v(\d{2})(\d{3})(\d{3})", verse_id)
        if match:
            self.current = tuple(map(int, match.groups()))

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.skip_depth:
            self.skip_depth -= 1
        elif tag in {"p", "div", "br"} and self.current and not self.skip_depth:
            self.verses[self.current].append(" ")

    def handle_data(self, data: str) -> None:
        if self.current and not self.skip_depth:
            # Verse-number spans contain only the numeric label.
            if not (data.strip().isdigit() and not self.verses[self.current]):
                self.verses[self.current].append(data)


def normalize(parts: list[str]) -> str:
    text = "".join(parts)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("epub", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    all_verses: dict[tuple[int, int, int], list[str]] = {}
    with zipfile.ZipFile(args.epub) as epub:
        for name in epub.namelist():
            if name.startswith("text/") and name.endswith((".html", ".xhtml")):
                verse_parser = VerseParser()
                verse_parser.feed(epub.read(name).decode("utf-8", "replace"))
                all_verses.update(verse_parser.verses)

    args.output.mkdir(parents=True, exist_ok=True)
    for book_number, slug in enumerate(OT_BOOKS, start=1):
        chapters: dict[int, dict[int, str]] = defaultdict(dict)
        for (book, chapter, verse), parts in all_verses.items():
            if book == book_number:
                chapters[chapter][verse] = normalize(parts)

        if not chapters:
            raise SystemExit(f"No verses found for {slug} (book {book_number})")

        payload = {
            "_id": slug,
            "title": slug,
            "translation": "NRSVue",
            "chapters": [
                {
                    "number": chapter,
                    "verses": [
                        {"text": verses[verse]}
                        for verse in range(1, max(verses) + 1)
                    ],
                }
                for chapter, verses in sorted(chapters.items())
            ],
        }
        path = args.output / f"{slug}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Imported {len(OT_BOOKS)} Old Testament books into {args.output}")


if __name__ == "__main__":
    main()
