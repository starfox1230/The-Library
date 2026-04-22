from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "apps" / "quiz-generator" / "standalone-quiz-template.html"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "standalone-quiz"


def validate_quiz_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Quiz JSON must be an object.")

    title = payload.get("title")
    questions = payload.get("questions")

    if not isinstance(title, str) or not title.strip():
        raise ValueError('Quiz JSON must include a non-empty "title" string.')
    if not isinstance(questions, list) or not questions:
        raise ValueError('Quiz JSON must include a non-empty "questions" array.')

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise ValueError(f"Question {index} must be an object.")
        if not isinstance(question.get("question"), str) or not question["question"].strip():
            raise ValueError(f'Question {index} is missing a valid "question" string.')
        if not isinstance(question.get("options"), list) or len(question["options"]) < 2:
            raise ValueError(f'Question {index} must have an "options" array with at least two entries.')
        if not isinstance(question.get("correctAnswer"), str) or question["correctAnswer"] not in question["options"]:
            raise ValueError(f'Question {index} must have a "correctAnswer" that exactly matches one option.')
        if "explanation" in question and not isinstance(question["explanation"], str):
            raise ValueError(f'Question {index} has a non-string "explanation".')


def build_page(quiz_payload: dict) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    quiz_title = quiz_payload["title"].strip()
    page_title = f"{quiz_title} Quiz"
    quiz_json = json.dumps(quiz_payload, indent=8, ensure_ascii=False)

    return (
        template
        .replace("__QUIZ_PAGE_TITLE__", page_title)
        .replace("__QUIZ_TITLE__", quiz_title)
        .replace("__QUIZ_DATA__", quiz_json)
    )


def main(argv: list[str]) -> int:
    if len(argv) not in {2, 3}:
        print(
            "Usage: python scripts/build_standalone_quiz_page.py <quiz.json> [output.html]",
            file=sys.stderr,
        )
        return 1

    input_path = Path(argv[1]).resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    with input_path.open("r", encoding="utf-8") as handle:
        quiz_payload = json.load(handle)

    validate_quiz_payload(quiz_payload)

    if len(argv) == 3:
        output_path = Path(argv[2]).resolve()
    else:
        output_name = f"{slugify(quiz_payload['title'])}.html"
        output_path = ROOT / "apps" / "quiz-generator" / output_name

    output_path.write_text(build_page(quiz_payload), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
