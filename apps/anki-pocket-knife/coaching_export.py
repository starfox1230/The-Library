from __future__ import annotations

from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import re
import time
from typing import Any
from urllib.parse import unquote, urlparse

from aqt import gui_hooks, mw
from aqt.qt import QTimer

from .hard_cards import compute_hard_cards_snapshot, load_hard_cards_config


_IMAGE_SRC_RE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", re.IGNORECASE)
_EXPORT_TIMER: QTimer | None = None
_LAST_EXPORT_MONOTONIC = 0.0


def _output_dir() -> Path:
    one_drive = Path(os.environ.get("OneDrive") or (Path.home() / "OneDrive"))
    return one_drive / "Study OS Private" / "anki-coaching"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _media_dir() -> Path | None:
    try:
        return Path(mw.col.media.dir()) if mw.col else None
    except Exception:
        return None


def _media_files(*html_values: str) -> list[dict[str, Any]]:
    media_dir = _media_dir()
    if not media_dir:
        return []
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for html in html_values:
        for raw_src in _IMAGE_SRC_RE.findall(str(html or "")):
            parsed = urlparse(raw_src)
            if parsed.scheme and parsed.scheme not in {"file"}:
                continue
            filename = Path(unquote(parsed.path or raw_src)).name
            if not filename or filename in seen:
                continue
            path = media_dir / filename
            if not path.is_file():
                continue
            seen.add(filename)
            found.append({"filename": filename, "path": str(path), "bytes": path.stat().st_size})
    return found


def _note_payload(card_id: int) -> dict[str, Any] | None:
    try:
        card = mw.col.get_card(int(card_id))
        note = card.note()
        fields = {str(name): str(value or "") for name, value in note.items()}
        return {
            "cardId": int(card.id),
            "noteId": int(note.id),
            "deck": str(mw.col.decks.name(card.did) or ""),
            "noteType": str(note.note_type().get("name", "")),
            "tags": [str(tag) for tag in note.tags],
            "fields": fields,
            "media": _media_files(*fields.values()),
        }
    except Exception:
        return None


def _review_later_source() -> dict[str, Any]:
    try:
        module = importlib.import_module("speed_streak_v1_25.review_later")
        config = mw.addonManager.getConfig("speed_streak_v1_25") or {}
        flag = int(config.get("review_later_flag", 0) or 0)
        entries = module.fetch_review_later_entries(flag) if flag > 0 else []
        cards = []
        for entry in entries:
            cards.append({
                "addedAt": entry.added_at.astimezone(timezone.utc).isoformat(),
                "cardId": int(entry.card_id),
                "noteId": int(entry.note_id),
                "deck": str(entry.deck_name),
                "noteType": str(entry.note_type_name),
                "tags": list(entry.tags),
                "fields": dict(entry.fields),
                "frontHtml": str(entry.front_html),
                "backHtml": str(entry.back_html),
                "frontText": str(entry.front_text),
                "backText": str(entry.back_text),
                "media": _media_files(entry.front_html, entry.back_html, *entry.fields.values()),
            })
        return {"ok": True, "flag": flag, "count": len(cards), "cards": cards}
    except Exception as error:
        return {"ok": False, "count": 0, "cards": [], "error": str(error)}


def _study_repair_source() -> dict[str, Any]:
    try:
        config = load_hard_cards_config()
        lookback_hours = max(1, int(config.get("default_lookback_hours", 24) or 24))
        top_n = max(1, int(config.get("default_top_n", 20) or 20))
        snapshot = compute_hard_cards_snapshot(
            mw.col,
            lookback_hours=lookback_hours,
            top_n=top_n,
            config=config,
        )
        cards = []
        for ranked in snapshot.ranked_cards:
            payload = _note_payload(ranked.metrics.card_id)
            if not payload:
                continue
            payload.update({
                "score": ranked.score,
                "reasons": list(ranked.explanation),
                "scoreComponents": dict(ranked.score_components),
                "reviewMetrics": {
                    "state": ranked.metrics.current_state,
                    "totalReps": ranked.metrics.total_reps,
                    "totalLapses": ranked.metrics.total_lapses,
                    "againCount": ranked.metrics.again_count,
                    "hardCount": ranked.metrics.hard_count,
                    "goodCount": ranked.metrics.good_count,
                    "easyCount": ranked.metrics.easy_count,
                    "lastReviewAt": ranked.metrics.last_review_at_s,
                    "failureClusterCount": ranked.metrics.failure_cluster_count,
                    "fsrsDifficulty": ranked.metrics.fsrs_difficulty,
                },
            })
            cards.append(payload)
        return {
            "ok": True,
            "lookbackHours": snapshot.lookback_hours,
            "reviewedCardCount": snapshot.reviewed_card_count,
            "candidateCount": snapshot.candidate_count,
            "count": len(cards),
            "cards": cards,
        }
    except Exception as error:
        return {"ok": False, "count": 0, "cards": [], "error": str(error)}


def export_coaching_sources(*, force: bool = False) -> None:
    global _LAST_EXPORT_MONOTONIC
    if not mw.col:
        return
    now = time.monotonic()
    if not force and now - _LAST_EXPORT_MONOTONIC < 30:
        return
    _LAST_EXPORT_MONOTONIC = now
    try:
        payload = {
            "schemaVersion": 1,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "profile": str(getattr(mw.pm, "name", "") or ""),
            "mediaDirectory": str(_media_dir() or ""),
            "reviewLater": _review_later_source(),
            "studyRepair": _study_repair_source(),
        }
        _atomic_json(_output_dir() / "latest.json", payload)
    except Exception as error:
        try:
            _atomic_json(
                _output_dir() / "last-error.json",
                {"generatedAt": datetime.now(timezone.utc).isoformat(), "error": str(error)},
            )
        except Exception:
            pass


def _schedule_export(*_args: Any) -> None:
    QTimer.singleShot(1200, export_coaching_sources)


def install() -> None:
    global _EXPORT_TIMER
    profile_opened = getattr(gui_hooks, "profile_did_open", None)
    if profile_opened is not None:
        profile_opened.append(_schedule_export)
    reviewer_answered = getattr(gui_hooks, "reviewer_did_answer_card", None)
    if reviewer_answered is not None:
        reviewer_answered.append(_schedule_export)
    _EXPORT_TIMER = QTimer(mw)
    _EXPORT_TIMER.setInterval(5 * 60 * 1000)
    _EXPORT_TIMER.timeout.connect(export_coaching_sources)
    _EXPORT_TIMER.start()
    QTimer.singleShot(5000, lambda: export_coaching_sources(force=True))
