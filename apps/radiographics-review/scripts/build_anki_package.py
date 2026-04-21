from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path

import genanki


def resolve_model_id() -> int:
    candidate = os.environ.get("SACLOZE_PLUSPLUS_MODEL_ID", "1761198205290")
    try:
        value = int(candidate)
    except ValueError as error:
        raise ValueError(f"Invalid SACLOZE_PLUSPLUS_MODEL_ID: {candidate}") from error
    if value <= 0:
        raise ValueError("SACLOZE_PLUSPLUS_MODEL_ID must be a positive integer.")
    return value


SACLOZE_PLUSPLUS_FRONT_TEMPLATE = """<div id="kard">

<div class="tbar" data-seconds="12" role="timer" aria-label="Front timer">
  <div class="ttrack"><div class="tfill"></div></div>
  <span class="tleft">00:12</span>
</div>

<div class="tags">{{Tags}}</div>
{{edit:cloze:Text}}
</div>

<script>
(function(){
  function isIOSClient(){
    var htmlCls = (document.documentElement && document.documentElement.className) || "";
    var bodyCls = (document.body && document.body.className) || "";
    var cls = (htmlCls + " " + bodyCls).toLowerCase();
    return /\\biphone\\b|\\bipad\\b/.test(cls);
  }

  if (!isIOSClient()) return;

  function colorFor(p){
    var hStart = 170, hEnd = 0, h = hEnd + (hStart - hEnd) * p;
    return "hsl(" + h + ",95%,55%)";
  }
  function pad2(n){ return (n<10 ? "0" : "") + n; }

  function startTimerOn(el){
    if (!el || el.hasAttribute("data-bar-started")) return;
    el.setAttribute("data-bar-started","1");

    var secs = parseFloat(el.getAttribute("data-seconds") || "12");
    if (!(secs > 0)) secs = 1;

    var fill = el.querySelector(".tfill");
    var txt = el.querySelector(".tleft");
    if (!fill || !txt) return;

    var durMs = secs * 1000;
    var start = performance.now();

    function tick(t){
      var left = Math.max(0, durMs - (t - start));
      var frac = left / durMs;

      fill.style.width = (frac * 100).toFixed(3) + "%";
      fill.style.background = colorFor(frac);

      var s = Math.ceil(left / 1000);
      var mm = Math.floor(s / 60);
      var ss = s % 60;
      txt.textContent = mm ? (mm + ":" + pad2(ss)) : (s + "s");

      if (left > 0) {
        requestAnimationFrame(tick);
      } else {
        el.classList.add("done");
      }
    }

    requestAnimationFrame(tick);
  }

  function scanAndStart(){
    var bars = document.querySelectorAll(".tbar");
    for (var i = 0; i < bars.length; i++) startTimerOn(bars[i]);
  }

  scanAndStart();

  var mo = new MutationObserver(function(){
    scanAndStart();
  });

  if (document.body){
    mo.observe(document.body, { childList: true, subtree: true });
  } else {
    document.addEventListener("DOMContentLoaded", function(){
      mo.observe(document.body, { childList: true, subtree: true });
      scanAndStart();
    });
  }
})();
</script>

<br>

{{edit:tts en_US voices=Apple_Evan_(Enhanced) speed=1.1:cloze:Text}}
"""


SACLOZE_PLUSPLUS_BACK_TEMPLATE = """<div id="kard">

<div class="tbar" data-seconds="12" role="timer" aria-label="Front timer">
  <div class="ttrack"><div class="tfill"></div></div>
  <span class="tleft">00:12</span>
</div>

<div class="tags" id='tags'>{{Tags}}</div>
{{edit:cloze:Text}}
<div>&nbsp;</div>
<div id='extra'>{{edit:Extra}}</div>

</div>

<script>
(function(){
  function isIOSClient(){
    var htmlCls = (document.documentElement && document.documentElement.className) || "";
    var bodyCls = (document.body && document.body.className) || "";
    var cls = (htmlCls + " " + bodyCls).toLowerCase();
    return /\\biphone\\b|\\bipad\\b/.test(cls);
  }

  if (!isIOSClient()) return;

  function colorFor(p){
    var hStart = 170, hEnd = 0, h = hEnd + (hStart - hEnd) * p;
    return "hsl(" + h + ",95%,55%)";
  }

  function pad2(n){ return (n<10 ? "0" : "") + n; }

  function startTimerOn(el){
    if (!el || el.hasAttribute("data-bar-started")) return;
    el.setAttribute("data-bar-started","1");

    var secs = parseFloat(el.getAttribute("data-seconds") || "12");
    if (!(secs > 0)) secs = 1;

    var fill = el.querySelector(".tfill");
    var txt = el.querySelector(".tleft");
    if (!fill || !txt) return;

    var durMs = secs * 1000;
    var start = performance.now();

    function tick(t){
      var left = Math.max(0, durMs - (t - start));
      var frac = left / durMs;

      fill.style.width = (frac * 100).toFixed(3) + "%";
      fill.style.background = colorFor(frac);

      var s = Math.ceil(left / 1000);
      var mm = Math.floor(s / 60);
      var ss = s % 60;
      txt.textContent = mm ? (mm + ":" + pad2(ss)) : (s + "s");

      if (left > 0) {
        requestAnimationFrame(tick);
      } else {
        el.classList.add("done");
      }
    }

    requestAnimationFrame(tick);
  }

  function scanAndStart(){
    var bars = document.querySelectorAll(".tbar");
    for (var i = 0; i < bars.length; i++) startTimerOn(bars[i]);
  }

  scanAndStart();

  var mo = new MutationObserver(function(){
    scanAndStart();
  });

  if (document.body){
    mo.observe(document.body, { childList: true, subtree: true });
  } else {
    document.addEventListener("DOMContentLoaded", function(){
      mo.observe(document.body, { childList: true, subtree: true });
      scanAndStart();
    });
  }
})();
</script>

<br>

{{edit:tts en_US voices=Apple_Evan_(Enhanced) speed=1.1:cloze-only:Text}}
"""


SACLOZE_PLUSPLUS_CSS = """html { overflow: scroll; overflow-x: hidden; }

#kard {
padding: 0px 0px;
background-color:;
max-width: 700px;
margin: 0 auto;
word-wrap: break-word;
background-color: ;
}

.card {
font-family: helvetica;
font-size: 20px;
text-align: center;
color: #D7DEE9;
line-height: 1.6em;
background-color: #2F2F31;
}

.cloze, .cloze b, .cloze u, .cloze i { font-weight: bold; color: MediumSeaGreen !important;}

.tbar {
  display: none;
}

.iphone .tbar,
.ipad .tbar {
  display: grid;
}

.tbar{
  position: sticky; top: 0; z-index: 1;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  column-gap: 8px;
  padding: 6px 8px; margin: 0 0 12px 0;
  background: rgba(16,24,40,.25); border: 1px solid rgba(34,50,77,.65);
  border-radius: 12px; backdrop-filter: blur(6px);
}
.ttrack{
  min-width: 0;
  height: 8px; border-radius: 999px;
  background: #102035; border: 1px solid #22324d; overflow: hidden;
}
.tfill{
  height: 100%; width: 100%; background: #27d3ff;
  transform-origin: left center;
}
.tleft{
  display: inline-flex;
  align-items: center;
  font-size: 12px; color: #A6ABB9; line-height: 1;
  white-space: nowrap; font-variant-numeric: tabular-nums;
  min-width: 52px; text-align: right;
}
.tbar.done .tleft{ color:#CC5B5B }

.tags{ pointer-events: none; }

#extra, #extra i { font-size: 15px; color:#D7DEE9; font-style: italic; }

#list { color: #A6ABB9; font-size: 10px; width: 100%; text-align: center; }

.tags { color: #A6ABB9; opacity: 0; font-size: 10px; background-color: ; width: 100%; height: ; text-align: center; text-transform: uppercase; position: fixed; padding: 0px; top:0;  right: 0;}

img { display: block; max-width: 100%; max-height: none; margin-left: auto; margin: 10px auto 10px auto;}
img:active { width: 100%; }
tr {font-size: 12px; }

b { color: #C695C6 !important; }
u { text-decoration: none; color: #5EB3B3;}
i  { color: IndianRed; }
a { color: LightBlue !important; text-decoration: none; font-size: 14px; font-style: normal;  }

::-webkit-scrollbar {
    background: #fff;
    width: 0px; }
::-webkit-scrollbar-thumb { background: #bbb; }

.mobile .card { color: #D7DEE9; background-color: #2F2F31; }
.iphone .card img {max-width: 100%; max-height: none;}
.mobile .card img:active { width: inherit; max-height: none;}
"""


MODEL = genanki.Model(
    resolve_model_id(),
    "saCloze++",
    fields=[
        {"name": "Text"},
        {"name": "Extra"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": SACLOZE_PLUSPLUS_FRONT_TEMPLATE,
            "afmt": SACLOZE_PLUSPLUS_BACK_TEMPLATE,
        }
    ],
    css=SACLOZE_PLUSPLUS_CSS,
    model_type=genanki.Model.CLOZE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an Anki package for one RadioGraphics article.")
    parser.add_argument("--article-json", type=Path, required=True)
    parser.add_argument("--notes-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def stable_int(value: str, digits: int = 9) -> int:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return (int(digest[:digits], 16) % 2_000_000_000) + 1_000_000


def escape_text(text: str) -> str:
    return html.escape(text or "", quote=True)


def build_key_fact_list(article: dict) -> str:
    summary_sections = article.get("summarySections") or []
    if summary_sections:
        return "".join(
            f"<li><b>{escape_text(section.get('label', 'Key point'))}</b> {escape_text(section.get('text', ''))}</li>"
            for section in summary_sections[:5]
        )

    return "".join(f"<li>{escape_text(fact)}</li>" for fact in article.get("keyFacts", [])[:5])


def build_figure_appendix(article: dict) -> str:
    parts: list[str] = []
    for figure in article.get("figures", []):
        image_name = figure.get("localImageName")
        if image_name:
            parts.append(f"<div><b>{escape_text(figure.get('label', 'Figure'))}</b></div>")
            parts.append(f"<img src=\"{escape_text(image_name)}\">")
        if figure.get("caption"):
            parts.append(f"<div class='figure-caption'>{escape_text(figure['caption'])}</div>")
        parts.append("<hr>")

    return "".join(parts)


def extra_html(article: dict) -> str:
    facts = build_key_fact_list(article)
    metadata_bits = [
        article.get("journal") or "RadioGraphics",
        article.get("publishedAt", "")[:10] if article.get("publishedAt") else "",
        f"Vol {article['volume']}" if article.get("volume") else "",
        f"Issue {article['issue']}" if article.get("issue") else "",
    ]
    metadata = " | ".join(bit for bit in metadata_bits if bit)
    parts = [
        f"<div><b>{escape_text(article.get('title', 'Untitled article'))}</b></div>",
        f"<div>{escape_text(metadata)}</div>" if metadata else "",
        "<hr>",
        f"<div><b>Key facts</b><ul>{facts}</ul></div>",
        (
            f"<div class='source'><a href=\"{escape_text(article.get('link', ''))}\">Open article</a>"
            f" &middot; DOI: {escape_text(article.get('doi', ''))}</div>"
        ),
        "<hr>",
        "<div><b>All article figures</b></div>",
        build_figure_appendix(article),
    ]
    return "".join(part for part in parts if part)


def validate_note_definitions(note_defs: list[dict]) -> None:
    for note in note_defs:
        if not isinstance(note, dict):
            raise ValueError("Each note must be an object.")
        keys = set(note.keys())
        if not keys.issubset({"content", "html", "tags", "id"}):
            raise ValueError(f"Invalid note keys: {keys}")
        has_content = "content" in note
        has_html = "html" in note
        if (1 if has_content else 0) + (1 if has_html else 0) != 1:
            raise ValueError("Each note must have exactly one of content or html.")
        if not isinstance(note.get("tags"), list) or len(note["tags"]) != 1:
            raise ValueError("Each note must have exactly one batch tag.")


def build_notes(article: dict, note_defs: list[dict]) -> tuple[list[genanki.Note], list[str]]:
    validate_note_definitions(note_defs)

    extra = extra_html(article)
    notes: list[genanki.Note] = []
    media_files: list[str] = [
        figure["localImagePath"]
        for figure in article.get("figures", [])
        if figure.get("localImagePath")
    ]

    for index, note_def in enumerate(note_defs):
        text = note_def.get("content") or note_def.get("html") or ""
        note = genanki.Note(
            model=MODEL,
            fields=[text, extra],
            guid=genanki.guid_for(article["doi"], note_def.get("id", f"note-{index + 1:03d}")),
            tags=note_def.get("tags", []),
        )
        notes.append(note)

    return notes, sorted(set(media_files))


def main() -> int:
    args = parse_args()
    article = json.loads(args.article_json.read_text(encoding="utf-8"))
    note_defs = json.loads(args.notes_json.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)

    deck = genanki.Deck(
        stable_int(article["doi"]),
        f"Radiographics::{article['title'][:90]}",
    )
    notes, media_files = build_notes(article, note_defs)
    for note in notes:
        deck.add_note(note)

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(args.output)

    print(str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
