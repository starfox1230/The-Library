#!/usr/bin/env python3
"""Extract text from two PDFs and generate comparison reports."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import difflib
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata


PAGE_NUMBER_RE = re.compile(r"^(?:page\s+)?\d+\s*$", re.IGNORECASE)
DEFAULT_CONTEXT_LINES = 3


@dataclass(frozen=True)
class LocatedLine:
    page: int
    line_number: int
    text: str

    def display(self) -> str:
        return f"[p{self.page:03d}] {self.text}"


@dataclass
class PdfExtraction:
    path: Path
    label: str
    extractor: str
    page_lines: list[list[str]]
    lines: list[LocatedLine]

    @property
    def page_count(self) -> int:
        return len(self.page_lines)

    @property
    def line_count(self) -> int:
        return len(self.lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert two PDFs to text, then generate a side-by-side HTML diff plus "
            "structured summaries of every detected change."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("left_pdf", type=Path, help="Path to the older or left-hand PDF.")
    parser.add_argument("right_pdf", type=Path, help="Path to the newer or right-hand PDF.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for extracted text files and comparison reports.",
    )
    parser.add_argument(
        "--left-label",
        default=None,
        help="Display name for the left PDF in the report.",
    )
    parser.add_argument(
        "--right-label",
        default=None,
        help="Display name for the right PDF in the report.",
    )
    parser.add_argument(
        "--extractor",
        choices=("auto", "pdfplumber", "fitz", "ghostscript"),
        default="auto",
        help="Preferred extraction backend.",
    )
    parser.add_argument(
        "--keep-page-furniture",
        action="store_true",
        help="Keep repeated headers, footers, and standalone page numbers in the diff.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    left_pdf = args.left_pdf.resolve()
    right_pdf = args.right_pdf.resolve()

    if not left_pdf.exists():
        raise SystemExit(f"Left PDF not found: {left_pdf}")
    if not right_pdf.exists():
        raise SystemExit(f"Right PDF not found: {right_pdf}")

    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else Path.cwd() / "pdf-compare-output" / build_pair_slug(left_pdf, right_pdf)
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    left = extract_pdf(
        left_pdf,
        label=args.left_label or left_pdf.stem,
        extractor=args.extractor,
        strip_page_furniture=not args.keep_page_furniture,
    )
    right = extract_pdf(
        right_pdf,
        label=args.right_label or right_pdf.stem,
        extractor=args.extractor,
        strip_page_furniture=not args.keep_page_furniture,
    )

    summary = build_comparison(left, right)

    left_text_path = output_dir / f"{safe_stem(left_pdf)}.extracted.txt"
    right_text_path = output_dir / f"{safe_stem(right_pdf)}.extracted.txt"
    base_name = build_pair_slug(left_pdf, right_pdf)
    summary_json_path = output_dir / f"{base_name}.changes.json"
    summary_markdown_path = output_dir / f"{base_name}.summary.md"
    diff_html_path = output_dir / f"{base_name}.diff.html"

    left_text_path.write_text(render_extracted_text(left), encoding="utf-8")
    right_text_path.write_text(render_extracted_text(right), encoding="utf-8")
    summary_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_markdown_path.write_text(render_markdown_summary(summary), encoding="utf-8")
    diff_html_path.write_text(render_html_report(summary), encoding="utf-8")

    print(f"Left extractor:  {left.extractor}")
    print(f"Right extractor: {right.extractor}")
    print(f"Output directory: {output_dir}")
    print(f"Extracted text:  {left_text_path.name}")
    print(f"Extracted text:  {right_text_path.name}")
    print(f"Summary JSON:    {summary_json_path.name}")
    print(f"Summary Markdown:{summary_markdown_path.name}")
    print(f"HTML diff:       {diff_html_path.name}")
    print(
        "Change blocks:   "
        f"{summary['stats']['change_blocks']} "
        f"(similarity {summary['stats']['similarity_ratio']:.2%})"
    )
    return 0


def extract_pdf(
    pdf_path: Path,
    *,
    label: str,
    extractor: str,
    strip_page_furniture: bool,
) -> PdfExtraction:
    candidates = [extractor] if extractor != "auto" else ["pdfplumber", "fitz", "ghostscript"]
    errors: list[str] = []

    for candidate in candidates:
        try:
            raw_pages = extract_pages(pdf_path, candidate)
            page_lines = prepare_page_lines(raw_pages, strip_page_furniture=strip_page_furniture)
            located_lines = [
                LocatedLine(page=page_number, line_number=line_number, text=line)
                for page_number, lines in enumerate(page_lines, start=1)
                for line_number, line in enumerate(lines, start=1)
            ]
            if not located_lines:
                raise RuntimeError("extraction produced no text")
            return PdfExtraction(
                path=pdf_path,
                label=label,
                extractor=candidate,
                page_lines=page_lines,
                lines=located_lines,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{candidate}: {exc}")

    raise RuntimeError(
        "Unable to extract text from PDF. Tried: " + "; ".join(errors)
    )


def extract_pages(pdf_path: Path, extractor: str) -> list[str]:
    if extractor == "pdfplumber":
        return extract_with_pdfplumber(pdf_path)
    if extractor == "fitz":
        return extract_with_fitz(pdf_path)
    if extractor == "ghostscript":
        return extract_with_ghostscript(pdf_path)
    raise ValueError(f"Unsupported extractor: {extractor}")


def extract_with_pdfplumber(pdf_path: Path) -> list[str]:
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        return [normalize_text(page.extract_text() or "") for page in pdf.pages]


def extract_with_fitz(pdf_path: Path) -> list[str]:
    import fitz

    with fitz.open(pdf_path) as document:
        return [normalize_text(page.get_text("text")) for page in document]


def extract_with_ghostscript(pdf_path: Path) -> list[str]:
    gs_path = find_ghostscript()
    if gs_path is None:
        raise RuntimeError("Ghostscript executable not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        output_pattern = temp_root / "page-%03d.txt"
        result = subprocess.run(
            [
                str(gs_path),
                "-q",
                "-sDEVICE=txtwrite",
                "-o",
                str(output_pattern),
                str(pdf_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout).strip() or "Ghostscript failed")

        files = sorted(temp_root.glob("page-*.txt"))
        if not files:
            raise RuntimeError("Ghostscript did not emit any page text files")
        return [normalize_text(path.read_text(encoding="utf-8", errors="replace")) for path in files]


def find_ghostscript() -> Path | None:
    executable_names = ("gswin64c.exe", "gswin32c.exe", "gs")
    for name in executable_names:
        resolved = shutil.which(name)
        if resolved:
            return Path(resolved)

    install_root = Path("C:/Program Files/gs")
    if install_root.exists():
        matches = sorted(install_root.glob("*/bin/gswin64c.exe"), reverse=True)
        if matches:
            return matches[0]
    return None


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = (
        normalized.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\u00a0", " ")
        .replace("\u00ad", "")
    )
    return "\n".join(line.rstrip() for line in normalized.split("\n")).strip("\n")


def prepare_page_lines(raw_pages: list[str], *, strip_page_furniture: bool) -> list[list[str]]:
    pages = [page.splitlines() for page in raw_pages]
    if strip_page_furniture:
        pages = strip_repeated_page_furniture(pages)

    cleaned_pages: list[list[str]] = []
    for lines in pages:
        cleaned_lines: list[str] = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            cleaned_lines.append(line)
        cleaned_pages.append(cleaned_lines)
    return cleaned_pages


def strip_repeated_page_furniture(pages: list[list[str]]) -> list[list[str]]:
    if len(pages) < 2:
        return pages

    boundary_counter: Counter[str] = Counter()
    boundary_positions_per_page: list[set[int]] = []

    for page_lines in pages:
        non_empty_positions = [index for index, line in enumerate(page_lines) if line.strip()]
        boundary_positions = set(non_empty_positions[:3] + non_empty_positions[-3:])
        boundary_positions_per_page.append(boundary_positions)
        boundary_counter.update(
            page_lines[index].strip()
            for index in boundary_positions
            if page_lines[index].strip()
        )

    threshold = max(3, math.ceil(len(pages) * 0.2))
    repeated_boundary_lines = {
        line for line, count in boundary_counter.items() if count >= threshold
    }

    cleaned_pages: list[list[str]] = []
    for page_lines, boundary_positions in zip(pages, boundary_positions_per_page):
        cleaned_lines: list[str] = []
        for index, raw_line in enumerate(page_lines):
            stripped = raw_line.strip()
            if not stripped:
                cleaned_lines.append(raw_line)
                continue
            if PAGE_NUMBER_RE.fullmatch(stripped):
                continue
            if index in boundary_positions and stripped in repeated_boundary_lines:
                continue
            cleaned_lines.append(raw_line)
        cleaned_pages.append(cleaned_lines)
    return cleaned_pages


def build_comparison(left: PdfExtraction, right: PdfExtraction) -> dict[str, object]:
    left_text = [line.text for line in left.lines]
    right_text = [line.text for line in right.lines]
    matcher = difflib.SequenceMatcher(a=left_text, b=right_text, autojunk=False)

    changes: list[dict[str, object]] = []
    inserted_lines = 0
    deleted_lines = 0
    replaced_left_lines = 0
    replaced_right_lines = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        left_chunk = left.lines[i1:i2]
        right_chunk = right.lines[j1:j2]

        if tag == "insert":
            inserted_lines += len(right_chunk)
        elif tag == "delete":
            deleted_lines += len(left_chunk)
        elif tag == "replace":
            replaced_left_lines += len(left_chunk)
            replaced_right_lines += len(right_chunk)

        changes.append(
            {
                "kind": tag,
                "left": build_side_payload(left_chunk, i1, i2),
                "right": build_side_payload(right_chunk, j1, j2),
            }
        )

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "left_pdf": str(left.path),
        "right_pdf": str(right.path),
        "left_label": left.label,
        "right_label": right.label,
        "extractors": {
            "left": left.extractor,
            "right": right.extractor,
        },
        "stats": {
            "left_pages": left.page_count,
            "right_pages": right.page_count,
            "left_lines": left.line_count,
            "right_lines": right.line_count,
            "change_blocks": len(changes),
            "inserted_lines": inserted_lines,
            "deleted_lines": deleted_lines,
            "replaced_left_lines": replaced_left_lines,
            "replaced_right_lines": replaced_right_lines,
            "similarity_ratio": matcher.ratio(),
        },
        "changes": changes,
        "left_display_lines": [line.display() for line in left.lines],
        "right_display_lines": [line.display() for line in right.lines],
    }


def build_side_payload(lines: list[LocatedLine], start_index: int, end_index: int) -> dict[str, object]:
    if not lines:
        return {
            "start_index": start_index + 1,
            "end_index": end_index,
            "start_page": None,
            "end_page": None,
            "lines": [],
            "display_lines": [],
        }

    return {
        "start_index": start_index + 1,
        "end_index": end_index,
        "start_page": lines[0].page,
        "end_page": lines[-1].page,
        "lines": [line.text for line in lines],
        "display_lines": [line.display() for line in lines],
    }


def render_extracted_text(extraction: PdfExtraction) -> str:
    output_lines = [
        f"# Label: {extraction.label}",
        f"# Source: {extraction.path}",
        f"# Extractor: {extraction.extractor}",
        "",
    ]

    for page_number, page_lines in enumerate(extraction.page_lines, start=1):
        output_lines.append(f"=== Page {page_number} ===")
        output_lines.extend(page_lines or [""])
        output_lines.append("")

    return "\n".join(output_lines).rstrip() + "\n"


def render_markdown_summary(summary: dict[str, object]) -> str:
    stats = summary["stats"]
    changes = summary["changes"]

    lines = [
        "# PDF Text Comparison Summary",
        "",
        f"- Generated: `{summary['generated_at_utc']}`",
        f"- Left PDF: `{summary['left_pdf']}`",
        f"- Right PDF: `{summary['right_pdf']}`",
        f"- Left label: `{summary['left_label']}`",
        f"- Right label: `{summary['right_label']}`",
        f"- Left extractor: `{summary['extractors']['left']}`",
        f"- Right extractor: `{summary['extractors']['right']}`",
        f"- Left pages / lines: `{stats['left_pages']}` / `{stats['left_lines']}`",
        f"- Right pages / lines: `{stats['right_pages']}` / `{stats['right_lines']}`",
        f"- Change blocks: `{stats['change_blocks']}`",
        f"- Similarity ratio: `{stats['similarity_ratio']:.2%}`",
        "",
        "## Changes",
        "",
    ]

    for index, change in enumerate(changes, start=1):
        lines.append(f"### {index}. {change['kind'].title()}")
        lines.append("")
        lines.extend(render_markdown_side("Left", change["left"]))
        lines.extend(render_markdown_side("Right", change["right"]))

    if not changes:
        lines.append("No changes detected.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_markdown_side(label: str, side: dict[str, object]) -> list[str]:
    lines = side["display_lines"]
    start_page = side["start_page"]
    end_page = side["end_page"]
    page_label = format_page_range(start_page, end_page)
    output = [f"**{label} ({page_label})**", ""]
    output.append("```text")
    output.extend(lines or ["<no lines>"])
    output.append("```")
    output.append("")
    return output


def render_diff_table(
    left_lines: list[str],
    right_lines: list[str],
    left_label: str,
    right_label: str,
    *,
    context: bool = False,
    numlines: int = 0,
) -> str:
    return difflib.HtmlDiff(wrapcolumn=96).make_table(
        left_lines or [""],
        right_lines or [""],
        fromdesc=html.escape(left_label),
        todesc=html.escape(right_label),
        context=context,
        numlines=numlines,
    )


def render_change_cards(
    summary: dict[str, object],
    left_display_lines: list[str],
    right_display_lines: list[str],
) -> str:
    if not summary["changes"]:
        return "<p class=\"empty-note\">No changes detected.</p>"

    cards: list[str] = []
    left_label = summary["left_label"]
    right_label = summary["right_label"]

    for index, change in enumerate(summary["changes"], start=1):
        left_page_range = format_page_range(
            change["left"]["start_page"], change["left"]["end_page"]
        )
        right_page_range = format_page_range(
            change["right"]["start_page"], change["right"]["end_page"]
        )
        left_count = len(change["left"]["display_lines"])
        right_count = len(change["right"]["display_lines"])
        change_table = render_diff_table(
            change["left"]["display_lines"],
            change["right"]["display_lines"],
            left_label,
            right_label,
        )
        context_table = render_context_table(
            change,
            left_display_lines,
            right_display_lines,
            left_label,
            right_label,
        )
        cards.append(
            "<article class=\"change-card\" id=\"change-"
            + str(index)
            + "\">"
            + "<div class=\"change-header\">"
            + "<div>"
            + f"<p class=\"change-kicker\">Change {index}</p>"
            + f"<h3>{html.escape(change['kind'].title())}</h3>"
            + "<p class=\"change-meta\">"
            + f"{html.escape(left_page_range)} ({left_count} line{pluralize(left_count)})"
            + " &middot; "
            + f"{html.escape(right_page_range)} ({right_count} line{pluralize(right_count)})"
            + "</p>"
            + "</div>"
            + "<a class=\"jump-top\" href=\"#report-top\">Top</a>"
            + "</div>"
            + "<div class=\"diff-frame change-diff\">"
            + change_table
            + "</div>"
            + "<details class=\"context-panel\">"
            + "<summary>Show nearby context</summary>"
            + f"<p class=\"context-note\">Includes up to {DEFAULT_CONTEXT_LINES} unchanged lines before and after this change block.</p>"
            + "<div class=\"diff-frame context-diff\">"
            + context_table
            + "</div>"
            + "</details>"
            + "</article>"
        )

    return "".join(cards)


def render_context_table(
    change: dict[str, object],
    left_display_lines: list[str],
    right_display_lines: list[str],
    left_label: str,
    right_label: str,
) -> str:
    left_start, left_end = context_window_bounds(change["left"], len(left_display_lines))
    right_start, right_end = context_window_bounds(change["right"], len(right_display_lines))
    return render_diff_table(
        left_display_lines[left_start:left_end],
        right_display_lines[right_start:right_end],
        left_label,
        right_label,
    )


def context_window_bounds(side: dict[str, object], total_lines: int) -> tuple[int, int]:
    start_index = side["start_index"]
    end_index = side["end_index"]
    start = max(start_index - 1 - DEFAULT_CONTEXT_LINES, 0)
    end_anchor = max(end_index, start_index - 1)
    end = min(end_anchor + DEFAULT_CONTEXT_LINES, total_lines)
    return start, end


def render_html_report(summary: dict[str, object]) -> str:
    left_display_lines = summary["left_display_lines"]
    right_display_lines = summary["right_display_lines"]
    stats = summary["stats"]
    summary_without_display_lines = {
        key: value
        for key, value in summary.items()
        if key not in {"left_display_lines", "right_display_lines"}
    }

    changes_only_html = render_change_cards(summary, left_display_lines, right_display_lines)
    diff_table = render_diff_table(
        left_display_lines,
        right_display_lines,
        summary["left_label"],
        summary["right_label"],
        context=False,
        numlines=2,
    )

    change_preview_items: list[str] = []
    for index, change in enumerate(summary["changes"], start=1):
        left_page_range = format_page_range(
            change["left"]["start_page"], change["left"]["end_page"]
        )
        right_page_range = format_page_range(
            change["right"]["start_page"], change["right"]["end_page"]
        )
        change_preview_items.append(
            "<li>"
            f"<a href=\"#change-{index}\">"
            f"<strong>{index}. {html.escape(change['kind'].title())}</strong> "
            f"<span>left {html.escape(left_page_range)} | right {html.escape(right_page_range)}</span>"
            "</a>"
            "</li>"
        )

    preview_html = (
        "<ul class=\"change-list jump-list\">"
        + "".join(change_preview_items)
        + "</ul>"
        if change_preview_items
        else "<p class=\"empty-note\">No changes detected.</p>"
    )

    summary_json = html.escape(json.dumps(summary_without_display_lines, ensure_ascii=False, indent=2))
    generated = html.escape(summary["generated_at_utc"])
    left_pdf = html.escape(summary["left_pdf"])
    right_pdf = html.escape(summary["right_pdf"])
    left_extractor = html.escape(summary["extractors"]["left"])
    right_extractor = html.escape(summary["extractors"]["right"])
    left_label = html.escape(summary["left_label"])
    right_label = html.escape(summary["right_label"])
    note = "Repeated boundary headers/footers and standalone page-number lines were removed before diffing."

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PDF Text Comparison</title>
  <style>
    :root {{
      --bg: #f6f2e8;
      --paper: #fffdf8;
      --ink: #23313a;
      --ink-soft: #5d6b74;
      --line: #d9d1c4;
      --accent: #1f6b75;
      --accent-soft: rgba(31, 107, 117, 0.12);
      --shadow: 0 18px 40px rgba(49, 37, 21, 0.08);
      --radius: 20px;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      padding: 24px;
      background:
        radial-gradient(circle at top left, rgba(198, 148, 54, 0.12), transparent 28%),
        linear-gradient(180deg, #fbf8f1 0%, var(--bg) 100%);
      color: var(--ink);
      font-family: "Segoe UI", system-ui, sans-serif;
    }}

    .shell {{
      max-width: 1480px;
      margin: 0 auto;
    }}

    .hero,
    .card {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }}

    .hero {{
      padding: 28px;
      margin-bottom: 18px;
    }}

    h1 {{
      margin: 0 0 12px;
      font-size: clamp(2rem, 4vw, 3rem);
      line-height: 1;
      letter-spacing: -0.03em;
    }}

    .lede {{
      margin: 0;
      color: var(--ink-soft);
      max-width: 78ch;
      line-height: 1.6;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 18px 0 0;
    }}

    .metric {{
      padding: 16px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, #fffef9, #f7f0e6);
    }}

    .metric-label {{
      display: block;
      color: var(--ink-soft);
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}

    .metric-value {{
      margin-top: 8px;
      font-size: 1.8rem;
      font-weight: 700;
    }}

    .two-up {{
      display: grid;
      grid-template-columns: 1.1fr 1fr;
      gap: 18px;
      margin-bottom: 18px;
    }}

    .card {{
      padding: 22px;
    }}

    h2 {{
      margin: 0 0 12px;
      font-size: 1.1rem;
      letter-spacing: 0.02em;
    }}

    .meta-list {{
      margin: 0;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 10px;
    }}

    .meta-list li {{
      padding: 12px 14px;
      border-radius: 14px;
      background: #fbf7ef;
      border: 1px solid var(--line);
    }}

    .meta-key {{
      display: block;
      color: var(--ink-soft);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
    }}

    .meta-value {{
      margin-top: 6px;
      word-break: break-word;
      line-height: 1.5;
    }}

    .change-list {{
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 10px;
    }}

    .jump-list {{
      max-height: 320px;
      overflow: auto;
      padding-right: 8px;
    }}

    .change-list a {{
      color: inherit;
      text-decoration: none;
      display: block;
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid transparent;
    }}

    .change-list a:hover {{
      border-color: var(--line);
      background: #f7f2e8;
    }}

    .change-list li span,
    .empty-note,
    .note {{
      color: var(--ink-soft);
    }}

    .note {{
      margin: 12px 0 0;
      line-height: 1.5;
      background: var(--accent-soft);
      border: 1px solid rgba(31, 107, 117, 0.18);
      border-radius: 14px;
      padding: 12px 14px;
    }}

    .section-title {{
      margin-bottom: 8px;
    }}

    .section-lede {{
      margin: 0 0 16px;
      color: var(--ink-soft);
      line-height: 1.6;
    }}

    .change-stack {{
      display: grid;
      gap: 16px;
    }}

    .change-card {{
      border: 1px solid var(--line);
      border-radius: 18px;
      background: linear-gradient(180deg, #fffef9, #fbf6ee);
      padding: 18px;
    }}

    .change-header {{
      display: flex;
      align-items: start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 12px;
    }}

    .change-kicker {{
      margin: 0 0 4px;
      color: var(--ink-soft);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
    }}

    h3 {{
      margin: 0;
      font-size: 1.1rem;
    }}

    .change-meta {{
      margin: 8px 0 0;
      color: var(--ink-soft);
      line-height: 1.5;
    }}

    .jump-top {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 700;
      white-space: nowrap;
    }}

    .diff-frame {{
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fffdf8;
    }}

    .diff-wrap {{
      overflow: auto;
      padding: 18px;
    }}

    table.diff {{
      width: 100%;
      border-collapse: collapse;
      font-family: Consolas, "Courier New", monospace;
      font-size: 0.88rem;
    }}

    .diff_header,
    td {{
      padding: 6px 8px;
      border: 1px solid var(--line);
      vertical-align: top;
    }}

    .diff_header {{
      position: sticky;
      top: 0;
      background: #f1ece1;
      z-index: 1;
    }}

    .diff_next {{
      background: #f9f4ea;
    }}

    .diff_add {{
      background: #e5f4e8;
    }}

    .diff_sub {{
      background: #fde8e1;
    }}

    .diff_chg {{
      background: #fff0c9;
    }}

    pre {{
      margin: 0;
      white-space: pre-wrap;
    }}

    .context-panel {{
      margin-top: 14px;
    }}

    .context-note {{
      color: var(--ink-soft);
      line-height: 1.5;
      margin: 10px 0 12px;
    }}

    details {{
      margin-top: 16px;
    }}

    summary {{
      cursor: pointer;
      font-weight: 700;
    }}

    @media (max-width: 1100px) {{
      .grid,
      .two-up {{
        grid-template-columns: 1fr 1fr;
      }}
    }}

    @media (max-width: 760px) {{
      body {{
        padding: 14px;
      }}

      .grid,
      .two-up {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell" id="report-top">
    <section class="hero">
      <h1>PDF Text Comparison</h1>
      <p class="lede">
        {left_label} and {right_label} were converted to text and compared line by line.
        This report hides matching text by default so you can move straight through the differences.
      </p>
      <div class="grid">
        <div class="metric">
          <span class="metric-label">Similarity</span>
          <div class="metric-value">{stats['similarity_ratio']:.2%}</div>
        </div>
        <div class="metric">
          <span class="metric-label">Change Blocks</span>
          <div class="metric-value">{stats['change_blocks']}</div>
        </div>
        <div class="metric">
          <span class="metric-label">Left Pages / Lines</span>
          <div class="metric-value">{stats['left_pages']} / {stats['left_lines']}</div>
        </div>
        <div class="metric">
          <span class="metric-label">Right Pages / Lines</span>
          <div class="metric-value">{stats['right_pages']} / {stats['right_lines']}</div>
        </div>
      </div>
    </section>

    <section class="two-up">
      <div class="card">
        <h2>Sources</h2>
        <ul class="meta-list">
          <li>
            <span class="meta-key">Generated</span>
            <div class="meta-value">{generated}</div>
          </li>
          <li>
            <span class="meta-key">Left PDF</span>
            <div class="meta-value">{left_pdf}</div>
          </li>
          <li>
            <span class="meta-key">Right PDF</span>
            <div class="meta-value">{right_pdf}</div>
          </li>
          <li>
            <span class="meta-key">Extractors</span>
            <div class="meta-value">{left_extractor} / {right_extractor}</div>
          </li>
        </ul>
        <p class="note">{html.escape(note)}</p>
      </div>

      <div class="card">
        <h2>Jump To Changes</h2>
        {preview_html}
        <details>
          <summary>Show raw JSON metadata</summary>
          <pre>{summary_json}</pre>
        </details>
      </div>
    </section>

    <section class="card">
      <h2 class="section-title">Changes Only</h2>
      <p class="section-lede">
        Each block below shows only the differing lines. Open nearby context when you want a few surrounding unchanged lines for orientation.
      </p>
      <div class="change-stack">
        {changes_only_html}
      </div>
    </section>

    <section class="card diff-wrap">
      <details>
        <summary>Show full document diff</summary>
        <p class="context-note">
          This is the complete side-by-side diff, including unchanged material between change blocks.
        </p>
        {diff_table}
      </details>
    </section>
  </div>
</body>
</html>
"""


def format_page_range(start_page: int | None, end_page: int | None) -> str:
    if start_page is None or end_page is None:
        return "no lines"
    if start_page == end_page:
        return f"page {start_page}"
    return f"pages {start_page}-{end_page}"


def safe_stem(path: Path) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9]+", "-", path.stem.lower()).strip("-")
    return sanitized or "document"


def build_pair_slug(left_pdf: Path, right_pdf: Path) -> str:
    return f"{safe_stem(left_pdf)}__vs__{safe_stem(right_pdf)}"


def pluralize(count: int) -> str:
    return "" if count == 1 else "s"


if __name__ == "__main__":
    sys.exit(main())
