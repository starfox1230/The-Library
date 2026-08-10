from __future__ import annotations

import html
import json
from pathlib import Path
import time
from urllib.parse import quote

from .learning_notes import (
    note_display_timestamp,
    read_transcript,
    render_transcript_with_notes,
)
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
              <div class="image-wrap">
                <button class="image-button" data-time="{capture.timestamp_seconds:.3f}"
                        aria-label="Play from {html.escape(timestamp)}">
                  <img class="capture-image" src="{image_url}" alt="{label}">
                </button>
                <button class="expand" type="button" data-image="{image_url}"
                        data-label="{label}" aria-label="Expand {label}">
                  ⛶ Expand
                </button>
              </div>
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
    video_path = (
        session.playback_path
        if session.playback_path.is_file()
        else session.recording_path
    )
    video_url = quote(video_path.name)
    resume_key = json.dumps(f"screen-capture-transcriber:{session.created_at}")
    review_version = str(time.time_ns())
    (session.folder / "anatomy-review-version.js").write_text(
        f"window.__ANATOMY_REVIEW_VERSION__ = {json.dumps(review_version)};\n",
        encoding="utf-8",
    )
    captures_html = "\n".join(cards) or (
        "<p class='empty'>No anatomy captures were saved in this session.</p>"
    )
    note_cards: list[str] = []
    for note in sorted(
        session.learning_notes,
        key=lambda item: (item.timestamp_seconds, item.created_at, item.id),
    ):
        timestamp = format_duration(note_display_timestamp(note))
        note_cards.append(
            f"""
            <article class="learning-note" id="{html.escape(note.id)}">
              <div class="note-heading">
                <button class="seek" data-time="{note.timestamp_seconds:.3f}">
                  ▶ {html.escape(timestamp)}
                </button>
                <button class="copy-note" type="button"
                        data-copy="{html.escape(note.text, quote=True)}">
                  Copy note
                </button>
              </div>
              <p>{html.escape(note.text)}</p>
            </article>"""
        )
    notes_html = "\n".join(note_cards) or (
        "<p class='empty'>No timestamped learning notes were saved.</p>"
    )
    transcript_text = read_transcript(session)
    transcript_html = (
        f"<pre>{html.escape(transcript_text)}</pre>"
        if transcript_text
        else "<p class='empty'>No transcript is available for this session.</p>"
    )
    transcript_json = json.dumps(transcript_text, ensure_ascii=False)
    transcript_notes_json = json.dumps(
        render_transcript_with_notes(session),
        ensure_ascii=False,
    )
    session.review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Session review</title>
  <style>
    :root {{ color-scheme: dark; font-family: "Segoe UI", system-ui, sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #09101c; color: #eef4fc; }}
    header {{ position: sticky; top: 0; z-index: 2; padding: 18px 24px;
              background: rgba(9,16,28,.96); border-bottom: 1px solid #26364d; }}
    h1 {{ margin: 0 0 12px; font-size: clamp(1.25rem, 3vw, 2rem); }}
    video {{ display: block; width: min(100%, 960px); max-height: 48vh;
             background: #000; border-radius: 10px; }}
    main {{ padding: 24px; display: grid; gap: 22px; }}
    .review-section {{ min-width: 0; }}
    .section-heading {{ display: flex; flex-wrap: wrap; align-items: center;
                        gap: 10px; margin: 0 0 12px; }}
    .section-heading h2 {{ margin: 0; font-size: 1.3rem; }}
    .capture-grid {{ display: grid; gap: 18px; align-items: start;
                     grid-template-columns:
                     repeat(auto-fit, minmax(min(100%, 300px), 1fr)); }}
    .capture {{ display: flex; flex-direction: column; min-width: 0; overflow: hidden;
                background: #101b2b; border: 1px solid #26364d;
                border-radius: 12px; }}
    .image-wrap {{ position: relative; min-width: 0; overflow: hidden;
                   background: #05080d; }}
    .image-button {{ display: flex; align-items: center; justify-content: center;
                     width: 100%; min-width: 0;
                     height: clamp(190px, 34vh, 340px); padding: 10px;
                     overflow: hidden; border: 0; background: #05080d;
                     cursor: pointer; }}
    .capture-image {{ display: block; width: 100%; height: 100%; min-width: 0;
                      min-height: 0; object-fit: contain; }}
    .expand {{ position: absolute; top: 10px; right: 10px; color: #f5f8fc;
               background: rgba(9,16,28,.88); border: 1px solid #8aa4c4;
               border-radius: 7px; padding: 7px 10px; cursor: pointer; }}
    .expand:hover, .expand:focus-visible {{ background: #1a7390;
                                           border-color: #58d7ff; }}
    .capture-copy {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px;
                     min-width: 0; padding: 14px; }}
    h2 {{ flex: 0 0 100%; min-width: 0; margin: 0; font-size: 1.05rem;
          overflow-wrap: anywhere; }}
    .seek {{ color: #eef4fc; background: #1a7390; border: 1px solid #58d7ff;
             border-radius: 7px; padding: 8px 12px; cursor: pointer;
             white-space: nowrap; }}
    .badge {{ color: #ffd47b; }}
    .empty {{ color: #9eb0c8; }}
    .learning-notes {{ display: grid; gap: 10px; }}
    .learning-note {{ scroll-margin-top: 58vh; padding: 14px;
                      background: #101b2b; border: 1px solid #26364d;
                      border-radius: 10px; }}
    .learning-note:target {{ border-color: #58d7ff;
                             box-shadow: 0 0 0 2px rgba(88,215,255,.18); }}
    .learning-note p {{ margin: 10px 0 0; white-space: pre-wrap;
                        line-height: 1.5; }}
    .note-heading {{ display: flex; align-items: center; gap: 10px; }}
    .copy-note, .copy-action {{ color: #eef4fc; background: #17273a;
                               border: 1px solid #36516f; border-radius: 7px;
                               padding: 8px 12px; cursor: pointer; }}
    .transcript pre {{ margin: 0; padding: 16px; max-height: 60vh;
                       overflow: auto; white-space: pre-wrap; line-height: 1.5;
                       background: #07101b; border: 1px solid #26364d;
                       border-radius: 10px; }}
    #lightbox[hidden] {{ display: none; }}
    #lightbox {{ position: fixed; inset: 0; z-index: 20; display: grid;
                 place-items: center; padding: 24px; cursor: zoom-out;
                 background: rgba(2,5,10,.96); }}
    #lightbox img {{ display: block; max-width: calc(100vw - 48px);
                     max-height: calc(100vh - 48px); width: auto; height: auto;
                     object-fit: contain; }}
    #lightbox .close {{ position: absolute; top: 14px; right: 18px;
                       color: #fff; background: rgba(9,16,28,.9);
                       border: 1px solid #8aa4c4; border-radius: 8px;
                       padding: 8px 12px; font-size: 1rem; cursor: pointer; }}
    body.lightbox-open {{ overflow: hidden; }}
    @media (max-width: 520px) {{
      header, main {{ padding: 14px; }}
      .image-button {{ height: clamp(170px, 31vh, 280px); }}
      .capture-copy {{ padding: 12px; }}
    }}
  </style>
  <script src="anatomy-review-version.js"></script>
</head>
<body>
  <header>
    <h1>{title} — Session review</h1>
    <p>Your playback position is remembered automatically on this computer.</p>
    <video id="recording" controls preload="metadata" src="{video_url}"></video>
  </header>
  <main>
    <section class="review-section">
      <div class="section-heading"><h2>Timestamped Learning Notes</h2></div>
      <div class="learning-notes">{notes_html}</div>
    </section>
    <section class="review-section">
      <div class="section-heading"><h2>Anatomy Captures</h2></div>
      <div class="capture-grid">{captures_html}</div>
    </section>
    <section class="review-section transcript">
      <div class="section-heading">
        <h2>Transcript</h2>
        <button id="copy-transcript" class="copy-action" type="button">
          Copy Transcript
        </button>
        <button id="copy-transcript-notes" class="copy-action" type="button">
          Copy Transcript + Notes
        </button>
      </div>
      {transcript_html}
    </section>
  </main>
  <div id="lightbox" role="dialog" aria-modal="true" aria-label="Expanded anatomy image"
       hidden>
    <button class="close" type="button" aria-label="Close expanded image">✕ Close</button>
    <img id="lightbox-image" src="" alt="">
  </div>
  <script>
    const video = document.getElementById("recording");
    const lightbox = document.getElementById("lightbox");
    const lightboxImage = document.getElementById("lightbox-image");
    const resumeKey = {resume_key};
    const transcriptText = {transcript_json};
    const transcriptAndNotesText = {transcript_notes_json};
    const loadedReviewVersion = window.__ANATOMY_REVIEW_VERSION__;
    video.addEventListener("loadedmetadata", () => {{
      const requested = Number(new URLSearchParams(window.location.search).get("t"));
      if (Number.isFinite(requested) && requested >= 0 && requested < video.duration) {{
        video.currentTime = requested;
        return;
      }}
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
    window.addEventListener("beforeunload", () => {{
      if (Number.isFinite(video.currentTime) && video.currentTime > 0) {{
        localStorage.setItem(resumeKey, String(video.currentTime));
      }}
    }});
    let updateCheckRunning = false;
    function checkForReviewUpdate() {{
      if (updateCheckRunning) return;
      updateCheckRunning = true;
      const script = document.createElement("script");
      script.src = "anatomy-review-version.js?checked=" + Date.now();
      script.onload = () => {{
        updateCheckRunning = false;
        script.remove();
        if (window.__ANATOMY_REVIEW_VERSION__ !== loadedReviewVersion) {{
          window.location.reload();
        }}
      }};
      script.onerror = () => {{
        updateCheckRunning = false;
        script.remove();
      }};
      document.head.appendChild(script);
    }}
    window.addEventListener("focus", checkForReviewUpdate);
    document.addEventListener("visibilitychange", () => {{
      if (!document.hidden) checkForReviewUpdate();
    }});
    document.querySelectorAll("[data-time]").forEach((button) => {{
      button.addEventListener("click", () => {{
        video.currentTime = Number(button.dataset.time);
        video.play();
        window.scrollTo({{top: 0, behavior: "smooth"}});
      }});
    }});
    async function copyText(text) {{
      if (!text) return;
      try {{
        await navigator.clipboard.writeText(text);
      }} catch (_error) {{
        const area = document.createElement("textarea");
        area.value = text;
        area.style.position = "fixed";
        area.style.opacity = "0";
        document.body.appendChild(area);
        area.select();
        document.execCommand("copy");
        area.remove();
      }}
    }}
    document.querySelectorAll(".copy-note").forEach((button) => {{
      button.addEventListener("click", () => {{
        const article = button.closest(".learning-note");
        const timestamp = article?.querySelector(".seek")?.textContent?.trim() || "";
        copyText(`[USER LEARNING NOTE — ${{timestamp.replace("▶", "").trim()}}] ${{button.dataset.copy || ""}}`);
      }});
    }});
    document.getElementById("copy-transcript").addEventListener(
      "click", () => copyText(transcriptText)
    );
    document.getElementById("copy-transcript-notes").addEventListener(
      "click", () => copyText(transcriptAndNotesText)
    );
    function closeLightbox() {{
      lightbox.hidden = true;
      lightboxImage.src = "";
      lightboxImage.alt = "";
      document.body.classList.remove("lightbox-open");
    }}
    document.querySelectorAll(".expand").forEach((button) => {{
      button.addEventListener("click", (event) => {{
        event.stopPropagation();
        lightboxImage.src = button.dataset.image;
        lightboxImage.alt = button.dataset.label || "Expanded anatomy capture";
        lightbox.hidden = false;
        document.body.classList.add("lightbox-open");
        lightbox.querySelector(".close").focus();
      }});
    }});
    lightbox.addEventListener("click", closeLightbox);
    document.addEventListener("keydown", (event) => {{
      if (event.key === "Escape" && !lightbox.hidden) closeLightbox();
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
