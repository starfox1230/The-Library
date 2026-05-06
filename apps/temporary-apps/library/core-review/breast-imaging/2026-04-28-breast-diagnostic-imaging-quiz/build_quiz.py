from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path
from urllib.parse import unquote

from lxml import html as lxml_html

APP_DIR = Path(__file__).resolve().parent
EPUB_SOURCE = Path(r"G:/My Drive/0. Radiology/Core Review Books/Breast Imaging_ A Core Review, 2e.epub")
EPUB_DIR = APP_DIR / "epub_src" / "OEBPS"
CHAPTER_FILE = EPUB_DIR / "ch003.xhtml"
ASSET_DIR = APP_DIR / "assets"
MAX_QUESTIONS = 130

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
QUESTION_CLASSES = {"num", "num1", "num2", "Questbnum", "Questbnum1", "Questbnum2"}
FOLLOWUP_CLASSES = {"Questbtext", "Ansbtext", "Ansbtextbflush", "Ansbtextbflushbtop", "Ansbtextbflushb_bottom", "Unnblistbflushbtop", "Unnblistbflushb_bottom"}
ANSWER_TEXT_CLASSES = FOLLOWUP_CLASSES | {"Ansbref"}


def clean_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def classes(el) -> set[str]:
    return set((el.get("class") or "").split())


def text_without_colnum(el) -> str:
    clone = lxml_html.fromstring(lxml_html.tostring(el, encoding="unicode"))
    for span in clone.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " colnum ")]'):
        span.drop_tree()
    return clean_text(clone.text_content())


def element_text(el) -> str:
    rows = []
    if el.tag == "table" or el.xpath(".//table"):
        for tr in el.xpath(".//tr"):
            cells = [clean_text(td.text_content()) for td in tr.xpath("./th|./td")]
            if cells:
                rows.append(" | ".join(cells))
        if rows:
            return "\n".join(rows)
    return clean_text(el.text_content())


def image_sources(el) -> list[str]:
    return [unquote(img.get("src")) for img in el.xpath(".//img[@src]")]


def copy_image(src: str, prefix: str) -> str:
    source = (EPUB_DIR / src).resolve()
    suffix = source.suffix.lower() or ".jpg"
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", prefix).strip("_")
    dest = ASSET_DIR / f"{safe}_{source.name}"
    shutil.copy2(source, dest)
    return f"assets/{dest.name}"


def parse_option_list(ol) -> list[dict]:
    opts = []
    for i, li in enumerate(ol.xpath("./li")):
        if i >= len(LETTERS):
            break
        opts.append({"letter": LETTERS[i], "text": clean_text(li.text_content())})
    return opts


def parse_answer_from_text(text: str) -> str:
    answers = re.findall(r"Answer\s+([A-Z])\.", text)
    if answers:
        return ", ".join(answers)
    matching_answers = re.findall(r"(\d+)\s*[–-]\s*([A-Z])", text)
    if matching_answers:
        return ", ".join(f"{number}-{answer}" for number, answer in matching_answers)
    return ""


def load_chapter_root():
    if not CHAPTER_FILE.exists():
        if not EPUB_SOURCE.exists():
            raise FileNotFoundError(f"Missing EPUB source: {EPUB_SOURCE}")
        (APP_DIR / "epub_src").mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(EPUB_SOURCE) as zf:
            zf.extractall(APP_DIR / "epub_src")
    return lxml_html.fromstring(CHAPTER_FILE.read_bytes())


def parse_questions(root) -> list[dict]:
    body_nodes = root.xpath("//body//*[not(self::span)]")
    questions = []
    in_questions = False
    i = 0
    while i < len(body_nodes):
        el = body_nodes[i]
        txt = clean_text(el.text_content())
        if el.tag == "h2" and "QUESTIONS" in txt.upper():
            in_questions = True
            i += 1
            continue
        if el.tag == "h2" and "ANSWERS" in txt.upper():
            break
        cls = classes(el)
        col = el.xpath('./span[contains(concat(" ", normalize-space(@class), " "), " colnum ")]')
        if in_questions and el.tag == "p" and cls & QUESTION_CLASSES and col:
            qid = clean_text(col[0].text_content())
            stem_parts = [text_without_colnum(el)]
            images = []
            options = []
            j = i + 1
            while j < len(body_nodes):
                nxt = body_nodes[j]
                ntxt = clean_text(nxt.text_content())
                ncls = classes(nxt)
                if nxt.tag == "h2" and "ANSWERS" in ntxt.upper():
                    break
                if nxt.tag == "p" and ncls & QUESTION_CLASSES and nxt.xpath('./span[contains(concat(" ", normalize-space(@class), " "), " colnum ")]'):
                    break
                for src in image_sources(nxt):
                    asset = copy_image(src, f"q{qid}")
                    if asset not in images:
                        images.append(asset)
                if nxt.tag == "p" and ncls & FOLLOWUP_CLASSES:
                    part = element_text(nxt)
                    if part:
                        stem_parts.append(part)
                if nxt.tag == "div" and ("tableft" in ncls or nxt.xpath(".//table")):
                    part = element_text(nxt)
                    if part:
                        stem_parts.append(part)
                if nxt.tag == "ol":
                    options = parse_option_list(nxt)
                    j += 1
                    break
                j += 1
            questions.append({"number": qid, "stem": "\n\n".join(p for p in stem_parts if p), "options": options, "images": images, "explanationImages": []})
            i = j
            continue
        i += 1
    return questions


def apply_epub_fixes(questions: list[dict]) -> None:
    for q in questions:
        if str(q["number"]) == "2" and not q["options"]:
            q["options"] = [
                {"letter": "A", "text": "BI-RADS 2"},
                {"letter": "B", "text": "BI-RADS 4"},
            ]


def split_matching_questions(questions: list[dict]) -> list[dict]:
    split_questions: list[dict] = []
    for q in questions:
        matching_answer = re.fullmatch(r"\s*(\d+\s*[-–]\s*[A-Z](?:\s*,\s*\d+\s*[-–]\s*[A-Z])*)\s*", q.get("answer", ""))
        if matching_answer:
            pairs = re.findall(r"(\d+)\s*[-–]\s*([A-Z])", matching_answer.group(1))
            for part_id, answer in pairs:
                split_questions.append({
                    "number": f"{q['number']}-{part_id}",
                    "stem": f"{q['stem']}\n\nPart {part_id}: choose the matching answer choice.",
                    "options": q["options"],
                    "images": q["images"],
                    "answer": answer,
                    "explanation": f"Part {part_id}: Answer {answer}.\n\n{q.get('explanation', '')}",
                    "explanationImages": q.get("explanationImages", []),
                })
            continue

        if str(q["number"]) != "2":
            split_questions.append(q)
            continue

        explanation = q.get("explanation", "")
        reference_parts = re.split(r"\n\nReferences?:", explanation, maxsplit=1)
        answer_block = reference_parts[0]
        references = f"\n\nReferences:{reference_parts[1]}" if len(reference_parts) > 1 else ""
        matches = list(re.finditer(r"(?m)^([A-Z])\.\s+Answer\s+([A-Z])\.\s+(.+?)(?=\n\n[A-Z]\.\s+Answer\s+[A-Z]\.|$)", answer_block, re.S))
        if not matches:
            split_questions.append(q)
            continue

        for match in matches:
            part_id = match.group(1)
            answer = match.group(2)
            reason = clean_text(match.group(3))
            split_questions.append({
                "number": f"2{part_id}",
                "stem": f"{q['stem']}\n\nPart {part_id}: assign the BI-RADS assessment for image/panel {part_id}.",
                "options": [
                    {"letter": "A", "text": "BI-RADS 2"},
                    {"letter": "B", "text": "BI-RADS 4"},
                ],
                "images": q["images"],
                "answer": answer,
                "explanation": f"Part {part_id}: Answer {answer}. {reason}{references}",
                "explanationImages": q.get("explanationImages", []),
            })
    return split_questions


def propagate_sibling_images(questions: list[dict]) -> None:
    by_prefix: dict[str, list[str]] = {}
    for q in questions:
        number = str(q["number"])
        match = re.fullmatch(r"(\d+)[a-z]", number)
        if match and q.get("images"):
            by_prefix.setdefault(match.group(1), [])
            for image in q["images"]:
                if image not in by_prefix[match.group(1)]:
                    by_prefix[match.group(1)].append(image)
    for q in questions:
        number = str(q["number"])
        match = re.fullmatch(r"(\d+)[a-z]", number)
        if match and not q.get("images") and match.group(1) in by_prefix:
            q["images"] = list(by_prefix[match.group(1)])


def parse_answers(root, questions: list[dict]) -> None:
    by_id = {str(q["number"]): q for q in questions}
    body_nodes = root.xpath("//body//*[not(self::span)]")
    in_answers = False
    i = 0
    while i < len(body_nodes):
        el = body_nodes[i]
        txt = clean_text(el.text_content())
        if el.tag == "h2" and "ANSWERS" in txt.upper():
            in_answers = True
            i += 1
            continue
        cls = classes(el)
        col = el.xpath('./span[contains(concat(" ", normalize-space(@class), " "), " colnum ")]')
        if in_answers and el.tag == "p" and cls & QUESTION_CLASSES and col:
            qid = clean_text(col[0].text_content())
            if qid not in by_id and qid.endswith("c") and f"{qid[:-1]}b" in by_id:
                # Chapter 3 has a source typo: question 100b's explanation is
                # labeled 100c in the EPUB answer section.
                qid = f"{qid[:-1]}b"
            q = by_id.get(qid)
            explanation_parts = [text_without_colnum(el)]
            answer = parse_answer_from_text(txt)
            explanation_images = []
            j = i + 1
            while j < len(body_nodes):
                nxt = body_nodes[j]
                ncls = classes(nxt)
                if nxt.tag == "p" and ncls & QUESTION_CLASSES and nxt.xpath('./span[contains(concat(" ", normalize-space(@class), " "), " colnum ")]'):
                    break
                for src in image_sources(nxt):
                    asset = copy_image(src, f"a{qid}")
                    if asset not in explanation_images:
                        explanation_images.append(asset)
                if nxt.tag == "p" and (ncls & ANSWER_TEXT_CLASSES or clean_text(nxt.text_content())):
                    part = element_text(nxt)
                    if part:
                        explanation_parts.append(part)
                        if not answer:
                            answer = parse_answer_from_text(part)
                if nxt.tag == "div" and ("tableft" in ncls or nxt.xpath(".//table")):
                    part = element_text(nxt)
                    if part:
                        explanation_parts.append(part)
                j += 1
            if q is not None:
                q["answer"] = answer
                q["explanation"] = "\n\n".join(p for p in explanation_parts if p)
                q["explanationImages"] = explanation_images
            i = j
            continue
        i += 1

def render_html(questions: list[dict]) -> str:
    data = json.dumps(questions, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Breast Diagnostic Imaging Quiz</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0f1218;
      --ink: #eef2f7;
      --muted: #9ca7b8;
      --panel: #171c25;
      --panel-2: #10151e;
      --line: #2e3747;
      --accent: #38bdf8;
      --accent-2: #0ea5e9;
      --good: #5ee0a0;
      --bad: #ff8a8a;
      --warn: #f4c76b;
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
      background: #111721;
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
    main.nav-closed {{ grid-template-columns: 1fr; }}
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
    .nav-head {{
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: center;
      margin-bottom: 10px;
    }}
    .nav-title {{ font-weight: 800; }}
    main.nav-closed nav {{ display: none; }}
    button {{
      border: 1px solid var(--line);
      background: #111721;
      color: var(--ink);
      border-radius: 6px;
      min-height: 38px;
      padding: 8px 10px;
      font-weight: 650;
      cursor: pointer;
    }}
    button:hover {{ border-color: var(--accent); }}
    button.primary {{ background: var(--accent); color: #06111a; border-color: var(--accent); }}
    button.primary:hover {{ background: var(--accent-2); }}
    button.icon {{ min-width: 42px; }}
    button:disabled {{ opacity: 0.48; cursor: not-allowed; }}
    button.current {{ outline: 2px solid var(--accent); }}
    button.correct {{ background: #123326; border-color: #2f8e62; color: var(--good); }}
    button.wrong {{ background: #3a171b; border-color: #9b3f48; color: var(--bad); }}
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
    .mode-switch {{
      display: inline-flex;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: var(--panel-2);
    }}
    .mode-switch button {{
      border: 0;
      border-radius: 0;
      min-height: 38px;
      background: transparent;
    }}
    .mode-switch button.active {{
      background: var(--accent);
      color: #06111a;
    }}
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
      cursor: zoom-in;
    }}
    .explanation-images {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 10px;
      margin: 0 0 12px;
    }}
    .explanation-images img {{
      width: 100%;
      background: #111;
      border: 1px solid var(--line);
      border-radius: 6px;
      object-fit: contain;
      cursor: zoom-in;
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
      background: #243044;
      font-weight: 800;
    }}
    .actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }}
    .notice {{
      color: var(--muted);
      font-size: 0.9rem;
      margin-top: 10px;
      min-height: 1.2em;
    }}
    .result {{
      border-top: 1px solid var(--line);
      margin-top: 18px;
      padding-top: 16px;
      display: none;
    }}
    .result.show {{ display: block; }}
    .review-panel {{
      border-top: 1px solid var(--line);
      margin-top: 18px;
      padding-top: 16px;
      display: none;
    }}
    .review-panel.show {{ display: block; }}
    .review-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(44px, 1fr)); gap: 6px; margin-top: 12px; }}
    .review-meta {{
      color: var(--muted);
      font-size: 0.92rem;
      margin-bottom: 8px;
    }}
    .status {{ font-weight: 800; margin-bottom: 10px; }}
    .status.good {{ color: var(--good); }}
    .status.bad {{ color: var(--bad); }}
    .feedback-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }}
    .feedback-head .status {{ margin-bottom: 0; }}
    .feedback-tools {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .explanation {{
      white-space: pre-wrap;
      line-height: 1.48;
      color: var(--ink);
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      max-height: 360px;
      overflow: auto;
    }}
    dialog {{
      width: min(720px, 94vw);
      color: var(--ink);
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0;
    }}
    dialog::backdrop {{ background: rgba(0, 0, 0, 0.68); }}
    .lightbox {{
      position: fixed;
      inset: 0;
      z-index: 20;
      display: none;
      place-items: center;
      background: rgba(0, 0, 0, 0.94);
      cursor: zoom-out;
      padding: 0;
    }}
    .lightbox.show {{ display: grid; }}
    .lightbox img {{
      width: 100vw;
      height: 100vh;
      object-fit: contain;
      display: block;
    }}
    .settings-body {{ padding: 16px; display: grid; gap: 12px; }}
    .settings-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      border-bottom: 1px solid var(--line);
      padding: 12px 16px;
    }}
    .settings-head h2 {{ margin: 0; font-size: 1.1rem; letter-spacing: 0; }}
    .settings-row {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .settings-field label {{
      display: block;
      color: var(--muted);
      font-size: 0.9rem;
      margin-bottom: 6px;
    }}
    .settings-field textarea {{
      position: static;
      left: auto;
      top: auto;
      width: 100%;
      min-height: 150px;
      resize: vertical;
      color: var(--ink);
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      font: 0.9rem ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
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
        <h1>Breast Diagnostic Imaging Quiz</h1>
      </div>
      <div class="counter" id="score">0 answered</div>
    </div>
  </header>
  <main>
    <nav aria-label="Question list">
      <div class="nav-head">
        <div class="nav-title">Questions</div>
        <button type="button" id="hideNav">Hide</button>
      </div>
      <div class="nav-grid" id="navGrid"></div>
    </nav>
    <section class="question-panel" aria-live="polite">
      <div class="topline">
        <div>
          <div class="counter" id="questionCounter"></div>
          <button type="button" id="showNav">Show Questions</button>
        </div>
        <div class="tools">
          <div class="mode-switch" aria-label="Study mode">
            <button type="button" id="tutorMode" class="active">Tutor</button>
            <button type="button" id="quizMode">Quiz</button>
          </div>
          <button type="button" id="settingsButton">Settings</button>
        </div>
      </div>
      <div id="imageGrid" class="images"></div>
      <div id="stem" class="stem"></div>
      <div id="choices" class="choices"></div>
      <div class="actions">
        <button type="button" class="primary" id="submit">Submit Answer</button>
        <button type="button" id="prev">Previous</button>
        <button type="button" id="next">Next</button>
        <button type="button" id="reviewQuiz">Review Quiz</button>
      </div>
      <div class="result" id="result">
        <div class="feedback-head">
          <div class="status" id="status"></div>
          <div class="feedback-tools">
            <button type="button" id="copyQuestionText">Copy Question Text</button>
            <button type="button" id="copyScreenshot">Copy Screenshot</button>
          </div>
        </div>
        <div id="explanationImageGrid" class="explanation-images"></div>
        <div class="explanation" id="explanation"></div>
      </div>
      <div class="review-panel" id="reviewPanel">
        <div class="status" id="reviewStatus"></div>
        <div class="review-meta">Select a question below to review its answer explanation above.</div>
        <div class="review-grid" id="reviewGrid"></div>
      </div>
      <div class="notice" id="notice"></div>
    </section>
  </main>
  <div class="lightbox" id="lightbox" role="presentation">
    <img id="lightboxImage" alt="" />
  </div>
  <dialog id="settingsDialog">
    <div class="settings-head">
      <h2>Settings</h2>
      <button type="button" id="closeSettings">Close</button>
    </div>
    <div class="settings-body">
      <div class="settings-row">
        <button type="button" id="copyState">Copy Saved State JSON</button>
        <button type="button" id="downloadState">Download Saved State</button>
        <button type="button" id="resetState">Reset Test</button>
      </div>
      <div class="settings-field">
        <label for="stateImport">Paste saved state JSON from another computer</label>
        <textarea id="stateImport" placeholder='{{"version":1,"appId":"breast-imaging-regulatory-quiz-ch1",...}}'></textarea>
      </div>
      <div class="settings-row">
        <button type="button" class="primary" id="importState">Load Pasted State</button>
      </div>
    </div>
  </dialog>
  <textarea id="clipboardScratch"></textarea>
  <script>
    const QUESTIONS = {data};
    const APP_ID = "breast-diagnostic-imaging-quiz-ch3";
    const STORAGE_KEY = "temporary-app-state:" + APP_ID;
    const DEFAULT_SELECTED = {{}};
    const DEFAULT_SUBMITTED = Object.fromEntries(Object.keys(DEFAULT_SELECTED).map(number => [number, true]));
    const DEFAULT_STATE = {{ index: 0, selected: DEFAULT_SELECTED, submitted: DEFAULT_SUBMITTED, mode: "tutor", reviewOpen: false, navOpen: true }};
    const state = loadState();
    const el = (id) => document.getElementById(id);

    function loadState() {{
      try {{
        const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
        if (!saved || saved.appId !== APP_ID) return {{ ...DEFAULT_STATE }};
        return {{
          ...DEFAULT_STATE,
          index: Number.isInteger(saved.index) ? Math.min(Math.max(saved.index, 0), QUESTIONS.length - 1) : 0,
          selected: saved.selected && typeof saved.selected === "object" ? saved.selected : {{}},
          submitted: saved.submitted && typeof saved.submitted === "object" ? saved.submitted : {{}},
          mode: saved.mode === "quiz" ? "quiz" : "tutor",
          reviewOpen: !!saved.reviewOpen,
          navOpen: saved.navOpen !== false,
        }};
      }} catch {{
        return {{ ...DEFAULT_STATE }};
      }}
    }}

    function statePayload() {{
      return {{
        version: 1,
        appId: APP_ID,
        savedAt: new Date().toISOString(),
        index: state.index,
        selected: state.selected,
        submitted: state.submitted,
        mode: state.mode,
        reviewOpen: state.reviewOpen,
        navOpen: state.navOpen,
      }};
    }}

    function saveState() {{
      localStorage.setItem(STORAGE_KEY, JSON.stringify(statePayload()));
    }}

    function applyImportedState(payload) {{
      if (!payload || payload.appId !== APP_ID) throw new Error("This saved state is for a different quiz.");
      state.index = Number.isInteger(payload.index) ? Math.min(Math.max(payload.index, 0), QUESTIONS.length - 1) : 0;
      state.selected = payload.selected && typeof payload.selected === "object" ? payload.selected : {{}};
      state.submitted = payload.submitted && typeof payload.submitted === "object" ? payload.submitted : {{}};
      state.mode = payload.mode === "quiz" ? "quiz" : "tutor";
      state.reviewOpen = !!payload.reviewOpen;
      state.navOpen = payload.navOpen !== false;
      saveState();
    }}

    function flash(message) {{
      el("notice").textContent = message;
      window.clearTimeout(flash.timer);
      flash.timer = window.setTimeout(() => {{ el("notice").textContent = ""; }}, 2600);
    }}

    function questionText(q) {{
      const opts = q.options.map(o => `${{o.letter}}. ${{o.text}}`).join("\\n");
      return `Question ${{q.number}}\\n${{q.stem}}\\n\\n${{opts}}`;
    }}

    function fullQuestionText(q) {{
      const chosen = state.selected[q.number] || "not selected";
      const result = state.submitted[q.number] ? (chosen === q.answer ? "correct" : "incorrect") : "not yet submitted";
      const questionImages = q.images.length ? `\\n\\nQuestion image files:\\n${{q.images.join("\\n")}}` : "";
      const explanationImages = (q.explanationImages || []).length ? `\\n\\nExplanation image files:\\n${{q.explanationImages.join("\\n")}}` : "";
      return `${{questionText(q)}}${{questionImages}}\\n\\nSelected answer: ${{chosen}}\\nCorrect answer: ${{q.answer}}\\nAttempt: ${{result}}\\n\\nSource explanation:\\n${{q.explanation}}${{explanationImages}}`;
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
      flash("Copied.");
    }}

    function escapeHtml(value) {{
      return String(value).replace(/[&<>"']/g, char => ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }}[char]));
    }}

    function wrapCanvasText(ctx, text, x, y, maxWidth, lineHeight) {{
      const paragraphs = String(text).split("\\n");
      paragraphs.forEach(paragraph => {{
        const words = paragraph.split(/\\s+/).filter(Boolean);
        let line = "";
        if (!words.length) {{
          y += lineHeight;
          return;
        }}
        words.forEach(word => {{
          const test = line ? `${{line}} ${{word}}` : word;
          if (ctx.measureText(test).width > maxWidth && line) {{
            ctx.fillText(line, x, y);
            line = word;
            y += lineHeight;
          }} else {{
            line = test;
          }}
        }});
        if (line) {{
          ctx.fillText(line, x, y);
          y += lineHeight;
        }}
        y += Math.round(lineHeight * 0.45);
      }});
      return y;
    }}

    function textCardDataUrl(title, body) {{
      const width = 900;
      const padding = 46;
      const lineHeight = 34;
      const measure = document.createElement("canvas").getContext("2d");
      measure.font = "24px Arial";
      const estimateLines = Math.max(8, Math.ceil(String(body).length / 52) + String(body).split("\\n").length * 2);
      const height = Math.min(2600, Math.max(900, 170 + estimateLines * lineHeight));
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#0f1218";
      ctx.fillRect(0, 0, width, height);
      ctx.fillStyle = "#17202d";
      ctx.fillRect(18, 18, width - 36, height - 36);
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 4;
      ctx.strokeRect(18, 18, width - 36, height - 36);
      ctx.fillStyle = "#eef2f7";
      ctx.font = "700 34px Arial";
      ctx.fillText(title, padding, 76);
      ctx.fillStyle = "#dbe5f2";
      ctx.font = "24px Arial";
      wrapCanvasText(ctx, body, padding, 130, width - padding * 2, lineHeight);
      return canvas.toDataURL("image/png");
    }}

    async function imageToDataUrl(src) {{
      return new Promise((resolve) => {{
        const img = new Image();
        img.onload = () => {{
          try {{
            const canvas = document.createElement("canvas");
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            canvas.getContext("2d").drawImage(img, 0, 0);
            resolve(canvas.toDataURL("image/png"));
          }} catch {{
            resolve(src);
          }}
        }};
        img.onerror = () => resolve(src);
        img.src = src;
      }});
    }}

    async function copyScreenshotPack(q) {{
      const chosen = state.selected[q.number] || "not selected";
      const options = q.options.map(o => `${{o.letter}}. ${{o.text}}`).join("\\n");
      const questionCard = textCardDataUrl(`Question ${{q.number}}`, `${{q.stem}}\\n\\n${{options}}`);
      const explanationCard = textCardDataUrl(`Answer ${{q.answer}}`, `Selected: ${{chosen}}\\nCorrect: ${{q.answer}}\\n\\n${{q.explanation}}`);
      const questionImages = await Promise.all(q.images.map(src => imageToDataUrl(src)));
      const explanationImages = await Promise.all((q.explanationImages || []).map(src => imageToDataUrl(src)));
      const imageTags = [...questionImages, questionCard, ...explanationImages, explanationCard]
        .map(src => `<p><img src="${{src}}" style="max-width:900px;width:100%;height:auto;display:block;"></p>`)
        .join("");
      const html = `<div>${{imageTags}}</div>`;
      try {{
        await navigator.clipboard.write([
          new ClipboardItem({{
            "text/html": new Blob([html], {{ type: "text/html" }}),
            "text/plain": new Blob([fullQuestionText(q)], {{ type: "text/plain" }}),
          }})
        ]);
        flash("Copied screenshot pack.");
      }} catch {{
        await copy(fullQuestionText(q));
        flash("Rich screenshot copy was blocked; copied full text instead.");
      }}
    }}

    function renderNav() {{
      const nav = el("navGrid");
      nav.innerHTML = "";
      QUESTIONS.forEach((q, i) => {{
        const b = document.createElement("button");
        b.textContent = q.number;
        b.className = i === state.index ? "current" : "";
        if (state.submitted[q.number]) {{
          if (state.mode === "tutor" || state.reviewOpen) b.classList.add(state.selected[q.number] === q.answer ? "correct" : "wrong");
        }}
        b.addEventListener("click", () => {{ state.index = i; render(); }});
        nav.appendChild(b);
      }});
    }}

    function render() {{
      const q = QUESTIONS[state.index];
      const reveal = state.mode === "tutor" || state.reviewOpen;
      document.querySelector("main").classList.toggle("nav-closed", !state.navOpen);
      el("showNav").style.display = state.navOpen ? "none" : "inline-block";
      el("questionCounter").textContent = `Question ${{q.number}} of ${{QUESTIONS.length}}`;
      el("stem").textContent = q.stem;
      el("imageGrid").innerHTML = q.images.map(src => `<img src="${{src}}" alt="Question ${{q.number}} image" />`).join("");
      el("imageGrid").querySelectorAll("img").forEach(img => {{
        img.addEventListener("click", () => openLightbox(img.src, img.alt));
      }});
      const choices = el("choices");
      choices.innerHTML = "";
      q.options.forEach(option => {{
        const b = document.createElement("button");
        b.type = "button";
        b.className = "choice";
        if (state.selected[q.number] === option.letter) b.classList.add("current");
        if (state.submitted[q.number] && reveal) {{
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
      el("result").classList.toggle("show", !!submitted && reveal);
      if (submitted && reveal) {{
        const ok = state.selected[q.number] === q.answer;
        el("status").className = `status ${{ok ? "good" : "bad"}}`;
        el("status").textContent = ok ? `Correct: ${{q.answer}}` : `Incorrect. You chose ${{state.selected[q.number] || "nothing"}}; correct answer: ${{q.answer}}`;
        el("explanationImageGrid").innerHTML = (q.explanationImages || []).map(src => `<img src="${{src}}" alt="Question ${{q.number}} explanation image" />`).join("");
        el("explanationImageGrid").querySelectorAll("img").forEach(img => {{
          img.addEventListener("click", () => openLightbox(img.src, img.alt));
        }});
        el("explanation").textContent = q.explanation;
      }}
      const answered = Object.keys(state.submitted).length;
      const right = QUESTIONS.filter(x => state.submitted[x.number] && state.selected[x.number] === x.answer).length;
      el("score").textContent = state.mode === "quiz" && !state.reviewOpen ? `${{answered}} of ${{QUESTIONS.length}} answered` : `${{answered}} answered | ${{right}} correct`;
      el("submit").textContent = state.submitted[q.number] ? "Answer Saved" : "Submit Answer";
      el("reviewQuiz").style.display = state.mode === "quiz" ? "inline-block" : "none";
      el("reviewQuiz").disabled = answered !== QUESTIONS.length;
      el("reviewQuiz").textContent = answered === QUESTIONS.length ? "Review Quiz" : `Review unlocks at ${{QUESTIONS.length}}`;
      el("copyScreenshot").style.display = state.mode === "tutor" || state.reviewOpen ? "inline-block" : "none";
      el("tutorMode").classList.toggle("active", state.mode === "tutor");
      el("quizMode").classList.toggle("active", state.mode === "quiz");
      renderNav();
      renderReview();
      saveState();
    }}

    function renderReview() {{
      const answered = Object.keys(state.submitted).length;
      const complete = answered === QUESTIONS.length;
      el("reviewPanel").classList.toggle("show", state.mode === "quiz" && state.reviewOpen);
      if (!(state.mode === "quiz" && state.reviewOpen)) return;
      const right = QUESTIONS.filter(q => state.submitted[q.number] && state.selected[q.number] === q.answer).length;
      el("reviewStatus").textContent = complete ? `Quiz complete: ${{right}} / ${{QUESTIONS.length}} correct` : `Reviewing ${{answered}} of ${{QUESTIONS.length}} answered questions: ${{right}} correct so far`;
      const grid = el("reviewGrid");
      grid.innerHTML = "";
      QUESTIONS.forEach((q, i) => {{
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = q.number;
        if (i === state.index) b.classList.add("current");
        if (state.submitted[q.number]) b.classList.add(state.selected[q.number] === q.answer ? "correct" : "wrong");
        b.addEventListener("click", () => {{
          state.index = i;
          render();
          window.scrollTo({{ top: 0, behavior: "smooth" }});
        }});
        grid.appendChild(b);
      }});
    }}

    function openLightbox(src, alt) {{
      el("lightboxImage").src = src;
      el("lightboxImage").alt = alt || "Expanded quiz image";
      el("lightbox").classList.add("show");
    }}

    function closeLightbox() {{
      el("lightbox").classList.remove("show");
      el("lightboxImage").removeAttribute("src");
    }}

    el("submit").addEventListener("click", () => {{
      const q = QUESTIONS[state.index];
      if (!state.selected[q.number]) return;
      state.submitted[q.number] = true;
      if (state.mode === "quiz" && state.index < QUESTIONS.length - 1) state.index += 1;
      render();
    }});
    el("prev").addEventListener("click", () => {{ state.index = Math.max(0, state.index - 1); render(); }});
    el("next").addEventListener("click", () => {{ state.index = Math.min(QUESTIONS.length - 1, state.index + 1); render(); }});
    el("tutorMode").addEventListener("click", () => {{ state.mode = "tutor"; state.reviewOpen = false; render(); }});
    el("quizMode").addEventListener("click", () => {{ state.mode = "quiz"; state.reviewOpen = false; render(); }});
    el("reviewQuiz").addEventListener("click", () => {{
      if (Object.keys(state.submitted).length !== QUESTIONS.length) return;
      state.reviewOpen = true;
      render();
    }});
    el("hideNav").addEventListener("click", () => {{ state.navOpen = false; render(); }});
    el("showNav").addEventListener("click", () => {{ state.navOpen = true; render(); }});
    el("settingsButton").addEventListener("click", () => {{
      el("stateImport").value = JSON.stringify(statePayload(), null, 2);
      el("settingsDialog").showModal();
    }});
    el("closeSettings").addEventListener("click", () => el("settingsDialog").close());
    el("copyState").addEventListener("click", () => copy(JSON.stringify(statePayload(), null, 2)));
    el("downloadState").addEventListener("click", () => {{
      const blob = new Blob([JSON.stringify(statePayload(), null, 2)], {{ type: "application/json" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${{APP_ID}}-state.json`;
      a.click();
      URL.revokeObjectURL(url);
      flash("Downloaded saved state.");
    }});
    el("resetState").addEventListener("click", () => {{
      if (!confirm("Reset all answers and saved progress for this quiz?")) return;
      Object.assign(state, {{ ...DEFAULT_STATE, selected: {{}}, submitted: {{}} }});
      localStorage.removeItem(STORAGE_KEY);
      el("settingsDialog").close();
      render();
      flash("Test reset.");
    }});
    el("importState").addEventListener("click", () => {{
      try {{
        applyImportedState(JSON.parse(el("stateImport").value));
        el("settingsDialog").close();
        render();
        flash("Saved state loaded.");
      }} catch (error) {{
        flash(error.message || "Could not load saved state JSON.");
      }}
    }});
    el("lightbox").addEventListener("click", closeLightbox);
    el("copyQuestionText").addEventListener("click", () => copy(fullQuestionText(QUESTIONS[state.index])));
    el("copyScreenshot").addEventListener("click", () => copyScreenshotPack(QUESTIONS[state.index]));
    render();
  </script>
</body>
</html>
"""


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for old in ASSET_DIR.glob("*"):
        old.unlink()
    root = load_chapter_root()
    questions = parse_questions(root)
    apply_epub_fixes(questions)
    parse_answers(root, questions)
    questions = split_matching_questions(questions)
    propagate_sibling_images(questions)
    for q in questions:
        q.setdefault("answer", "")
        q.setdefault("explanation", "No extracted explanation found.")
        q.setdefault("explanationImages", [])
    (APP_DIR / "questions.json").write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")
    (APP_DIR / "index.html").write_text(render_html(questions), encoding="utf-8")
    print(f"wrote {len(questions)} questions, {sum(len(q['images']) for q in questions)} images")
    missing = [q["number"] for q in questions if not q["answer"]]
    if missing:
        print("missing answers:", missing)


if __name__ == "__main__":
    main()

