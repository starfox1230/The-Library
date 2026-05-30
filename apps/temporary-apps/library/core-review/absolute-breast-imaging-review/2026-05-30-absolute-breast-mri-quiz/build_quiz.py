from __future__ import annotations

import json
import re
from io import BytesIO
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


APP_DIR = Path(__file__).resolve().parent
SOURCE_PDF = Path(r"G:/My Drive/0. Radiology/Core Review Books/Breast Imaging/Off Brand/Absolute Breast Imaging Review.pdf")
ASSET_DIR = APP_DIR / "assets"

TITLE = "Absolute Breast Imaging Review Breast MRI Quiz"
APP_ID = "absolute-breast-imaging-review-breast-mri-quiz-ch5"
DEFAULT_SEED_VERSION = 1
DEFAULT_SELECTED: dict[str, str] = {}
QUESTION_PAGES = range(201, 225)
ANSWER_PAGES = range(225, 247)


def clean_text(value: str) -> str:
    value = value.replace("\t", " ").replace("\u00a0", " ")
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = value.replace("\u2018", "'").replace("\u2019", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = value.replace(") - *", ") *")
    value = re.sub(r"\s+", " ", value)
    value = value.replace("t1his", "this")
    value = re.sub(r"(\w)- (\w)", r"\1\2", value)
    value = re.sub(r"(\w)\s+-\s+(\w)", r"\1\2", value)
    value = re.sub(r"\s+([,.;:])", r"\1", value)
    return value.strip()


def page_lines(reader: PdfReader, page_index: int) -> list[str]:
    text = reader.pages[page_index].extract_text(extraction_mode="layout") or ""
    return [clean_text(line) for line in text.splitlines() if clean_text(line)]


def is_noise_line(line: str) -> bool:
    if re.fullmatch(r"\d+\s+M\s*\.\s*M\s*\.\s*Joines et al\.", line):
        return True
    if re.fullmatch(r"5\s+Breast MRI\s+\d+", line):
        return True
    if re.fullmatch(r"\d+\s+\d+\s+M\s*\.\s*M\s*\.\s*Joines et al\.", line):
        return True
    if re.fullmatch(r"5\s+Breast MRI\s+\d+\s+\d+", line):
        return True
    if line in {"Answers", "References", "a", "b"}:
        return True
    return False


def parse_questions(reader: PdfReader) -> list[dict]:
    questions: list[dict] = []
    current: dict | None = None
    current_option: dict | None = None
    seen_answers = False
    seen_question_ids: set[str] = set()

    def flush_option() -> None:
        nonlocal current_option
        if current and current_option:
            current_option["text"] = clean_text(current_option["text"])
            current["options"].append(current_option)
        current_option = None

    def flush_question() -> None:
        nonlocal current, current_option
        flush_option()
        if current and current.get("stem"):
            current["stem"] = clean_text(current["stem"])
            questions.append(current)
        current = None
        current_option = None

    for page_index in QUESTION_PAGES:
        for line in page_lines(reader, page_index):
            if line == "Answers":
                seen_answers = True
                break
            if is_noise_line(line):
                continue
            qmatch = re.match(r"^(\d{1,2}[a-z]?)\.\s*(.+)$", line, flags=re.I)
            if qmatch and 1 <= int(re.match(r"\d+", qmatch.group(1)).group(0)) <= 44:
                if qmatch.group(1) in seen_question_ids:
                    if current_option:
                        current_option["text"] += " " + line
                    elif current:
                        current["stem"] += " " + line
                    continue
                flush_question()
                current = {"number": qmatch.group(1), "stem": qmatch.group(2), "options": [], "images": [], "explanationImages": []}
                seen_question_ids.add(qmatch.group(1))
                continue
            omatch = re.match(r"^\(([a-f])\)\s*(.*)$", line, flags=re.I)
            if current and omatch:
                flush_option()
                current_option = {"letter": omatch.group(1).upper(), "text": omatch.group(2)}
                continue
            if current_option:
                current_option["text"] += " " + line
            elif current:
                current["stem"] += " " + line
        if seen_answers:
            break
    flush_question()
    return questions


def parse_answers(reader: PdfReader) -> dict[str, dict[str, str]]:
    answers: dict[str, dict[str, str]] = {}
    current_id: str | None = None
    in_answers = False
    for page_index in ANSWER_PAGES:
        for line in page_lines(reader, page_index):
            if line == "Answers":
                in_answers = True
                continue
            if line == "References":
                return answers
            if not in_answers or is_noise_line(line):
                continue
            amatch = re.match(r"^(\d{1,2}[a-z]?)\.\s*([a-f])\.\s*(.*)$", line, flags=re.I)
            if amatch:
                current_id, letter, rest = amatch.groups()
                answers[current_id] = {"answer": letter.upper(), "explanation": f"{letter.lower()}. {rest}".strip()}
                continue
            if current_id:
                answers[current_id]["explanation"] += " " + line
    return answers


def write_image(image, filename: str) -> str | None:
    path = ASSET_DIR / f"{Path(filename).stem}.jpg"
    with Image.open(BytesIO(image.data)) as pil_image:
        if pil_image.width * pil_image.height < 5000 or (pil_image.width <= 40 and pil_image.height <= 40):
            return None
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        pil_image.save(path, format="JPEG", quality=92, optimize=True)
    return f"assets/{path.name}"


def add_image(reader: PdfReader, page_index: int, image_index: int, targets: list[str], prefix: str, by_number: dict[str, dict]) -> None:
    images = list(reader.pages[page_index].images)
    if image_index > len(images):
        return
    rel = write_image(images[image_index - 1], f"{prefix}{'_'.join(targets)}_p{page_index + 1:03d}_{image_index:02d}")
    if not rel:
        return
    field = "images" if prefix == "q" else "explanationImages"
    for target in targets:
        if target in by_number and rel not in by_number[target][field]:
            by_number[target][field].append(rel)


def extract_images(reader: PdfReader, questions: list[dict]) -> None:
    by_number = {q["number"]: q for q in questions}
    question_image_targets = {
        (201, 1): ["1a", "1b"],
        (202, 1): ["3"],
        (203, 1): ["4"],
        (203, 2): ["5"],
        (204, 1): ["6"],
        (205, 1): ["7"],
        (205, 2): ["8"],
        (206, 1): ["9a", "9b"],
        (206, 2): ["10a"],
        (207, 1): ["10b"],
        (208, 1): ["11"],
        (208, 2): ["12"],
        (209, 1): ["13"],
        (210, 1): ["14"],
        (210, 2): ["15"],
        (211, 1): ["16"],
        (211, 2): ["17"],
        (212, 1): ["18"],
        (212, 2): ["19"],
        (213, 1): ["20a", "20b"],
        (213, 2): ["21a", "21b", "21c"],
        (214, 1): ["22"],
        (215, 1): ["24"],
        (216, 1): ["25"],
        (216, 2): ["26"],
        (217, 1): ["28"],
        (217, 2): ["29"],
        (219, 1): ["33"],
        (219, 2): ["34"],
        (220, 1): ["35"],
        (221, 1): ["36"],
        (221, 2): ["37"],
        (222, 1): ["38"],
        (222, 2): ["39"],
        (223, 1): ["40"],
        (223, 2): ["41"],
        (224, 1): ["44"],
    }
    explanation_image_targets = {
        (225, 1): ["3"],
        (226, 1): ["5"],
        (227, 1): ["7"],
        (227, 2): ["8"],
        (228, 1): ["10a"],
        (229, 1): ["12"],
        (230, 1): ["13"],
        (230, 2): ["14"],
        (230, 3): ["14"],
        (231, 1): ["15"],
        (231, 2): ["16"],
        (232, 1): ["17"],
        (232, 2): ["19"],
        (233, 1): ["20a", "20b", "21a", "21b", "21c"],
        (235, 1): ["25"],
        (236, 1): ["26"],
        (240, 1): ["36"],
        (240, 2): ["36"],
        (240, 3): ["36"],
        (240, 4): ["36"],
        (241, 1): ["37"],
        (242, 1): ["38", "39", "40"],
        (243, 1): ["40", "41"],
        (245, 1): ["43"],
        (245, 2): ["44"],
        (245, 3): ["44"],
        (245, 4): ["44"],
    }
    for (page_index, image_index), targets in question_image_targets.items():
        add_image(reader, page_index, image_index, targets, "q", by_number)
    for (page_index, image_index), targets in explanation_image_targets.items():
        add_image(reader, page_index, image_index, targets, "a", by_number)


def render_html(questions: list[dict]) -> str:
    template = (APP_DIR / "_template.html").read_text(encoding="utf-8")
    data = json.dumps(questions, ensure_ascii=False)
    template = re.sub(r"const QUESTIONS = \[.*?\];", lambda _match: f"const QUESTIONS = {data};", template, flags=re.S)
    title_pattern = r"(Pediatric GI Imaging Quiz|Pediatric Gastrointestinal Tract Quiz|Neuroradiology Spine Trauma and Degeneration Quiz|Neuroradiology Spine Infection, Inflammation, and Demyelination Quiz|Neuroradiology Spine Neoplasms and Vascular Diseases Quiz|Neuroradiology Congenital and Developmental Spine Quiz|Gastrointestinal Imaging Small Bowel Quiz|Interventional Radiology Thoracic Quiz|Absolute Breast Imaging Review Regulations and Standards of Care Quiz|Absolute Breast Imaging Review BI-RADS Terminology Quiz|Absolute Breast Imaging Review Screening Mammogram Quiz|Absolute Breast Imaging Review Diagnostic Mammogram and Ultrasound Quiz)"
    template = re.sub(title_pattern, TITLE, template)
    id_pattern = r"(pediatric-gi-imaging-quiz-ch1|neuroradiology-spine-trauma-degeneration-quiz-ch9|neuroradiology-spine-infection-inflammation-demyelination-quiz-ch10|neuroradiology-spine-neoplasms-vascular-diseases-quiz-ch11|neuroradiology-congenital-developmental-spine-quiz-ch12|gi-imaging-small-bowel-quiz-ch3|ir-thoracic-quiz-ch4|absolute-breast-imaging-review-regulations-standards-quiz-ch1|absolute-breast-imaging-review-birads-terminology-quiz-ch2|absolute-breast-imaging-review-screening-mammogram-quiz-ch3|absolute-breast-imaging-review-diagnostic-mammogram-ultrasound-quiz-ch4)"
    template = re.sub(id_pattern, APP_ID, template)
    default_selected_json = json.dumps(DEFAULT_SELECTED, ensure_ascii=False)
    template = re.sub(r"const DEFAULT_SELECTED = \{.*?\};", f"const DEFAULT_SELECTED = {default_selected_json};", template)
    if "DEFAULT_SEED_VERSION" not in template:
        template = re.sub(r"(const DEFAULT_SELECTED = .*?;\n)", rf"\1    const DEFAULT_SEED_VERSION = {DEFAULT_SEED_VERSION};\n", template)
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
    answers = parse_answers(reader)
    for q in questions:
        answer = answers.get(q["number"])
        if not answer and q["number"][-1:].isalpha():
            answer = answers.get(re.match(r"\d+", q["number"]).group(0))
        if answer:
            q["answer"] = answer["answer"]
            q["explanation"] = clean_text(answer["explanation"])
        elif q["number"] == "20b":
            q["answer"] = "B"
            q["explanation"] = "b. Inflamed cyst."
        else:
            q["answer"] = ""
            q["explanation"] = ""
    extract_images(reader, questions)
    (APP_DIR / "questions.json").write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")
    (APP_DIR / "index.html").write_text(render_html(questions), encoding="utf-8")
    print(f"wrote {len(questions)} questions")
    print("missing answers:", [q["number"] for q in questions if not q.get("answer")])
    print("bad option counts:", [(q["number"], len(q["options"])) for q in questions if len(q["options"]) < 3 or len(q["options"]) > 5])
    print("question image refs:", sum(len(q["images"]) for q in questions))
    print("explanation image refs:", sum(len(q["explanationImages"]) for q in questions))


if __name__ == "__main__":
    main()
