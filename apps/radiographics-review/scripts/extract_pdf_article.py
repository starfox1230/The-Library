import argparse
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pdfplumber
from PIL import Image
from pypdf import PdfReader


def normalize_whitespace(value):
    return re.sub(r"\s+", " ", value or "").strip()


def strip_html(value):
    return normalize_whitespace(re.sub(r"</?[A-Za-z][^>]*>", " ", value or ""))


def slugify(value, max_length=80):
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_whitespace(value).lower()).strip("-")
    if not slug:
        slug = "untitled"
    return slug[:max_length].rstrip("-") or "untitled"


def iso_date_from_parts(parts):
    if not parts:
        return ""
    year = parts[0]
    month = parts[1] if len(parts) > 1 else 1
    day = parts[2] if len(parts) > 2 else 1
    return f"{year:04d}-{month:02d}-{day:02d}T00:00:00.000Z"


def first_crossref_date(message):
    for key in ("published-print", "published-online", "issued", "created"):
        parts = message.get(key, {}).get("date-parts", [[]])[0]
        value = iso_date_from_parts(parts)
        if value:
            return value
    return ""


def fetch_crossref_metadata(doi):
    if not doi:
        return {}
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            return json.loads(response.read().decode("utf-8")).get("message", {})
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return {}


def pdf_text(pdf_path):
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def clean_text_for_body(text):
    value = text.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"(\w)-\n(\w)", r"\1\2", value)
    value = re.sub(r"\n+", "\n", value)
    value = re.sub(r"\bOPEN IN VIEWER\b", " ", value, flags=re.I)
    value = re.sub(r"\bDownload as PowerPoint\b", " ", value, flags=re.I)
    value = re.sub(r"\bThis copy is for personal\s+use only\..*?reprints@rsna\.org", " ", value, flags=re.I | re.S)
    value = re.sub(r"\bRG\s*[•\-.]\s*Volume\s+\d+\s+Number\s+\d+.*?\d{4}\b", " ", value, flags=re.I)
    value = re.sub(r"\bVolume\s+\d+\s+Number\s+\d+\s+\d+\s+radiographics\.rsna\.org\b", " ", value, flags=re.I)
    value = re.sub(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:-[A-Za-z]+)?\s+\d{4}\s+radiographics\.rsna\.org\b", " ", value, flags=re.I)
    value = re.split(r"\nReferences\b", value, flags=re.I)[0]
    return normalize_whitespace(value)


def split_body_blocks(text):
    cleaned = clean_text_for_body(text)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", cleaned)
    blocks = []
    current = []
    word_count = 0
    for sentence in sentences:
        sentence = normalize_whitespace(sentence)
        if not sentence:
            continue
        current.append(sentence)
        word_count += len(sentence.split())
        if word_count >= 120:
            blocks.append(" ".join(current))
            current = []
            word_count = 0
    if current:
        blocks.append(" ".join(current))
    return blocks[:28]


def extract_doi(text):
    match = re.search(r"10\.1148/rg\.[A-Za-z0-9]+", text)
    return match.group(0) if match else ""


def extract_citation(text):
    match = re.search(r"RadioGraphics\s+(\d{4});\s*(\d+)(?:\((\d+)\))?:\s*([A-Za-z0-9eE\-–]+)", text)
    if not match:
        return {}
    return {
        "year": match.group(1),
        "volume": match.group(2),
        "issue": match.group(3) or "",
        "pages": match.group(4).replace("–", "-"),
    }


def extract_authors_from_text(text):
    names = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z]+),\s+MD(?:,\s+MS)?", text)
    return list(dict.fromkeys(names))


def crossref_authors(message):
    authors = []
    for author in message.get("author") or []:
        name = normalize_whitespace(f"{author.get('given', '')} {author.get('family', '')}")
        if name:
            authors.append(name)
    return authors


def title_from_sources(reader, crossref_message):
    titles = crossref_message.get("title") or []
    if titles:
        return strip_html(html.unescape(titles[0]))
    metadata_title = reader.metadata.get("/Title") if reader.metadata else ""
    return normalize_whitespace(metadata_title or "Untitled RadioGraphics article")


def caption_from_page_text(page_text, figure_number):
    pattern = re.compile(rf"Figure\s+{figure_number}\.\s+", re.I)
    match = pattern.search(page_text)
    if not match:
        return f"Figure {figure_number}."
    start = match.start()
    rest = page_text[start:]
    next_figure = re.search(rf"\sFigure\s+{figure_number + 1}\.\s+", rest, re.I)
    end = next_figure.start() if next_figure else len(rest)
    for stop_pattern in (
        r"\sTable\s+\d+:",
        r"\sScenario\s+\d+:",
        r"\sRG\s*[•\-.]\s*Volume",
        r"\sVolume\s+\d+\s+Number",
        r"\s(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:-[A-Za-z]+)?\s+\d{4}\s+radiographics\.rsna\.org",
    ):
        stop = re.search(stop_pattern, rest[:end], re.I)
        if stop:
            end = min(end, stop.start())
    caption = normalize_whitespace(rest[:end])
    if len(caption) > 1200:
        caption = normalize_whitespace(caption[:1200])
    return caption or f"Figure {figure_number}."


def find_pdftoppm(explicit_path):
    if explicit_path:
        return explicit_path
    bundled_exe = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "native" / "poppler" / "Library" / "bin" / "pdftoppm.exe"
    if bundled_exe.exists():
        return str(bundled_exe)
    bundled = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "bin" / "pdftoppm.cmd"
    if bundled.exists():
        return str(bundled)
    found = shutil.which("pdftoppm") or shutil.which("pdftoppm.cmd")
    if found:
        return found
    raise RuntimeError("pdftoppm was not found. Install Poppler or set --pdftoppm.")


def render_page(pdf_path, page_number, pdftoppm_path, temp_dir):
    prefix = str(Path(temp_dir) / f"page-{page_number}")
    subprocess.run(
        [pdftoppm_path, "-r", "220", "-f", str(page_number), "-l", str(page_number), "-png", str(pdf_path), prefix],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    matches = sorted(glob.glob(f"{prefix}*.png"))
    if not matches:
        raise RuntimeError(f"pdftoppm did not render page {page_number}.")
    return matches[0]


def crop_image(page_png, page_width, page_height, image_box, output_path):
    with Image.open(page_png) as image:
        scale_x = image.width / page_width
        scale_y = image.height / page_height
        pad = 8
        left = max(0, int((image_box["x0"] - pad) * scale_x))
        top = max(0, int((image_box["top"] - pad) * scale_y))
        right = min(image.width, int((image_box["x1"] + pad) * scale_x))
        bottom = min(image.height, int((image_box["bottom"] + pad) * scale_y))
        image.crop((left, top, right, bottom)).save(output_path)


def extract_figures(pdf_path, assets_dir, pdftoppm_path):
    figures = []
    assets_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        with pdfplumber.open(str(pdf_path)) as pdf:
            rendered_pages = {}
            figure_number = 1
            for page_index, page in enumerate(pdf.pages, start=1):
                image_boxes = [
                    image
                    for image in page.images
                    if image.get("width", 0) >= 50 and image.get("height", 0) >= 50
                ]
                image_boxes.sort(key=lambda item: (round(item["top"], 1), round(item["x0"], 1)))
                if not image_boxes:
                    continue
                page_text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                if page_index not in rendered_pages:
                    rendered_pages[page_index] = render_page(pdf_path, page_index, pdftoppm_path, temp_dir)
                for image_box in image_boxes:
                    file_name = f"figure-{figure_number:02d}.png"
                    output_path = assets_dir / file_name
                    crop_image(rendered_pages[page_index], page.width, page.height, image_box, output_path)
                    caption = caption_from_page_text(page_text, figure_number)
                    figures.append(
                        {
                            "label": f"Figure {figure_number}",
                            "index": figure_number,
                            "page": page_index,
                            "rawCaption": caption,
                            "caption": caption,
                            "localImageName": file_name,
                            "localImagePath": str(output_path),
                            "relativeImagePath": f"assets/{file_name}",
                            "isVisualAbstract": False,
                        }
                    )
                    figure_number += 1
    return figures


def build_article_dir(articles_dir, published_at, doi, title):
    date = (published_at or "undated")[:10]
    return articles_dir / f"{date}-{slugify(doi or 'article', 32)}-{slugify(title or 'article', 72)}"


def extract_article(pdf_path, articles_dir, pdftoppm_path):
    reader = PdfReader(str(pdf_path))
    text = pdf_text(pdf_path)
    doi = extract_doi(text)
    crossref = fetch_crossref_metadata(doi)
    title = title_from_sources(reader, crossref)
    citation = extract_citation(text)
    published_at = first_crossref_date(crossref)
    if not published_at and citation.get("year"):
        published_at = f"{citation['year']}-01-01T00:00:00.000Z"
    article_dir = build_article_dir(articles_dir, published_at, doi, title)
    assets_dir = article_dir / "assets"
    figures = extract_figures(pdf_path, assets_dir, pdftoppm_path)
    body_blocks = split_body_blocks(text)
    authors = crossref_authors(crossref) or extract_authors_from_text(text)
    link = crossref.get("URL") or (f"https://doi.org/{doi}" if doi else "")

    return {
        "title": title,
        "doi": doi,
        "journal": "RadioGraphics",
        "publishedAt": published_at,
        "volume": str(crossref.get("volume") or citation.get("volume") or ""),
        "issue": str(crossref.get("issue") or citation.get("issue") or ""),
        "pages": str(crossref.get("page") or citation.get("pages") or ""),
        "link": link,
        "pdfUrl": str(pdf_path),
        "sourcePdfPath": str(pdf_path),
        "authors": authors,
        "abstract": body_blocks[0] if body_blocks else "",
        "rawBodyBlocks": body_blocks,
        "rawBodyText": "\n\n".join(body_blocks),
        "bodyBlocks": body_blocks,
        "bodyText": "\n\n".join(body_blocks),
        "articleDir": str(article_dir),
        "figures": figures,
    }


def main():
    parser = argparse.ArgumentParser(description="Extract a RadioGraphics article package from a local PDF.")
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--articles-dir", required=True)
    parser.add_argument("--pdftoppm", default="")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    articles_dir = Path(args.articles_dir).resolve()
    pdftoppm_path = find_pdftoppm(args.pdftoppm)
    article = extract_article(pdf_path, articles_dir, pdftoppm_path)
    json.dump(article, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
