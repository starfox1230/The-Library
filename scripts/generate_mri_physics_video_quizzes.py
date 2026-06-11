from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path

from mri_physics_video_bank import VIDEO_QUESTIONS


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "apps/core-studying/YT Physics"
SOURCE_INDEX = SOURCE_ROOT / "index.json"
OUTPUT_ROOT = ROOT / "apps/temporary-apps/library/physics-video-quizzes"
MRI_ROOT = OUTPUT_ROOT / "mri"
TEMP_APPS_INDEX = ROOT / "apps/temporary-apps/index.html"
TEMPLATE = (
    ROOT
    / "apps/temporary-apps/library/core-review/absolute-breast-imaging-review"
    / "2026-06-10-absolute-breast-pathology-quiz/_template.html"
)
DATE = "2026-06-11"
BANK_VERSION = 1
REGISTER_START = "      // PHYSICS_VIDEO_QUIZZES_START"
REGISTER_END = "      // PHYSICS_VIDEO_QUIZZES_END"

DISPLAY_TITLES = {
    "03.01": "MRI Physics Overview",
    "03.02": "MRI Machine: Main, Gradient, and RF Coils",
    "03.03": "Spin, Precession, Resonance, and Flip Angle",
    "03.04": "T2 Relaxation and Free Induction Decay",
    "03.05": "T1 Relaxation and Longitudinal Recovery",
    "03.06": "T1, T2, and Proton-Density Weighting",
    "03.07": "MRI Slice Selection",
    "03.08": "Frequency-Encoding Gradient",
    "03.09": "Phase-Encoding Gradient",
    "03.10": "K-Space",
    "03.11": "FOV, Matrix, Receiver Bandwidth, and Dwell Time",
    "03.12": "Receiver Bandwidth and SNR",
    "03.13": "Aliasing and Parallel Imaging",
    "03.14": "Chemical-Shift Artifact",
    "03.15": "Spin Echo, Multiecho, Multislice, and Fast Spin Echo",
    "03.16": "Gradient-Echo MRI",
    "03.17": "Flip Angle and Ernst Angle",
    "03.18": "Coherent, Spoiled, and SSFP Gradient Echo",
    "03.19": "Inversion Recovery, STIR, and FLAIR",
    "03.20": "Partial Saturation, Saturation Bands, and CHESS",
    "03.21": "Echo-Planar Imaging and Fast Spin Echo",
    "03.22": "Diffusion-Weighted Imaging and ADC",
    "03.23": "High-Velocity Signal Loss and Turbulence",
    "03.24": "Time-of-Flight Angiography",
    "03.25": "Spin Phase Effects and Gradient Moment Nulling",
    "03.26": "Phase-Contrast MRA and VENC",
    "03.27": "Contrast-Enhanced MRA and Gadolinium",
    "03.28": "MR Spectroscopy and PRESS",
}


def slugify(value: str) -> str:
    value = value.lower().replace("t2-star", "t2-star")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def load_source_manifest() -> tuple[dict, dict]:
    source = json.loads(SOURCE_INDEX.read_text(encoding="utf-8"))
    modalities = {}
    for source_key, data in source.items():
        modality_id = source_key.split()[0]
        modalities[modality_id] = {
            "title": data["title"],
            "sections": data["sections"],
        }
    mri_sections = modalities["03"]["sections"]
    if set(mri_sections) != set(VIDEO_QUESTIONS):
        missing = sorted(set(mri_sections) - set(VIDEO_QUESTIONS))
        extra = sorted(set(VIDEO_QUESTIONS) - set(mri_sections))
        raise ValueError(f"MRI bank/source mismatch; missing={missing}, extra={extra}")
    if set(DISPLAY_TITLES) != set(mri_sections):
        raise ValueError("Display-title map does not match MRI source sections")
    return modalities, mri_sections


def transcript_metadata(relative_file: str) -> dict:
    path = SOURCE_ROOT / relative_file
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if len(lines) < 3:
        raise ValueError(f"Transcript header is incomplete: {path}")
    source_title = lines[1].removeprefix("#").strip()
    video_url = lines[2].removeprefix("#").strip()
    if not video_url.startswith("https://"):
        raise ValueError(f"Transcript has no source video URL: {path}")
    return {
        "path": path,
        "relative": relative_file,
        "sourceTitle": source_title,
        "videoUrl": video_url,
    }


def balance_options(item: dict, target_answer: str) -> tuple[list[dict], str]:
    source_index = "ABCD".index(item["answer"])
    correct_text = item["options"][source_index]
    distractors = [
        option for index, option in enumerate(item["options"]) if index != source_index
    ]
    ordered = distractors[:]
    ordered.insert("ABCD".index(target_answer), correct_text)
    return [
        {"letter": letter, "text": text}
        for letter, text in zip("ABCD", ordered, strict=True)
    ], target_answer


def make_questions(video_id: str, items: list[dict]) -> list[dict]:
    questions = []
    offset = int(video_id.split(".")[1]) - 1
    for index, item in enumerate(items, start=1):
        target_answer = "ABCD"[(index + offset - 1) % 4]
        options, answer = balance_options(item, target_answer)
        questions.append(
            {
                "number": str(index),
                "objective": item["objective"],
                "stem": item["stem"],
                "options": options,
                "answer": answer,
                "explanation": item["explanation"],
                "images": [],
                "explanationImages": [],
                "sourceVideo": video_id,
            }
        )
    return questions


def validate_questions(video_id: str, questions: list[dict]) -> dict:
    if [q["number"] for q in questions] != [
        str(number) for number in range(1, len(questions) + 1)
    ]:
        raise ValueError(f"{video_id}: question IDs are not sequential")

    correct_longest = 0
    correct_substantially_longest = 0
    for question in questions:
        options = question["options"]
        texts = [option["text"].strip() for option in options]
        if [option["letter"] for option in options] != list("ABCD"):
            raise ValueError(f"{video_id} Q{question['number']}: invalid option letters")
        if len(texts) != 4 or len(set(texts)) != 4:
            raise ValueError(f"{video_id} Q{question['number']}: duplicate/missing options")
        if not question["stem"].strip().endswith("?"):
            raise ValueError(f"{video_id} Q{question['number']}: lead-in is not closed")
        if len(question["explanation"].split()) < 18:
            raise ValueError(f"{video_id} Q{question['number']}: explanation is too short")
        if re.search(r"\baccording to (the|this)\b", question["stem"], re.I):
            raise ValueError(f"{video_id} Q{question['number']}: source boilerplate")
        correct = next(
            option["text"]
            for option in options
            if option["letter"] == question["answer"]
        )
        longest_distractor = max(
            len(option["text"])
            for option in options
            if option["letter"] != question["answer"]
        )
        if len(correct) >= longest_distractor + 5:
            correct_longest += 1
        distractor_lengths = [
            len(option["text"])
            for option in options
            if option["letter"] != question["answer"]
        ]
        if len(correct) > (sum(distractor_lengths) / 3) + 20:
            correct_substantially_longest += 1

    longest_rate = correct_longest / len(questions)
    if longest_rate > 0.6:
        raise ValueError(
            f"{video_id}: correct option is materially longest in "
            f"{longest_rate:.0%} of items"
        )
    substantial_rate = correct_substantially_longest / len(questions)
    if substantial_rate > 0.6:
        raise ValueError(
            f"{video_id}: correct option is substantially longest in "
            f"{substantial_rate:.0%} of items"
        )
    distribution = Counter(question["answer"] for question in questions)
    if max(distribution.values()) - min(distribution.values()) > 1:
        raise ValueError(f"{video_id}: unbalanced answers {distribution}")
    return {
        "answerDistribution": dict(sorted(distribution.items())),
        "correctLongestRate": round(longest_rate, 3),
        "correctSubstantiallyLongestRate": round(substantial_rate, 3),
    }


def render_html(
    template: str, questions: list[dict], title: str, app_id: str, video_url: str
) -> str:
    rendered = re.sub(
        r"const QUESTIONS = \[.*?\];",
        lambda _: f"const QUESTIONS = {json.dumps(questions, ensure_ascii=False)};",
        template,
        flags=re.S,
    )
    rendered = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)}</title>", rendered, count=1)
    rendered = re.sub(
        r"<h1>.*?</h1>",
        f'<h1>{html.escape(title)}</h1><div class="series-links">'
        '<a href="../../index.html">Physics Video Quiz Library</a>'
        f'<a href="{html.escape(video_url, quote=True)}" target="_blank" rel="noreferrer">Source video</a></div>',
        rendered,
        count=1,
    )
    rendered = rendered.replace(
        "    h1 { font-size: 1.15rem; margin: 0 0 3px; letter-spacing: 0; }",
        "    h1 { font-size: 1.15rem; margin: 0 0 3px; letter-spacing: 0; }\n"
        "    .series-links { display: flex; flex-wrap: wrap; gap: 12px; }\n"
        "    .series-links a { color: var(--muted); font-size: 0.82rem; text-decoration: none; }\n"
        "    .series-links a:hover { color: var(--accent); }",
        1,
    )
    rendered = re.sub(
        r'const APP_ID = ".*?";', f'const APP_ID = "{app_id}";', rendered, count=1
    )
    rendered = rendered.replace(
        'const STORAGE_KEY = "temporary-app-state:" + APP_ID;',
        f'const STORAGE_KEY = "temporary-app-state:" + APP_ID + ":bank-{BANK_VERSION}";',
        1,
    )
    rendered = re.sub(
        r"const DEFAULT_SELECTED = \{.*?\};",
        "const DEFAULT_SELECTED = {};",
        rendered,
        count=1,
    )
    rendered = re.sub(
        r"const DEFAULT_STATE = \{.*?\};",
        'const DEFAULT_STATE = { index: 0, selected: DEFAULT_SELECTED, submitted: DEFAULT_SUBMITTED, mode: "tutor", reviewOpen: false, navOpen: false };',
        rendered,
        count=1,
    )
    rendered = rendered.replace("version: 1,", f"version: {BANK_VERSION},", 1)
    rendered = rendered.replace(
        'if (!payload || payload.appId !== APP_ID) throw new Error("This saved state is for a different quiz.");',
        f'if (!payload || payload.appId !== APP_ID || payload.version !== {BANK_VERSION}) throw new Error("This saved state is for a different quiz version.");',
        1,
    )
    rendered = rendered.replace(
        '{"version":1,"appId":"pediatric-gi-imaging-quiz-ch1",...}',
        f'{{"version":{BANK_VERSION},"appId":"{app_id}",...}}',
        1,
    )
    rendered = rendered.replace("PDF explanation:", "Source explanation:")
    return rendered


def chapter_readme(entry: dict) -> str:
    return (
        f"# {entry['videoId']} {entry['title']} Quiz\n\n"
        f"- Source transcript: `apps/core-studying/YT Physics/{entry['source']}`\n"
        f"- Source video: {entry['videoUrl']}\n"
        f"- Questions: {entry['questions']} manually authored, source-grounded items\n"
        "- Images: none; the source is a spoken-video transcript\n"
        "- Default answers: empty; progress is stored locally in the browser\n"
        f"- Question-bank version: {BANK_VERSION}\n\n"
        "The bank emphasizes causal relationships, parameter tradeoffs, common confusions, and operational application. "
        "Edit `scripts/mri_physics_video_bank.py`, then run "
        "`python scripts\\generate_mri_physics_video_quizzes.py` to regenerate the collection.\n"
    )


def modality_items(modality_id: str, modality: dict, entries: list[dict]) -> str:
    if modality_id == "03":
        rows = "".join(
            f'<li><a href="mri/{entry["folder"]}/index.html">'
            f'<span class="item-code">{entry["videoId"]}</span>'
            f'<span>{html.escape(entry["title"])}</span>'
            f'<span class="count">{entry["questions"]} questions</span></a></li>'
            for entry in entries
        )
        return f'<ol class="quiz-list">{rows}</ol>'
    planned = "".join(
        f'<li><span class="planned-row"><span class="item-code">{code}</span>'
        f'<span>{html.escape(data["title"].split(" - ", 1)[-1])}</span>'
        '<span class="planned">Planned</span></span></li>'
        for code, data in modality["sections"].items()
    )
    return f'<ol class="quiz-list planned-list">{planned}</ol>'


def render_landing(modalities: dict, entries: list[dict]) -> str:
    modality_order = ["01", "02", "03", "04"]
    sections = []
    for modality_id in modality_order:
        modality = modalities[modality_id]
        available = len(entries) if modality_id == "03" else 0
        summary = (
            f"{available} quizzes"
            if available
            else f"{len(modality['sections'])} transcripts, quizzes planned"
        )
        sections.append(
            f'<details data-section="{modality_id}"><summary>'
            f'<span>{html.escape(modality["title"])}</span><span>{summary}</span>'
            f'</summary>{modality_items(modality_id, modality, entries)}</details>'
        )
    total = sum(entry["questions"] for entry in entries)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Physics Video Quiz Library</title>
  <style>
    :root {{ color-scheme: dark; --bg:#0f1218; --panel:#171c25; --line:#2e3747; --ink:#eef2f7; --muted:#9ca7b8; --accent:#38bdf8; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif; }}
    header {{ border-bottom:1px solid var(--line); background:#111721; }}
    .bar, main {{ width:min(980px,94vw); margin:0 auto; }}
    .bar {{ padding:18px 0; }}
    h1 {{ margin:0; font-size:1.35rem; letter-spacing:0; }}
    .meta {{ color:var(--muted); margin-top:5px; font-size:.9rem; }}
    .back {{ color:var(--accent); text-decoration:none; display:inline-block; margin-bottom:12px; }}
    main {{ padding:20px 0 40px; }}
    details {{ border-top:1px solid var(--line); }}
    details:last-child {{ border-bottom:1px solid var(--line); }}
    summary {{ cursor:pointer; display:flex; justify-content:space-between; gap:16px; padding:17px 4px; font-weight:750; }}
    summary span:last-child {{ color:var(--muted); font-size:.86rem; font-weight:600; text-align:right; }}
    .quiz-list {{ list-style:none; margin:0 0 18px; padding:0; border:1px solid var(--line); background:var(--panel); border-radius:6px; overflow:hidden; }}
    .quiz-list li + li {{ border-top:1px solid var(--line); }}
    .quiz-list a, .planned-row {{ min-height:48px; padding:10px 12px; display:grid; grid-template-columns:56px minmax(0,1fr) auto; align-items:center; gap:10px; color:var(--ink); text-decoration:none; }}
    .quiz-list a:hover {{ background:#111721; }}
    .item-code, .count, .planned {{ color:var(--muted); font-size:.84rem; }}
    .count {{ white-space:nowrap; }}
    .planned-list {{ opacity:.72; }}
    @media (max-width:640px) {{
      .quiz-list a, .planned-row {{ grid-template-columns:48px minmax(0,1fr); }}
      .count, .planned {{ grid-column:2; }}
      summary {{ align-items:flex-start; }}
    }}
  </style>
</head>
<body>
  <header><div class="bar"><h1>Physics Video Quiz Library</h1><div class="meta">MRI: {len(entries)} quizzes, {total} questions. Progress is saved separately inside each quiz.</div></div></header>
  <main>
    <a class="back" href="../../index.html">Temporary Apps Library</a>
    {''.join(sections)}
  </main>
  <script>
    const STORAGE_KEY = "physics-video-quiz-library:open-sections";
    const details = [...document.querySelectorAll("details[data-section]")];
    let openSections = [];
    try {{ openSections = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); }} catch {{}}
    details.forEach((section) => {{
      section.open = openSections.includes(section.dataset.section);
      section.addEventListener("toggle", () => {{
        const open = details.filter(item => item.open).map(item => item.dataset.section);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(open));
      }});
    }});
  </script>
</body>
</html>
"""


def update_temp_apps_index(entries: list[dict]) -> None:
    index = TEMP_APPS_INDEX.read_text(encoding="utf-8")
    index = re.sub(
        rf"\n{re.escape(REGISTER_START)}.*?{re.escape(REGISTER_END)}",
        "",
        index,
        flags=re.S,
    )
    app_entries = [
        {
            "name": "Physics Video Quiz Library",
            "path": "library/physics-video-quizzes/index.html",
            "description": "A modality-organized landing page for transcript-based X-ray, CT, MRI, and ultrasound physics quizzes.",
        }
    ]
    app_entries.extend(
        {
            "name": f"MRI Physics {entry['videoId']}: {entry['title']} Quiz",
            "path": f"library/physics-video-quizzes/mri/{entry['folder']}/index.html",
            "description": f"A {entry['questions']}-question transcript-based MRI physics quiz covering {entry['title'].lower()}.",
        }
        for entry in entries
    )
    lines = [REGISTER_START]
    for app in app_entries:
        lines.extend(
            [
                "      {",
                f'        name: {json.dumps(app["name"])},',
                f'        path: {json.dumps(app["path"])},',
                f'        createdAt: "{DATE}",',
                f'        updatedAt: "{DATE}",',
                f'        description: {json.dumps(app["description"])},',
                "      },",
            ]
        )
    lines.append(REGISTER_END)
    block = "\n".join(lines)
    index = index.replace("    const TEMP_APPS = [", f"    const TEMP_APPS = [\n{block}", 1)
    TEMP_APPS_INDEX.write_text(index, encoding="utf-8")


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    modalities, mri_sections = load_source_manifest()
    MRI_ROOT.mkdir(parents=True, exist_ok=True)
    entries = []
    for video_id, source in mri_sections.items():
        title = DISPLAY_TITLES[video_id]
        source_meta = transcript_metadata(source["file"])
        questions = make_questions(video_id, VIDEO_QUESTIONS[video_id])
        qa = validate_questions(video_id, questions)
        folder_name = f"{DATE}-mri-{video_id.replace('.', '-')}-{slugify(title)}-quiz"
        folder = MRI_ROOT / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        app_title = f"MRI {video_id}: {title} Quiz"
        app_id = f"yt-physics-mri-{video_id.replace('.', '-')}-quiz"
        entry = {
            "videoId": video_id,
            "title": title,
            "folder": folder_name,
            "questions": len(questions),
            "source": source["file"],
            "sourceTitle": source_meta["sourceTitle"],
            "videoUrl": source_meta["videoUrl"],
            "appId": app_id,
            "bankVersion": BANK_VERSION,
            **qa,
        }
        (folder / "questions.json").write_text(
            json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (folder / "index.html").write_text(
            render_html(
                template, questions, app_title, app_id, source_meta["videoUrl"]
            ),
            encoding="utf-8",
        )
        (folder / "README.md").write_text(chapter_readme(entry), encoding="utf-8")
        entries.append(entry)
        print(
            f"{video_id}: {len(questions)} questions; "
            f"answers={qa['answerDistribution']}; longest={qa['correctLongestRate']:.0%}"
        )

    (OUTPUT_ROOT / "quiz-manifest.json").write_text(
        json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    total = sum(entry["questions"] for entry in entries)
    (OUTPUT_ROOT / "README.md").write_text(
        "# Physics Video Quiz Library\n\n"
        "This collection organizes transcript-based physics quizzes by modality. "
        f"The initial MRI release contains {len(entries)} quizzes and {total} questions.\n\n"
        "Sources are the transcripts and video links registered in `apps/core-studying/YT Physics/index.json`. "
        "Question content is curated in `scripts/mri_physics_video_bank.py`; rendering and validation are handled by "
        "`scripts/generate_mri_physics_video_quizzes.py`.\n\n"
        "Regenerate with:\n\n"
        "```powershell\n"
        "python scripts\\generate_mri_physics_video_quizzes.py\n"
        "```\n",
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "index.html").write_text(
        render_landing(modalities, entries), encoding="utf-8"
    )
    update_temp_apps_index(entries)
    print(f"Generated {len(entries)} MRI quizzes with {total} questions.")


if __name__ == "__main__":
    main()
