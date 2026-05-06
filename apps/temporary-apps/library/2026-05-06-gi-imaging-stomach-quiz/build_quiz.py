from __future__ import annotations

import json
import re
from io import BytesIO
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


APP_DIR = Path(__file__).resolve().parent
SOURCE_PDF = Path(r"G:/My Drive/0. Radiology/Core Review - Gastrointestinal Imaging .pdf")
ASSET_DIR = APP_DIR / "assets"

TITLE = "Gastrointestinal Imaging Stomach Quiz"
APP_ID = "gi-imaging-stomach-quiz-ch2"
DEFAULT_SEED_VERSION = 1
DEFAULT_SELECTED = {}

# Zero-based PDF page indexes for chapter 2.
QUESTION_RANGES = [range(112, 155), range(180, 184)]
ANSWER_RANGES = [range(155, 180), range(184, 187)]
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


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
    if line in {"QUESTIONS", "Questions", "ANSWERS AND EXPLANATIONS", "Answers and Explanations", "Endocrine System", "Musculoskeletal System", "Head and Neck", "Nuclear Cardiology", "Vascular and Lymphatics", "Pulmonary System", "Gastrointestinal System", "Genitourinary System", "Pediatric Nuclear Medicine", "Oncology", "Pharynx and Esophagus", "Stomach"}:
        return True
    if line in {"2", "3", "4", "5", "6", "7", "8", "9", "10"}:
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
                if "ANSWERS AND EXPLANATIONS" in line or "Answers and Explanations" in line:
                    flush_question()
                    current = None
                    break
                if is_noise_line(line):
                    continue
                qmatch = re.match(r"^(\d{1,2}(?:[A-Ha-h])?)\s+(.+)$", line)
                if qmatch and not re.fullmatch(r"\d{1,2}", qmatch.group(2)):
                    qid, stem = qmatch.groups()
                    if qid == "2" and "Stomach" in stem:
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
                match = re.match(r"^(\d{1,2}(?:[A-Ha-h])?)(?:s)?\s+Answer\s+([A-J])\.\s*(.*)$", line)
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
    match_explanation = re.search(r"34b\s+Answers:\s*(.*?)(?=35\s+Answer\s+[A-J]\.)", answer_text(reader))
    if match_explanation:
        explanation = clean_text("34b Answers: " + match_explanation.group(1))
        for q in questions:
            if re.fullmatch(r"34b[A-H]", q["number"]):
                q["explanation"] = explanation
    full_answer_text = answer_text(reader)
    q12_explanation = re.search(r"12\s+Answers:\s*(.*?)(?=13\s+Answer:)", full_answer_text)
    q13_explanation = re.search(r"13\s+Answer:\s*(.*?)(?=14\s+Answer\s+[A-J]\.)", full_answer_text)
    if q12_explanation:
        explanation = clean_text("12 Answers: " + q12_explanation.group(1))
        for q in questions:
            if re.fullmatch(r"12[a-d]", q["number"]):
                q["explanation"] = explanation
    if q13_explanation:
        explanation = clean_text("13 Answer: " + q13_explanation.group(1))
        for q in questions:
            if re.fullmatch(r"13[a-d]", q["number"]):
                q["explanation"] = explanation


def apply_manual_fixes(questions: list[dict]) -> None:
    fixed: list[dict] = []
    for q in questions:
        q["number"] = q["number"].replace("A", "a").replace("B", "b")
        if q["number"] == "12":
            answers = {"a": "D", "b": "B", "c": "A", "d": "C"}
            labels = {"a": "Patient 1", "b": "Patient 2", "c": "Patient 3", "d": "Patient 4"}
            for suffix, answer in answers.items():
                fixed.append({
                    **q,
                    "number": f"12{suffix}",
                    "stem": f"{q['stem']} Select the best diagnosis for {labels[suffix]}.",
                    "options": [dict(choice) for choice in q["options"]],
                    "answer": answer,
                })
            continue
        if q["number"] == "13":
            answers = {"a": "C", "b": "A", "c": "B", "d": "D"}
            labels = {"a": "Example 1", "b": "Example 2", "c": "Example 3", "d": "Example 4"}
            for suffix, answer in answers.items():
                fixed.append({
                    **q,
                    "number": f"13{suffix}",
                    "stem": f"{q['stem']} Identify {labels[suffix]}.",
                    "options": [dict(choice) for choice in q["options"]],
                    "answer": answer,
                })
            continue
        if q["number"] == "34b":
            choices = [
                {"letter": "A", "text": "1. Esophagus"},
                {"letter": "B", "text": "2. Laryngeal ventricle"},
                {"letter": "C", "text": "3. Laryngeal vestibule"},
                {"letter": "D", "text": "4. True cord"},
                {"letter": "E", "text": "5. False cord"},
                {"letter": "F", "text": "6. Trachea"},
                {"letter": "G", "text": "7. Pyriform sinus"},
                {"letter": "H", "text": "8. Epiglottis"},
                {"letter": "I", "text": "9. Vallecula"},
            ]
            answers = {"A": "G", "B": "D", "C": "E", "D": "B", "E": "I", "F": "H", "G": "C", "H": "F"}
            for label, answer in answers.items():
                fixed.append({
                    **q,
                    "number": f"34b{label}",
                    "stem": f"{q['stem']} Identify structure {label}.",
                    "options": [dict(choice) for choice in choices],
                    "answer": answer,
                })
            continue
        if q["number"] == "2" and not q["options"]:
            q["options"] = [{"letter": letter, "text": f"Case {letter}"} for letter in "ABCDE"]
        if q["number"] == "32" and not q["options"]:
            q["options"] = [{"letter": letter, "text": f"Case {letter}"} for letter in "ABCD"]
        fixed.append(q)
    questions[:] = fixed


def write_image(image, filename: str) -> str:
    path = ASSET_DIR / f"{Path(filename).stem}.jpg"
    with Image.open(BytesIO(image.data)) as pil_image:
        if pil_image.mode not in {"RGB", "L"}:
            pil_image = pil_image.convert("RGB")
        elif pil_image.mode == "L":
            pil_image = pil_image.convert("RGB")
        pil_image.save(path, format="JPEG", quality=92, optimize=True)
    return f"assets/{path.name}"


def extract_images(reader: PdfReader, questions: list[dict]) -> None:
    # Manually checked chapter page ranges. Continuation pages inherit the
    # current or visually associated question when the text layer is sparse.
    question_page_targets = {
        113: ["1"],
        114: ["2"],
        115: ["3"],
        116: ["3"],
        119: ["6"],
        120: ["6"],
        121: ["8"],
        122: ["9"],
        123: ["10a"],
        124: ["10a"],
        125: ["11a"],
        126: ["12a", "12b", "12c", "12d"],
        127: ["12a", "12b", "12c", "12d"],
        128: ["12a", "12b", "12c", "12d"],
        129: ["12a", "12b", "12c", "12d"],
        130: ["12a", "12b", "12c", "12d"],
        131: ["12a", "12b", "12c", "12d"],
        132: ["12a", "12b", "12c", "12d"],
        133: ["12a", "12b", "12c", "12d"],
        134: ["13a", "13b", "13c", "13d"],
        135: ["13a", "13b", "13c", "13d"],
        136: ["14"],
        137: ["15"],
        138: ["15"],
        139: ["16"],
        140: ["16"],
        141: ["17"],
        142: ["18"],
        143: ["18"],
        144: ["19"],
        145: ["20"],
        146: ["20"],
        147: ["21"],
        148: ["21"],
        149: ["22"],
        150: ["23"],
        151: ["24"],
        152: ["25"],
        153: ["25"],
        154: ["26"],
        180: ["27"],
        181: ["28"],
        182: ["28"],
        183: ["28"],
    }
    question_image_targets = {
        (117, 1): ["4"],
        (117, 2): ["5a"],
    }
    answer_page_targets = {
        155: ["1"],
        158: ["5c"],
        167: ["15"],
        170: ["16"],
        176: ["21"],
        184: ["27"],
    }
    by_number = {q["number"]: q for q in questions}
    for page_index, targets in question_page_targets.items():
        for image_index, image in enumerate(reader.pages[page_index].images, start=1):
            rel = write_image(image, f"q{'_'.join(targets)}_p{page_index + 1:03d}_{image_index:02d}")
            for target in targets:
                if target in by_number and rel not in by_number[target]["images"]:
                    by_number[target]["images"].append(rel)
    for (page_index, image_index), targets in question_image_targets.items():
        images = list(reader.pages[page_index].images)
        if image_index > len(images):
            continue
        rel = write_image(images[image_index - 1], f"q{'_'.join(targets)}_p{page_index + 1:03d}_{image_index:02d}")
        for target in targets:
            if target in by_number and rel not in by_number[target]["images"]:
                by_number[target]["images"].append(rel)
    for (page_index, image_index), targets in question_image_targets.items():
        images = list(reader.pages[page_index].images)
        if image_index > len(images):
            continue
        image = images[image_index - 1]
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
    for q in questions:
        match = re.fullmatch(r"(\d+)([bc])", q["number"])
        if not match:
            continue
        parent = by_number.get(f"{match.group(1)}a")
        if parent and parent["images"] and not q["images"]:
            q["images"] = list(parent["images"])


def render_html(questions: list[dict]) -> str:
    template = (APP_DIR / "_template.html").read_text(encoding="utf-8")
    data = json.dumps(questions, ensure_ascii=False)
    template = re.sub(r"const QUESTIONS = \[.*?\];", lambda _match: f"const QUESTIONS = {data};", template, flags=re.S)
    template = template.replace("Core Review Pediatric Imaging Quiz", TITLE)
    template = template.replace("Pediatric GI Imaging Quiz", TITLE)
    template = template.replace("Pediatric Gastrointestinal Tract Quiz", TITLE)
    template = template.replace("Nuclear Medicine Musculoskeletal System Quiz", TITLE)
    template = template.replace("Nuclear Medicine Head and Neck Quiz", TITLE)
    template = template.replace("Nuclear Medicine Cardiology Quiz", TITLE)
    template = template.replace("Nuclear Medicine Vascular and Lymphatics Quiz", TITLE)
    template = template.replace("Nuclear Medicine Pulmonary System Quiz", TITLE)
    template = template.replace("Nuclear Medicine Gastrointestinal System Quiz", TITLE)
    template = template.replace("Nuclear Medicine Genitourinary System Quiz", TITLE)
    template = template.replace("Nuclear Medicine Pediatric Nuclear Medicine Quiz", TITLE)
    template = template.replace("Nuclear Medicine Oncology Quiz", TITLE)
    template = template.replace("pediatric-imaging-quiz-ch1", APP_ID)
    template = template.replace("pediatric-gi-imaging-quiz-ch1", APP_ID)
    template = template.replace("nuclear-medicine-msk-quiz-ch3-v2", APP_ID)
    template = template.replace("nuclear-medicine-head-neck-quiz-ch4", APP_ID)
    template = template.replace("nuclear-medicine-cardiology-quiz-ch5", APP_ID)
    template = template.replace("nuclear-medicine-vascular-lymphatics-quiz-ch6", APP_ID)
    template = template.replace("nuclear-medicine-pulmonary-quiz-ch7", APP_ID)
    template = template.replace("nuclear-medicine-gastrointestinal-quiz-ch8", APP_ID)
    template = template.replace("nuclear-medicine-genitourinary-quiz-ch9", APP_ID)
    template = template.replace("nuclear-medicine-pediatric-quiz-ch10", APP_ID)
    template = template.replace("nuclear-medicine-oncology-quiz-ch11", APP_ID)
    default_selected_json = json.dumps(DEFAULT_SELECTED, ensure_ascii=False)
    template = re.sub(r"const DEFAULT_SELECTED = \{.*?\};", f"const DEFAULT_SELECTED = {default_selected_json};", template)
    template = re.sub(r"(const DEFAULT_SELECTED = .*?;\n)", rf"\1    const DEFAULT_SEED_VERSION = {DEFAULT_SEED_VERSION};\n", template)
    template = template.replace(
        "if (!saved || saved.appId !== APP_ID) return { ...DEFAULT_STATE };",
        "if (!saved || saved.appId !== APP_ID || saved.defaultSeedVersion !== DEFAULT_SEED_VERSION) return { ...DEFAULT_STATE };",
    )
    template = template.replace(
        "appId: APP_ID,\n        savedAt:",
        "appId: APP_ID,\n        defaultSeedVersion: DEFAULT_SEED_VERSION,\n        savedAt:",
    )
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
