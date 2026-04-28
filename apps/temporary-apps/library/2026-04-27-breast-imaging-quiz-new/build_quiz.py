from __future__ import annotations

import json
import re
from pathlib import Path

import fitz


APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[3]
SOURCE_PDF = Path(r"G:/My Drive/0. Radiology/Core Review Books/Breast Imaging/1RegulatoryStandardso_BreastImagingACoreRev.pdf")
REFERENCE_QUESTIONS = APP_DIR.parent / "2026-04-27-breast-imaging-quiz" / "questions.json"
ASSET_DIR = APP_DIR / "assets"

QUESTION_PAGE_RANGE = range(0, 50)
ANSWER_PAGE_RANGE = range(50, 84)


def write_block_image(block: dict, prefix: str, page_num: int, index: int) -> str:
    ext = block.get("ext") or "png"
    if ext == "jpx":
        ext = "jpg"
    filename = f"{prefix}_p{page_num:03d}_{index:02d}.{ext}"
    (ASSET_DIR / filename).write_bytes(block["image"])
    return f"assets/{filename}"


def block_text(block: dict) -> str:
    return " ".join(
        "".join(span["text"] for span in line["spans"])
        for line in block.get("lines", [])
    )


def target_for_question_image(page_num: int, detected: str) -> str:
    # The printed PDF places the BI-RADS matching images for question 2 on
    # separate image-only pages before question 3 starts.
    if 2 <= page_num <= 9:
        return "2"
    return detected


def dedupe_images(questions: list[dict]) -> None:
    for question in questions:
        for key in ("images", "explanationImages"):
            seen: set[str] = set()
            deduped = []
            for image in question.get(key, []):
                if image not in seen:
                    seen.add(image)
                    deduped.append(image)
            question[key] = deduped


def extract_pdf_images(questions: list[dict]) -> None:
    by_number = {str(question["number"]): question for question in questions}
    doc = fitz.open(str(SOURCE_PDF))
    try:
        q_start_re = re.compile(r"(?<!\d)(\d{1,2}[ab]?)(?=\s+(?:A\.\s+B\.|A\.))", re.I)
        current = "1"
        for page_index in QUESTION_PAGE_RANGE:
            page_num = page_index + 1
            blocks = sorted(
                doc[page_index].get_text("dict")["blocks"],
                key=lambda block: (block["bbox"][1], block["bbox"][0]),
            )
            image_index = 0
            for block in blocks:
                if block["type"] == 0:
                    matches = q_start_re.findall(block_text(block))
                    if matches:
                        current = matches[-1]
                elif block["type"] == 1:
                    image_index += 1
                    target = target_for_question_image(page_num, current)
                    rel_path = write_block_image(block, f"q{target}", page_num, image_index)
                    if target == "2":
                        for letter in "ABCDEFGH":
                            question = by_number.get(f"2{letter}")
                            if question:
                                question["images"].append(rel_path)
                    elif target in by_number:
                        by_number[target]["images"].append(rel_path)

        a_start_re = re.compile(r"(?<!\d)(\d{1,2}[ab]?)(?=\s+(?:References?:|Answer\s+[A-Z]\.))", re.I)
        current_answer = "1"
        for page_index in ANSWER_PAGE_RANGE:
            page_num = page_index + 1
            blocks = sorted(
                doc[page_index].get_text("dict")["blocks"],
                key=lambda block: (block["bbox"][1], block["bbox"][0]),
            )
            image_index = 0
            for block in blocks:
                if block["type"] == 0:
                    matches = a_start_re.findall(block_text(block))
                    if matches:
                        current_answer = matches[-1]
                elif block["type"] == 1:
                    image_index += 1
                    rel_path = write_block_image(block, f"a{current_answer}", page_num, image_index)
                    question = by_number.get(current_answer)
                    if question:
                        question["explanationImages"].append(rel_path)
    finally:
        doc.close()


def main() -> None:
    if not SOURCE_PDF.exists():
        raise FileNotFoundError(f"Missing source PDF: {SOURCE_PDF}")
    if not REFERENCE_QUESTIONS.exists():
        raise FileNotFoundError(f"Missing reference question data: {REFERENCE_QUESTIONS}")

    ASSET_DIR.mkdir(exist_ok=True)
    for child in ASSET_DIR.iterdir():
        if child.is_file():
            child.unlink()

    questions = json.loads(REFERENCE_QUESTIONS.read_text(encoding="utf-8"))
    for question in questions:
        question["images"] = []
        question["explanationImages"] = []

    extract_pdf_images(questions)
    dedupe_images(questions)

    (APP_DIR / "questions.json").write_text(
        json.dumps(questions, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    html_path = APP_DIR / "index.html"
    html = html_path.read_text(encoding="utf-8")
    html = html.replace("Breast Imaging Regulatory Quiz", "Breast Imaging Regulatory Quiz (New)")
    html = html.replace("Breast Imaging Regulatory Quiz (New) (New)", "Breast Imaging Regulatory Quiz (New)")
    html = html.replace("breast-imaging-regulatory-quiz-ch1", "breast-imaging-regulatory-quiz-new-ch1")
    html_path.write_text(html, encoding="utf-8")

    print(f"wrote {len(questions)} questions")
    print(f"wrote {len(list(ASSET_DIR.iterdir()))} PDF images")
    print(f"question image refs: {sum(len(q['images']) for q in questions)}")
    print(f"explanation image refs: {sum(len(q['explanationImages']) for q in questions)}")


if __name__ == "__main__":
    main()
