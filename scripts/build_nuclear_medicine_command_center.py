import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import quote

from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "apps" / "core-studying" / "nuclear-medicine-command-center"
WORK = ROOT / ".tmp-nuclear-medicine-command-center"

CORE_BASE = ROOT / "apps" / "core-studying" / "Core_Radiology"
CORE_INDEX = CORE_BASE / "index.json"
REQ_BASE = ROOT / "apps" / "core-studying" / "Nuclear Medicine - The Requisites"
REQ_INDEX = REQ_BASE / "index.json"
CORE_PDF = Path(r"C:\Users\sterl\OneDrive\Desktop\Core Radiology Chapters\06 - Nuclear and Molecular Imaging.pdf")
CORE_REVIEW_NUKES = ROOT / "apps" / "temporary-apps" / "library" / "core-review" / "nuclear-medicine"


def bad_encoding_score(s: str) -> int:
    return (
        s.count("\ufffd") * 4
        + s.count("\u00c3") * 2
        + s.count("\u00c2") * 2
        + s.count("\u00e2") * 2
        + s.count("ï¿½") * 4
    )


def repair_mojibake(s: str) -> str:
    best = s
    for encoding in ("cp1252", "latin1"):
        try:
            candidate = s.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
        if bad_encoding_score(candidate) < bad_encoding_score(best):
            best = candidate
    return best


def clean_text(s: str) -> str:
    s = repair_mojibake(s)
    s = re.sub(r"(?m)^�\s+", "• ", s)
    replacements = {
        "â€“": "-",
        "â€”": "-",
        "â€œ": '"',
        "â€": '"',
        "â€™": "'",
        "â€˜": "'",
        "â€¢": "•",
        "Î²": "beta",
        "Î»": "lambda",
        "â„": "/",
        "Â": "",
        "�": "-",
        "fi ": "fi ",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def line_is_heading(line: str) -> bool:
    t = line.strip()
    if not t or t.startswith("•") or t.startswith("- "):
        return False
    if t in {"A", "-A"}:
        return False
    if not re.search(r"[A-Za-z0-9]", t):
        return False
    if len(t) > 92:
        return False
    if t.endswith((".", ",", ";", ":")) and not re.search(r"\bscan\b|\bimaging\b|\bPET\b|\bCT\b|\btherapy\b", t, re.I):
        return False
    if re.match(r"^(Fig\.|FIG\.|Box |Table |\d+\.)", t):
        return False
    words = t.split()
    if len(words) <= 9:
        return True
    capish = sum(1 for w in words if w[:1].isupper() or re.search(r"[A-Z0-9]", w))
    return capish / max(1, len(words)) > 0.55


def split_bullets(text: str) -> list[str]:
    text = clean_text(text)
    bullets = []
    current = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if current:
                bullets.append(" ".join(current))
                current = []
            continue
        if line.startswith("•"):
            if current:
                bullets.append(" ".join(current))
            current = [line.lstrip("• ").strip()]
        elif current:
            current.append(line)
        elif re.match(r"^(Q:|A:|Pearl\b)", line):
            bullets.append(line)
        elif re.search(r"\b(half-life|mCi|keV|SUV|FDG|Tc-99m|I-123|I-131|Ga-68|F-18|sensitivity|specificity|contraindicat|false-positive|normal|abnormal|uptake|scan|therapy|radiotracer)\b", line, re.I):
            if len(line) > 25 and len(line) < 240:
                bullets.append(line)
    if current:
        bullets.append(" ".join(current))
    cleaned = []
    seen = set()
    for b in bullets:
        b = re.sub(r"\s+", " ", b).strip()
        if len(b) < 18 or b.lower() in seen:
            continue
        if b.startswith("Lung cancer initial staging:") and len(b) > 260:
            b = b[:240].rsplit(" ", 1)[0] + "."
        seen.add(b.lower())
        cleaned.append(b)
    return cleaned


def extract_section(path: Path, code: str, title: str) -> dict:
    text = clean_text(path.read_text(encoding="utf-8", errors="replace"))
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    headings = []
    for ln in lines[1:]:
        if line_is_heading(ln) and ln not in headings and ln != title:
            headings.append(ln)
        if len(headings) >= 18:
            break
    bullets = split_bullets(text)
    return {
        "code": code,
        "title": clean_text(title).replace("_", "/"),
        "file": str(path),
        "headings": headings,
        "keyBullets": bullets[:5],
        "facts": bullets[:18],
        "wordCount": len(re.findall(r"\w+", text)),
    }


def load_core_sections() -> list[dict]:
    index = json.loads(CORE_INDEX.read_text(encoding="utf-8"))
    chapter = index["Chapter06"]
    sections = []
    for code, meta in chapter.items():
        if code == "title":
            continue
        sections.append(extract_section(CORE_BASE / meta["file"], code, meta["title"]))
    return sections


NOISE_PREFIXES = (
    "fig.",
    "figure",
    "table",
    "box",
    "chapter",
    "references",
    "bibliography",
)

FACT_TERMS = (
    "radiopharmaceutical",
    "radiotracer",
    "tracer",
    "uptake",
    "scan",
    "imaging",
    "scintigraphy",
    "spect",
    "pet",
    "ct",
    "mri",
    "fdg",
    "tc-99m",
    "i-123",
    "i-131",
    "f-18",
    "ga-68",
    "lu-177",
    "dose",
    "half-life",
    "kev",
    "suv",
    "sensitivity",
    "specificity",
    "false",
    "normal",
    "abnormal",
    "indication",
    "contraindication",
    "diagnosis",
    "therapy",
    "treatment",
    "metast",
    "tumor",
    "patient",
    "protocol",
    "delayed",
    "dynamic",
    "quantitative",
    "clearance",
    "perfusion",
    "ventilation",
    "renal",
    "thyroid",
    "bone",
    "cardiac",
)


def is_noise_line(line: str) -> bool:
    t = line.strip()
    low = t.lower()
    if not t:
        return False
    if any(low.startswith(prefix) for prefix in NOISE_PREFIXES):
        return True
    if re.match(r"^[A-Z]\)$", t):
        return True
    if re.match(r"^\d+$", t):
        return True
    if len(t) < 4 and not re.search(r"\d", t):
        return True
    return False


def looks_like_paragraph_start(line: str) -> bool:
    t = line.strip()
    if len(t) < 42:
        return False
    return bool(re.search(
        r"^(A|An|The|In|With|For|On|Patients|Patient|More|Most|Many|Some|Because|Although|When|If|After|Before|During|Overall)\b",
        t,
    ))


def is_requisites_heading(line: str, title: str) -> bool:
    t = line.strip()
    if not t or t.lower() == title.lower():
        return True
    if len(t) > 100 or re.search(r"[.;]$", t):
        return False
    if ":" in t and len(t.split()) > 4:
        return False
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9-]*", t)
    if not words:
        return True
    capish = sum(1 for word in words if word[:1].isupper() or re.search(r"[A-Z0-9]", word))
    return len(words) <= 10 and capish / len(words) > 0.62


def normalize_fact(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"\([^)]*(?:Fig\.|Figs\.|Table|Box)[^)]*\)", "", text, flags=re.I)
    text = re.sub(r"\b(?:Fig\.|Table|Box)\s+\d+(?:\.\d+)?[A-Z]?\b", "", text, flags=re.I)
    text = re.sub(r"\b\(?(?:Figs?\.|Tables?|Boxes?)\s*[^).]*(?:\)|\.)?", "", text, flags=re.I)
    text = re.sub(r"\b\d+\.\d+\s+(?:and|to)\s+\d+\.\d+\)?", "", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\(see\s*,?\s*[A-Z]?\)", "", text, flags=re.I)
    text = re.sub(r";\s*\)\.?", ".", text)
    text = re.sub(r"\(\s*;?\s*\)", "", text)
    text = re.sub(r";\s*\.", ".", text)
    text = re.sub(r"\s+", " ", text).strip(" -;:,")
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"\.\s+\.", ".", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"([a-z0-9])\s+(However|Although|Because|Therefore)\b", r"\1. \2", text)
    text = re.sub(r",\s+and\b", " and", text)
    text = re.sub(r"\bnon-small ?cell\b", "non-small-cell", text, flags=re.I)
    text = re.sub(r"\bF-18 fluorodeoxyglucose\b", "F-18 FDG", text, flags=re.I)
    text = re.sub(r"\btechnetium-99m\b", "Tc-99m", text, flags=re.I)
    if text and text[-1] not in ".!?":
        text += "."
    return text


def requisites_paragraphs(text: str, title: str) -> list[str]:
    lines = []
    skip_mode = None
    for raw in clean_text(text).splitlines():
        line = raw.strip()
        low = line.lower()

        if low.startswith(("fig.", "figure")):
            skip_mode = "caption"
            continue
        if low.startswith(("table", "box")):
            skip_mode = "table"
            continue

        if skip_mode == "caption":
            if re.search(r"[.!?]$", line):
                skip_mode = None
            continue
        if skip_mode == "table":
            if looks_like_paragraph_start(line):
                skip_mode = None
            else:
                continue

        if is_noise_line(line):
            line = ""
        if is_requisites_heading(line, title):
            line = ""
        lines.append(line)

    paragraphs = []
    current = []
    for line in lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return [normalize_fact(p) for p in paragraphs if len(normalize_fact(p)) >= 35]


def split_sentences(paragraph: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", paragraph)
    sentences = []
    for piece in pieces:
        sentence = normalize_fact(piece)
        if 45 <= len(sentence) <= 320:
            sentences.append(sentence)
    return sentences


def sentence_score(sentence: str, title_words: set[str], position: int) -> float:
    low = sentence.lower()
    score = max(0, 8 - position * 0.15)
    score += sum(1.8 for term in FACT_TERMS if term in low)
    score += min(5, len(re.findall(r"\b\d+(?:\.\d+)?%?|\b(?:mci|mbq|kev|hours?|minutes?|days?)\b", low)))
    score += sum(0.5 for word in title_words if len(word) > 4 and word in low)
    if re.search(r"\b(common|most|primary|preferred|classic|characteristic|sensitive|specific|normal|abnormal|pitfall|false-positive|false-negative)\b", low):
        score += 3
    if re.search(r"\b(shown|demonstrates|image|images|views|coronal|axial|sagittal|slice)\b", low):
        score -= 4
    if len(sentence) > 260:
        score -= 2
    return score


def shorten_fact(sentence: str) -> str:
    sentence = normalize_fact(sentence)
    if len(sentence) <= 235:
        return sentence
    cut_points = [
        sentence.find("; "),
        sentence.find(". ", 160),
        sentence.find(", although "),
        sentence.find(", but "),
    ]
    cut_points = [p for p in cut_points if 110 <= p <= 235]
    if cut_points:
        sentence = sentence[: min(cut_points)].rstrip(" ,;") + "."
    elif len(sentence) > 255:
        sentence = sentence[:252].rsplit(" ", 1)[0].rstrip(" ,;") + "."
    return sentence


def extract_requisites_facts(path: Path, title: str, max_facts: int = 10) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    title_words = set(re.findall(r"[a-z0-9]+", title.lower()))
    candidates = []
    for p_index, paragraph in enumerate(requisites_paragraphs(text, title)):
        for sentence in split_sentences(paragraph):
            if not re.match(r"^[A-Z0-9]", sentence):
                continue
            if re.search(r"\(\s*\)|\bsee\s*,", sentence, re.I):
                continue
            score = sentence_score(sentence, title_words, p_index)
            if score >= 7:
                candidates.append((score, p_index, sentence))

    candidates.sort(key=lambda item: (-item[0], item[1]))
    facts = []
    seen = set()
    for _, _, sentence in candidates:
        fact = shorten_fact(sentence)
        if not re.match(r"^[A-Z0-9]", fact):
            continue
        if re.search(r"\(\s*\)|\bsee\s*,", fact, re.I):
            continue
        key = re.sub(r"[^a-z0-9]+", " ", fact.lower()).strip()
        if not key or any(key in old or old in key for old in seen):
            continue
        facts.append(fact)
        seen.add(key)
        if len(facts) >= max_facts:
            break

    if len(facts) < 4:
        for paragraph in requisites_paragraphs(text, title)[:8]:
            fact = shorten_fact(paragraph)
            key = re.sub(r"[^a-z0-9]+", " ", fact.lower()).strip()
            if key and not any(key in old or old in key for old in seen):
                facts.append(fact)
                seen.add(key)
            if len(facts) >= 4:
                break
    return facts


def load_requisites_outline() -> list[dict]:
    index = json.loads(REQ_INDEX.read_text(encoding="utf-8"))
    chapters = []
    for ck, ch in index.items():
        items = []
        for sk, sec in ch.items():
            if sk == "title":
                continue
            if isinstance(sec, dict) and "title" in sec:
                path = REQ_BASE / sec.get("file", "")
                items.append({
                    "code": sk,
                    "title": clean_text(sec["title"]),
                    "file": sec.get("file", ""),
                    "facts": extract_requisites_facts(path, sec["title"]),
                })
        chapters.append({"code": ck, "title": clean_text(ch.get("title", ck)), "sections": items})
    return chapters


def count_quizzes() -> dict:
    title_overrides = {
        "2026-05-03-nuclear-medicine-endocrine-quiz": "Chapter 2: Endocrine System",
        "2026-05-03-nuclear-medicine-msk-quiz": "Chapter 3: Musculoskeletal System",
        "2026-05-05-nuclear-medicine-head-neck-quiz": "Chapter 4: Head and Neck",
        "2026-05-05-nuclear-medicine-cardiology-quiz": "Chapter 5: Nuclear Cardiology",
        "2026-05-05-nuclear-medicine-vascular-lymphatics-quiz": "Chapter 6: Vascular and Lymphatics",
        "2026-05-05-nuclear-medicine-pulmonary-quiz": "Chapter 7: Pulmonary System",
        "2026-05-05-nuclear-medicine-gastrointestinal-quiz": "Chapter 8: Gastrointestinal System",
        "2026-05-05-nuclear-medicine-genitourinary-quiz": "Chapter 9: Genitourinary System",
        "2026-05-05-nuclear-medicine-pediatric-quiz": "Chapter 10: Pediatric Nuclear Medicine",
        "2026-05-06-nuclear-medicine-oncology-quiz": "Chapter 11: Oncology",
    }
    quizzes = []
    for d in sorted(CORE_REVIEW_NUKES.glob("*-quiz")) if CORE_REVIEW_NUKES.exists() else []:
        questions_file = d / "questions.json"
        if not questions_file.exists() or not (d / "index.html").exists():
            continue
        questions = json.loads(questions_file.read_text(encoding="utf-8"))
        title = title_overrides.get(d.name, re.sub(r"^\d{4}-\d{2}-\d{2}-", "", d.name).replace("-", " ").title())
        quizzes.append({
            "slug": d.name,
            "title": title,
            "questionCount": len(questions),
            "href": f"../../temporary-apps/library/core-review/nuclear-medicine/{quote(d.name)}/index.html",
        })
    quizzes.sort(key=lambda q: int(re.search(r"Chapter (\d+)", q["title"]).group(1)) if re.search(r"Chapter (\d+)", q["title"]) else 999)
    return {
        "quiz_count": len(quizzes),
        "question_total": sum(q["questionCount"] for q in quizzes),
        "theoretical_more_from_existing_group": max(0, 10 - len(quizzes)),
        "library_href": "../../temporary-apps/library/core-review/index.html",
        "quizzes": quizzes,
    }


def make_pdf() -> dict:
    output_pdf = OUTPUTS / "core-radiology-nuclear-molecular-imaging-spliced.pdf"
    reader = PdfReader(str(CORE_PDF))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata({
        "/Title": "Core Radiology - Nuclear and Molecular Imaging Study Splice",
        "/Subject": "Nuclear medicine study chapter extracted for weekly review",
    })
    # The source file is already the chapter-level splice. Add section bookmarks for fast PDF navigation.
    # The first page in this chapter PDF is printed page Nucs: 444.
    section_starts = [
        ("PET/CT", 445),
        ("Cerebrovascular", 452),
        ("Thyroid", 457),
        ("Parathyroid", 461),
        ("Gastrointestinal", 462),
        ("Pulmonary", 468),
        ("Musculoskeletal", 471),
        ("Kidneys", 477),
        ("Whole-Body Imaging", 481),
        ("Other Non-PET Imaging", 485),
    ]
    page_count = len(reader.pages)
    for title, printed_page in section_starts:
        page_num = min(page_count - 1, max(0, printed_page - 444))
        writer.add_outline_item(title, page_num)
    with output_pdf.open("wb") as f:
        writer.write(f)
    return {"path": str(output_pdf), "pages": len(reader.pages), "source": str(CORE_PDF)}


def render_passes(sections: list[dict]) -> str:
    broad = []
    key = []
    facts = []
    for sec in sections:
        sid = f"s-{sec['code'].replace('.', '-')}"
        broad.append(f"""
          <article class="section-card" id="{sid}-broad">
            <div class="section-top"><span>{escape(sec['code'])}</span><h3>{escape(sec['title'])}</h3></div>
            <ol class="heading-list">
              {''.join(f'<li>{escape(h)}</li>' for h in sec['headings'][:12])}
            </ol>
          </article>""")
        key.append(f"""
          <article class="section-card" id="{sid}-key">
            <div class="section-top"><span>{escape(sec['code'])}</span><h3>{escape(sec['title'])}</h3></div>
            <ul>
              {''.join(f'<li>{escape(b)}</li>' for b in sec['keyBullets'])}
            </ul>
          </article>""")
        facts.append(f"""
          <article class="section-card" id="{sid}-facts">
            <div class="section-top"><span>{escape(sec['code'])}</span><h3>{escape(sec['title'])}</h3></div>
            <ul class="fact-list">
              {''.join(f'<li>{escape(b)}</li>' for b in sec['facts'])}
            </ul>
          </article>""")
    return f"""
      <section class="pass active" data-pass="broad">{''.join(broad)}</section>
      <section class="pass" data-pass="key">{''.join(key)}</section>
      <section class="pass" data-pass="facts">{''.join(facts)}</section>
    """


def render_requisites(chapters: list[dict]) -> str:
    blocks = []
    for ch in chapters:
        chapter_number = str(int(re.search(r"\d+", ch["code"]).group(0))) if re.search(r"\d+", ch["code"]) else ch["code"]
        sections = []
        for item in ch["sections"]:
            fact_count = len(item["facts"])
            facts = "".join(f"<li>{escape(fact)}</li>" for fact in item["facts"])
            sections.append(f"""
              <details class="req-section">
                <summary>
                  <span class="req-code">{escape(item["code"])}</span>
                  <span class="req-title">{escape(item["title"])}</span>
                  <span class="req-count">{fact_count} facts</span>
                </summary>
                <ul class="req-facts">{facts}</ul>
              </details>""")
        blocks.append(f"""
          <article class="req-chapter">
            <div class="req-chapter-head">
              <span class="chapter-badge">Chapter {escape(chapter_number)}</span>
              <h3>{escape(ch["title"])}</h3>
              <span class="section-total">{len(ch["sections"])} sections</span>
            </div>
            <div class="req-section-list">{''.join(sections)}</div>
          </article>""")
    return "".join(blocks)


def render_quiz_links(quiz: dict) -> str:
    return "".join(
        f"""
          <a class="quiz-card" href="{escape(item['href'])}">
            <span>{escape(item['title'])}</span>
            <b>{item['questionCount']} questions</b>
          </a>"""
        for item in quiz["quizzes"]
    )


def make_html(core_sections: list[dict], req_outline: list[dict], quiz: dict, pdf: dict) -> Path:
    html_path = OUTPUTS / "index.html"
    total_words = sum(s["wordCount"] for s in core_sections)
    req_sections = sum(len(ch["sections"]) for ch in req_outline)
    pass_html = render_passes(core_sections)
    req_html = render_requisites(req_outline)
    quiz_links = render_quiz_links(quiz)
    pdf_name = Path(pdf["path"]).name
    source_pdf = escape(pdf["source"])
    generated = date.today().isoformat()
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>Nuclear Medicine Command Center</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0d1117;
      --panel: #161b22;
      --card: #1f2630;
      --border: #30363d;
      --text: #d6dee8;
      --muted: #8b949e;
      --accent: #58a6ff;
      --accent2: #45d49b;
      --warn: #d29922;
      --danger: #f85149;
      --radius: 8px;
    }}
    * {{ box-sizing: border-box; }}
    header, .panel, .section-card, .metric, .quiz-card, .req-chapter, .req-section, .button, button {{ min-width: 0; }}
    html {{ background: var(--bg); overflow-x: hidden; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.45;
      padding: max(14px, env(safe-area-inset-top)) max(12px, env(safe-area-inset-right)) max(28px, env(safe-area-inset-bottom)) max(12px, env(safe-area-inset-left));
      width: 100vw;
      overflow-x: hidden;
    }}
    a {{ color: inherit; text-decoration: none; }}
    code {{ overflow-wrap: anywhere; word-break: break-word; }}
    .page {{ width: min(1120px, calc(100vw - 40px)); max-width: 100%; margin: 0 auto; display: grid; gap: 14px; overflow-x: hidden; }}
    header, .panel, .section-card, details {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
    }}
    header {{ padding: 18px; display: grid; gap: 14px; }}
    .kicker {{ color: var(--accent); text-transform: uppercase; letter-spacing: .12em; font-weight: 800; font-size: .72rem; }}
    h1 {{ margin: 0; font-size: clamp(1.65rem, 7vw, 3rem); line-height: 1.04; letter-spacing: 0; }}
    h2 {{ margin: 0 0 10px; font-size: 1.05rem; }}
    h3 {{ margin: 0; font-size: 1rem; }}
    p {{ margin: 0; color: var(--muted); overflow-wrap: anywhere; }}
    .top-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }}
    .metric {{ background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px; min-height: 86px; }}
    .metric strong {{ display: block; font-size: 1.5rem; color: var(--text); }}
    .metric span {{ color: var(--muted); font-size: .82rem; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .button, button {{
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 9px 12px;
      font: inherit;
      font-weight: 700;
      color: var(--text);
      background: #21262d;
      cursor: pointer;
      white-space: normal;
    }}
    .button.primary, button.active {{ background: var(--accent); color: #07101d; border-color: var(--accent); }}
    .button.good {{ color: #06140f; background: var(--accent2); border-color: var(--accent2); }}
    .layout {{ display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 14px; align-items: start; }}
    nav.panel {{ position: sticky; top: 12px; padding: 12px; display: grid; gap: 8px; }}
    nav a {{ display: block; padding: 8px 9px; border-radius: 6px; color: var(--muted); }}
    nav a:hover {{ background: var(--card); color: var(--text); }}
    .panel {{ padding: 14px; }}
    .pass-tabs {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }}
    .pass {{ display: none; gap: 10px; }}
    .pass.active {{ display: grid; }}
    .section-card {{ padding: 14px; background: var(--card); }}
    .section-top {{ display: flex; gap: 10px; align-items: baseline; margin-bottom: 8px; }}
    .section-top span, details summary span, details li span {{ color: var(--accent); font-weight: 800; min-width: 44px; }}
    ol, ul {{ margin: 8px 0 0 1.1rem; padding: 0; }}
    li {{ margin: 6px 0; }}
    .heading-list {{ columns: 2; column-gap: 28px; }}
    .fact-list li {{ margin-bottom: 8px; }}
    .quiz-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }}
    .quiz-links {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }}
    .quiz-card {{ display: grid; gap: 5px; padding: 11px 12px; border: 1px solid var(--border); border-radius: 6px; background: var(--card); }}
    .quiz-card span {{ color: var(--text); font-weight: 750; }}
    .quiz-card b {{ color: var(--accent); font-size: .82rem; }}
    .quiz-card:hover {{ border-color: var(--accent); }}
    .note {{ border-left: 3px solid var(--warn); padding: 10px 12px; background: rgba(210,153,34,.08); color: var(--text); border-radius: 6px; }}
    .req-atlas {{ display: grid; gap: 12px; margin-top: 12px; }}
    .req-chapter {{ background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }}
    .req-chapter-head {{
      display: grid;
      grid-template-columns: minmax(92px, auto) minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
      padding: 13px;
      border-bottom: 1px solid var(--border);
    }}
    .req-chapter-head h3 {{ min-width: 0; font-size: .98rem; line-height: 1.25; }}
    .chapter-badge {{ color: var(--accent); font-weight: 850; font-size: .82rem; white-space: nowrap; }}
    .section-total, .req-count {{ color: var(--muted); font-size: .78rem; white-space: nowrap; }}
    .req-section-list {{ display: grid; gap: 8px; padding: 10px; }}
    .req-section {{ background: #171d26; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }}
    .req-section summary {{
      display: grid;
      grid-template-columns: 52px minmax(0, 1fr) auto;
      gap: 9px;
      align-items: center;
      padding: 10px 11px;
    }}
    .req-code {{ color: var(--accent); font-weight: 850; }}
    .req-title {{ color: var(--text); font-weight: 720; min-width: 0; overflow-wrap: anywhere; }}
    .req-facts {{ margin: 0; padding: 10px 14px 12px 30px; color: var(--text); background: rgba(13,17,23,.42); }}
    .req-facts li {{ margin: 7px 0; }}
    details {{ padding: 0; overflow: hidden; }}
    summary {{ list-style: none; cursor: pointer; padding: 11px 12px; display: grid; grid-template-columns: 52px 1fr auto; gap: 8px; align-items: center; }}
    summary::-webkit-details-marker {{ display: none; }}
    details[open] summary {{ border-bottom: 1px solid var(--border); }}
    details ol {{ padding: 0 14px 12px 24px; }}
    details li {{ color: var(--muted); }}
    details li a {{ color: var(--muted); display: inline-flex; gap: 8px; align-items: baseline; }}
    details li a:hover {{ color: var(--text); }}
    .search {{ width: 100%; padding: 10px 12px; border-radius: 6px; border: 1px solid var(--border); background: #0d1117; color: var(--text); font: inherit; margin-bottom: 10px; }}
    .footer {{ color: var(--muted); font-size: .82rem; padding: 4px 2px 16px; }}
    @media (max-width: 820px) {{
      .layout {{ grid-template-columns: 1fr; }}
      nav.panel {{ position: static; grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .top-grid, .quiz-grid, .quiz-links {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .req-chapter-head {{ grid-template-columns: 1fr; gap: 4px; }}
      .heading-list {{ columns: 1; }}
    }}
    @media (max-width: 520px) {{
      body {{ padding-left: 10px; padding-right: 10px; }}
      header {{ padding: 14px; }}
      .top-grid, .quiz-grid, .quiz-links, nav.panel {{ grid-template-columns: 1fr; }}
      .actions {{ display: grid; grid-template-columns: 1fr; }}
      .metric {{ min-height: auto; }}
      summary {{ grid-template-columns: 46px 1fr auto; }}
      .req-section summary {{ grid-template-columns: 1fr; gap: 4px; }}
      .req-count {{ justify-self: start; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <header>
      <div>
        <div class="kicker">Study week command center</div>
        <h1>Nuclear Medicine</h1>
        <p>Core review, key facts, quizzes, PDF.</p>
      </div>
      <div class="top-grid">
        <div class="metric"><strong>{len(core_sections)}</strong><span>Core Radiology sections</span></div>
        <div class="metric"><strong>{pdf["pages"]}</strong><span>PDF pages in the splice</span></div>
        <div class="metric"><strong>{total_words:,}</strong><span>Approx. extracted core words</span></div>
        <div class="metric"><strong>{req_sections}</strong><span>Requisites reference sections</span></div>
      </div>
      <div class="actions">
        <a class="button primary" href="{pdf_name}">Open spliced PDF</a>
        <a class="button" href="#passes">Start three-pass review</a>
        <a class="button" href="#quizzes">Quiz inventory</a>
        <a class="button good" href="#requisites">Requisites key facts</a>
      </div>
    </header>

    <div class="layout">
      <nav class="panel" aria-label="Sections">
        {''.join(f'<a href="#s-{s["code"].replace(".", "-")}-broad">{escape(s["code"])} {escape(s["title"])}</a>' for s in core_sections)}
      </nav>
      <div class="main">
        <section class="panel" id="passes">
          <h2>Three Passes</h2>
          <div class="pass-tabs">
            <button class="active" data-target="broad">1. Broad headings</button>
            <button data-target="key">2. Key bullets</button>
            <button data-target="facts">3. Key facts</button>
          </div>
          <input class="search" id="search" placeholder="Filter sections and facts..." />
          {pass_html}
        </section>

        <section class="panel" id="quizzes">
          <h2>Core Review Nuclear Medicine Quizzes</h2>
          <div class="quiz-grid">
            <div class="metric"><strong>{quiz["quiz_count"]}</strong><span>Nuclear Medicine quiz modules made</span></div>
            <div class="metric"><strong>{quiz["question_total"]}</strong><span>Total Core Review questions linked</span></div>
            <div class="metric"><strong>{quiz["theoretical_more_from_existing_group"]}</strong><span>More obvious modules left in this existing group</span></div>
          </div>
          <p class="note">These are the organized Core Review Nuclear Medicine quiz modules under <code>apps/temporary-apps/library/core-review/nuclear-medicine</code>.</p>
          <div class="actions"><a class="button" href="{escape(quiz["library_href"])}">Open Core Review Quiz Library</a></div>
          <div class="quiz-links">{quiz_links}</div>
        </section>

        <section class="panel" id="requisites">
          <h2>Nuclear Medicine Requisites Key Facts</h2>
          <p>Use this as the deeper review-textbook map after the Core Radiology passes. Each section expands into cleaned high-yield facts instead of sending you to raw extracted textbook text.</p>
          <input class="search" id="reqSearch" placeholder="Filter Requisites chapters, sections, and facts..." />
          <div class="req-atlas">{req_html}</div>
        </section>

        <section class="panel">
          <h2>Source Notes</h2>
          <p>Generated {generated}. PDF source: <code>{source_pdf}</code>. The output PDF is a chapter-level splice because the source PDF is already the nuclear/molecular imaging chapter.</p>
        </section>
      </div>
    </div>
    <div class="footer">Tip: on your phone, use the pass buttons first, then search a radiotracer, organ system, or pitfall when drilling facts.</div>
  </main>
  <script>
    const tabs = [...document.querySelectorAll('.pass-tabs button')];
    const passes = [...document.querySelectorAll('.pass')];
    tabs.forEach(btn => btn.addEventListener('click', () => {{
      tabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      passes.forEach(p => p.classList.toggle('active', p.dataset.pass === btn.dataset.target));
    }}));
    const search = document.getElementById('search');
    search.addEventListener('input', () => {{
      const q = search.value.trim().toLowerCase();
      document.querySelectorAll('.section-card').forEach(card => {{
        card.style.display = !q || card.textContent.toLowerCase().includes(q) ? '' : 'none';
      }});
    }});
    const reqSearch = document.getElementById('reqSearch');
    reqSearch.addEventListener('input', () => {{
      const q = reqSearch.value.trim().toLowerCase();
      document.querySelectorAll('.req-section').forEach(section => {{
        const matched = !q || section.textContent.toLowerCase().includes(q);
        section.style.display = matched ? '' : 'none';
        if (q && matched) section.open = true;
      }});
      document.querySelectorAll('.req-chapter').forEach(chapter => {{
        const hasVisibleSection = [...chapter.querySelectorAll('.req-section')].some(section => section.style.display !== 'none');
        chapter.style.display = hasVisibleSection || (!q && chapter.textContent.toLowerCase().includes(q)) ? '' : 'none';
      }});
    }});
  </script>
</body>
</html>"""
    html_path.write_text(html, encoding="utf-8")
    return html_path


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    core_sections = load_core_sections()
    req_outline = load_requisites_outline()
    quiz = count_quizzes()
    pdf = make_pdf()
    html = make_html(core_sections, req_outline, quiz, pdf)
    manifest = {
        "html": str(html),
        "pdf": pdf,
        "core_sections": len(core_sections),
        "requisites_sections": sum(len(ch["sections"]) for ch in req_outline),
        "quiz": quiz,
    }
    (OUTPUTS / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
