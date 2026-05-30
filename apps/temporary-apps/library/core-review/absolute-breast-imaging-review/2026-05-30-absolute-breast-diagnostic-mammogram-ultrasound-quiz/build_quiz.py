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

TITLE = "Absolute Breast Imaging Review Diagnostic Mammogram and Ultrasound Quiz"
APP_ID = "absolute-breast-imaging-review-diagnostic-mammogram-ultrasound-quiz-ch4"
DEFAULT_SEED_VERSION = 1
DEFAULT_SELECTED: dict[str, str] = {}
QUESTION_PAGES = range(130, 168)
ANSWER_PAGES = range(167, 198)


def clean_text(value: str) -> str:
    value = value.replace("\t", " ").replace("\u00a0", " ")
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = value.replace("\u2018", "'").replace("\u2019", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
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
    if re.fullmatch(r"\d+\s+T\s*\.\s*L\s*\.\s*Chan et al\.", line):
        return True
    if re.fullmatch(r"4 Diagnostic Mammogram and Ultrasound\s+\d+", line):
        return True
    if re.fullmatch(r"\d+\s+\d+\s+T\s*\.\s*L\s*\.\s*Chan et al\.", line):
        return True
    if re.fullmatch(r"4 Diagnostic Mammogram and Ultrasound\s+\d+\s+\d+", line):
        return True
    if line in {"Answers", "References", "a", "b"}:
        return True
    return False


def parse_questions(reader: PdfReader) -> list[dict]:
    questions: list[dict] = []
    current: dict | None = None
    current_option: dict | None = None
    seen_answers = False

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
            if qmatch and 1 <= int(re.match(r"\d+", qmatch.group(1)).group(0)) <= 33:
                flush_question()
                current = {"number": qmatch.group(1), "stem": qmatch.group(2), "options": [], "images": [], "explanationImages": []}
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
        (130, 1): ["1a", "1b", "1c", "1d"], (130, 2): ["2a", "2b"],
        (131, 1): ["3a", "3b", "3c", "3d"],
        (132, 1): ["4a", "4b"],
        (133, 1): ["5a", "5b", "5c", "5d"],
        (134, 1): ["6a", "6b"], (135, 1): ["7a", "7b"], (135, 2): ["7a", "7b"],
        (136, 1): ["8a"], (137, 1): ["8b", "8c"],
        (138, 1): ["9"],
        (139, 1): ["10a", "10b", "10c", "10d"],
        (140, 1): ["11a", "11b"],
        (141, 1): ["12a"], (142, 1): ["12b", "12c"], (142, 2): ["12b", "12c"], (143, 1): ["12d", "12e"],
        (144, 1): ["13a", "13b"], (145, 1): ["13c"], (146, 1): ["14a", "14b", "14c"],
        (147, 1): ["15a", "15b"], (148, 1): ["15c"],
        (149, 1): ["16a"], (150, 1): ["16b", "16c"], (151, 1): ["17a", "17b", "17c", "17d", "17e"],
        (152, 1): ["18a", "18b"],
        (153, 1): ["19a", "19b", "19c"], (153, 2): ["19a", "19b", "19c"],
        (154, 1): ["20a", "20b"],
        (155, 1): ["21a", "21b"],
        (156, 1): ["22a"], (156, 2): ["22b", "22c"], (157, 1): ["22b", "22c"],
        (158, 1): ["23a", "23b", "23c"],
        (159, 1): ["24a", "24b"],
        (160, 1): ["25a", "25b"],
        (161, 1): ["26", "27"],
        (162, 1): ["28a", "28b"],
        (163, 1): ["29"],
        (164, 1): ["30"],
        (165, 1): ["31", "32"],
        (166, 1): ["33"],
    }
    explanation_image_targets = {
        (167, 1): ["1a"],
        (168, 1): ["2a"],
        (169, 1): ["2a"],
        (170, 1): ["3a"],
        (171, 1): ["4b"],
        (174, 1): ["8a"],
        (175, 1): ["8b"],
        (176, 1): ["10d"],
        (177, 1): ["10d"],
        (178, 1): ["11a"],
        (180, 1): ["13c"],
        (183, 1): ["15b"],
        (184, 1): ["15c"],
        (187, 1): ["18a"],
        (188, 1): ["19c"],
        (189, 1): ["19c"],
        (190, 1): ["20a"],
        (191, 1): ["21a"],
        (191, 2): ["21a"],
        (192, 1): ["22a"],
        (195, 1): ["25a"],
    }
    for (page_index, image_index), targets in question_image_targets.items():
        add_image(reader, page_index, image_index, targets, "q", by_number)
    for (page_index, image_index), targets in explanation_image_targets.items():
        add_image(reader, page_index, image_index, targets, "a", by_number)


def render_html(questions: list[dict]) -> str:
    template = (APP_DIR / "_template.html").read_text(encoding="utf-8")
    data = json.dumps(questions, ensure_ascii=False)
    template = re.sub(r"const QUESTIONS = \[.*?\];", lambda _match: f"const QUESTIONS = {data};", template, flags=re.S)
    title_pattern = r"(Pediatric GI Imaging Quiz|Pediatric Gastrointestinal Tract Quiz|Neuroradiology Spine Trauma and Degeneration Quiz|Neuroradiology Spine Infection, Inflammation, and Demyelination Quiz|Neuroradiology Spine Neoplasms and Vascular Diseases Quiz|Neuroradiology Congenital and Developmental Spine Quiz|Gastrointestinal Imaging Small Bowel Quiz|Interventional Radiology Thoracic Quiz|Absolute Breast Imaging Review Regulations and Standards of Care Quiz|Absolute Breast Imaging Review BI-RADS Terminology Quiz|Absolute Breast Imaging Review Screening Mammogram Quiz)"
    template = re.sub(title_pattern, TITLE, template)
    id_pattern = r"(pediatric-gi-imaging-quiz-ch1|neuroradiology-spine-trauma-degeneration-quiz-ch9|neuroradiology-spine-infection-inflammation-demyelination-quiz-ch10|neuroradiology-spine-neoplasms-vascular-diseases-quiz-ch11|neuroradiology-congenital-developmental-spine-quiz-ch12|gi-imaging-small-bowel-quiz-ch3|ir-thoracic-quiz-ch4|absolute-breast-imaging-review-regulations-standards-quiz-ch1|absolute-breast-imaging-review-birads-terminology-quiz-ch2|absolute-breast-imaging-review-screening-mammogram-quiz-ch3)"
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
