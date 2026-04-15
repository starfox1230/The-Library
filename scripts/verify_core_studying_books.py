#!/usr/bin/env python3
"""Verify core-studying book registrations, manifests, and referenced files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_STUDYING_DIR = REPO_ROOT / "apps" / "core-studying"
BOOKS_JSON_PATH = CORE_STUDYING_DIR / "books.json"
CHAPTER_META_KEYS = {"title", "introFile", "introTitle", "sections"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify apps/core-studying books.json, manifests, and referenced section files."
    )
    parser.add_argument(
        "--book",
        action="append",
        help="Only verify the named book from books.json. Repeat to verify multiple books.",
    )
    return parser.parse_args()


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc


def ensure_string(value: object, *, label: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: expected a non-empty string")
        return None
    return value


def verify_section(
    *,
    book_name: str,
    base_dir: Path,
    section_key: str,
    section_value: object,
    location: str,
    errors: list[str],
) -> int:
    if not isinstance(section_value, dict):
        errors.append(f"{book_name} {location} {section_key}: expected an object")
        return 0

    ensure_string(section_value.get("title"), label=f"{book_name} {location} {section_key}.title", errors=errors)
    file_value = ensure_string(
        section_value.get("file"),
        label=f"{book_name} {location} {section_key}.file",
        errors=errors,
    )
    if file_value is not None and not (base_dir / Path(file_value)).exists():
        errors.append(
            f"{book_name} {location} {section_key}: referenced file not found: {(base_dir / Path(file_value))}"
        )
    return 1


def iter_sections(chapter_value: dict[str, object]) -> tuple[dict[str, object], str]:
    nested = chapter_value.get("sections")
    if nested is not None:
        if not isinstance(nested, dict):
            raise TypeError('"sections" must be an object when present')
        return nested, "sections"

    flat_sections = {
        key: value
        for key, value in chapter_value.items()
        if key not in CHAPTER_META_KEYS
    }
    return flat_sections, "flat"


def verify_book(book_name: str, book_info: object) -> tuple[int, list[str], list[str]]:
    errors: list[str] = []
    messages: list[str] = []

    if not isinstance(book_info, dict):
        return 0, messages, [f"{book_name}: expected books.json entry to be an object"]

    base_path_value = ensure_string(book_info.get("basePath"), label=f"{book_name}.basePath", errors=errors)
    manifest_value = ensure_string(book_info.get("manifest"), label=f"{book_name}.manifest", errors=errors)
    if base_path_value is None or manifest_value is None:
        return 0, messages, errors

    base_dir = CORE_STUDYING_DIR / Path(base_path_value)
    manifest_path = CORE_STUDYING_DIR / Path(manifest_value)

    if not base_dir.exists():
        errors.append(f"{book_name}: basePath does not exist: {base_dir}")
    if not manifest_path.exists():
        errors.append(f"{book_name}: manifest does not exist: {manifest_path}")
        return 0, messages, errors

    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict) or not manifest:
        errors.append(f"{book_name}: manifest must be a non-empty JSON object")
        return 0, messages, errors

    section_count = 0
    chapter_count = 0
    for chapter_key, chapter_value in manifest.items():
        chapter_count += 1
        if not isinstance(chapter_value, dict):
            errors.append(f"{book_name} {chapter_key}: expected chapter entry to be an object")
            continue

        ensure_string(
            chapter_value.get("title"),
            label=f"{book_name} {chapter_key}.title",
            errors=errors,
        )

        intro_file = chapter_value.get("introFile")
        if intro_file is not None:
            intro_title = chapter_value.get("introTitle")
            ensure_string(
                intro_title if intro_title is not None else "Chapter intro",
                label=f"{book_name} {chapter_key}.introTitle",
                errors=errors,
            )
            intro_path_value = ensure_string(
                intro_file,
                label=f"{book_name} {chapter_key}.introFile",
                errors=errors,
            )
            if intro_path_value is not None and not (base_dir / Path(intro_path_value)).exists():
                errors.append(
                    f"{book_name} {chapter_key}: introFile not found: {(base_dir / Path(intro_path_value))}"
                )

        try:
            sections, mode = iter_sections(chapter_value)
        except TypeError as exc:
            errors.append(f"{book_name} {chapter_key}: {exc}")
            continue

        if not sections:
            errors.append(f"{book_name} {chapter_key}: no sections found")
            continue

        for section_key, section_value in sections.items():
            section_count += verify_section(
                book_name=book_name,
                base_dir=base_dir,
                section_key=section_key,
                section_value=section_value,
                location=f"{chapter_key} ({mode})",
                errors=errors,
            )

    messages.append(
        f"OK  {book_name}: chapters={chapter_count}, sections={section_count}, manifest={manifest_path.relative_to(REPO_ROOT)}"
    )
    return section_count, messages, errors


def main() -> int:
    args = parse_args()
    books_data = load_json(BOOKS_JSON_PATH)
    if not isinstance(books_data, dict) or not books_data:
        raise SystemExit(f"{BOOKS_JSON_PATH}: expected a non-empty JSON object")

    selected_names = args.book or list(books_data)
    unknown = [name for name in selected_names if name not in books_data]
    if unknown:
        raise SystemExit("Unknown books: " + ", ".join(unknown))

    total_sections = 0
    all_messages: list[str] = []
    all_errors: list[str] = []

    for book_name in selected_names:
        section_count, messages, errors = verify_book(book_name, books_data[book_name])
        total_sections += section_count
        all_messages.extend(messages)
        all_errors.extend(errors)

    for message in all_messages:
        print(message)

    if all_errors:
        print("\nErrors:", file=sys.stderr)
        for error in all_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"\nVerified {len(selected_names)} book(s) and {total_sections} referenced section file(s) in apps/core-studying."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
