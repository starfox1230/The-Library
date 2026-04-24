from __future__ import annotations

import html
import json
import re
from pathlib import Path

import fitz
from pypdf import PdfReader


APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[3]
SOURCE_PDF_PATH = Path("G:/My Drive/0. Radiology/Core Review Pediatric Imaging.pdf")
WORKSPACE_PDF_PATH = REPO_ROOT / "apps" / "temporary-apps" / "Core Review Pediatric Imaging.pdf"
PDF_PATH = SOURCE_PDF_PATH if SOURCE_PDF_PATH.exists() else WORKSPACE_PDF_PATH
ASSET_DIR = APP_DIR / "assets"

QUESTION_START_PAGE = 8
QUESTION_END_PAGE = 56
ANSWER_START_PAGE = 56
ANSWER_END_PAGE = 90


def clean_text(text: str) -> str:
    text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
    text = re.sub(r"-\s+", "-", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([.?!])([A-Z0-9])", r"\1 \2", text)
    text = re.sub(r"([a-z,;:])(\d+\s+Answer)", r"\1 \2", text)
    return text.strip()


def strip_page_noise(text: str) -> str:
    text = re.sub(r"^1 Pediatric Gastrointestinal Tract Questions\s*", "", text)
    text = re.sub(r"\s+Answers and Explanations\s*", " ", text)
    text = re.sub(r"\s+\d{1,3}\s*$", "", text)
    return clean_text(text)


def page_text(reader: PdfReader, start: int, end: int) -> str:
    parts = []
    for idx in range(start, end):
        parts.append(strip_page_noise(reader.pages[idx].extract_text() or ""))
    return clean_text(" ".join(parts))


def split_questions(text: str) -> list[dict]:
    raw_matches = list(re.finditer(r"(?<!Question )\b(\d{1,2})\.\s+", text))
    matches = []
    expected = 1
    for match in raw_matches:
        if int(match.group(1)) == expected:
            matches.append(match)
            expected += 1
    questions = []
    for i, match in enumerate(matches):
        number = int(match.group(1))
        if not 1 <= number <= 46:
            continue
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        option_matches = list(re.finditer(r"\b([A-D])\.\s*", body))
        if not option_matches:
            continue
        stem = body[: option_matches[0].start()].strip()
        options = []
        for j, opt in enumerate(option_matches[:4]):
            opt_start = opt.end()
            opt_end = option_matches[j + 1].start() if j + 1 < len(option_matches[:4]) else len(body)
            options.append({"letter": opt.group(1), "text": body[opt_start:opt_end].strip()})
        questions.append({"number": number, "stem": stem, "options": options, "images": []})
    return questions


def split_answers(text: str) -> dict[int, dict]:
    matches = list(re.finditer(r"(?:^|\s)(\d{1,2})\s+Answer\s+([A-D])\.", text))
    answers: dict[int, dict] = {}
    for i, match in enumerate(matches):
        number = int(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        explanation = text[start:end].strip()
        explanation = re.sub(r"\s+References?:\s+", "\n\nReferences: ", explanation)
        answers[number] = {"answer": match.group(2), "explanation": explanation}
    return answers


def extract_images(questions: list[dict]) -> None:
    by_number = {q["number"]: q for q in questions}
    current_question = 1
    q_start_re = re.compile(r"^\s*(\d{1,2})\.\s+")
    doc = fitz.open(str(PDF_PATH))
    try:
        for page_index in range(QUESTION_START_PAGE, QUESTION_END_PAGE):
            blocks = sorted(doc[page_index].get_text("dict")["blocks"], key=lambda b: (b["bbox"][1], b["bbox"][0]))
            image_index = 0
            for block in blocks:
                if block["type"] == 0:
                    text = " ".join("".join(span["text"] for span in line["spans"]) for line in block["lines"])
                    starts = [int(m.group(1)) for m in q_start_re.finditer(text) if 1 <= int(m.group(1)) <= 46]
                    if starts:
                        current_question = starts[-1]
                elif block["type"] == 1:
                    image_index += 1
                    ext = block.get("ext", "jpg")
                    filename = f"q{current_question:02d}_p{page_index + 1:03d}_{image_index}.{ext}"
                    (ASSET_DIR / filename).write_bytes(block["image"])
                    if current_question in by_number:
                        by_number[current_question]["images"].append(f"assets/{filename}")
    finally:
        doc.close()


def render_html(questions: list[dict]) -> str:
    data = json.dumps(questions, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Pediatric GI Imaging Quiz</title>
  <style>
    :root {{
      --bg: #f7f8fb;
      --ink: #17202f;
      --muted: #5b6472;
      --panel: #ffffff;
      --line: #d9dee8;
      --accent: #146c94;
      --accent-2: #0f4d68;
      --good: #197a4d;
      --bad: #aa2f2f;
      --warn: #805b10;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: #ffffff;
      position: sticky;
      top: 0;
      z-index: 2;
    }}
    .bar {{
      width: min(1180px, 94vw);
      margin: 0 auto;
      padding: 14px 0;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 16px;
      align-items: center;
    }}
    h1 {{ font-size: 1.15rem; margin: 0 0 3px; letter-spacing: 0; }}
    .sub {{ color: var(--muted); font-size: 0.9rem; }}
    main {{
      width: min(1180px, 94vw);
      margin: 20px auto 36px;
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 18px;
    }}
    nav, .question-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    nav {{
      padding: 12px;
      align-self: start;
      position: sticky;
      top: 78px;
      max-height: calc(100vh - 96px);
      overflow: auto;
    }}
    .nav-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; }}
    button {{
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      min-height: 38px;
      padding: 8px 10px;
      font-weight: 650;
      cursor: pointer;
    }}
    button:hover {{ border-color: var(--accent); }}
    button.primary {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
    button.primary:hover {{ background: var(--accent-2); }}
    button.icon {{ min-width: 42px; }}
    button.current {{ outline: 2px solid var(--accent); }}
    button.correct {{ background: #e5f5ec; border-color: #97d3b3; color: var(--good); }}
    button.wrong {{ background: #fae8e8; border-color: #e0a1a1; color: var(--bad); }}
    .question-panel {{ padding: 18px; }}
    .topline {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }}
    .counter {{ color: var(--muted); font-size: 0.92rem; }}
    .tools {{ display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }}
    .stem {{
      font-size: 1.12rem;
      line-height: 1.48;
      margin: 8px 0 16px;
    }}
    .images {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 10px;
      margin: 8px 0 18px;
    }}
    .images img {{
      width: 100%;
      background: #111;
      border: 1px solid var(--line);
      border-radius: 6px;
      object-fit: contain;
    }}
    .choices {{ display: grid; gap: 8px; margin: 14px 0; }}
    .choice {{
      width: 100%;
      text-align: left;
      display: grid;
      grid-template-columns: 32px 1fr;
      gap: 10px;
      align-items: start;
      font-weight: 500;
      line-height: 1.35;
      min-height: 48px;
    }}
    .choice .letter {{
      display: inline-grid;
      place-items: center;
      width: 26px;
      height: 26px;
      border-radius: 50%;
      background: #eef2f7;
      font-weight: 800;
    }}
    .actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }}
    .result {{
      border-top: 1px solid var(--line);
      margin-top: 18px;
      padding-top: 16px;
      display: none;
    }}
    .result.show {{ display: block; }}
    .status {{ font-weight: 800; margin-bottom: 10px; }}
    .status.good {{ color: var(--good); }}
    .status.bad {{ color: var(--bad); }}
    .explanation {{
      white-space: pre-wrap;
      line-height: 1.48;
      color: #202938;
      background: #f9fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      max-height: 360px;
      overflow: auto;
    }}
    textarea {{
      position: fixed;
      left: -9999px;
      top: -9999px;
    }}
    @media (max-width: 780px) {{
      .bar {{ grid-template-columns: 1fr; }}
      main {{ grid-template-columns: 1fr; }}
      nav {{ position: static; max-height: none; }}
      .nav-grid {{ grid-template-columns: repeat(8, 1fr); }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="bar">
      <div>
        <h1>Pediatric Gastrointestinal Tract Quiz</h1>
        <div class="sub">Core Review Pediatric Imaging, chapter 1. Choose an answer, submit, then copy a chatbot-ready explanation prompt.</div>
      </div>
      <div class="counter" id="score">0 answered</div>
    </div>
  </header>
  <main>
    <nav aria-label="Question list">
      <div class="nav-grid" id="navGrid"></div>
    </nav>
    <section class="question-panel" aria-live="polite">
      <div class="topline">
        <div class="counter" id="questionCounter"></div>
        <div class="tools">
          <button type="button" id="copyQuestion">Copy Question</button>
          <button type="button" id="copyPrompt">Copy Chatbot Prompt</button>
        </div>
      </div>
      <div id="imageGrid" class="images"></div>
      <div id="stem" class="stem"></div>
      <div id="choices" class="choices"></div>
      <div class="actions">
        <button type="button" class="primary" id="submit">Submit Answer</button>
        <button type="button" id="prev">Previous</button>
        <button type="button" id="next">Next</button>
      </div>
      <div class="result" id="result">
        <div class="status" id="status"></div>
        <div class="explanation" id="explanation"></div>
      </div>
    </section>
  </main>
  <textarea id="clipboardScratch"></textarea>
  <script>
    const QUESTIONS = {data};
    const state = {{ index: 0, selected: {{}}, submitted: {{}} }};
    const el = (id) => document.getElementById(id);

    function questionText(q) {{
      const opts = q.options.map(o => `${{o.letter}}. ${{o.text}}`).join("\\n");
      return `Question ${{q.number}}\\n${{q.stem}}\\n\\n${{opts}}`;
    }}

    function promptText(q) {{
      const chosen = state.selected[q.number] || "not selected";
      const result = state.submitted[q.number] ? (chosen === q.answer ? "correct" : "incorrect") : "not yet submitted";
      return `You are tutoring pediatric radiology. Explain this multiple-choice question in detail. The user chose ${{chosen}} and the correct answer is ${{q.answer}}; the attempt was ${{result}}. Explain why the correct answer is right, why each wrong answer is wrong, and emphasize the selected wrong answer if one was missed.\\n\\n${{questionText(q)}}\\n\\nPDF explanation:\\n${{q.explanation}}`;
    }}

    async function copy(text) {{
      try {{
        await navigator.clipboard.writeText(text);
      }} catch {{
        const scratch = el("clipboardScratch");
        scratch.value = text;
        scratch.select();
        document.execCommand("copy");
      }}
    }}

    function renderNav() {{
      const nav = el("navGrid");
      nav.innerHTML = "";
      QUESTIONS.forEach((q, i) => {{
        const b = document.createElement("button");
        b.textContent = q.number;
        b.className = i === state.index ? "current" : "";
        if (state.submitted[q.number]) b.classList.add(state.selected[q.number] === q.answer ? "correct" : "wrong");
        b.addEventListener("click", () => {{ state.index = i; render(); }});
        nav.appendChild(b);
      }});
    }}

    function render() {{
      const q = QUESTIONS[state.index];
      el("questionCounter").textContent = `Question ${{q.number}} of ${{QUESTIONS.length}}`;
      el("stem").textContent = q.stem;
      el("imageGrid").innerHTML = q.images.map(src => `<img src="${{src}}" alt="Question ${{q.number}} image" />`).join("");
      const choices = el("choices");
      choices.innerHTML = "";
      q.options.forEach(option => {{
        const b = document.createElement("button");
        b.type = "button";
        b.className = "choice";
        if (state.selected[q.number] === option.letter) b.classList.add("current");
        if (state.submitted[q.number]) {{
          if (option.letter === q.answer) b.classList.add("correct");
          if (option.letter === state.selected[q.number] && option.letter !== q.answer) b.classList.add("wrong");
        }}
        const letter = document.createElement("span");
        letter.className = "letter";
        letter.textContent = option.letter;
        const label = document.createElement("span");
        label.textContent = option.text;
        b.append(letter, label);
        b.addEventListener("click", () => {{
          if (!state.submitted[q.number]) state.selected[q.number] = option.letter;
          render();
        }});
        choices.appendChild(b);
      }});
      const submitted = state.submitted[q.number];
      el("result").classList.toggle("show", !!submitted);
      if (submitted) {{
        const ok = state.selected[q.number] === q.answer;
        el("status").className = `status ${{ok ? "good" : "bad"}}`;
        el("status").textContent = ok ? `Correct: ${{q.answer}}` : `Incorrect. You chose ${{state.selected[q.number] || "nothing"}}; correct answer: ${{q.answer}}`;
        el("explanation").textContent = q.explanation;
      }}
      const answered = Object.keys(state.submitted).length;
      const right = QUESTIONS.filter(x => state.submitted[x.number] && state.selected[x.number] === x.answer).length;
      el("score").textContent = `${{answered}} answered | ${{right}} correct`;
      renderNav();
    }}

    el("submit").addEventListener("click", () => {{
      const q = QUESTIONS[state.index];
      if (!state.selected[q.number]) return;
      state.submitted[q.number] = true;
      render();
    }});
    el("prev").addEventListener("click", () => {{ state.index = Math.max(0, state.index - 1); render(); }});
    el("next").addEventListener("click", () => {{ state.index = Math.min(QUESTIONS.length - 1, state.index + 1); render(); }});
    el("copyQuestion").addEventListener("click", () => copy(questionText(QUESTIONS[state.index])));
    el("copyPrompt").addEventListener("click", () => copy(promptText(QUESTIONS[state.index])));
    render();
  </script>
</body>
</html>
"""


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for old in ASSET_DIR.glob("*"):
        old.unlink()
    reader = PdfReader(str(PDF_PATH))
    questions = split_questions(page_text(reader, QUESTION_START_PAGE, QUESTION_END_PAGE))
    answers = split_answers(page_text(reader, ANSWER_START_PAGE, ANSWER_END_PAGE))
    extract_images(questions)
    for q in questions:
        answer = answers.get(q["number"], {})
        q["answer"] = answer.get("answer", "")
        q["explanation"] = answer.get("explanation", "No extracted explanation found.")
    (APP_DIR / "questions.json").write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")
    (APP_DIR / "index.html").write_text(render_html(questions), encoding="utf-8")
    print(f"wrote {len(questions)} questions, {sum(len(q['images']) for q in questions)} images")
    missing = [q["number"] for q in questions if not q["answer"]]
    if missing:
        print("missing answers:", missing)


if __name__ == "__main__":
    main()
