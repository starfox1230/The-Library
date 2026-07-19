#!/usr/bin/env python3
"""Build a private, mobile-first visual study feed from PDF crop metadata."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium
from PIL import Image, ImageDraw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scale", type=float, default=2.5)
    return parser.parse_args()


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def validate_config(config: dict) -> None:
    items = config.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Visual-feed config needs a nonempty items array.")
    ids = [str(item.get("id", "")) for item in items]
    if any(not item_id for item_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("Every visual panel needs a unique nonempty id.")
    strict = bool(config.get("strictSinglePanel", True))
    if strict and not str(config.get("qaReviewedBy", "")).strip():
        raise ValueError("Strict visual feeds require qaReviewedBy after manual crop review.")
    figure_panels: dict[str, dict[str, object]] = {}
    for index, item in enumerate(items, 1):
        crop = item.get("cropPoints")
        if not isinstance(crop, list) or len(crop) != 4:
            raise ValueError(f"Visual panel {index} needs four cropPoints.")
        left, top, right, bottom = map(float, crop)
        if left < 0 or top < 0 or right <= left or bottom <= top:
            raise ValueError(f"Visual panel {index} has invalid crop bounds.")
        if not strict:
            continue
        figure_id = str(item.get("sourceFigureId", "")).strip()
        panel_index = int(item.get("sourcePanelIndex", 0) or 0)
        panel_count = int(item.get("sourcePanelCount", 0) or 0)
        qa = item.get("qa") if isinstance(item.get("qa"), dict) else {}
        if not figure_id or panel_count < 1 or panel_index < 1 or panel_index > panel_count:
            raise ValueError(f"Visual panel {index} needs a valid sourceFigureId and source-panel index/count.")
        if qa.get("singleSourcePanel") is not True or qa.get("noSurroundingPageText") is not True:
            raise ValueError(f"Visual panel {index} lacks the required single-panel/no-page-text QA attestation.")
        group = figure_panels.setdefault(figure_id, {"count": panel_count, "indices": set()})
        if group["count"] != panel_count:
            raise ValueError(f"Source figure {figure_id} has inconsistent sourcePanelCount values.")
        if panel_index in group["indices"]:
            raise ValueError(f"Source figure {figure_id} repeats sourcePanelIndex {panel_index}.")
        group["indices"].add(panel_index)
    if strict:
        for figure_id, group in figure_panels.items():
            expected = set(range(1, int(group["count"]) + 1))
            if group["indices"] != expected:
                raise ValueError(
                    f"Source figure {figure_id} is incomplete: expected panel indices "
                    f"{sorted(expected)}, found {sorted(group['indices'])}."
                )


def words_inside_crop(page: object, crop: list[float]) -> list[str]:
    left, top, right, bottom = map(float, crop)
    hits = []
    for word in page.extract_words() or []:
        center_x = (float(word["x0"]) + float(word["x1"])) / 2
        center_y = (float(word["top"]) + float(word["bottom"])) / 2
        if left <= center_x <= right and top <= center_y <= bottom:
            text = str(word.get("text", "")).strip()
            if any(character.isalpha() for character in text):
                hits.append(text)
    return hits


def write_contact_sheet(items: list[dict], output: Path) -> None:
    columns, tile_width, tile_height = 3, 460, 500
    rows = (len(items) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height), "#20252b")
    draw = ImageDraw.Draw(sheet)
    for index, item in enumerate(items):
        image = Image.open(output / item["asset"]).convert("RGB")
        image.thumbnail((tile_width - 24, tile_height - 64))
        x = (index % columns) * tile_width
        y = (index // columns) * tile_height
        sheet.paste(image, (x + (tile_width - image.width) // 2, y + 44))
        draw.text((x + 10, y + 12), f"{index + 1}. {item['id']}", fill="white")
    sheet.save(output / "contact-sheet.jpg", format="JPEG", quality=90)


def render_html(config: dict, manifest: dict) -> str:
    cards = []
    for index, item in enumerate(manifest["items"], 1):
        cards.append(
            f"""
            <article class="figure-card" id="visual-{escape(item['id'])}">
              <div class="card-meta">
                <span>{index} / {manifest['extractedCount']}</span>
                <span>{escape(item['kind'])}</span>
                <span>MSK {escape(item['printedPage'])}</span>
              </div>
              <h2>{escape(item['title'])}</h2>
              <img src="{escape(item['asset'])}" alt="{escape(item['alt'])}" loading="lazy">
              <div class="teaching">
                <p><strong>See:</strong> {escape(item['see'])}</p>
                <p><strong>Why it matters:</strong> {escape(item['why'])}</p>
              </div>
              <details class="caption"><summary>Caption</summary><p>{escape(item['caption'])}</p></details>
              <button class="save" type="button" data-save="{escape(item['id'])}" aria-pressed="false">Save for Anki</button>
            </article>
            """
        )

    safe_title = escape(config["title"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#101419">
  <title>{safe_title}</title>
  <style>
    :root {{ color-scheme: dark; --bg:#0c1014; --panel:#151b22; --line:#29323d; --text:#f5f7fa; --muted:#aab5c0; --accent:#d6a83d; }}
    * {{ box-sizing:border-box; }}
    html {{ scroll-snap-type:y proximity; background:var(--bg); }}
    body {{ margin:0; background:var(--bg); color:var(--text); font:16px/1.45 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    header {{ position:sticky; top:0; z-index:3; padding:calc(12px + env(safe-area-inset-top)) 18px 12px; background:color-mix(in srgb,var(--bg) 92%,transparent); backdrop-filter:blur(18px); border-bottom:1px solid var(--line); }}
    header h1 {{ margin:0; font-size:1.05rem; }}
    header p {{ margin:3px 0 0; color:var(--muted); font-size:.8rem; }}
    main {{ width:min(100%,680px); margin:auto; padding:14px 12px calc(30px + env(safe-area-inset-bottom)); }}
    .figure-card {{ min-height:calc(100svh - 92px); scroll-snap-align:start; display:flex; flex-direction:column; justify-content:center; gap:12px; padding:18px 0 24px; border-bottom:1px solid var(--line); }}
    .card-meta {{ display:flex; gap:8px; flex-wrap:wrap; color:var(--muted); font-size:.74rem; text-transform:uppercase; letter-spacing:.07em; }}
    .card-meta span {{ padding:4px 8px; border:1px solid var(--line); border-radius:999px; }}
    h2 {{ margin:0; font-size:clamp(1.25rem,5vw,1.7rem); line-height:1.15; }}
    img {{ width:100%; max-height:61svh; object-fit:contain; border-radius:14px; background:#000; box-shadow:0 12px 36px #0008; }}
    .teaching {{ padding:12px 14px; border-radius:12px; background:var(--panel); border:1px solid var(--line); }}
    .teaching p {{ margin:0; }} .teaching p + p {{ margin-top:7px; }}
    .caption {{ border:1px solid var(--line); border-radius:12px; background:var(--panel); overflow:hidden; }}
    .caption summary {{ padding:11px 14px; color:var(--muted); font-size:.78rem; font-weight:700; cursor:pointer; }}
    .caption p {{ margin:0; padding:0 14px 14px; color:var(--muted); font-size:.78rem; }}
    .save {{ align-self:flex-start; min-width:132px; border:1px solid var(--line); border-radius:999px; padding:10px 15px; background:var(--panel); color:var(--text); font:inherit; font-weight:700; }}
    .save[aria-pressed="true"] {{ color:#201600; background:var(--accent); border-color:var(--accent); }}
    @media (min-width:700px) {{ main {{ padding-inline:20px; }} }}
  </style>
</head>
<body>
  <header><h1>{safe_title}</h1><p>{manifest['extractedCount']} visuals · printed pages MSK {escape(config['printedPageRange'])} · private pilot</p></header>
  <main>{''.join(cards)}</main>
  <script>
    const storageKey = {json.dumps('visual-feed-saves:' + config['id'])};
    const saved = new Set(JSON.parse(localStorage.getItem(storageKey) || '[]'));
    document.querySelectorAll('[data-save]').forEach(button => {{
      const id = button.dataset.save;
      const paint = () => {{ const on=saved.has(id); button.setAttribute('aria-pressed', String(on)); button.textContent=on ? 'Saved' : 'Save for Anki'; }};
      button.addEventListener('click', () => {{ saved.has(id) ? saved.delete(id) : saved.add(id); localStorage.setItem(storageKey, JSON.stringify([...saved])); paint(); }});
      paint();
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    validate_config(config)
    output = args.output.resolve()
    assets = output / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    document = pdfium.PdfDocument(str(args.pdf.resolve()))
    text_document = pdfplumber.open(str(args.pdf.resolve()))
    rendered_pages: dict[int, object] = {}
    manifest_items = []

    try:
        for item in config["items"]:
            page_number = int(item["pdfPage"])
            page_index = page_number - 1 - int(config.get("pageOffset", 0))
            if page_number not in rendered_pages:
                page = document[page_index]
                rendered_pages[page_number] = page.render(scale=args.scale).to_pil()
            page_image = rendered_pages[page_number]
            left, top, right, bottom = item["cropPoints"]
            text_hits = words_inside_crop(text_document.pages[page_index], item["cropPoints"])
            allow_embedded_text = bool(item.get("allowEmbeddedText", False))
            if text_hits and not allow_embedded_text:
                preview = " ".join(text_hits[:12])
                raise ValueError(f"{item['id']} intersects extractable page text: {preview}")
            pixel_box = tuple(round(value * args.scale) for value in (left, top, right, bottom))
            cropped = page_image.crop(pixel_box)
            asset_name = f"{item['id']}.png"
            cropped.save(assets / asset_name, format="PNG", optimize=True)
            caption = item.get("caption") or config.get("captions", {}).get(item["id"]) or "No separate caption is provided in the source PDF."
            manifest_items.append({
                **item,
                "caption": caption,
                "asset": f"assets/{asset_name}",
                "pixelSize": list(cropped.size),
                "extractablePageTextHits": [] if allow_embedded_text else text_hits,
                "allowedEmbeddedTextHits": text_hits if allow_embedded_text else [],
            })
    finally:
        text_document.close()

    manifest = {
        "schemaVersion": 1,
        "feedId": config["id"],
        "title": config["title"],
        "source": config["source"],
        "printedPageRange": config["printedPageRange"],
        "pdfPageRange": config["pdfPageRange"],
        "expectedCount": len(config["items"]),
        "extractedCount": len(manifest_items),
        "failures": [],
        "qaSummary": {
            "strictSinglePanel": bool(config.get("strictSinglePanel", True)),
            "reviewedBy": config.get("qaReviewedBy"),
            "singlePanelAttestations": sum(item.get("qa", {}).get("singleSourcePanel") is True for item in manifest_items),
            "noSurroundingTextAttestations": sum(item.get("qa", {}).get("noSurroundingPageText") is True for item in manifest_items),
            "extractablePageTextHits": sum(len(item.get("extractablePageTextHits", [])) for item in manifest_items),
            "allowedEmbeddedTextHits": sum(len(item.get("allowedEmbeddedTextHits", [])) for item in manifest_items),
        },
        "items": manifest_items,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "index.html").write_text(render_html(config, manifest), encoding="utf-8")
    write_contact_sheet(manifest_items, output)
    print(f"Built {manifest['extractedCount']} visuals at {output}")


if __name__ == "__main__":
    main()
