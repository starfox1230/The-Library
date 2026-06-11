from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "apps/core-studying/Radioisotope Safety Document/RISC-game-design-plan.md"
SOURCE_DIR = ROOT / "apps/core-studying/Radioisotope Safety Document 2026"
OUTPUT_ROOT = ROOT / "apps/temporary-apps/library/core-review/radioisotope-safety-document-2026"
TEMPLATE = (
    ROOT
    / "apps/temporary-apps/library/core-review/absolute-breast-imaging-review"
    / "2026-06-10-absolute-breast-pathology-quiz/_template.html"
)

CHAPTERS = {
    1: ("Introduction and Radiation Protection", "introduction-radiation-protection"),
    2: ("Radiation Biology", "radiation-biology"),
    3: ("Transport and Management of Radioactive Materials", "transport-management"),
    4: ("Regulatory Exposure Limits", "regulatory-exposure-limits"),
    5: ("Radiopharmaceutical Administration", "radiopharmaceutical-administration"),
    6: ("Administrative Regulations, Responsibilities, and Training", "administrative-regulations"),
    7: ("Emergency Procedures and Special Circumstances", "emergency-procedures"),
    8: ("Radiation-Measuring Instrumentation and QC", "instrumentation-quality-control"),
}

SOURCE_FILES = {
    1: "01. Introduction and Radiation protection.txt",
    2: "02. Radiation Biology.txt",
    3: "03. Transport and management of radioactive materials.txt",
    4: "04. Regulatory exposure limits to radioactive materials.txt",
    5: "05. Radiopharmaceutical administration.txt",
    6: "06. Administrative and practice regulations, responsibilities and training.txt",
    7: "07. Emergency procedures, accidents and incidents, special circumstances.txt",
    8: "08. Appendix 1. Radiation-Measuring Instrumentation and Quality Control Tests.txt",
}

SWAPS = [
    ("annual", "monthly"),
    ("annually", "monthly"),
    ("quarterly", "annually"),
    ("every 3 months", "every 12 months"),
    ("every 12 months", "every 3 months"),
    ("must", "need not"),
    ("required", "prohibited"),
    ("higher", "lower"),
    ("high", "low"),
    ("shorter", "longer"),
    ("less than", "greater than"),
    ("more than", "less than"),
    ("diagnostic", "therapeutic"),
    ("therapeutic", "diagnostic"),
    ("restricted", "unrestricted"),
    ("unrestricted", "restricted"),
    ("internal", "external"),
    ("external", "internal"),
    ("alpha", "gamma"),
    ("gamma", "alpha"),
    ("beta", "neutron"),
    ("physical", "biological"),
    ("biological", "physical"),
    ("stochastic", "deterministic"),
    ("deterministic", "stochastic"),
    ("RSO", "patient"),
    ("NRC", "FDA"),
]


def clean(text: str) -> str:
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    text = text.replace("–", "-").replace("—", "-").replace("×", "x")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_plan() -> dict[int, list[dict]]:
    chapters: dict[int, list[dict]] = {number: [] for number in CHAPTERS}
    chapter = 0
    section = ""
    mode = ""
    for raw in PLAN.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        chapter_match = re.match(r"## Chapter (\d+)\.", line)
        if chapter_match:
            chapter = int(chapter_match.group(1))
            section = ""
            mode = ""
            continue
        section_match = re.match(r"### (.+)", line)
        if section_match:
            section = clean(section_match.group(1))
            mode = ""
            continue
        if line == "**Facts to teach**":
            mode = "facts"
            continue
        if line.startswith("**"):
            mode = ""
            continue
        if chapter and mode == "facts" and line.startswith("- "):
            fact = clean(line[2:])
            if len(fact) >= 20:
                chapters[chapter].append({"section": section, "fact": fact})
    return chapters


def replace_first(text: str, old: str, new: str) -> str | None:
    pattern = re.escape(old)
    if old[0].isalnum() and old[-1].isalnum():
        pattern = rf"\b{pattern}\b"
    match = re.search(pattern, text, flags=re.I)
    if not match:
        return None
    return text[: match.start()] + new + text[match.end() :]


def mutate_number(text: str, offset: int) -> str | None:
    matches = list(re.finditer(r"(?<![A-Za-z])(\d+(?:\.\d+)?)", text))
    if not matches:
        return None
    match = matches[min(offset, len(matches) - 1)]
    value = float(match.group(1))
    if value == 0:
        replacement = "1"
    elif value < 2:
        replacement = f"{value * (2 + offset):g}"
    elif value <= 10:
        replacement = f"{value + 2 + offset:g}"
    else:
        replacement = f"{value * (2 if offset % 2 == 0 else 0.5):g}"
    return text[: match.start()] + replacement + text[match.end() :]


def make_distractors(fact: str) -> list[str]:
    candidates: list[str] = []
    for old, new in SWAPS:
        changed = replace_first(fact, old, new)
        if (
            changed
            and changed != fact
            and not re.search(r"\b(\w+)\s+(?:or|and)\s+\1\b", changed, flags=re.I)
        ):
            candidates.append(changed)
    for index in range(3):
        changed = mutate_number(fact, index)
        if changed and changed != fact:
            candidates.append(changed)
    negated = None
    for old, new in [
        (" does not ", " does "),
        (" do not ", " do "),
        (" cannot ", " can "),
        (" can ", " cannot "),
        (" are ", " are not "),
        (" is ", " is not "),
        (" includes ", " excludes "),
        (" include ", " exclude "),
    ]:
        negated = replace_first(fact, old, new)
        if negated:
            candidates.append(negated)
            break
    unique = []
    for candidate in candidates:
        candidate = clean(candidate)
        if candidate != fact and candidate not in unique:
            unique.append(candidate)
    fallbacks = [
        "The guidance treats this as optional and leaves the decision entirely to individual preference.",
        "The rule applies only to nonmedical industrial facilities, not to clinical nuclear radiology.",
        "No documentation, training, or radiation-safety oversight is required for this issue.",
    ]
    for fallback in fallbacks:
        if len(unique) >= 3:
            break
        unique.append(fallback)
    return unique[:3]


def make_questions(items: list[dict], chapter_number: int) -> list[dict]:
    questions = []
    answer_positions = [0, 2, 1, 3]
    for index, item in enumerate(items, start=1):
        fact = item["fact"]
        distractors = make_distractors(fact)
        position = answer_positions[(index - 1) % len(answer_positions)]
        choices = distractors[:]
        choices.insert(position, fact)
        letters = "ABCD"
        options = [{"letter": letters[i], "text": choice} for i, choice in enumerate(choices)]
        section = re.sub(r"^\d+(?:\.\d+)*\s*", "", item["section"]).strip()
        stem = f"According to the 2026 RISC guidance, which statement about {section.lower()} is correct?"
        questions.append(
            {
                "number": str(index),
                "stem": stem,
                "options": options,
                "answer": letters[position],
                "explanation": (
                    f"Correct answer: {letters[position]}. {fact} "
                    f"This point is drawn from Chapter {chapter_number}, section '{item['section']}', "
                    "and is tested because it is a practical safety rule, regulatory requirement, "
                    "high-yield distinction, or commonly confused threshold."
                ),
                "images": [],
                "explanationImages": [],
            }
        )
    return questions


def render_html(template: str, questions: list[dict], title: str, app_id: str) -> str:
    html = re.sub(
        r"const QUESTIONS = \[.*?\];",
        lambda _: f"const QUESTIONS = {json.dumps(questions, ensure_ascii=False)};",
        template,
        flags=re.S,
    )
    html = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html, count=1)
    html = re.sub(r'const APP_ID = ".*?";', f'const APP_ID = "{app_id}";', html, count=1)
    html = re.sub(r"const DEFAULT_SELECTED = \{.*?\};", "const DEFAULT_SELECTED = {};", html, count=1)
    html = re.sub(
        r"const DEFAULT_STATE = \{.*?\};",
        'const DEFAULT_STATE = { index: 0, selected: DEFAULT_SELECTED, submitted: DEFAULT_SUBMITTED, mode: "tutor", reviewOpen: false, navOpen: false };',
        html,
        count=1,
    )
    return html


def main() -> None:
    parsed = parse_plan()
    template = TEMPLATE.read_text(encoding="utf-8")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for chapter_number, (chapter_title, slug) in CHAPTERS.items():
        items = parsed[chapter_number]
        questions = make_questions(items, chapter_number)
        folder = OUTPUT_ROOT / f"2026-06-10-risc-{slug}-quiz"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "assets").mkdir(exist_ok=True)
        title = f"RISC Chapter {chapter_number}: {chapter_title} Quiz"
        app_id = f"risc-2026-{slug}-quiz-ch{chapter_number}"
        (folder / "questions.json").write_text(
            json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (folder / "index.html").write_text(
            render_html(template, questions, title, app_id), encoding="utf-8"
        )
        source_file = SOURCE_FILES[chapter_number]
        readme = (
            f"# RISC 2026 Chapter {chapter_number} Quiz\n\n"
            f"- Chapter: {chapter_title}.\n"
            f"- Authoritative source: `apps/core-studying/Radioisotope Safety Document 2026/{source_file}`.\n"
            f"- Coverage map: `apps/core-studying/Radioisotope Safety Document/RISC-game-design-plan.md`.\n"
            f"- Output: {len(questions)} scored entries, one for each major fact identified in the coverage map.\n"
            "- Images: none by design.\n"
            "- Default answers: empty. Progress is saved locally by the quiz app.\n\n"
            "The generator creates answer choices deterministically, rotates correct-answer positions, "
            "and includes a source-section explanation for every item. Re-run "
            "`python scripts/generate_risc_quizzes.py` after updating the source or coverage map.\n"
        )
        (folder / "README.md").write_text(readme, encoding="utf-8")
        manifest.append(
            {
                "chapter": chapter_number,
                "title": chapter_title,
                "slug": slug,
                "folder": folder.name,
                "questions": len(questions),
                "source": source_file,
            }
        )
        print(f"Chapter {chapter_number}: {len(questions)} questions")
    (OUTPUT_ROOT / "quiz-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Total: {sum(item['questions'] for item in manifest)} questions")


if __name__ == "__main__":
    main()
