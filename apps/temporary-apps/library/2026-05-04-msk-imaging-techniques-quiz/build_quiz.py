from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader


APP_DIR = Path(__file__).resolve().parent
SOURCE_PDF = Path(r"G:/My Drive/0. Radiology/Core Review MSK.pdf")
ASSET_DIR = APP_DIR / "assets"

TITLE = "MSK Imaging Techniques/Physics/Quality and Safety Quiz"
APP_ID = "msk-imaging-techniques-quiz-ch1"

# Zero-based PDF page indexes. Chapter 1's question and answer sections are
# split into two blocks before chapter 2 starts.
QUESTION_RANGES = [range(13, 42), range(50, 55)]
ANSWER_RANGES = [range(41, 50), range(54, 56)]
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
HIGHLIGHTED_QUESTIONS = {
    "1", "2a", "2b", "2c", "3a", "3b", "3c", "4", "5", "6",
    "7", "8", "9", "10", "11", "12", "13", "14", "15", "16",
    "17", "18", "19", "20", "21", "22", "23", "24", "25", "26",
    "27", "28a", "28b", "29", "30", "31", "32", "33", "34",
    "35", "36", "37", "38", "39", "40", "41",
}


def clean_text(value: str) -> str:
    value = value.replace("\t", " ")
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = value.replace("\u2018", "'").replace("\u2019", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+([,.;:])", r"\1", value)
    return value.strip()


def page_lines(reader: PdfReader, page_index: int) -> list[str]:
    text = reader.pages[page_index].extract_text(extraction_mode="layout") or ""
    lines = [clean_text(line) for line in text.splitlines()]
    return [line for line in lines if line]


def is_noise_line(line: str) -> bool:
    if re.fullmatch(r"\d{1,3}", line):
        return True
    if re.fullmatch(r"\d{1,2}[A-Z]", line):
        return True
    if line in {"QUESTIONS", "ANSWERS AND EXPLANATIONS"}:
        return True
    if line in {"1", "Safety", "1 Imaging Techniques/Physics/Qualityand Safety"}:
        return True
    return False


def question_lines(reader: PdfReader) -> list[str]:
    lines: list[str] = []
    for page_range in QUESTION_RANGES:
        for page_index in page_range:
            for line in page_lines(reader, page_index):
                if not is_noise_line(line):
                    lines.append(line)
    return lines


def parse_questions(reader: PdfReader) -> list[dict]:
    questions: list[dict] = []
    current: dict | None = None
    current_option: dict | None = None

    def flush_option() -> None:
        nonlocal current_option
        if current and current_option:
            current_option["text"] = clean_text(current_option["text"])
            current["options"].append(current_option)
        current_option = None

    def flush_question() -> None:
        nonlocal current
        flush_option()
        if current and current.get("stem"):
            current["stem"] = clean_text(current["stem"])
            questions.append(current)
        current = None

    for page_range in QUESTION_RANGES:
        for page_index in page_range:
            for line in page_lines(reader, page_index):
                if "ANSWERS AND EXPLANATIONS" in line:
                    flush_question()
                    current = None
                    break
                if is_noise_line(line):
                    continue
                qmatch = re.match(r"^(\d{1,2}[A-Za-z]?)\s+(.+)$", line)
                if qmatch and not re.fullmatch(r"\d{1,2}", qmatch.group(2)):
                    qid, stem = qmatch.groups()
                    if int(re.match(r"\d+", qid).group(0)) > 49:
                        if current:
                            current["stem"] += " " + line
                        continue
                    if qid == "1" and "Imaging Techniques" in stem:
                        continue
                    flush_question()
                    current = {"number": qid, "stem": stem, "options": [], "images": [], "explanationImages": []}
                    continue
                omatch = re.match(r"^([A-J])\.\s*(.*)$", line)
                if current and omatch:
                    flush_option()
                    current_option = {"letter": omatch.group(1), "text": omatch.group(2)}
                    continue
                if current_option:
                    current_option["text"] += " " + line
                elif current:
                    current["stem"] += " " + line

    flush_question()
    return questions


def answer_text(reader: PdfReader) -> str:
    parts: list[str] = []
    for page_range in ANSWER_RANGES:
        for page_index in page_range:
            lines = [line for line in page_lines(reader, page_index) if not is_noise_line(line)]
            parts.append(" ".join(lines))
    return clean_text(" ".join(parts))


def parse_answers(reader: PdfReader, questions: list[dict]) -> None:
    entries: list[tuple[str, str]] = []
    current_id: str | None = None
    current_text: list[str] = []
    for page_range in ANSWER_RANGES:
        for page_index in page_range:
            for line in page_lines(reader, page_index):
                if is_noise_line(line):
                    continue
                match = re.match(r"^(\d{1,2}[A-Za-z]?)\s+Answer\s+([A-J])\.\s*(.*)$", line)
                if match:
                    qid, answer, rest = match.groups()
                    if current_id:
                        entries.append((current_id, clean_text(" ".join(current_text))))
                    current_id = qid
                    current_text = [f"Answer {answer}. {rest}"]
                    continue
                alternate = re.match(r"^Answer\s+([A-J])\.\s*(\d{1,2}[A-Za-z]?)\s+(.+)$", line)
                if alternate:
                    answer, qid, rest = alternate.groups()
                    if current_id:
                        entries.append((current_id, clean_text(" ".join(current_text))))
                    current_id = qid
                    current_text = [f"Answer {answer}. {rest}"]
                elif current_id:
                    current_text.append(line)
    if current_id:
        entries.append((current_id, clean_text(" ".join(current_text))))

    by_id = {str(q["number"]): q for q in questions}
    for qid, explanation in entries:
        q = by_id.get(qid)
        if q:
            q["answer"] = (re.search(r"Answer\s+([A-J])\.", explanation) or ["", ""])[1]
            q["explanation"] = re.sub(r"\s+References?:\s+", "\n\nReferences: ", explanation)
    if "25" in by_id and not by_id["25"].get("answer"):
        page = " ".join(page_lines(reader, 63))
        match = re.search(r"Answer\s+B\.\s*(.+?)(?=\s+References?:|\s+26\s+Answer)", page)
        by_id["25"]["answer"] = "B"
        by_id["25"]["explanation"] = clean_text("Answer B. " + (match.group(1) if match else "See source explanation."))


def apply_manual_fixes(questions: list[dict]) -> None:
    for q in questions:
        q["number"] = q["number"].replace("A", "a").replace("B", "b")
        if q["number"] in {"2a", "3a", "24", "33", "39"} and not q["options"]:
            q["options"] = [{"letter": letter, "text": f"Image {letter}"} for letter in "ABCD"]


def write_image(image, filename: str) -> str:
    suffix = Path(image.name).suffix or ".png"
    if not filename.endswith(suffix):
        filename += suffix
    path = ASSET_DIR / filename
    path.write_bytes(image.data)
    return f"assets/{path.name}"


def extract_images(reader: PdfReader, questions: list[dict]) -> None:
    # Manually checked chapter page ranges. Continuation pages inherit the
    # current or visually associated question when the text layer is sparse.
    question_page_targets = {
        14: ["2a"],
        15: ["2c"],
        16: ["2c"],
        17: ["3a"],
        18: ["3a"],
        20: ["3c"],
        21: ["4"],
        22: ["5"],
        24: ["15"],
        25: ["17"],
        26: ["18"],
        28: ["24"],
        29: ["28a"],
        31: ["33"],
        32: ["35"],
        33: ["36"],
        34: ["37"],
        36: ["38"],
        37: ["39"],
        38: ["39"],
        39: ["39"],
        40: ["39"],
        51: ["46"],
        53: ["49"],
        54: ["49"],
    }
    answer_page_targets = {
        42: ["2c"],
        46: ["24"],
        55: ["46"],
    }
    by_number = {q["number"]: q for q in questions}
    for page_index, targets in question_page_targets.items():
        for image_index, image in enumerate(reader.pages[page_index].images, start=1):
            rel = write_image(image, f"q{'_'.join(targets)}_p{page_index + 1:03d}_{image_index:02d}")
            for target in targets:
                if target in by_number and rel not in by_number[target]["images"]:
                    by_number[target]["images"].append(rel)
    for page_index, targets in answer_page_targets.items():
        for image_index, image in enumerate(reader.pages[page_index].images, start=1):
            rel = write_image(image, f"a{'_'.join(targets)}_p{page_index + 1:03d}_{image_index:02d}")
            for target in targets:
                if target in by_number and rel not in by_number[target]["explanationImages"]:
                    by_number[target]["explanationImages"].append(rel)


def render_html(questions: list[dict]) -> str:
    template = (APP_DIR / "_template.html").read_text(encoding="utf-8")
    data = json.dumps(questions, ensure_ascii=False)
    template = re.sub(r"const QUESTIONS = \[.*?\];", lambda _match: f"const QUESTIONS = {data};", template, flags=re.S)
    template = template.replace("Core Review Pediatric Imaging Quiz", TITLE)
    template = template.replace("Pediatric GI Imaging Quiz", TITLE)
    template = template.replace("Pediatric Gastrointestinal Tract Quiz", TITLE)
    template = template.replace("Nuclear Medicine Musculoskeletal System Quiz", TITLE)
    template = template.replace("pediatric-imaging-quiz-ch1", APP_ID)
    template = template.replace("pediatric-gi-imaging-quiz-ch1", APP_ID)
    template = template.replace("nuclear-medicine-msk-quiz-ch3-v2", APP_ID)
    default_selected = {
        q["number"]: q["answer"]
        for q in questions
        if q["number"] in HIGHLIGHTED_QUESTIONS and q.get("answer")
    }
    default_data = json.dumps(default_selected, ensure_ascii=False)
    template = re.sub(r"const DEFAULT_SELECTED = \{.*?\};", f"const DEFAULT_SELECTED = {default_data};", template)
    return template


def main() -> None:
    if not SOURCE_PDF.exists():
        raise FileNotFoundError(SOURCE_PDF)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for old in ASSET_DIR.glob("*"):
        if old.is_file():
            old.unlink()

    reader = PdfReader(str(SOURCE_PDF))
    questions = parse_questions(reader)
    apply_manual_fixes(questions)
    parse_answers(reader, questions)
    extract_images(reader, questions)
    for q in questions:
        q.setdefault("answer", "")
        q.setdefault("explanation", "No extracted explanation found.")
        q.setdefault("explanationImages", [])
    (APP_DIR / "questions.json").write_text(json.dumps(questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (APP_DIR / "index.html").write_text(render_html(questions), encoding="utf-8")
    print(f"wrote {len(questions)} questions")
    print("missing answers:", [q["number"] for q in questions if not q["answer"]])
    print("bad option counts:", [(q["number"], len(q["options"])) for q in questions if len(q["options"]) < 2])
    print(f"question image refs: {sum(len(q['images']) for q in questions)}")
    print(f"explanation image refs: {sum(len(q['explanationImages']) for q in questions)}")


if __name__ == "__main__":
    main()
