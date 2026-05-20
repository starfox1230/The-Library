from __future__ import annotations

import json
import re
from io import BytesIO
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


APP_DIR = Path(__file__).resolve().parent
SOURCE_PDF = Path(r"G:/My Drive/0. Radiology/Core Review Books/IR/1_ Fundamentals of Interventional Radiology.pdf")
ASSET_DIR = APP_DIR / "assets"

TITLE = "Interventional Radiology Fundamentals Quiz"
APP_ID = "ir-fundamentals-quiz-ch1"
DEFAULT_SEED_VERSION = 1
DEFAULT_SELECTED: dict[str, str] = {}
CONTENT_PAGES = range(0, 44)
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def clean_text(value: str) -> str:
    value = value.replace("\t", " ").replace("\u00a0", " ")
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = value.replace("\u2018", "'").replace("\u2019", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = value.replace("â€“", "-").replace("â€™", "'").replace("â€œ", '"').replace("â€", '"')
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+([,.;:])", r"\1", value)
    return value.strip()


def page_lines(reader: PdfReader, page_index: int) -> list[str]:
    text = reader.pages[page_index].extract_text(extraction_mode="layout") or ""
    return [clean_text(line) for line in text.splitlines() if clean_text(line)]


def is_noise_line(line: str) -> bool:
    if line in {"QUESTIONS", "ANSWERS AND EXPLANATIONS", "CHAPTER 1", "Fundamentals of Interventional Radiology"}:
        return True
    if "Vascular and Interventional Radiology" in line or "ISBN:" in line or "Elbich," in line:
        return True
    if line.startswith("ab999 |"):
        return True
    if re.fullmatch(r"\(?Print pagebreak \d+\)?", line):
        return True
    if re.fullmatch(r"\d+\.", line):
        return True
    if re.fullmatch(r"\d+\. View Answer", line):
        return True
    return False


def parse_questions(reader: PdfReader) -> list[dict]:
    questions: list[dict] = []
    current: dict | None = None
    current_option: dict | None = None
    mode: str | None = None

    def flush_option() -> None:
        nonlocal current_option
        if current and current_option:
            current_option["text"] = clean_text(current_option["text"])
            current["options"].append(current_option)
        current_option = None

    def flush_question() -> None:
        nonlocal current, current_option, mode
        flush_option()
        if current and current.get("stem"):
            current["stem"] = clean_text(current["stem"])
            current["explanation"] = clean_text(current.get("explanation", ""))
            questions.append(current)
        current = None
        current_option = None
        mode = None

    for page_index in CONTENT_PAGES:
        for line in page_lines(reader, page_index):
            if is_noise_line(line):
                continue
            if line == "ANSWERS AND EXPLANATIONS":
                flush_question()
                return questions
            amatch = re.match(r"^(\d{1,2})\s+Answer\s+([A-E])\.\s*(.*)$", line, flags=re.I)
            if amatch:
                qid, answer, rest = amatch.groups()
                flush_option()
                if current is None or current["number"] != qid:
                    flush_question()
                    current = {"number": qid, "stem": "", "options": [], "images": [], "explanationImages": []}
                current["answer"] = answer.upper()
                current["explanation"] = f"Answer {answer.upper()}. {rest}"
                mode = "answer"
                continue
            qmatch = re.match(r"^(\d{1,2})\s+(?!Answer\b)(.+)$", line, flags=re.I)
            if qmatch:
                qid, stem = qmatch.groups()
                # Lines such as reference years or doses can look numeric; only accept plausible next question ids.
                if 1 <= int(qid) <= 34 and (current is None or mode == "answer" or int(qid) != int(current["number"])):
                    flush_question()
                    current = {"number": qid, "stem": stem, "options": [], "images": [], "explanationImages": []}
                    mode = "question"
                    continue
            omatch = re.match(r"^([A-E])\.\s*(.*)$", line)
            if current and mode != "answer" and omatch:
                flush_option()
                current_option = {"letter": omatch.group(1), "text": omatch.group(2)}
                continue
            if current_option and mode != "answer":
                current_option["text"] += " " + line
            elif current and mode == "answer":
                current["explanation"] += " " + line
            elif current:
                current["stem"] += " " + line
    flush_question()
    return questions


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
        (2, 1): ["5"],
        (3, 1): ["6"],
        (8, 1): ["12"],
        (11, 2): ["14"],
        (13, 1): ["15"], (13, 2): ["15"],
        (14, 1): ["16"],
        (18, 1): ["20"],
        (22, 1): ["21"],
        (25, 1): ["22"],
        (27, 1): ["23"],
        (28, 1): ["24"],
        (31, 1): ["26"],
        (32, 2): ["27"],
        (33, 2): ["28"],
        (35, 1): ["29"],
        (37, 1): ["30"],
        (38, 1): ["31"], (38, 2): ["31"],
        (41, 1): ["34"],
    }
    explanation_image_targets = {
        (1, 2): ["3"],
        (2, 1): ["5"],
        (4, 1): ["6"], (4, 2): ["6"], (5, 1): ["6"], (5, 2): ["6"],
        (8, 1): ["12"], (9, 1): ["12"],
        (10, 1): ["13"],
        (11, 2): ["14"], (12, 1): ["14"], (12, 2): ["14"],
        (13, 1): ["15"], (13, 2): ["15"],
        (14, 1): ["16"], (15, 1): ["16"],
        (17, 1): ["19"],
        (18, 1): ["20"], (19, 1): ["20"], (20, 1): ["20"], (21, 2): ["20"],
        (22, 1): ["21"], (23, 1): ["21"], (24, 1): ["21"],
        (25, 1): ["22"], (26, 1): ["22"],
        (27, 1): ["23"],
        (28, 1): ["24"], (29, 1): ["24"],
        (30, 1): ["26"], (31, 1): ["26"],
        (32, 2): ["27"], (33, 1): ["27"],
        (33, 2): ["28"], (34, 1): ["28"],
        (35, 1): ["29"], (36, 1): ["29"],
        (36, 2): ["30"], (37, 1): ["30"],
        (38, 1): ["31"], (38, 2): ["31"],
        (41, 1): ["34"], (42, 1): ["34"], (42, 3): ["34"], (43, 1): ["34"],
    }
    for (page_index, image_index), targets in question_image_targets.items():
        add_image(reader, page_index, image_index, targets, "q", by_number)
    for (page_index, image_index), targets in explanation_image_targets.items():
        add_image(reader, page_index, image_index, targets, "a", by_number)


def render_html(questions: list[dict]) -> str:
    template = (APP_DIR / "_template.html").read_text(encoding="utf-8")
    data = json.dumps(questions, ensure_ascii=False)
    template = re.sub(r"const QUESTIONS = \[.*?\];", lambda _match: f"const QUESTIONS = {data};", template, flags=re.S)
    for old in [
        "Pediatric GI Imaging Quiz",
        "Pediatric Gastrointestinal Tract Quiz",
        "Neuroradiology Spine Trauma and Degeneration Quiz",
        "Neuroradiology Spine Infection, Inflammation, and Demyelination Quiz",
        "Neuroradiology Spine Neoplasms and Vascular Diseases Quiz",
        "Neuroradiology Congenital and Developmental Spine Quiz",
        "Gastrointestinal Imaging Small Bowel Quiz",
    ]:
        template = template.replace(old, TITLE)
    for old_id in [
        "pediatric-gi-imaging-quiz-ch1",
        "neuroradiology-spine-trauma-degeneration-quiz-ch9",
        "neuroradiology-spine-infection-inflammation-demyelination-quiz-ch10",
        "neuroradiology-spine-neoplasms-vascular-diseases-quiz-ch11",
        "neuroradiology-congenital-developmental-spine-quiz-ch12",
        "gi-imaging-small-bowel-quiz-ch3",
    ]:
        template = template.replace(old_id, APP_ID)
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
