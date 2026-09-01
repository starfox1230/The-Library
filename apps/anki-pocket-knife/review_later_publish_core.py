from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from html import escape
import json
from typing import Any, Iterable


SCHEMA_VERSION = 1


def _clean_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _canonical_cards(cards: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for card in cards:
        normalized.append(
            {
                "card_id": int(card.get("card_id", 0) or 0),
                "note_id": int(card.get("note_id", 0) or 0),
                "flagged_at": str(card.get("flagged_at", "") or ""),
                "deck": str(card.get("deck", "") or ""),
                "note_type": str(card.get("note_type", "") or ""),
                "tags": [str(tag) for tag in card.get("tags", []) or []],
                "fields": {
                    str(name): str(value or "")
                    for name, value in dict(card.get("fields", {}) or {}).items()
                },
                "front_html": str(card.get("front_html", "") or ""),
                "back_html": str(card.get("back_html", "") or ""),
                "front_text": str(card.get("front_text", "") or ""),
                "back_text": str(card.get("back_text", "") or ""),
                "media": sorted(str(item) for item in card.get("media", []) or []),
            }
        )
    return normalized


def content_hash(
    cards: Iterable[dict[str, Any]],
    standing_instructions: str,
    *,
    source_addon: str,
    review_later_flag: int,
) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source_addon": str(source_addon),
        "review_later_flag": int(review_later_flag),
        "standing_instructions": str(standing_instructions).strip(),
        "cards": _canonical_cards(cards),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def cards_markdown(cards: Iterable[dict[str, Any]], updated_at: str) -> str:
    cards_list = list(cards)
    lines = [
        "# Anki Speed Streak — Review Later",
        "",
        f"Updated: {updated_at}",
        f"Cards: {len(cards_list)}",
    ]
    if not cards_list:
        lines.extend(["", "No cards are currently flagged for Review Later."])
        return "\n".join(lines).rstrip() + "\n"

    for index, card in enumerate(cards_list, start=1):
        tags = ", ".join(str(tag) for tag in card.get("tags", []) or []) or "None"
        lines.extend(
            [
                "",
                f"## Card {index}",
                "",
                f"Deck: {_clean_text(card.get('deck'), 'Unknown Deck')}",
                f"Tags: {tags}",
                f"Flagged: {_clean_text(card.get('flagged_at'), 'Unknown')}",
                f"Card ID: {int(card.get('card_id', 0) or 0)}",
                f"Note ID: {int(card.get('note_id', 0) or 0)}",
                "",
                "Question:",
                _clean_text(card.get("front_text"), "(empty)"),
                "",
                "Answer:",
                _clean_text(card.get("back_text"), "(empty)"),
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def chat_markdown(standing_instructions: str, cards_only_markdown: str) -> str:
    instructions = str(standing_instructions).strip()
    return (
        "# Standing instructions\n\n"
        f"{instructions}\n\n"
        "---\n\n"
        f"{cards_only_markdown.strip()}\n"
    )


def data_document(
    cards: Iterable[dict[str, Any]],
    *,
    updated_at: str,
    digest: str,
    source_addon: str,
    review_later_flag: int,
) -> dict[str, Any]:
    cards_list = _canonical_cards(cards)
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": str(updated_at),
        "content_hash": str(digest),
        "source": {
            "addon": str(source_addon),
            "review_later_flag": int(review_later_flag),
        },
        "count": len(cards_list),
        "cards": cards_list,
    }


def data_json(document: dict[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _card_html(card: dict[str, Any], index: int) -> str:
    tags = card.get("tags", []) or []
    tags_html = "".join(f"<span>{escape(str(tag))}</span>" for tag in tags)
    if not tags_html:
        tags_html = "<span>No tags</span>"
    deck = escape(_clean_text(card.get("deck"), "Unknown Deck"))
    flagged = escape(_clean_text(card.get("flagged_at"), "Unknown"))
    front = str(card.get("front_html", "") or "<em>(empty)</em>")
    back = str(card.get("back_html", "") or "<em>(empty)</em>")
    return f"""
      <article class="entry">
        <div class="entry-head">
          <div>
            <div class="card-number">Card {index}</div>
            <h2>{deck}</h2>
          </div>
          <div class="flagged">Flagged {flagged}</div>
        </div>
        <div class="tags">{tags_html}</div>
        <section class="face">
          <div class="face-label">Question</div>
          <div class="card-preview">{front}</div>
        </section>
        <section class="face">
          <div class="face-label">Answer</div>
          <div class="card-preview">{back}</div>
        </section>
        <details class="ids"><summary>Card details</summary><div>Card ID {int(card.get('card_id', 0) or 0)} · Note ID {int(card.get('note_id', 0) or 0)}</div></details>
      </article>"""


def page_html(
    cards: Iterable[dict[str, Any]],
    *,
    updated_at: str,
    chat_payload: str,
    cards_payload: str,
) -> str:
    cards_list = list(cards)
    entries = "\n".join(_card_html(card, index) for index, card in enumerate(cards_list, 1))
    if not entries:
        entries = '<div class="empty">No cards are currently flagged for Review Later.</div>'
    chat_json = json.dumps(str(chat_payload), ensure_ascii=False).replace("</", "<\\/")
    cards_json = json.dumps(str(cards_payload), ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#111827">
  <title>Anki Review Later</title>
  <style>
    :root {{ color-scheme: dark; --bg:#0b1020; --panel:#151c2e; --panel2:#0e1527; --text:#f5f7ff; --muted:#9fb0d8; --blue:#4f7cff; --green:#34d399; }}
    * {{ box-sizing:border-box; }}
    html,body {{ margin:0; min-height:100%; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    body {{ padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left); }}
    .shell {{ width:min(960px,100%); margin:0 auto; padding:18px 14px 48px; }}
    .hero {{ position:sticky; top:0; z-index:10; margin:-18px -14px 16px; padding:18px 14px 14px; background:linear-gradient(180deg,rgba(11,16,32,.98) 78%,rgba(11,16,32,0)); backdrop-filter:blur(12px); }}
    h1 {{ margin:0; font-size:clamp(24px,7vw,38px); letter-spacing:-.03em; }}
    .summary {{ color:var(--muted); margin:7px 0 14px; font-size:14px; }}
    .actions {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; }}
    button {{ min-height:50px; border:0; border-radius:14px; padding:12px 16px; font:700 15px/1.15 inherit; cursor:pointer; touch-action:manipulation; }}
    .primary {{ background:linear-gradient(135deg,#3b82f6,#6558f5); color:white; box-shadow:0 10px 26px rgba(61,93,246,.28); }}
    .secondary {{ background:#263149; color:#e8edff; border:1px solid rgba(255,255,255,.09); }}
    .status {{ min-height:22px; margin-top:8px; color:var(--green); font-size:13px; }}
    .entries {{ display:grid; gap:16px; }}
    .entry {{ border:1px solid rgba(136,169,255,.16); border-radius:20px; padding:16px; background:radial-gradient(circle at top,rgba(71,117,255,.13),transparent 44%),linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.02)); box-shadow:0 14px 32px rgba(0,0,0,.24); overflow:hidden; }}
    .entry-head {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }}
    .card-number,.face-label {{ color:#8ea0cc; font-size:11px; font-weight:800; letter-spacing:.11em; text-transform:uppercase; }}
    h2 {{ margin:4px 0 0; font-size:17px; overflow-wrap:anywhere; }}
    .flagged {{ color:var(--muted); font-size:12px; text-align:right; }}
    .tags {{ display:flex; gap:6px; flex-wrap:wrap; margin:12px 0; }}
    .tags span {{ border-radius:999px; padding:5px 9px; background:rgba(79,124,255,.13); color:#cad7ff; font-size:11px; overflow-wrap:anywhere; }}
    .face {{ margin-top:10px; border-radius:16px; padding:13px; background:linear-gradient(180deg,rgba(8,12,22,.92),rgba(24,28,40,.94)); border:1px solid rgba(255,255,255,.07); }}
    .card-preview {{ margin-top:9px; line-height:1.55; overflow-wrap:anywhere; max-width:100%; }}
    .card-preview img {{ display:block; max-width:100%; height:auto; margin:10px auto; border-radius:10px; }}
    .card-preview table {{ max-width:100%; overflow:auto; display:block; }}
    .ids {{ margin-top:12px; color:#7888ae; font-size:11px; }}
    .ids summary {{ cursor:pointer; }}
    .empty {{ padding:36px 18px; border-radius:18px; text-align:center; color:var(--muted); background:var(--panel); }}
    @media (max-width:560px) {{ .actions {{ grid-template-columns:1fr; }} .hero {{ padding-bottom:10px; }} .entry {{ padding:13px; border-radius:17px; }} .entry-head {{ display:block; }} .flagged {{ margin-top:6px; text-align:left; }} }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="hero">
      <h1>Review Later</h1>
      <div class="summary">{len(cards_list)} active card{'s' if len(cards_list) != 1 else ''} · Updated {escape(updated_at)}</div>
      <div class="actions">
        <button class="primary" type="button" data-copy="chat">Copy for ChatGPT</button>
        <button class="secondary" type="button" data-copy="cards">Copy Cards Only</button>
      </div>
      <div class="status" role="status" aria-live="polite"></div>
    </header>
    <section class="entries">{entries}</section>
  </main>
  <script>
    const payloads = {{ chat: {chat_json}, cards: {cards_json} }};
    const status = document.querySelector('.status');
    async function copyText(text) {{
      if (navigator.clipboard && window.isSecureContext) {{ await navigator.clipboard.writeText(text); return; }}
      const area = document.createElement('textarea'); area.value = text; area.setAttribute('readonly',''); area.style.position='fixed'; area.style.opacity='0'; document.body.appendChild(area); area.select();
      if (!document.execCommand('copy')) throw new Error('Copy was not available');
      area.remove();
    }}
    document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {{
      const original = button.textContent;
      try {{ await copyText(payloads[button.dataset.copy]); button.textContent='Copied'; status.textContent = button.dataset.copy === 'chat' ? 'ChatGPT-ready prompt copied.' : 'Cards copied.'; }}
      catch (error) {{ button.textContent='Copy failed'; status.textContent='Your browser blocked clipboard access. Open chat.md as a fallback.'; }}
      window.setTimeout(() => {{ button.textContent=original; }}, 1800);
    }}));
  </script>
</body>
</html>
"""


def display_timestamp(now: datetime | None = None) -> str:
    value = now or datetime.now().astimezone()
    if value.tzinfo is None:
        value = value.astimezone()
    return value.strftime("%Y-%m-%d %H:%M %Z")
