from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEWS_ROOT = ROOT / "apps" / "anki-card-creation-codex-helper" / "boardvitals"
OUTPUT = ROOT / "apps" / "boardvitals-reviews" / "reviews.js"


def count_from_report(text: str, label: str) -> int | None:
    match = re.search(rf"^{re.escape(label)}:\s*(\d+)", text, re.MULTILINE)
    return int(match.group(1)) if match else None


def missed_from_report(text: str) -> list[int]:
    match = re.search(r"^Missed questions:\s*(.+?)\.?\s*$", text, re.MULTILINE)
    return [int(value) for value in re.findall(r"Q(\d+)", match.group(1))] if match else []


def collect_reviews() -> list[dict[str, object]]:
    reviews: list[dict[str, object]] = []
    for folder in REVIEWS_ROOT.glob("*-quiz-*"):
        match = re.match(r"(\d{4}-\d{2}-\d{2})-quiz-(\d+)$", folder.name)
        if not match:
            continue
        review_html = next(folder.glob("quiz-*-review.html"), None)
        if not review_html:
            continue
        review_date, quiz_id = match.groups()
        report_path = folder / "run-report.md"
        report = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
        reviews.append(
            {
                "quizId": quiz_id,
                "date": review_date,
                "href": f"../anki-card-creation-codex-helper/boardvitals/{folder.name}/{review_html.name}",
                "questions": count_from_report(report, "Questions") or 50,
                "missed": missed_from_report(report),
                "stemImages": count_from_report(report, "Stem images"),
                "explanationImages": count_from_report(report, "Explanation images"),
                "hasDeck": (folder / f"boardvitals-quiz-{quiz_id}.apkg").exists(),
            }
        )
    return sorted(reviews, key=lambda item: (str(item["date"]), str(item["quizId"])), reverse=True)


def main() -> None:
    payload = {"generatedOn": date.today().isoformat(), "reviews": collect_reviews()}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("window.BOARDVITALS_REVIEWS = " + json.dumps(payload, indent=2) + ";\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(payload['reviews'])} reviews)")


if __name__ == "__main__":
    main()
