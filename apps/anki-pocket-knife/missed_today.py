from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urlsplit

from aqt import mw
from aqt.qt import QApplication, QDesktopServices, QUrl
from aqt.utils import showInfo, showWarning

from .common import (
    card_id_search,
    collection_media_dir,
    create_or_update_filtered_deck,
    deck_name,
    get_card,
    note_fields,
    note_type_name,
    note_tags,
    user_files_dir,
)


MISSED_TODAY_DECK_NAME_PREFIX = "Pocket Knife Missed Today "


class _HtmlToTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "img":
            self.parts.append("[Image was here]")
            return
        if tag in {"br", "p", "div", "li"}:
            self.parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"} or self._skip_depth:
            return
        if tag == "img":
            self.parts.append("[Image was here]")
            return
        if tag in {"br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag in {"p", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self.parts.append(data)

    def get_text(self) -> str:
        text = "".join(self.parts)
        lines = [line.rstrip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line).strip()


def html_to_text(html: str) -> str:
    parser = _HtmlToTextParser()
    parser.feed(html or "")
    return parser.get_text()


class _MediaPathRewriter(HTMLParser):
    def __init__(self, media_dir: Path) -> None:
        super().__init__(convert_charrefs=False)
        self.media_dir = media_dir
        self.parts: list[str] = []
        self._skip_script_depth = 0

    def _rewrite_url(self, value: str) -> str:
        raw = str(value or "").strip()
        if not raw:
            return raw

        lower = raw.lower()
        if (
            lower.startswith(("http://", "https://", "file://", "data:", "mailto:", "#"))
            or raw.startswith("/")
            or re.match(r"^[A-Za-z]:[\\/]", raw)
            or raw.startswith("\\\\")
        ):
            return raw

        split = urlsplit(raw)
        if split.scheme:
            return raw

        relative_path = split.path.replace("\\", "/")
        absolute_path = (self.media_dir / relative_path).resolve()
        uri = absolute_path.as_uri()
        if split.query:
            uri = f"{uri}?{split.query}"
        if split.fragment:
            uri = f"{uri}#{split.fragment}"
        return uri

    def _rewrite_srcset(self, value: str) -> str:
        items: list[str] = []
        for item in str(value or "").split(","):
            candidate = item.strip()
            if not candidate:
                continue
            pieces = candidate.split()
            if not pieces:
                continue
            rewritten = self._rewrite_url(pieces[0])
            items.append(" ".join([rewritten, *pieces[1:]]))
        return ", ".join(items)

    def _rewrite_style(self, value: str) -> str:
        def replace(match: re.Match[str]) -> str:
            inner = match.group(1).strip().strip("'\"")
            rewritten = self._rewrite_url(inner)
            return f"url('{rewritten}')"

        return re.sub(r"url\((.*?)\)", replace, str(value or ""), flags=re.IGNORECASE)

    def _append_tag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
        *,
        self_closing: bool,
    ) -> None:
        rendered_attrs: list[str] = []
        for name, value in attrs:
            attr_name = str(name)
            attr_value = "" if value is None else str(value)
            if attr_name in {"src", "poster"}:
                attr_value = self._rewrite_url(attr_value)
            elif attr_name == "srcset":
                attr_value = self._rewrite_srcset(attr_value)
            elif attr_name == "style":
                attr_value = self._rewrite_style(attr_value)

            if value is None:
                rendered_attrs.append(attr_name)
            else:
                rendered_attrs.append(f'{attr_name}="{escape(attr_value, quote=True)}"')

        attrs_text = f" {' '.join(rendered_attrs)}" if rendered_attrs else ""
        if self_closing:
            self.parts.append(f"<{tag}{attrs_text} />")
        else:
            self.parts.append(f"<{tag}{attrs_text}>")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script":
            self._skip_script_depth += 1
            return
        if self._skip_script_depth:
            return
        self._append_tag(tag, attrs, self_closing=False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script":
            return
        if self._skip_script_depth:
            return
        self._append_tag(tag, attrs, self_closing=True)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script":
            self._skip_script_depth = max(0, self._skip_script_depth - 1)
            return
        if self._skip_script_depth:
            return
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if not self._skip_script_depth:
            self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if not self._skip_script_depth:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if not self._skip_script_depth:
            self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        if not self._skip_script_depth:
            self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        if not self._skip_script_depth:
            self.parts.append(f"<!{decl}>")

    def get_html(self) -> str:
        return "".join(self.parts)


def rewrite_media_html(html: str, media_dir: Path) -> str:
    parser = _MediaPathRewriter(media_dir)
    parser.feed(html or "")
    parser.close()
    return parser.get_html()


@dataclass
class MissedTodayEntry:
    card_id: int
    note_id: int
    deck_name: str
    note_type_name: str
    tags: list[str]
    field_entries: list[tuple[str, str]]
    question_html: str
    answer_html: str
    question_text: str
    answer_text: str
    miss_count: int
    first_missed_at: datetime
    last_missed_at: datetime


def _anki_day_bounds() -> tuple[datetime, datetime, int, int]:
    scheduler = getattr(mw.col, "sched", None)
    cutoff = None

    if scheduler is not None:
        cutoff = getattr(scheduler, "day_cutoff", None)
        if cutoff is None:
            cutoff = getattr(scheduler, "dayCutoff", None)

    if cutoff:
        end_seconds = int(cutoff)
        start_seconds = end_seconds - 86400
        return (
            datetime.fromtimestamp(start_seconds),
            datetime.fromtimestamp(end_seconds),
            start_seconds * 1000,
            end_seconds * 1000,
        )

    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = datetime.fromtimestamp(int(start.timestamp()) + 86400)
    return (start, end, int(start.timestamp() * 1000), int(end.timestamp() * 1000))


def fetch_missed_today_entries() -> list[MissedTodayEntry]:
    if mw.col is None:
        return []

    _start_dt, _end_dt, start_ms, end_ms = _anki_day_bounds()
    rows = mw.col.db.all(
        """
        SELECT
            r.cid,
            COUNT(*) AS miss_count,
            MIN(r.id) AS first_missed_at,
            MAX(r.id) AS last_missed_at
        FROM revlog AS r
        WHERE r.ease = 1
          AND r.id >= ?
          AND r.id < ?
        GROUP BY r.cid
        ORDER BY last_missed_at DESC, r.cid ASC
        """,
        int(start_ms),
        int(end_ms),
    )

    entries: list[MissedTodayEntry] = []
    for row in rows:
        card_id = int(row[0])
        try:
            card = get_card(card_id)
            note = card.note()
            question_html = str(card.question() or "")
            answer_html = str(card.answer() or "")
            field_entries = [
                (str(name), html_to_text(str(value)).strip() or "(blank)")
                for name, value in note_fields(note).items()
            ]
            entries.append(
                MissedTodayEntry(
                    card_id=card_id,
                    note_id=int(getattr(note, "id", 0) or 0),
                    deck_name=deck_name(card),
                    note_type_name=note_type_name(note),
                    tags=note_tags(note),
                    field_entries=field_entries,
                    question_html=question_html,
                    answer_html=answer_html,
                    question_text=html_to_text(question_html),
                    answer_text=html_to_text(answer_html),
                    miss_count=int(row[1]),
                    first_missed_at=datetime.fromtimestamp(int(row[2]) / 1000),
                    last_missed_at=datetime.fromtimestamp(int(row[3]) / 1000),
                )
            )
        except Exception:
            continue

    return entries


def summarize_missed_today(entries: list[MissedTodayEntry] | None = None) -> str:
    entries = fetch_missed_today_entries() if entries is None else entries
    start_dt, end_dt, _start_ms, _end_ms = _anki_day_bounds()
    count = len(entries)
    noun = "card" if count == 1 else "cards"
    return (
        f"{count} {noun} missed in the current Anki day "
        f"({start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')})."
    )


def build_export_text(entries: list[MissedTodayEntry]) -> str:
    today_text = datetime.now().strftime("%B %d, %Y").replace(" 0", " ")
    blocks: list[str] = []
    separator = "=" * 36
    for index, entry in enumerate(entries, start=1):
        field_blocks = [
            "\n".join([f"{field_name}:", field_value])
            for field_name, field_value in entry.field_entries
        ]
        blocks.append(
            "\n".join(
                [
                    separator,
                    f"Card {index}",
                    separator,
                    "\n\n".join(field_blocks) if field_blocks else "(blank)",
                ]
            )
        )
    body = "\n\n".join(blocks).strip()
    header = f"I incorrectly answered the following Anki cards on {today_text}:"
    if not body:
        return header
    return f"{header}\n\n{body}"


def _open_local_path(path: Path) -> None:
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def copy_missed_today_text() -> bool:
    entries = fetch_missed_today_entries()
    if not entries:
        showInfo("No cards have been missed in the current Anki day.")
        return False

    QApplication.clipboard().setText(build_export_text(entries))
    showInfo(f"Copied missed-today text for {len(entries)} cards.")
    return True


def _export_base_path(suffix: str) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d")
    return user_files_dir() / f"missed_today_{stamp}.{suffix}"


def export_missed_today_text_file() -> Path | None:
    entries = fetch_missed_today_entries()
    if not entries:
        showInfo("No cards have been missed in the current Anki day.")
        return None

    path = _export_base_path("txt")
    path.write_text(build_export_text(entries) + "\n", encoding="utf-8")
    showInfo(f"Saved missed-today text to:\n{path}")
    return path


def _viewer_html(entries: list[MissedTodayEntry]) -> str:
    start_dt, end_dt, _start_ms, _end_ms = _anki_day_bounds()
    media_dir = collection_media_dir()
    cards_html: list[str] = []

    for entry in entries:
        question_html = rewrite_media_html(entry.question_html, media_dir)
        answer_html = rewrite_media_html(entry.answer_html, media_dir)
        tags = ", ".join(entry.tags) if entry.tags else "No tags"
        cards_html.append(
            f"""
            <section class="entry">
              <div class="meta">
                <div><strong>{escape(entry.deck_name)}</strong></div>
                <div>{escape(entry.note_type_name)}</div>
                <div>Missed {entry.miss_count} time{'s' if entry.miss_count != 1 else ''} today</div>
                <div>Last miss {entry.last_missed_at.strftime("%Y-%m-%d %H:%M:%S")}</div>
              </div>
              <div class="tags">{escape(tags)}</div>
              <div class="card-face">
                <div class="face-label">Front</div>
                <div class="card-preview">{question_html}</div>
              </div>
              <div class="card-face">
                <div class="face-label">Back</div>
                <div class="card-preview">{answer_html}</div>
              </div>
            </section>
            """
        )

    count = len(entries)
    noun = "card" if count == 1 else "cards"
    body = "".join(cards_html) if cards_html else "<div class='empty'>No cards were missed today.</div>"

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Anki Pocket Knife: Missed Today</title>
  <style>
    :root {{
      --bg: #0d1320;
      --panel: rgba(17, 24, 39, 0.92);
      --line: rgba(148, 163, 184, 0.18);
      --text: #eef2ff;
      --muted: #9fb0d8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(88, 115, 255, 0.16), transparent 24%),
        radial-gradient(circle at top right, rgba(34, 197, 94, 0.12), transparent 24%),
        linear-gradient(180deg, #09101a, #111827 56%, #0f172a 100%);
      font-family: "Segoe UI", system-ui, sans-serif;
    }}
    main {{
      width: min(1180px, calc(100vw - 32px));
      margin: 24px auto 48px;
      display: grid;
      gap: 18px;
    }}
    .hero, .entry {{
      border: 1px solid var(--line);
      border-radius: 22px;
      background: var(--panel);
      box-shadow: 0 22px 44px rgba(0, 0, 0, 0.24);
    }}
    .hero {{
      padding: 18px 20px;
    }}
    .eyebrow {{
      color: #c8d7ff;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 12px;
      font-weight: 800;
    }}
    h1 {{
      margin: 10px 0 6px;
      font-size: clamp(28px, 4vw, 40px);
      line-height: 1.05;
    }}
    .hero p {{
      margin: 6px 0 0;
      color: var(--muted);
      line-height: 1.6;
    }}
    .list {{
      display: grid;
      gap: 16px;
    }}
    .entry {{
      padding: 18px;
      display: grid;
      gap: 12px;
      background:
        radial-gradient(circle at top, rgba(140, 183, 255, 0.12), transparent 48%),
        var(--panel);
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 16px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .tags {{
      color: #dbe7ff;
      font-size: 13px;
      line-height: 1.55;
    }}
    .card-face {{
      border-radius: 18px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(7, 12, 22, 0.78);
      padding: 14px;
      display: grid;
      gap: 10px;
    }}
    .face-label {{
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    .card-preview {{
      border-radius: 14px;
      min-height: 72px;
      padding: 14px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      background: rgba(255, 255, 255, 0.03);
      overflow-wrap: anywhere;
      line-height: 1.65;
    }}
    .card-preview img {{
      max-width: 100%;
      height: auto;
      display: block;
    }}
    .card-preview audio, .card-preview video {{
      max-width: 100%;
    }}
    .card-preview .card {{
      color: inherit;
      background: transparent;
      box-shadow: none;
    }}
    .empty {{
      color: var(--muted);
      padding: 18px;
      border-radius: 18px;
      border: 1px dashed var(--line);
      background: rgba(255, 255, 255, 0.03);
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="eyebrow">Anki Pocket Knife</div>
      <h1>Missed Today</h1>
      <p>{count} {noun} missed in the current Anki day.</p>
      <p>Anki day window: {start_dt.strftime("%Y-%m-%d %H:%M")} to {end_dt.strftime("%Y-%m-%d %H:%M")}.</p>
    </section>
    <section class="list">
      {body}
    </section>
  </main>
</body>
</html>
"""


def open_missed_today_html_viewer() -> Path | None:
    entries = fetch_missed_today_entries()
    if not entries:
        showInfo("No cards have been missed in the current Anki day.")
        return None

    path = _export_base_path("html")
    path.write_text(_viewer_html(entries), encoding="utf-8")
    _open_local_path(path)
    showInfo(f"Opened the missed-today HTML viewer:\n{path}")
    return path


def make_missed_today_filtered_deck() -> bool:
    entries = fetch_missed_today_entries()
    if not entries:
        showInfo("No cards have been missed in the current Anki day.")
        return False

    deck_name_value = datetime.now().strftime(f"{MISSED_TODAY_DECK_NAME_PREFIX}%Y-%m-%d %H-%M-%S")
    search = card_id_search([entry.card_id for entry in entries])

    try:
        create_or_update_filtered_deck(
            deck_name_value,
            search=search,
            limit=len(entries),
            resched=False,
        )
    except Exception as exc:
        showWarning(f"Could not create the missed-today filtered deck.\n\n{exc}")
        return False

    showInfo(f"Created '{deck_name_value}' with {len(entries)} cards.")
    return True
