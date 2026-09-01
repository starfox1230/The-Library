from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
import re
from typing import Any, Iterable


SCHEMA_VERSION = 2
PUBLISH_FORMAT_VERSION = 3
_ANSWER_SEPARATOR_RE = re.compile(
    r"<hr\b[^>]*\bid\s*=\s*(?:[\"']answer[\"']|answer)[^>]*>",
    flags=re.IGNORECASE,
)
_SCRIPT_RE = re.compile(
    r"<script\b[^>]*>.*?</script\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)
_AUDIO_ELEMENT_RE = re.compile(
    r"<(audio|video)\b[^>]*>.*?</\1\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)
_PLAY_ELEMENT_RE = re.compile(
    r"<(?:button|a)\b[^>]*(?:replay-button|replaybutton|soundLink|playsound:)[^>]*>.*?</(?:button|a)\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)
_ANKI_PLAY_RE = re.compile(r"\[(?:anki:play:[^\]]+|sound:[^\]]+)\]", flags=re.IGNORECASE)


class _TextParser(HTMLParser):
    BLOCKS = {
        "address", "article", "aside", "blockquote", "br", "div", "figcaption",
        "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header",
        "hr", "li", "main", "ol", "p", "pre", "section", "table", "td", "th",
        "tr", "ul",
    }
    VOID_ELEMENTS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_elements: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.casefold()
        attributes = {name.casefold(): str(value or "") for name, value in attrs}
        classes = {item.casefold() for item in attributes.get("class", "").split()}
        is_tag_metadata = (
            attributes.get("id", "").casefold() == "tags"
            or bool(classes.intersection({"tags", "tag-container", "tagcontainer"}))
        )
        if self._ignored_elements:
            if normalized not in self.VOID_ELEMENTS:
                self._ignored_elements.append(normalized)
            return
        if normalized in {"script", "style"} or is_tag_metadata:
            if normalized not in self.VOID_ELEMENTS:
                self._ignored_elements.append(normalized)
            return
        if normalized in self.BLOCKS:
            self.parts.append("\n")
        if normalized == "li":
            self.parts.append("- ")

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.casefold()
        if self._ignored_elements:
            if normalized == self._ignored_elements[-1]:
                self._ignored_elements.pop()
            return
        if normalized in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored_elements:
            self.parts.append(data)


def _clean_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def answer_side_only(value: str) -> str:
    text = str(value or "")
    match = _ANSWER_SEPARATOR_RE.search(text)
    return text[match.end() :] if match else text


def sanitize_card_html(value: str) -> str:
    text = str(value or "")
    # Keep each note type's CSS so the web card matches its Anki rendering.
    # Executable scripts and audio controls are unnecessary on this read-only page.
    text = _SCRIPT_RE.sub("", text)
    text = _AUDIO_ELEMENT_RE.sub("", text)
    text = _PLAY_ELEMENT_RE.sub("", text)
    text = _ANKI_PLAY_RE.sub("", text)
    return text.strip()


def html_to_text(value: str) -> str:
    parser = _TextParser()
    parser.feed(str(value or ""))
    parser.close()
    text = unescape("".join(parser.parts)).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _canonical_cards(cards: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for card in cards:
        front_html = sanitize_card_html(str(card.get("front_html", "") or ""))
        back_html = sanitize_card_html(answer_side_only(str(card.get("back_html", "") or "")))
        normalized.append(
            {
                "card_id": int(card.get("card_id", 0) or 0),
                "note_id": int(card.get("note_id", 0) or 0),
                "flagged_at": str(card.get("flagged_at", "") or ""),
                "last_seen_at": str(card.get("last_seen_at", "") or ""),
                "deck": str(card.get("deck", "") or ""),
                "note_type": str(card.get("note_type", "") or ""),
                "tags": [str(tag) for tag in card.get("tags", []) or []],
                "fields": {
                    str(name): str(value or "")
                    for name, value in dict(card.get("fields", {}) or {}).items()
                },
                "front_html": front_html,
                "back_html": back_html,
                "front_text": html_to_text(front_html)
                or str(card.get("front_text", "") or "").strip(),
                "back_text": html_to_text(back_html)
                or str(card.get("back_text", "") or "").strip(),
                "media": sorted(str(item) for item in card.get("media", []) or []),
                "tracked_by_speed_streak": bool(card.get("tracked_by_speed_streak", True)),
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
        "publish_format_version": PUBLISH_FORMAT_VERSION,
        "source_addon": str(source_addon),
        "review_later_flag": int(review_later_flag),
        "standing_instructions": str(standing_instructions).strip(),
        "cards": _canonical_cards(cards),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def cards_markdown(cards: Iterable[dict[str, Any]], updated_at: str) -> str:
    cards_list = _canonical_cards(cards)
    lines = [
        "# Anki Speed Streak — Review Later",
        "",
        f"Updated: {updated_at}",
        f"Cards: {len(cards_list)}",
    ]
    if not cards_list:
        lines.extend(["", "No currently blue cards were seen in this period."])
        return "\n".join(lines).rstrip() + "\n"

    for index, card in enumerate(cards_list, start=1):
        lines.extend(
            [
                "",
                f"## Card {index}",
                "",
                f"Deck: {_clean_text(card['deck'], 'Unknown Deck')}",
                f"Flagged: {_clean_text(card['flagged_at'], 'Unknown')}",
                f"Last seen: {_clean_text(card['last_seen_at'], 'Unknown')}",
                f"Card ID: {card['card_id']}",
                f"Note ID: {card['note_id']}",
                "",
                "Question:",
                _clean_text(card["front_text"], "(empty)"),
                "",
                "Answer:",
                _clean_text(card["back_text"], "(empty)"),
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def chat_markdown(standing_instructions: str, cards_only_markdown: str) -> str:
    return (
        "# Standing instructions\n\n"
        f"{str(standing_instructions).strip()}\n\n"
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
        "publish_format_version": PUBLISH_FORMAT_VERSION,
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


_PAGE_TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#0b1020">
  <title>Anki Review Later</title>
  <style>
    :root { color-scheme:dark; --bg:#090e1c; --panel:#141b2d; --line:rgba(142,169,235,.18); --text:#f5f7ff; --muted:#96a7ca; --blue:#6288ff; --green:#45d7a1; }
    * { box-sizing:border-box; }
    html { scroll-behavior:smooth; scroll-padding-top:78px; }
    body { margin:0; min-height:100%; background:radial-gradient(circle at 50% -20%,#172342 0,transparent 42%),var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    button,select,input { font:inherit; }
    .toolbar { position:sticky; top:0; z-index:20; padding:max(5px,env(safe-area-inset-top)) max(8px,env(safe-area-inset-right)) 5px max(8px,env(safe-area-inset-left)); background:rgba(9,14,28,.94); border-bottom:1px solid var(--line); backdrop-filter:blur(15px); }
    .controls { width:min(100%,980px); margin:auto; display:flex; align-items:center; gap:5px; min-height:36px; }
    .brand { font-size:12px; font-weight:800; letter-spacing:.02em; white-space:nowrap; margin-right:auto; }
    select,input,button { height:32px; border:1px solid var(--line); border-radius:8px; padding:0 8px; background:#1b253b; color:var(--text); font-size:12px; }
    select { max-width:112px; }
    input[type=date] { width:124px; }
    button { font-weight:750; cursor:pointer; touch-action:manipulation; white-space:nowrap; }
    button.primary { background:#4f73e8; border-color:#7190ef; }
    button.secondary { background:#202b43; }
    .summary { width:min(100%,980px); height:18px; margin:1px auto 0; color:var(--muted); font-size:10.5px; display:flex; gap:8px; align-items:center; overflow:hidden; white-space:nowrap; }
    #status { color:var(--green); margin-left:auto; }
    .shell { width:min(100%,980px); margin:auto; padding:12px max(10px,env(safe-area-inset-right)) 42px max(10px,env(safe-area-inset-left)); }
    .entries { display:grid; gap:14px; }
    .entry { border:1px solid var(--line); border-radius:17px; padding:11px; background:linear-gradient(180deg,rgba(27,38,64,.95),rgba(14,21,38,.97)); box-shadow:0 14px 35px rgba(0,0,0,.25); overflow:hidden; }
    .entry-head { display:grid; grid-template-columns:minmax(0,1fr) auto; align-items:start; gap:8px; margin:0 2px 9px; }
    .deck { font-size:13px; font-weight:780; overflow-wrap:anywhere; }
    .number { color:#91a7d9; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.08em; }
    .times { color:var(--muted); text-align:right; font-size:10px; line-height:1.35; white-space:nowrap; }
    .stage { position:relative; height:auto; border:1px solid rgba(255,255,255,.075); border-radius:14px; background:linear-gradient(180deg,#090e1a,#111827); overflow:hidden; cursor:pointer; outline:none; transition:height .22s ease; }
    .stage:focus-visible { box-shadow:0 0 0 2px var(--blue); }
    .side { position:relative; padding:13px 12px 38px; overflow:visible; opacity:0; transform:translateY(6px); transition:opacity .18s ease,transform .22s ease; }
    .side[hidden] { display:none; }
    .side.active { opacity:1; transform:none; }
    .face-label { position:static; margin:-13px -12px 10px; padding:7px 12px; background:rgba(9,14,26,.9); color:#8fa6db; font-size:10px; font-weight:850; letter-spacing:.11em; text-transform:uppercase; }
    .card-preview { overflow-wrap:anywhere; }
    .card-preview img { display:block; max-width:100%; width:auto; height:auto; margin:10px auto; border-radius:8px; }
    .card-preview table { display:block; max-width:100%; overflow:auto; }
    .card-preview script,.card-preview style,.card-preview audio,.card-preview video,.card-preview [role="timer"],.card-preview .tbar,.card-preview .tags,.card-preview #tags,.card-preview .tag-container,.card-preview .tagcontainer,.replay-button,.replaybutton,.soundLink,[href^="playsound:"] { display:none!important; }
    .flip-hint { position:absolute; z-index:3; left:50%; bottom:7px; transform:translateX(-50%); border-radius:999px; padding:5px 10px; background:rgba(28,39,65,.92); color:#b9c8eb; font-size:10px; pointer-events:none; box-shadow:0 2px 12px rgba(0,0,0,.25); }
    .empty { padding:50px 18px; border:1px solid var(--line); border-radius:16px; color:var(--muted); text-align:center; background:var(--panel); }
    @media (max-width:620px) {
      html { scroll-padding-top:82px; }
      .controls { gap:4px; }
      .brand { width:18px; overflow:hidden; color:transparent; position:relative; }
      .brand::after { content:"RL"; color:var(--text); position:absolute; left:0; }
      select,input,button { height:30px; padding:0 6px; font-size:11px; border-radius:7px; }
      select { max-width:94px; }
      input[type=date] { width:113px; }
      .entry { padding:9px; border-radius:14px; }
    }
    @media (prefers-reduced-motion:reduce) { * { scroll-behavior:auto!important; transition:none!important; } }
  </style>
</head>
<body>
  <header class="toolbar">
    <div class="controls">
      <div class="brand">Review Later</div>
      <select id="period" aria-label="Date period">
        <option value="1">Today</option><option value="2">2 days</option><option value="3">3 days</option>
        <option value="7">7 days</option><option value="14">14 days</option><option value="30">30 days</option>
        <option value="date">On date…</option>
      </select>
      <input id="date" type="date" aria-label="Review date" hidden>
      <select id="sort" aria-label="Sort cards"><option value="seen">Seen ↓</option><option value="flagged">Flagged ↓</option></select>
      <button class="primary" type="button" id="copyChat" title="Copy standing conversation instructions and the visible cards">ChatGPT</button>
      <button class="secondary" type="button" id="copyCards" title="Copy only the visible cards, without standing instructions">Cards</button>
    </div>
    <div class="summary"><span id="count"></span><span>Updated __UPDATED_TEXT__</span><span id="status" role="status" aria-live="polite"></span></div>
  </header>
  <main class="shell"><section class="entries" id="entries"></section></main>
  <script>
    const MODEL = __MODEL_JSON__;
    const STORAGE_KEY = 'anki-review-later-view-v2';
    const entries = document.getElementById('entries');
    const period = document.getElementById('period');
    const dateInput = document.getElementById('date');
    const sort = document.getElementById('sort');
    const count = document.getElementById('count');
    const status = document.getElementById('status');
    const DAY = 86400000;

    function localDay(date) { return new Date(date.getFullYear(), date.getMonth(), date.getDate()); }
    function addDays(date, days) { const result = new Date(date); result.setDate(result.getDate() + days); return result; }
    function dateValue(date) { const y=date.getFullYear(),m=String(date.getMonth()+1).padStart(2,'0'),d=String(date.getDate()).padStart(2,'0'); return `${y}-${m}-${d}`; }
    function parseDate(value) { const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? null : parsed; }
    function esc(value) { const node=document.createElement('div'); node.textContent=String(value??''); return node.innerHTML; }
    function pretty(value) { const parsed=parseDate(value); return parsed ? parsed.toLocaleString([], {month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}) : 'Unknown'; }
    function loadSettings() { try { return {...{mode:'range',days:1,dateOffset:0,sort:'seen'},...JSON.parse(localStorage.getItem(STORAGE_KEY)||'{}')}; } catch (_) { return {mode:'range',days:1,dateOffset:0,sort:'seen'}; } }
    let settings = loadSettings();
    function saveSettings() { localStorage.setItem(STORAGE_KEY, JSON.stringify(settings)); }
    function applySettings() {
      period.value = settings.mode === 'date' ? 'date' : String(settings.days || 1);
      dateInput.hidden = settings.mode !== 'date';
      dateInput.value = dateValue(addDays(localDay(new Date()), Number(settings.dateOffset)||0));
      sort.value = settings.sort === 'flagged' ? 'flagged' : 'seen';
    }
    function visibleCards() {
      const today=localDay(new Date());
      const filtered=MODEL.cards.filter(card => {
        const seen=parseDate(card.last_seen_at); if (!seen) return false;
        const seenDay=localDay(seen);
        if (settings.mode === 'date') return seenDay.getTime() === addDays(today, Number(settings.dateOffset)||0).getTime();
        const start=addDays(today, -(Math.max(1,Number(settings.days)||1)-1));
        return seenDay >= start && seenDay <= today;
      });
      const key=settings.sort === 'flagged' ? 'flagged_at' : 'last_seen_at';
      return filtered.sort((a,b)=>(parseDate(b[key])?.getTime()||0)-(parseDate(a[key])?.getTime()||0));
    }
    function cardHtml(card,index) {
      return `<article class="entry" data-card-id="${card.card_id}">
        <header class="entry-head"><div><div class="number">Card ${index+1}</div><div class="deck">${esc(card.deck||'Unknown Deck')}</div></div>
        <div class="times">Seen ${esc(pretty(card.last_seen_at))}<br>Flagged ${esc(pretty(card.flagged_at))}</div></header>
        <div class="stage" tabindex="0" role="button" aria-label="Show answer" aria-pressed="false">
          <section class="side front active"><div class="face-label">Question</div><div class="card-preview card">${card.front_html||'<em>(empty)</em>'}</div></section>
          <section class="side back" hidden><div class="face-label">Answer</div><div class="card-preview card">${card.back_html||'<em>(empty)</em>'}</div></section>
          <div class="flip-hint">Question · tap for answer</div></div></article>`;
    }
    function toggle(stage) {
      const front=stage.querySelector('.front'),back=stage.querySelector('.back');
      const showingAnswer=back.classList.contains('active');
      const current=showingAnswer?back:front,next=showingAnswer?front:back;
      const startHeight=stage.getBoundingClientRect().height;
      stage.style.height=`${startHeight}px`;
      current.classList.remove('active'); current.hidden=true;
      next.hidden=false; next.classList.add('active');
      const targetHeight=next.getBoundingClientRect().height;
      requestAnimationFrame(()=>requestAnimationFrame(()=>{ stage.style.height=`${targetHeight}px`; }));
      const release=()=>{ stage.style.height='auto'; };
      stage.addEventListener('transitionend',release,{once:true});
      window.setTimeout(release,280);
      stage.setAttribute('aria-pressed',String(!showingAnswer)); stage.setAttribute('aria-label',showingAnswer?'Show answer':'Show question');
      stage.querySelector('.flip-hint').textContent=showingAnswer?'Question · tap for answer':'Answer · tap for question';
    }
    function render() {
      const cards=visibleCards(); count.textContent=`${cards.length} card${cards.length===1?'':'s'}`;
      entries.innerHTML=cards.length ? cards.map(cardHtml).join('') : '<div class="empty">No currently blue cards were seen in this period.</div>';
      entries.querySelectorAll('.stage').forEach(stage => {
        stage.addEventListener('click',event=>{ if (!event.target.closest('a,button,input,select,textarea')) toggle(stage); });
        stage.addEventListener('keydown',event=>{ if (event.key==='Enter'||event.key===' ') { event.preventDefault(); toggle(stage); } });
      });
    }
    function cardsMarkdown(cards) {
      const lines=['# Anki Speed Streak — Review Later','',`Cards: ${cards.length}`];
      if (!cards.length) return lines.concat(['','No currently blue cards were seen in this period.']).join('\n')+'\n';
      cards.forEach((card,index)=>lines.push('',`## Card ${index+1}`,'',`Deck: ${card.deck||'Unknown Deck'}`,`Flagged: ${card.flagged_at||'Unknown'}`,`Last seen: ${card.last_seen_at||'Unknown'}`,`Card ID: ${card.card_id}`,`Note ID: ${card.note_id}`,'','Question:',card.front_text||'(empty)','','Answer:',card.back_text||'(empty)'));
      return lines.join('\n')+'\n';
    }
    async function copyText(text) {
      if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
      const area=document.createElement('textarea'); area.value=text; area.readOnly=true; area.style.cssText='position:fixed;opacity:0'; document.body.appendChild(area); area.select();
      if (!document.execCommand('copy')) throw new Error('copy unavailable'); area.remove();
    }
    async function copy(kind,button) {
      const cards=visibleCards(),body=cardsMarkdown(cards); const payload=kind==='chat'?`# Standing instructions\n\n${MODEL.instructions.trim()}\n\n---\n\n${body}`:body;
      try { await copyText(payload); status.textContent=`Copied ${cards.length} visible card${cards.length===1?'':'s'}`; button.textContent='Copied'; }
      catch (_) { status.textContent='Copy blocked'; }
      setTimeout(()=>{ button.textContent=kind==='chat'?'ChatGPT':'Cards'; status.textContent=''; },1600);
    }
    period.addEventListener('change',()=>{ if(period.value==='date'){settings.mode='date';}else{settings.mode='range';settings.days=Number(period.value);} applySettings();saveSettings();render(); });
    dateInput.addEventListener('change',()=>{ const chosen=new Date(`${dateInput.value}T12:00:00`); settings.dateOffset=Math.round((localDay(chosen)-localDay(new Date()))/DAY);saveSettings();render(); });
    sort.addEventListener('change',()=>{ settings.sort=sort.value;saveSettings();render(); });
    document.getElementById('copyChat').addEventListener('click',event=>copy('chat',event.currentTarget));
    document.getElementById('copyCards').addEventListener('click',event=>copy('cards',event.currentTarget));
    applySettings(); render();
  </script>
</body>
</html>'''


def page_html(
    cards: Iterable[dict[str, Any]],
    *,
    updated_at: str,
    standing_instructions: str,
) -> str:
    model = {
        "cards": _canonical_cards(cards),
        "instructions": str(standing_instructions).strip(),
    }
    model_json = json.dumps(model, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (
        _PAGE_TEMPLATE.replace("__UPDATED_TEXT__", str(updated_at))
        .replace("__MODEL_JSON__", model_json)
    )


def display_timestamp(now: datetime | None = None) -> str:
    value = now or datetime.now().astimezone()
    if value.tzinfo is None:
        value = value.astimezone()
    return value.strftime("%Y-%m-%d %H:%M %Z")
