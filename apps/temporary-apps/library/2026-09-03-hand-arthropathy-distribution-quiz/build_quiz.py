"""Render the standalone quiz page from the authored question bank."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
bank = json.loads((ROOT / "questions.json").read_text(encoding="utf-8"))
template = (ROOT / "_template.html").read_text(encoding="utf-8")
rendered = template.replace("__QUESTIONS_JSON__", json.dumps(bank["questions"], separators=(",", ":"))).replace("__VERSION__", str(bank["version"]))
(ROOT / "index.html").write_text(rendered, encoding="utf-8")
print(f"Built index.html with {len(bank['questions'])} questions (bank v{bank['version']}).")
