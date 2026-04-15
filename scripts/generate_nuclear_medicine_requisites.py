#!/usr/bin/env python3
"""Generate Textbook Copier assets for Nuclear Medicine: The Requisites."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import sys
import unicodedata

import fitz

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pdf_text_compare import extract_pdf


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = REPO_ROOT / "apps" / "core-studying" / "Nuclear Medicine - The Requisites"
PDF_PATH = BOOK_DIR / "Nuclear Medicine - The Requisites.pdf"
TXT_DIR = BOOK_DIR / "TXT"
MANIFEST_PATH = BOOK_DIR / "index.json"

CHAPTER_RE = re.compile(r"^(?P<number>\d+)\.\s+(?P<title>.+)$")
APPENDIX_RE = re.compile(r"^Appendix\s+(?P<number>\d+)\.\s+(?P<title>.+)$")
INVALID_FILENAME_CHARS_RE = re.compile(r'[<>:"/\\|?*]')
MULTISPACE_RE = re.compile(r"\s+")
MOJIBAKE_HINT_RE = re.compile(r"[Ãâ€™œžŸ]")

TITLE_OVERRIDES = {
    "Data Acquisition of Emission Tomographyn": "Data Acquisition of Emission Tomography",
}


@dataclass(frozen=True)
class Section:
    key: str
    title: str
    start_page: int
    end_page: int
    file_name: str


@dataclass(frozen=True)
class Chapter:
    key: str
    title: str
    sections: tuple[Section, ...]


@dataclass
class ChapterDraft:
    number: int
    title: str
    start_page: int
    section_starts: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class AppendixDraft:
    title: str
    start_page: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Textbook Copier text files and manifest for Nuclear Medicine: The Requisites."
    )
    parser.add_argument(
        "--extractor",
        choices=("auto", "pdfplumber", "fitz", "ghostscript"),
        default="fitz",
        help="Preferred PDF text extractor backend.",
    )
    return parser.parse_args()


def normalize_title(title: str) -> str:
    title = repair_mojibake(title)
    title = MULTISPACE_RE.sub(" ", title.strip())
    return TITLE_OVERRIDES.get(title, title)


def safe_filename(title: str) -> str:
    ascii_title = (
        unicodedata.normalize("NFKD", title)
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u2212", "-")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    ascii_title = INVALID_FILENAME_CHARS_RE.sub("", ascii_title)
    ascii_title = MULTISPACE_RE.sub(" ", ascii_title).strip().strip(".")
    return ascii_title or "section"


def build_section_text(page_lines: list[list[str]], start_page: int, end_page: int) -> str:
    lines: list[str] = []
    for page_number in range(start_page, end_page + 1):
        lines.extend(repair_mojibake(line) for line in page_lines[page_number - 1])
    return "\n".join(lines).strip() + "\n"


def repair_mojibake(text: str) -> str:
    repaired = text
    while MOJIBAKE_HINT_RE.search(repaired):
        try:
            candidate = repaired.encode("cp1252").decode("utf-8")
        except UnicodeError:
            break
        if candidate == repaired:
            break
        repaired = candidate
    return repaired


def load_outline() -> tuple[list[ChapterDraft], list[AppendixDraft], int, int]:
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"Source PDF not found: {PDF_PATH}")

    document = fitz.open(PDF_PATH)
    page_count = document.page_count
    toc = document.get_toc(simple=True)

    chapters: list[ChapterDraft] = []
    appendices: list[AppendixDraft] = []
    index_start_page = page_count + 1
    current_chapter: ChapterDraft | None = None

    for level, raw_title, page in toc:
        title = normalize_title(raw_title)

        if level == 1 and title == "Index":
            index_start_page = page
            current_chapter = None
            continue

        chapter_match = CHAPTER_RE.match(title)
        if level == 2 and chapter_match:
            current_chapter = ChapterDraft(
                number=int(chapter_match.group("number")),
                title=chapter_match.group("title"),
                start_page=page,
            )
            chapters.append(current_chapter)
            continue

        if level == 3 and current_chapter is not None:
            current_chapter.section_starts.append((title, page))
            continue

        appendix_match = APPENDIX_RE.match(title)
        if level == 1 and appendix_match:
            appendices.append(AppendixDraft(title=title, start_page=page))
            current_chapter = None

    if not chapters:
        raise RuntimeError("No numbered chapters were found in the PDF outline.")

    return chapters, appendices, index_start_page, page_count


def finalize_chapters(
    chapter_drafts: list[ChapterDraft],
    appendix_drafts: list[AppendixDraft],
    index_start_page: int,
    page_count: int,
) -> list[Chapter]:
    chapters: list[Chapter] = []
    appendix_start_page = appendix_drafts[0].start_page if appendix_drafts else None

    for index, draft in enumerate(chapter_drafts):
        next_chapter_start = (
            chapter_drafts[index + 1].start_page if index + 1 < len(chapter_drafts) else None
        )
        chapter_end_page = (
            (next_chapter_start - 1)
            if next_chapter_start is not None
            else (
                (appendix_start_page - 1)
                if appendix_start_page is not None
                else (index_start_page - 1 if index_start_page <= page_count else page_count)
            )
        )

        if not draft.section_starts:
            draft.section_starts.append((draft.title, draft.start_page))

        sections: list[Section] = []
        for section_index, (section_title, section_page) in enumerate(draft.section_starts, start=1):
            next_section_page = (
                draft.section_starts[section_index][1]
                if section_index < len(draft.section_starts)
                else chapter_end_page + 1
            )
            start_page = draft.start_page if section_index == 1 else section_page
            end_page = min(chapter_end_page, next_section_page - 1)
            if end_page < start_page:
                end_page = start_page
            key = f"{draft.number:02d}.{section_index:02d}"
            file_name = f"{key} - {safe_filename(section_title)}.txt"
            sections.append(
                Section(
                    key=key,
                    title=section_title,
                    start_page=start_page,
                    end_page=end_page,
                    file_name=file_name,
                )
            )

        chapters.append(
            Chapter(
                key=f"Chapter{draft.number:02d}",
                title=draft.title,
                sections=tuple(sections),
            )
        )

    return chapters


def finalize_appendices(
    appendix_drafts: list[AppendixDraft],
    index_start_page: int,
    page_count: int,
) -> Chapter | None:
    if not appendix_drafts:
        return None

    sections: list[Section] = []
    for index, draft in enumerate(appendix_drafts):
        next_page = (
            appendix_drafts[index + 1].start_page
            if index + 1 < len(appendix_drafts)
            else (index_start_page if index_start_page <= page_count else page_count + 1)
        )
        end_page = min(page_count, next_page - 1)
        if end_page < draft.start_page:
            end_page = draft.start_page
        letter = chr(ord("A") + index)
        short_title = APPENDIX_RE.match(draft.title).group("title") if APPENDIX_RE.match(draft.title) else draft.title
        file_name = f"Appendix {letter} - {safe_filename(short_title)}.txt"
        sections.append(
            Section(
                key=letter,
                title=draft.title,
                start_page=draft.start_page,
                end_page=end_page,
                file_name=file_name,
            )
        )

    return Chapter(key="Supplement", title="Appendices", sections=tuple(sections))


def write_outputs(chapters: list[Chapter], page_lines: list[list[str]]) -> None:
    TXT_DIR.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, dict[str, object]] = {}
    for chapter in chapters:
        manifest_entry: dict[str, object] = {"title": chapter.title}
        for section in chapter.sections:
            text = build_section_text(page_lines, section.start_page, section.end_page)
            (TXT_DIR / section.file_name).write_text(text, encoding="utf-8")
            manifest_entry[section.key] = {
                "title": section.title,
                "file": f"TXT/{section.file_name}",
            }
        manifest[chapter.key] = manifest_entry

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    chapter_drafts, appendix_drafts, index_start_page, page_count = load_outline()
    chapters = finalize_chapters(
        chapter_drafts,
        appendix_drafts,
        index_start_page=index_start_page,
        page_count=page_count,
    )
    appendices = finalize_appendices(
        appendix_drafts,
        index_start_page=index_start_page,
        page_count=page_count,
    )
    if appendices is not None:
        chapters.append(appendices)

    extraction = extract_pdf(
        PDF_PATH,
        label="nuclear-medicine-requisites",
        extractor=args.extractor,
        strip_page_furniture=True,
    )
    write_outputs(chapters, extraction.page_lines)

    section_total = sum(len(chapter.sections) for chapter in chapters)
    print(f"Wrote {len(chapters)} manifest groups and {section_total} text files to {BOOK_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
