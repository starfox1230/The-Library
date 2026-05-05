#!/usr/bin/env python3
r"""Build aligned English/Spanish Book of Mormon verse data.

The PDF at C:\Users\sterl\Downloads\parallel-bofm-spa-eng.pdf has an extractable
text layer, but the chapter pages at mormono.com already expose clean alternating
English/Spanish verse paragraphs. This script converts those pages into the local
JSON shape consumed by the app.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

from lxml import html
import requests

BASE_URL = "https://mormono.com/spanish/"
OUTPUT = Path(__file__).with_name("scriptures.json")


@dataclass(frozen=True)
class ChapterLink:
    book: str
    chapter: int
    url: str


BOOK_SLUGS = {
    "1 Nephi": "1-nephi",
    "2 Nephi": "2-nephi",
    "Jacob": "jacob",
    "Enos": "enos",
    "Jarom": "jarom",
    "Omni": "omni",
    "Words of Mormon": "words-of-mormon",
    "Mosiah": "mosiah",
    "Alma": "alma",
    "Helaman": "helaman",
    "3 Nephi": "3-nephi",
    "4 Nephi": "4-nephi",
    "Mormon": "mormon",
    "Ether": "ether",
    "Moroni": "moroni",
}

CHURCH_SLUGS = {
    "1 Nephi": "1-ne",
    "2 Nephi": "2-ne",
    "Jacob": "jacob",
    "Enos": "enos",
    "Jarom": "jarom",
    "Omni": "omni",
    "Words of Mormon": "w-of-m",
    "Mosiah": "mosiah",
    "Alma": "alma",
    "Helaman": "hel",
    "3 Nephi": "3-ne",
    "4 Nephi": "4-ne",
    "Mormon": "morm",
    "Ether": "ether",
    "Moroni": "moro",
}


def fetch(url: str) -> html.HtmlElement:
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 BookOfMormonStudyAppBuilder/1.0"},
                timeout=30,
            )
            response.raise_for_status()
            return html.fromstring(response.content)
        except Exception as error:
            last_error = error
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Unable to fetch {url}") from last_error


def chapter_links() -> list[ChapterLink]:
    doc = fetch(BASE_URL)
    links: list[ChapterLink] = []
    seen: set[str] = set()
    for anchor in doc.xpath("//a[@href]"):
        href = urljoin(BASE_URL, anchor.get("href"))
        match = re.search(r"/spanish/([^/]+)/?$", href)
        if not match or href in seen:
            continue
        slug = match.group(1)
        for book, book_slug in BOOK_SLUGS.items():
            prefix = f"{book_slug}-"
            if slug.startswith(prefix):
                chapter_text = slug.removeprefix(prefix)
                if chapter_text.isdigit():
                    links.append(ChapterLink(book, int(chapter_text), href))
                    seen.add(href)
                break
    if len(links) != 239:
        raise RuntimeError(f"Expected 239 chapter links, found {len(links)}")
    return links


def language_for(text: str) -> str:
    normalized = " " + text.lower() + " "
    spanish_score = len(re.findall(r"[áéíóúñ¿¡]", normalized)) * 3
    english_score = 0
    for token in (" que ", " de ", " del ", " el ", " la ", " los ", " las ", " y ", " en ", " por ", " para ", " con ", " no ", " sí ", " he aquí "):
        spanish_score += normalized.count(token)
    for token in (" the ", " and ", " of ", " unto ", " that ", " which ", " yea ", " behold ", " for ", " in ", " with ", " not ", " shall "):
        english_score += normalized.count(token)
    return "es" if spanish_score > english_score else "en"


def parse_chapter(link: ChapterLink) -> list[dict[str, object]]:
    doc = fetch(link.url)
    title_nodes = doc.xpath("//h1")
    title = " ".join(title_nodes[0].text_content().split()) if title_nodes else f"{link.book} {link.chapter}"
    body_text = "\n".join(
        line.strip()
        for line in doc.xpath("//body//text()")
        if line and line.strip()
    )
    lines = [line.strip() for line in body_text.splitlines() if line.strip()]

    verse_pairs: dict[int, dict[str, str]] = {}
    content_started = False
    pending_verse: int | None = None
    for line in lines:
        if line == title:
            content_started = True
            continue
        if not content_started:
            continue
        if "Proudly powered by WordPress" in line:
            break
        if pending_verse is not None:
            line = f"{pending_verse} {line}"
            pending_verse = None

        match = re.match(r"^(\d+)\s*$", line)
        if match:
            pending_verse = int(match.group(1))
            if pending_verse == 0:
                pending_verse = None
            continue

        match = re.match(r"^(\d+)\s+(.+)$", line)
        if not match:
            continue
        verse = int(match.group(1))
        if verse == 0:
            continue
        text = match.group(2).strip()
        pair = verse_pairs.setdefault(verse, {})
        pair[language_for(text)] = text

    verses: list[dict[str, object]] = []
    official_es: dict[int, str] | None = None
    official_en: dict[int, str] | None = None
    for verse in sorted(verse_pairs):
        pair = verse_pairs[verse]
        if "en" not in pair:
            official_en = official_en or parse_church_chapter(link, "eng")
            pair["en"] = official_en.get(verse, "")
        if "es" not in pair:
            official_es = official_es or parse_church_chapter(link, "spa")
            pair["es"] = official_es.get(verse, "")
        if not pair.get("en") or not pair.get("es"):
            raise RuntimeError(f"Missing language text for {link.book} {link.chapter}:{verse}")
        reference = f"{link.book} {link.chapter}:{verse}"
        verses.append(
            {
                "id": f"{BOOK_SLUGS[link.book]}-{link.chapter}-{verse}",
                "book": link.book,
                "chapter": link.chapter,
                "verse": verse,
                "reference": reference,
                "en": pair["en"],
                "es": pair["es"],
            }
        )
    if not verses:
        raise RuntimeError(f"No verses parsed from {link.url}")
    return verses


def parse_church_chapter(link: ChapterLink, lang: str) -> dict[int, str]:
    slug = CHURCH_SLUGS[link.book]
    url = f"https://www.churchofjesuschrist.org/study/scriptures/bofm/{slug}/{link.chapter}?lang={lang}"
    doc = fetch(url)
    lines = [line.strip() for line in doc.xpath("//body//text()") if line and line.strip()]
    verses: dict[int, str] = {}
    current_verse: int | None = None
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_verse, current_parts
        if current_verse is not None and current_parts:
            text = " ".join(" ".join(current_parts).split())
            text = re.sub(r"\s+([,.;:!?])", r"\1", text)
            verses[current_verse] = text
        current_parts = []

    started = False
    for line in lines:
        if line in {"Chapter " + str(link.chapter), "Capítulo " + str(link.chapter)}:
            started = True
            continue
        if not started:
            continue
        if line.startswith("*"):
            break
        if re.fullmatch(r"\d+", line):
            verse = int(line)
            if verse > 0:
                flush()
                current_verse = verse
            continue
        match = re.match(r"^(\d+)\s+(.+)$", line)
        if match:
            flush()
            current_verse = int(match.group(1))
            current_parts = [match.group(2)]
            continue
        if current_verse is not None:
            current_parts.append(line)
    flush()
    return verses


def main() -> None:
    links = chapter_links()
    books: list[dict[str, object]] = []
    all_verses: list[dict[str, object]] = []
    for book in BOOK_SLUGS:
        chapters = [link for link in links if link.book == book]
        book_verses: list[dict[str, object]] = []
        for chapter in chapters:
            print(f"Fetching {chapter.book} {chapter.chapter}")
            book_verses.extend(parse_chapter(chapter))
        books.append(
            {
                "name": book,
                "slug": BOOK_SLUGS[book],
                "chapters": max(v["chapter"] for v in book_verses),
                "verses": len(book_verses),
            }
        )
        all_verses.extend(book_verses)

    payload = {
        "source": {
            "name": "Mormono Spanish-English Book of Mormon",
            "url": BASE_URL,
            "pdfFallback": r"C:\Users\sterl\Downloads\parallel-bofm-spa-eng.pdf",
        },
        "counts": {
            "books": len(books),
            "chapters": len(links),
            "verses": len(all_verses),
        },
        "books": books,
        "verses": all_verses,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(all_verses)} verses")


if __name__ == "__main__":
    main()
