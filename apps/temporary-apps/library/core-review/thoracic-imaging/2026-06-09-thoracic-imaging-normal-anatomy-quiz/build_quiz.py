from __future__ import annotations

import json
import posixpath
import re
import shutil
import zipfile
from io import BytesIO
from pathlib import Path

from lxml import etree, html
from PIL import Image


APP_DIR = Path(__file__).resolve().parent
SOURCE_EPUB = Path(r"G:/My Drive/0. Radiology/Thoracic Imaging_ A Core Review.epub")
ASSET_DIR = APP_DIR / "assets"

TITLE = "Thoracic Imaging: A Core Review Normal Anatomy Quiz"
APP_ID = "thoracic-imaging-core-review-normal-anatomy-quiz-ch2"
DEFAULT_SEED_VERSION = 1
DEFAULT_SELECTED: dict[str, str] = {}

CHAPTER_FILES = [
    "OEBPS/xhtml/Hobbs9781975126223-ch002.xhtml",
    "OEBPS/xhtml/Hobbs9781975126223-ch002e.xhtml",
]


def clean_text(value: str) -> str:
    value = value.replace("\t", " ").replace("\u00a0", " ")
    value = value.replace("\ufeff", "")
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = value.replace("\u2018", "'").replace("\u2019", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"(\w)- (\w)", r"\1\2", value)
    value = re.sub(r"(\w)\s+-\s+(\w)", r"\1\2", value)
    value = re.sub(r"\s+([,.;:])", r"\1", value)
    return value.strip()


def local_name(node) -> str:
    return etree.QName(node).localname.lower()


def text_content(node) -> str:
    return clean_text(" ".join(t for t in node.itertext()))


def rel_from_src(chapter_file: str, src: str) -> str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(chapter_file), src))


def write_epub_image(zf: zipfile.ZipFile, epub_path: str) -> str | None:
    image_bytes = zf.read(epub_path)
    with Image.open(BytesIO(image_bytes)) as im:
        if im.width * im.height < 5000 or (im.width <= 40 and im.height <= 40):
            return None
        if im.mode != "RGB":
            im = im.convert("RGB")
        out = ASSET_DIR / Path(epub_path).name
        im.save(out, format="JPEG", quality=92, optimize=True)
    return f"assets/{Path(epub_path).name}"


def node_images(node, chapter_file: str, zf: zipfile.ZipFile) -> list[str]:
    images: list[str] = []
    for img in node.xpath('.//*[local-name()="img"]'):
        src = img.get("src")
        if not src:
            continue
        rel = write_epub_image(zf, rel_from_src(chapter_file, src))
        if rel and rel not in images:
            images.append(rel)
    return images


def parse_questions(doc, chapter_file: str, zf: zipfile.ZipFile) -> list[dict]:
    questions: list[dict] = []
    for qa in doc.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " Q-A ")]'):
        q_node = qa.xpath('./*[contains(concat(" ", normalize-space(@class), " "), " QUESTION ")]')
        r_node = qa.xpath('./*[contains(concat(" ", normalize-space(@class), " "), " RESPONSES ")]')
        if not q_node or not r_node:
            continue
        q_para = q_node[0].xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " QUESTION-PARA ")]')
        if not q_para:
            continue
        qid = (q_para[0].get("id") or "").removeprefix("q")
        if not re.fullmatch(r"\d+[a-z]?", qid):
            continue

        stem = text_content(q_para[0])
        stem = re.sub(rf"^{re.escape(qid)}\s*", "", stem, flags=re.I)
        options = []
        for ans in r_node[0].xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " ANSWER-PARA ")]'):
            text = text_content(ans)
            match = re.match(r"^([A-F])\.\s*(.*)$", text)
            if match:
                options.append({"letter": match.group(1), "text": clean_text(match.group(2))})
        questions.append(
            {
                "number": qid,
                "stem": clean_text(stem),
                "options": options,
                "images": node_images(q_node[0], chapter_file, zf),
                "explanationImages": [],
            }
        )
    return questions


def parse_explanations(doc, chapter_file: str, zf: zipfile.ZipFile) -> dict[str, dict[str, str | list[str]]]:
    explanations: dict[str, dict[str, str | list[str]]] = {}
    for node in doc.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " EXPLANATION ")]'):
        node_id = (node.get("id") or "").removeprefix("ans")
        if not re.fullmatch(r"\d+[a-z]?", node_id):
            continue
        paragraphs = [text_content(p) for p in node.xpath('./*[starts-with(@class, "EXPLANATION-PARA")]')]
        text = clean_text(" ".join(p for p in paragraphs if p))
        text = re.sub(rf"^{re.escape(node_id)}\s*", "", text, flags=re.I)
        match = re.search(r"Answer\s+([A-F])\.\s*(.*)$", text, flags=re.I)
        if match:
            answer = match.group(1).upper()
            explanation = clean_text(f"{answer.lower()}. {match.group(2)}")
        else:
            answer = ""
            explanation = text
        explanations[node_id] = {
            "answer": answer,
            "explanation": explanation,
            "images": node_images(node, chapter_file, zf),
        }
    return explanations


def parse_epub() -> list[dict]:
    if not SOURCE_EPUB.exists():
        raise FileNotFoundError(SOURCE_EPUB)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for old in ASSET_DIR.glob("*"):
        if old.is_file():
            old.unlink()

    questions: list[dict] = []
    explanations: dict[str, dict[str, str | list[str]]] = {}
    with zipfile.ZipFile(SOURCE_EPUB) as zf:
        for chapter_file in CHAPTER_FILES:
            raw = zf.read(chapter_file).decode("utf-8", errors="replace")
            doc = html.fromstring(raw)
            questions.extend(parse_questions(doc, chapter_file, zf))
            explanations.update(parse_explanations(doc, chapter_file, zf))

    for q in questions:
        answer = explanations.get(q["number"], {})
        q["answer"] = answer.get("answer", "")
        q["explanation"] = answer.get("explanation", "")
        q["explanationImages"] = answer.get("images", [])
    hydrate_short_multipart_explanations(questions)
    return questions


def base_number(question_number: str) -> str:
    return re.match(r"\d+", question_number).group(0)


def explanation_body(value: str) -> str:
    return clean_text(re.sub(r"^[a-f]\.\s*", "", value, flags=re.I))


def hydrate_short_multipart_explanations(questions: list[dict]) -> None:
    by_base: dict[str, list[dict]] = {}
    for q in questions:
        if re.fullmatch(r"\d+[a-z]", q["number"]):
            by_base.setdefault(base_number(q["number"]), []).append(q)
    for group in by_base.values():
        long_explanations = [q.get("explanation", "") for q in group if len(explanation_body(q.get("explanation", ""))) > 20]
        if not long_explanations:
            continue
        shared = explanation_body(max(long_explanations, key=len))
        for q in group:
            if len(explanation_body(q.get("explanation", ""))) <= 20 and q.get("answer"):
                q["explanation"] = clean_text(f"{q['answer'].lower()}. See related explanation: {shared}")


def render_html(questions: list[dict]) -> str:
    template = (APP_DIR / "_template.html").read_text(encoding="utf-8")
    data = json.dumps(questions, ensure_ascii=False)
    template = re.sub(r"const QUESTIONS = \[.*?\];", lambda _match: f"const QUESTIONS = {data};", template, flags=re.S)
    title_pattern = r"(Pediatric GI Imaging Quiz|Pediatric Gastrointestinal Tract Quiz|Absolute Breast Imaging Review Interventional Procedures Quiz)"
    template = re.sub(title_pattern, TITLE, template)
    id_pattern = r"(pediatric-gi-imaging-quiz-ch1|absolute-breast-imaging-review-interventional-procedures-quiz-ch6)"
    template = re.sub(id_pattern, APP_ID, template)
    default_selected_json = json.dumps(DEFAULT_SELECTED, ensure_ascii=False)
    template = re.sub(r"const DEFAULT_SELECTED = \{.*?\};", f"const DEFAULT_SELECTED = {default_selected_json};", template)
    if "DEFAULT_SEED_VERSION" not in template:
        template = re.sub(r"(const DEFAULT_SELECTED = .*?;\n)", rf"\1    const DEFAULT_SEED_VERSION = {DEFAULT_SEED_VERSION};\n", template)
    return template


def main() -> None:
    questions = parse_epub()
    (APP_DIR / "questions.json").write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")
    (APP_DIR / "index.html").write_text(render_html(questions), encoding="utf-8")
    print(f"wrote {len(questions)} questions")
    print("numbers:", [q["number"] for q in questions])
    print("missing answers:", [q["number"] for q in questions if not q.get("answer")])
    print("bad option counts:", [(q["number"], len(q["options"])) for q in questions if len(q["options"]) < 3 or len(q["options"]) > 6])
    print("question image refs:", sum(len(q["images"]) for q in questions))
    print("explanation image refs:", sum(len(q["explanationImages"]) for q in questions))


if __name__ == "__main__":
    main()
