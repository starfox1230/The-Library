#!/usr/bin/env python3
"""Build a private, mobile-first visual study feed from PDF crop metadata."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import pypdfium2 as pdfium


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scale", type=float, default=2.5)
    return parser.parse_args()


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


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
    output = args.output.resolve()
    assets = output / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    document = pdfium.PdfDocument(str(args.pdf.resolve()))
    rendered_pages: dict[int, object] = {}
    manifest_items = []

    for item in config["items"]:
        page_number = int(item["pdfPage"])
        if page_number not in rendered_pages:
            page = document[page_number - 1]
            rendered_pages[page_number] = page.render(scale=args.scale).to_pil()
        page_image = rendered_pages[page_number]
        left, top, right, bottom = item["cropPoints"]
        pixel_box = tuple(round(value * args.scale) for value in (left, top, right, bottom))
        cropped = page_image.crop(pixel_box)
        asset_name = f"{item['id']}.png"
        cropped.save(assets / asset_name, format="PNG", optimize=True)
        manifest_items.append({**item, "asset": f"assets/{asset_name}", "pixelSize": list(cropped.size)})

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
        "items": manifest_items,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "index.html").write_text(render_html(config, manifest), encoding="utf-8")
    print(f"Built {manifest['extractedCount']} visuals at {output}")


if __name__ == "__main__":
    main()
