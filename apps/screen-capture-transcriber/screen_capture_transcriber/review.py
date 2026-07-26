from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote

from .models import SessionManifest, format_duration


def build_anatomy_review(session: SessionManifest) -> Path:
    cards: list[str] = []
    for capture in session.anatomy_captures:
        image_url = quote(capture.annotated_image.replace("\\", "/"))
        label = html.escape(capture.label or "Unlabeled capture")
        timestamp = format_duration(capture.timestamp_seconds)
        card_badge = "<span class='badge'>Anki card</span>" if capture.create_anki_card else ""
        cards.append(
            f"""
            <article class="capture">
              <button class="image-button" data-time="{capture.timestamp_seconds:.3f}"
                      aria-label="Play from {html.escape(timestamp)}">
                <img src="{image_url}" alt="{label}">
              </button>
              <div class="capture-copy">
                <h2>{label}</h2>
                <button class="seek" data-time="{capture.timestamp_seconds:.3f}">
                  ▶ Play from {html.escape(timestamp)}
                </button>
                {card_badge}
              </div>
            </article>"""
        )

    title = html.escape(session.title)
    video_url = quote(session.playback_path.name)
    resume_key = json.dumps(f"screen-capture-transcriber:{session.created_at}")
    captures_html = "\n".join(cards) or (
        "<p class='empty'>No anatomy captures were saved in this session.</p>"
    )
    session.review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Anatomy review</title>
  <style>
    :root {{ color-scheme: dark; font-family: "Segoe UI", system-ui, sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #09101c; color: #eef4fc; }}
    header {{ position: sticky; top: 0; z-index: 2; padding: 18px 24px;
              background: rgba(9,16,28,.96); border-bottom: 1px solid #26364d; }}
    h1 {{ margin: 0 0 12px; font-size: clamp(1.25rem, 3vw, 2rem); }}
    video {{ display: block; width: min(100%, 960px); max-height: 48vh;
             background: #000; border-radius: 10px; }}
    main {{ padding: 24px; display: grid; gap: 18px;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }}
    .capture {{ overflow: hidden; background: #101b2b; border: 1px solid #26364d;
                border-radius: 12px; }}
    .image-button {{ display: block; width: 100%; padding: 0; border: 0;
                     background: #05080d; cursor: pointer; }}
    img {{ display: block; width: 100%; height: auto; }}
    .capture-copy {{ padding: 14px; }}
    h2 {{ margin: 0 0 10px; font-size: 1.05rem; }}
    .seek {{ color: #eef4fc; background: #1a7390; border: 1px solid #58d7ff;
             border-radius: 7px; padding: 8px 12px; cursor: pointer; }}
    .badge {{ margin-left: 8px; color: #ffd47b; }}
    .empty {{ color: #9eb0c8; }}
  </style>
</head>
<body>
  <header>
    <h1>{title} — Anatomy review</h1>
    <p>Your playback position is remembered automatically on this computer.</p>
    <video id="recording" controls preload="metadata" src="{video_url}"></video>
  </header>
  <main>{captures_html}</main>
  <script>
    const video = document.getElementById("recording");
    const resumeKey = {resume_key};
    video.addEventListener("loadedmetadata", () => {{
      const saved = Number(localStorage.getItem(resumeKey));
      if (Number.isFinite(saved) && saved > 0 && saved < video.duration - 2) {{
        video.currentTime = saved;
      }}
    }});
    let lastPositionSave = 0;
    video.addEventListener("timeupdate", () => {{
      const now = Date.now();
      if (now - lastPositionSave > 1000) {{
        localStorage.setItem(resumeKey, String(video.currentTime));
        lastPositionSave = now;
      }}
    }});
    video.addEventListener("ended", () => localStorage.removeItem(resumeKey));
    document.querySelectorAll("[data-time]").forEach((button) => {{
      button.addEventListener("click", () => {{
        video.currentTime = Number(button.dataset.time);
        video.play();
        window.scrollTo({{top: 0, behavior: "smooth"}});
      }});
    }});
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )
    return session.review_path


def write_anatomy_manifest(session: SessionManifest) -> Path:
    path = session.folder / "anki-notes.json"
    notes = [
        {
            "id": f"anatomy-capture-{capture.index:03d}",
            "label": capture.label,
            "timestamp_seconds": capture.timestamp_seconds,
            "image": capture.annotated_image,
            "create_anki_card": capture.create_anki_card,
        }
        for capture in session.anatomy_captures
    ]
    path.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
