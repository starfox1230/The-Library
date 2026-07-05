import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path

from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "apps" / "core-studying" / "nuclear-medicine-command-center"
WORK = ROOT / ".tmp-nuclear-medicine-command-center"

CORE_BASE = ROOT / "apps" / "core-studying" / "Core_Radiology"
CORE_INDEX = CORE_BASE / "index.json"
REQ_BASE = ROOT / "apps" / "core-studying" / "Nuclear Medicine - The Requisites"
REQ_INDEX = REQ_BASE / "index.json"
CORE_PDF = Path(r"C:\Users\sterl\OneDrive\Desktop\Core Radiology Chapters\06 - Nuclear and Molecular Imaging.pdf")
BOARDVITALS_OUT = ROOT / "apps" / "anki-card-creation-codex-helper" / "boardvitals"
BOARDVITALS_PARSED = Path(r"C:\Users\sterl\Documents\Codex\2026-05-12\https-www-boardvitals-com-dashboard-quizzes")
CORE_REVIEW = ROOT / "apps" / "core-studying" / "Core Review"


def clean_text(s: str) -> str:
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


def load_requisites_outline() -> list[dict]:
    index = json.loads(REQ_INDEX.read_text(encoding="utf-8"))
    chapters = []
    for ck, ch in index.items():
        items = []
        for sk, sec in ch.items():
            if sk == "title":
                continue
            if isinstance(sec, dict) and "title" in sec:
                items.append({"code": sk, "title": clean_text(sec["title"])})
        chapters.append({"code": ck, "title": clean_text(ch.get("title", ck)), "sections": items})
    return chapters


def count_quizzes() -> dict:
    apkgs = sorted(BOARDVITALS_OUT.glob("**/*.apkg")) if BOARDVITALS_OUT.exists() else []
    parsed_dirs = sorted(p for p in BOARDVITALS_PARSED.glob("boardvitals-*") if p.is_dir()) if BOARDVITALS_PARSED.exists() else []
    q_counts = {}
    for d in parsed_dirs:
        q_files = list(d.glob("q*.json")) + list(d.glob("question-*.json"))
        nums = set()
        for f in q_files:
            m = re.search(r"(\d+)", f.stem)
            if m:
                nums.add(int(m.group(1)))
        q_counts[d.name.replace("boardvitals-", "")] = len(nums)
    core_review_files = list(CORE_REVIEW.rglob("*")) if CORE_REVIEW.exists() else []
    return {
        "boardvitals_apkg_count": len(apkgs),
        "boardvitals_parsed_quiz_count": len(parsed_dirs),
        "boardvitals_parsed_question_total": sum(q_counts.values()),
        "boardvitals_more_from_scrape": max(0, len(parsed_dirs) - len(apkgs)),
        "core_review_file_count": sum(1 for p in core_review_files if p.is_file()),
        "apkg_names": [p.stem for p in apkgs],
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
        blocks.append(f"""
          <details>
            <summary><span>{escape(ch['code'])}</span>{escape(ch['title'])}<b>{len(ch['sections'])}</b></summary>
            <ol>
              {''.join(f'<li><span>{escape(item["code"])}</span>{escape(item["title"])}</li>' for item in ch['sections'])}
            </ol>
          </details>""")
    return "".join(blocks)


def make_html(core_sections: list[dict], req_outline: list[dict], quiz: dict, pdf: dict) -> Path:
    html_path = OUTPUTS / "index.html"
    total_words = sum(s["wordCount"] for s in core_sections)
    req_sections = sum(len(ch["sections"]) for ch in req_outline)
    pass_html = render_passes(core_sections)
    req_html = render_requisites(req_outline)
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
    html {{ background: var(--bg); }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.45;
      padding: max(14px, env(safe-area-inset-top)) max(12px, env(safe-area-inset-right)) max(28px, env(safe-area-inset-bottom)) max(12px, env(safe-area-inset-left));
    }}
    a {{ color: inherit; text-decoration: none; }}
    .page {{ width: min(1120px, 100%); margin: 0 auto; display: grid; gap: 14px; }}
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
    p {{ margin: 0; color: var(--muted); }}
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
    .note {{ border-left: 3px solid var(--warn); padding: 10px 12px; background: rgba(210,153,34,.08); color: var(--text); border-radius: 6px; }}
    details {{ padding: 0; overflow: hidden; }}
    summary {{ list-style: none; cursor: pointer; padding: 11px 12px; display: grid; grid-template-columns: 52px 1fr auto; gap: 8px; align-items: center; }}
    summary::-webkit-details-marker {{ display: none; }}
    details[open] summary {{ border-bottom: 1px solid var(--border); }}
    details ol {{ padding: 0 14px 12px 24px; }}
    details li {{ color: var(--muted); }}
    .search {{ width: 100%; padding: 10px 12px; border-radius: 6px; border: 1px solid var(--border); background: #0d1117; color: var(--text); font: inherit; margin-bottom: 10px; }}
    .footer {{ color: var(--muted); font-size: .82rem; padding: 4px 2px 16px; }}
    @media (max-width: 820px) {{
      .layout {{ grid-template-columns: 1fr; }}
      nav.panel {{ position: static; grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .top-grid, .quiz-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .heading-list {{ columns: 1; }}
    }}
    @media (max-width: 520px) {{
      body {{ padding-left: 10px; padding-right: 10px; }}
      header {{ padding: 14px; }}
      .top-grid, .quiz-grid, nav.panel {{ grid-template-columns: 1fr; }}
      .metric {{ min-height: auto; }}
      summary {{ grid-template-columns: 46px 1fr auto; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <header>
      <div>
        <div class="kicker">Study week command center</div>
        <h1>Nuclear Medicine</h1>
        <p>Three passes through Core Radiology Chapter 06, with the deeper Nuclear Medicine Requisites outline parked underneath for review-textbook coverage.</p>
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
        <a class="button good" href="#requisites">Deep reference outline</a>
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
          <h2>Quiz Inventory</h2>
          <div class="quiz-grid">
            <div class="metric"><strong>{quiz["boardvitals_apkg_count"]}</strong><span>BoardVitals quiz APKGs made</span></div>
            <div class="metric"><strong>{quiz["boardvitals_parsed_quiz_count"]}</strong><span>Parsed quiz folders found</span></div>
            <div class="metric"><strong>{quiz["boardvitals_more_from_scrape"]}</strong><span>More possible from the already-scraped quiz set</span></div>
          </div>
          <p class="note">The local <code>Core Review</code> folder currently has {quiz["core_review_file_count"]} files, so I could not verify a separate Core Review textbook corpus from that folder. The concrete quiz count above is from the BoardVitals review-question corpus and matching generated APKGs.</p>
          <p>The parsed BoardVitals folders contain about {quiz["boardvitals_parsed_question_total"]} question records total. If you use the Requisites section outline as a future source map, there are {req_sections} section-sized units that could theoretically become new focused quizzes.</p>
        </section>

        <section class="panel" id="requisites">
          <h2>Nuclear Medicine Requisites Outline</h2>
          <p>Use this as the deeper review-textbook map after the Core Radiology passes.</p>
          {req_html}
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
