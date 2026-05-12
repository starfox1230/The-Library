from __future__ import annotations

import json
import re
from io import BytesIO
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


APP_DIR = Path(__file__).resolve().parent
SOURCE_PDF = Path(r"G:/My Drive/0. Radiology/Core Review Books/Neuroradiology/10SpineInfectionInfla_NeuroradiologyACoreRe.pdf")
ASSET_DIR = APP_DIR / "assets"

TITLE = "Neuroradiology Spine Infection, Inflammation, and Demyelination Quiz"
APP_ID = "neuroradiology-spine-infection-inflammation-demyelination-quiz-ch10"
DEFAULT_SEED_VERSION = 1
DEFAULT_SELECTED: dict[str, str] = {}

QUESTION_RANGES = [range(0, 18)]
ANSWER_RANGES = [range(17, 41)]
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def clean_text(value: str) -> str:
    value = value.replace("\t", " ")
    value = value.replace("\u00a0", " ")
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
    if re.fullmatch(r"\d{3}", line):
        return True
    if line in {"QUESTIONS", "Questions", "ANSWERS AND EXPLANATIONS", "Answers and Explanations"}:
        return True
    if line in {"Inflammation, and Demyelination"}:
        return True
    if re.fullmatch(r"10\s+Spine\s+Infection,", line):
        return True
    return False


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
                    return questions
                if is_noise_line(line) or line.startswith("Images courtesy"):
                    continue
                qmatch = re.match(r"^(\d{1,2}[a-b]?)\s+(.+)$", line, flags=re.I)
                if qmatch and not re.fullmatch(r"\d{1,3}", qmatch.group(2)):
                    qid, stem = qmatch.groups()
                    flush_question()
                    current = {"number": qid.lower(), "stem": stem, "options": [], "images": [], "explanationImages": []}
                    continue
                bare_qmatch = re.fullmatch(r"(\d{1,2}[a-b])", line, flags=re.I)
                if bare_qmatch:
                    flush_question()
                    current = {"number": bare_qmatch.group(1).lower(), "stem": "", "options": [], "images": [], "explanationImages": []}
                    continue
                omatch = re.match(r"^([A-P])\.\s*(.*)$", line)
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


def answer_lines(reader: PdfReader) -> list[str]:
    lines: list[str] = []
    for page_range in ANSWER_RANGES:
        for page_index in page_range:
            for line in page_lines(reader, page_index):
                if not is_noise_line(line):
                    lines.append(line)
    return lines


def parse_answers(reader: PdfReader, questions: list[dict]) -> None:
    entries: list[tuple[str, str]] = []
    current_id: str | None = None
    current_text: list[str] = []
    start_re = re.compile(r"^(\d{1,2}[a-b]?)(?:\s+Answers?|\s+Answer)\s+([A-D])\.\s*(.*)$", re.I)

    for line in answer_lines(reader):
        match = start_re.match(line)
        if match:
            qid, answer, rest = match.groups()
            if current_id:
                entries.append((current_id, clean_text(" ".join(current_text))))
            current_id = qid.lower()
            current_text = [f"Answer {answer.upper()}. {rest}"]
            continue
        if current_id:
            current_text.append(line)
    if current_id:
        entries.append((current_id, clean_text(" ".join(current_text))))

    by_id = {q["number"]: q for q in questions}
    for qid, explanation in entries:
        q = by_id.get(qid)
        if not q:
            continue
        q["answer"] = (re.search(r"Answer\s+([A-D])\.", explanation) or ["", ""])[1]
        q["explanation"] = re.sub(r"\s+References?:\s+", "\n\nReferences: ", explanation)
    if "3a" in by_id and not by_id["3a"].get("answer"):
        by_id["3a"]["answer"] = "B"
        by_id["3a"]["explanation"] = by_id.get("3b", {}).get("explanation", "Answer B. Diskitis/osteomyelitis with a right psoas abscess.")


def normalize_options(questions: list[dict]) -> None:
    parent_stems = {q["number"]: q["stem"] for q in questions if re.fullmatch(r"\d{1,2}", q["number"]) and not q["options"]}
    parent_stems["1"] = "A 50-year-old female with back pain, fevers, and chills presented to the ER. A contrast-enhanced CT was performed. Key image is shown below."
    collapsed: list[dict] = []
    for q in questions:
        if re.fullmatch(r"\d{1,2}", q["number"]) and not q["options"]:
            continue
        subpart = re.fullmatch(r"(\d{1,2})[a-b]", q["number"])
        if subpart and subpart.group(1) in parent_stems:
            q["stem"] = clean_text(parent_stems[subpart.group(1)] + " " + q["stem"])
        normalized = []
        for index, option in enumerate(q["options"]):
            if index >= 4:
                break
            normalized.append({"letter": LETTERS[index], "text": option["text"]})
        q["options"] = normalized
        collapsed.append(q)
    questions[:] = collapsed


def write_image(image, filename: str) -> str:
    path = ASSET_DIR / f"{Path(filename).stem}.jpg"
    with Image.open(BytesIO(image.data)) as pil_image:
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        pil_image.save(path, format="JPEG", quality=92, optimize=True)
    return f"assets/{path.name}"


def add_image(reader: PdfReader, page_index: int, image_index: int, targets: list[str], prefix: str, by_number: dict[str, dict]) -> None:
    images = list(reader.pages[page_index].images)
    if image_index > len(images):
        return
    rel = write_image(images[image_index - 1], f"{prefix}{'_'.join(targets)}_p{page_index + 1:03d}_{image_index:02d}")
    field = "images" if prefix == "q" else "explanationImages"
    for target in targets:
        if target in by_number and rel not in by_number[target][field]:
            by_number[target][field].append(rel)


def extract_images(reader: PdfReader, questions: list[dict]) -> None:
    by_number = {q["number"]: q for q in questions}

    question_image_targets = {
        (1, 1): ["1a"],
        (2, 1): ["1b"],
        (3, 1): ["2a"],
        (3, 2): ["2a"],
        (4, 1): ["2b"],
        (5, 1): ["3a", "3b"],
        (6, 1): ["4a", "4b"],
        (7, 1): ["5a"],
        (7, 1): ["5a", "5b"],
        (8, 1): ["6a", "6b"],
        (9, 1): ["7a", "7b"],
        (10, 1): ["8a", "8b"],
        (11, 1): ["9a", "9b"],
        (12, 1): ["10a", "10b"],
        (13, 1): ["11a", "11b"],
        (14, 1): ["12a", "12b"],
        (15, 1): ["13a", "13b"],
        (16, 1): ["14"],
        (17, 1): ["15"],
    }
    answer_image_targets = {
        (18, 1): ["1a"],
        (19, 1): ["1b"],
        (20, 1): ["1a", "1b"],
        (21, 1): ["2a", "2b"],
        (22, 1): ["3a", "3b"],
        (23, 1): ["4a", "4b"],
        (25, 1): ["5a"],
        (26, 1): ["5b"],
        (27, 1): ["6a", "6b"],
        (28, 1): ["7a", "7b"],
        (29, 1): ["8a", "8b"],
        (31, 1): ["9a", "9b"],
        (32, 1): ["10a", "10b"],
        (34, 1): ["11a", "11b"],
        (35, 1): ["12a", "12b"],
        (36, 1): ["13a", "13b"],
        (38, 1): ["14"],
        (39, 1): ["15"],
    }
    for (page_index, image_index), targets in question_image_targets.items():
        add_image(reader, page_index, image_index, targets, "q", by_number)
    for (page_index, image_index), targets in answer_image_targets.items():
        add_image(reader, page_index, image_index, targets, "a", by_number)


def render_html(questions: list[dict]) -> str:
    template = (APP_DIR / "_template.html").read_text(encoding="utf-8")
    data = json.dumps(questions, ensure_ascii=False)
    template = re.sub(r"const QUESTIONS = \[.*?\];", lambda _match: f"const QUESTIONS = {data};", template, flags=re.S)
    template = template.replace("Pediatric GI Imaging Quiz", TITLE)
    template = template.replace("Pediatric Gastrointestinal Tract Quiz", TITLE)
    template = template.replace("Neuroradiology Spine Trauma and Degeneration Quiz", TITLE)
    template = template.replace("Gastrointestinal Imaging Small Bowel Quiz", TITLE)
    template = template.replace("pediatric-gi-imaging-quiz-ch1", APP_ID)
    template = template.replace("neuroradiology-spine-trauma-degeneration-quiz-ch9", APP_ID)
    template = template.replace("gi-imaging-small-bowel-quiz-ch3", APP_ID)
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
    normalize_options(questions)
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
