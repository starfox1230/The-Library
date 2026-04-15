#!/usr/bin/env python3
"""Generate chapter text files for ABR study guides used by Textbook Copier."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pdf_text_compare import extract_pdf


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_STUDYING_DIR = REPO_ROOT / "apps" / "core-studying"


@dataclass(frozen=True)
class SectionSpec:
    key: str
    title: str
    file_name: str
    start_page: int
    end_page: int
    start_marker: str | None = None
    end_marker: str | None = None
    start_occurrence: int = 1


@dataclass(frozen=True)
class DocumentSpec:
    slug: str
    pdf_path: Path
    output_dir: Path
    manifest_key: str
    sections: tuple[SectionSpec, ...]
    ignored_line_patterns: tuple[re.Pattern[str], ...] = ()


DOCUMENT_SPECS: dict[str, DocumentSpec] = {
    "risc-2026": DocumentSpec(
        slug="risc-2026",
        pdf_path=CORE_STUDYING_DIR / "Radioisotope Safety Document" / "RISC-Study-Guide-2026.pdf",
        output_dir=CORE_STUDYING_DIR / "Radioisotope Safety Document 2026",
        manifest_key="Chapter01",
        ignored_line_patterns=(
            re.compile(r"^\d{4} Radioisotope Safety Content \(RISC\) Study Guide \d+$"),
        ),
        sections=(
            SectionSpec(
                key="01.01",
                title="Introduction and Radiation protection",
                file_name="01. Introduction and Radiation protection.txt",
                start_page=5,
                end_page=7,
                start_marker="Radioisotope Safety Content (RISC) Study Guide",
                end_marker="2 Radiation biology",
            ),
            SectionSpec(
                key="01.02",
                title="Radiation Biology",
                file_name="02. Radiation Biology.txt",
                start_page=8,
                end_page=14,
                start_marker="2 Radiation biology",
                end_marker="3. Transport and management of radioactive materials",
            ),
            SectionSpec(
                key="01.03",
                title="Transport and management of radioactive materials",
                file_name="03. Transport and management of radioactive materials.txt",
                start_page=15,
                end_page=20,
                start_marker="3. Transport and management of radioactive materials",
                end_marker="4. Regulatory exposure limits to radioactive materials",
            ),
            SectionSpec(
                key="01.04",
                title="Regulatory exposure limits to radioactive materials",
                file_name="04. Regulatory exposure limits to radioactive materials.txt",
                start_page=21,
                end_page=24,
                start_marker="4. Regulatory exposure limits to radioactive materials",
                end_marker="5. Radiopharmaceutical administration",
            ),
            SectionSpec(
                key="01.05",
                title="Radiopharmaceutical administration",
                file_name="05. Radiopharmaceutical administration.txt",
                start_page=25,
                end_page=29,
                start_marker="5. Radiopharmaceutical administration",
                end_marker="6. Administrative/practice regulations, responsibilities and training",
            ),
            SectionSpec(
                key="01.06",
                title="Administrative/practice regulations, responsibilities and training",
                file_name="06. Administrative and practice regulations, responsibilities and training.txt",
                start_page=30,
                end_page=43,
                start_marker="6. Administrative/practice regulations, responsibilities and training",
                end_marker="7. Emergency procedures, accidents/incidents, special circumstances",
            ),
            SectionSpec(
                key="01.07",
                title="Emergency procedures, accidents/incidents, special circumstances",
                file_name="07. Emergency procedures, accidents and incidents, special circumstances.txt",
                start_page=44,
                end_page=52,
                start_marker="7. Emergency procedures, accidents/incidents, special circumstances",
                end_marker="Appendix 1. Radiation-Measuring Instrumentation and Quality Control Tests",
            ),
            SectionSpec(
                key="01.08",
                title="Appendix 1. Radiation-Measuring Instrumentation and Quality Control Tests",
                file_name="08. Appendix 1. Radiation-Measuring Instrumentation and Quality Control Tests.txt",
                start_page=53,
                end_page=54,
                start_marker="Appendix 1. Radiation-Measuring Instrumentation and Quality Control Tests",
                end_marker="Appendix 2. ABR Currently-in-Use Radiopharmaceuticals (Through 12/31/2025)",
            ),
        ),
    ),
    "nis-2026": DocumentSpec(
        slug="nis-2026",
        pdf_path=CORE_STUDYING_DIR / "Non-Interpretive Skills Document" / "NIS-Study-Guide-2026.pdf",
        output_dir=CORE_STUDYING_DIR / "Non-Interpretive Skills Document 2026",
        manifest_key="Chapter01",
        ignored_line_patterns=(
            re.compile(r"^\d{4} Noninterpretive Skills Study Guide \d+$"),
        ),
        sections=(
            SectionSpec(
                key="01.00",
                title="Introduction",
                file_name="00. Introduction.txt",
                start_page=4,
                end_page=4,
            ),
            SectionSpec(
                key="01.01",
                title="Core Elements of Professionalism",
                file_name="01. Core Elements of Professionalism.txt",
                start_page=5,
                end_page=8,
            ),
            SectionSpec(
                key="01.02",
                title="Core Concepts of Quality and Safety",
                file_name="02. Core Concepts of Quality and Safety.txt",
                start_page=9,
                end_page=19,
            ),
            SectionSpec(
                key="01.03",
                title="Practical Quality and Safety Applications in Healthcare",
                file_name="03. Practical Quality and Safety Applications in Healthcare.txt",
                start_page=20,
                end_page=32,
            ),
            SectionSpec(
                key="01.04",
                title="Practical Safety Applications in Radiology",
                file_name="04. Practical Safety Applications in Radiology.txt",
                start_page=33,
                end_page=58,
            ),
            SectionSpec(
                key="01.05",
                title="Reimbursement, Regulatory Compliance, and Legal Considerations in Radiology",
                file_name="05. Reimbursement, Regulatory Compliance, and Legal Considerations in Radiology.txt",
                start_page=59,
                end_page=68,
            ),
            SectionSpec(
                key="01.06",
                title="Core Concepts of Imaging Informatics",
                file_name="06. Core Concepts of Imaging Informatics.txt",
                start_page=69,
                end_page=74,
            ),
        ),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate chapter text files and manifests for the 2026 ABR study guides."
    )
    parser.add_argument(
        "--document",
        action="append",
        choices=sorted(DOCUMENT_SPECS),
        help="Only generate the specified document slug. Repeat to generate multiple documents.",
    )
    parser.add_argument(
        "--extractor",
        choices=("auto", "pdfplumber", "fitz", "ghostscript"),
        default="auto",
        help="Preferred PDF extractor backend.",
    )
    return parser.parse_args()


def build_manifest(spec: DocumentSpec) -> dict[str, dict[str, object]]:
    root: dict[str, object] = {"title": "ROOT"}
    for section in spec.sections:
        root[section.key] = {"title": section.title, "file": section.file_name}
    return {spec.manifest_key: root}


def build_section_text(
    page_lines: list[list[str]],
    start_page: int,
    end_page: int,
    ignored_line_patterns: tuple[re.Pattern[str], ...],
) -> str:
    lines: list[str] = []
    for page_number in range(start_page, end_page + 1):
        for line in page_lines[page_number - 1]:
            if any(pattern.fullmatch(line) for pattern in ignored_line_patterns):
                continue
            lines.append(line)
    return "\n".join(lines).strip() + "\n"


def flatten_clean_lines(
    page_lines: list[list[str]],
    ignored_line_patterns: tuple[re.Pattern[str], ...],
) -> list[str]:
    lines: list[str] = []
    for page in page_lines:
        for line in page:
            if any(pattern.fullmatch(line) for pattern in ignored_line_patterns):
                continue
            lines.append(line)
    return lines


def find_marker_index(lines: list[str], marker: str, occurrence: int = 1) -> int:
    count = 0
    for index, line in enumerate(lines):
        if line == marker:
            count += 1
            if count == occurrence:
                return index
    raise ValueError(f"Marker not found ({occurrence}x): {marker!r}")


def build_marker_section_text(
    lines: list[str],
    start_marker: str,
    end_marker: str | None,
    *,
    start_occurrence: int = 1,
) -> str:
    start_index = find_marker_index(lines, start_marker, occurrence=start_occurrence)
    end_index = find_marker_index(lines, end_marker) if end_marker else len(lines)
    if end_index <= start_index:
        raise ValueError(
            f"End marker {end_marker!r} occurred before start marker {start_marker!r}"
        )
    return "\n".join(lines[start_index:end_index]).strip() + "\n"


def generate_document(spec: DocumentSpec, *, extractor: str) -> None:
    if not spec.pdf_path.exists():
        raise FileNotFoundError(f"Source PDF not found: {spec.pdf_path}")

    extraction = extract_pdf(
        spec.pdf_path,
        label=spec.slug,
        extractor=extractor,
        strip_page_furniture=True,
    )
    flattened_lines = flatten_clean_lines(
        extraction.page_lines,
        ignored_line_patterns=spec.ignored_line_patterns,
    )

    spec.output_dir.mkdir(parents=True, exist_ok=True)

    for section in spec.sections:
        if section.start_marker:
            section_text = build_marker_section_text(
                flattened_lines,
                start_marker=section.start_marker,
                end_marker=section.end_marker,
                start_occurrence=section.start_occurrence,
            )
        else:
            section_text = build_section_text(
                extraction.page_lines,
                start_page=section.start_page,
                end_page=section.end_page,
                ignored_line_patterns=spec.ignored_line_patterns,
            )
        section_path = spec.output_dir / section.file_name
        section_path.write_text(section_text, encoding="utf-8")

    manifest_path = spec.output_dir / "index.json"
    manifest_path.write_text(
        json.dumps(build_manifest(spec), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    selected = args.document or list(DOCUMENT_SPECS)

    for slug in selected:
        spec = DOCUMENT_SPECS[slug]
        print(f"Generating {slug} from {spec.pdf_path}")
        generate_document(spec, extractor=args.extractor)
        print(f"Wrote {spec.output_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
