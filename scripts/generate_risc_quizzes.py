from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from risc_curated_bank import CHAPTER_QUESTIONS


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "apps/core-studying/Radioisotope Safety Document 2026"
OUTPUT_ROOT = ROOT / "apps/temporary-apps/library/core-review/radioisotope-safety-document-2026"
TEMPLATE = (
    ROOT
    / "apps/temporary-apps/library/core-review/absolute-breast-imaging-review"
    / "2026-06-10-absolute-breast-pathology-quiz/_template.html"
)
BANK_VERSION = 2

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


def balance_options(item: dict, target_answer: str) -> tuple[list[dict], str]:
    letters = "ABCD"
    source_index = letters.index(item["answer"])
    correct_text = item["options"][source_index]
    distractors = [
        option for index, option in enumerate(item["options"]) if index != source_index
    ]
    target_index = letters.index(target_answer)
    ordered = distractors[:]
    ordered.insert(target_index, correct_text)
    return (
        [
            {"letter": letter, "text": text}
            for letter, text in zip(letters, ordered, strict=True)
        ],
        target_answer,
    )


def make_questions(items: list[dict], chapter_number: int) -> list[dict]:
    questions = []
    letters = "ABCD"
    for index, source_item in enumerate(items, start=1):
        target_answer = letters[(index + chapter_number - 2) % 4]
        options, answer = balance_options(source_item, target_answer)
        questions.append(
            {
                "number": str(index),
                "stem": source_item["stem"],
                "options": options,
                "answer": answer,
                "explanation": source_item["explanation"],
                "images": [],
                "explanationImages": [],
                "sourceChapter": chapter_number,
            }
        )
    return questions


def validate_questions(questions: list[dict], chapter_number: int) -> None:
    expected_numbers = [str(number) for number in range(1, len(questions) + 1)]
    actual_numbers = [question["number"] for question in questions]
    if actual_numbers != expected_numbers:
        raise ValueError(f"Chapter {chapter_number}: question numbers are not sequential")

    for question in questions:
        number = question["number"]
        options = question["options"]
        letters = [option["letter"] for option in options]
        texts = [option["text"].strip() for option in options]
        if letters != list("ABCD"):
            raise ValueError(f"Chapter {chapter_number}, question {number}: invalid letters")
        if question["answer"] not in letters:
            raise ValueError(f"Chapter {chapter_number}, question {number}: invalid answer")
        if len(set(texts)) != 4:
            raise ValueError(f"Chapter {chapter_number}, question {number}: duplicate options")
        if not question["stem"].strip().endswith("?"):
            raise ValueError(f"Chapter {chapter_number}, question {number}: open lead-in")
        if not question["explanation"].strip():
            raise ValueError(f"Chapter {chapter_number}, question {number}: no explanation")

    distribution = Counter(question["answer"] for question in questions)
    if max(distribution.values()) - min(distribution.values()) > 1:
        raise ValueError(
            f"Chapter {chapter_number}: unbalanced answer distribution {distribution}"
        )


def render_html(template: str, questions: list[dict], title: str, app_id: str) -> str:
    html = re.sub(
        r"const QUESTIONS = \[.*?\];",
        lambda _: f"const QUESTIONS = {json.dumps(questions, ensure_ascii=False)};",
        template,
        flags=re.S,
    )
    html = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html, count=1)
    html = re.sub(r'const APP_ID = ".*?";', f'const APP_ID = "{app_id}";', html, count=1)
    html = html.replace(
        'const STORAGE_KEY = "temporary-app-state:" + APP_ID;',
        f'const STORAGE_KEY = "temporary-app-state:" + APP_ID + ":bank-{BANK_VERSION}";',
        1,
    )
    html = re.sub(r"const DEFAULT_SELECTED = \{.*?\};", "const DEFAULT_SELECTED = {};", html, count=1)
    html = re.sub(
        r"const DEFAULT_STATE = \{.*?\};",
        'const DEFAULT_STATE = { index: 0, selected: DEFAULT_SELECTED, submitted: DEFAULT_SUBMITTED, mode: "tutor", reviewOpen: false, navOpen: false };',
        html,
        count=1,
    )
    html = html.replace("version: 1,", f"version: {BANK_VERSION},", 1)
    html = html.replace(
        'if (!payload || payload.appId !== APP_ID) throw new Error("This saved state is for a different quiz.");',
        f'if (!payload || payload.appId !== APP_ID || payload.version !== {BANK_VERSION}) throw new Error("This saved state is for a different quiz version.");',
        1,
    )
    html = html.replace(
        '{"version":1,"appId":"pediatric-gi-imaging-quiz-ch1",...}',
        f'{{"version":{BANK_VERSION},"appId":"{app_id}",...}}',
        1,
    )
    html = html.replace("PDF explanation:", "Source explanation:")
    return html


def chapter_readme(
    chapter_number: int, chapter_title: str, source_file: str, question_count: int
) -> str:
    return (
        f"# RISC 2026 Chapter {chapter_number} Quiz\n\n"
        f"- Chapter: {chapter_title}.\n"
        f"- Authoritative source: `apps/core-studying/Radioisotope Safety Document 2026/{source_file}`.\n"
        f"- Output: {question_count} manually authored, source-grounded questions.\n"
        "- Images: none by design.\n"
        "- Default answers: empty. Progress is saved locally by the quiz app.\n"
        f"- Question-bank version: {BANK_VERSION}. The versioned save key prevents answers from the superseded generated bank from being mapped to different questions.\n\n"
        "The bank emphasizes application, commonly confused distinctions, regulatory thresholds, and operational decisions. "
        "Distractors are authored as plausible alternatives rather than produced by mechanical word or number substitution. "
        "Re-run `python scripts/generate_risc_quizzes.py` after editing `scripts/risc_curated_bank.py`.\n"
    )


def series_readme(manifest: list[dict]) -> str:
    rows = "\n".join(
        f"| {item['chapter']}. {item['title']} | {item['questions']} |"
        for item in manifest
    )
    total = sum(item["questions"] for item in manifest)
    return (
        "# Radioisotope Safety Document 2026 Quiz Series\n\n"
        "This series converts the eight sections of the 2026 RISC source corpus into separate interactive quizzes.\n\n"
        "| Chapter | Questions |\n"
        "| --- | ---: |\n"
        f"{rows}\n"
        f"| **Total** | **{total}** |\n\n"
        "The authoritative text files are in `apps/core-studying/Radioisotope Safety Document 2026/`. "
        "The manually authored bank is in `scripts/risc_curated_bank.py`.\n\n"
        "Source ambiguities intentionally omitted from scored items include the conflicting 5.3 mSv and 6.2 mSv "
        "annual-population totals and the internally inconsistent Chapter 4 public-dose line that pairs 50 mrem with 5 mSv.\n\n"
        "Regenerate the full series with:\n\n"
        "```powershell\n"
        "python scripts\\generate_risc_quizzes.py\n"
        "```\n\n"
        "The generator validates sequential IDs, unique choices, closed lead-ins, answer keys, and balanced A-D positions. "
        "Bank version 2 intentionally starts with empty progress because the original mechanically generated questions were replaced.\n"
    )


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for chapter_number, (chapter_title, slug) in CHAPTERS.items():
        questions = make_questions(CHAPTER_QUESTIONS[chapter_number], chapter_number)
        validate_questions(questions, chapter_number)
        folder = OUTPUT_ROOT / f"2026-06-10-risc-{slug}-quiz"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "assets").mkdir(exist_ok=True)
        title = f"RISC Chapter {chapter_number}: {chapter_title} Quiz"
        app_id = f"risc-2026-{slug}-quiz-ch{chapter_number}"
        source_file = SOURCE_FILES[chapter_number]
        if not (SOURCE_DIR / source_file).is_file():
            raise FileNotFoundError(SOURCE_DIR / source_file)
        (folder / "questions.json").write_text(
            json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (folder / "index.html").write_text(
            render_html(template, questions, title, app_id), encoding="utf-8"
        )
        (folder / "README.md").write_text(
            chapter_readme(
                chapter_number, chapter_title, source_file, len(questions)
            ),
            encoding="utf-8",
        )
        manifest.append(
            {
                "chapter": chapter_number,
                "title": chapter_title,
                "slug": slug,
                "folder": folder.name,
                "questions": len(questions),
                "source": source_file,
                "bankVersion": BANK_VERSION,
            }
        )
        distribution = Counter(question["answer"] for question in questions)
        print(f"Chapter {chapter_number}: {len(questions)} questions {dict(distribution)}")

    (OUTPUT_ROOT / "quiz-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (OUTPUT_ROOT / "README.md").write_text(
        series_readme(manifest), encoding="utf-8"
    )
    print(f"Total: {sum(item['questions'] for item in manifest)} questions")


if __name__ == "__main__":
    main()
