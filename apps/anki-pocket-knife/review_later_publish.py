from __future__ import annotations

from concurrent.futures import Future
from datetime import datetime, timedelta
from html import escape as html_escape, unescape
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any
from urllib.parse import quote, unquote, urlparse

from aqt import gui_hooks, mw
from aqt.qt import QMessageBox, QTimer
from aqt.utils import tooltip

from .common import addon_root, user_files_dir
from .review_later_publish_core import (
    cards_markdown,
    chat_markdown,
    content_hash,
    data_document,
    data_json,
    display_timestamp,
    page_html,
)
from .speed_streak_review_later import fetch_current_review_later


CONFIG_PATH = user_files_dir() / "review_later_publish_config.json"
STATUS_PATH = user_files_dir() / "review_later_publish_status.json"
LOG_PATH = user_files_dir() / "review_later_publish.log"
PROMPT_PATH = addon_root() / "review_later_chat_prompt.txt"
DEFAULT_CONFIG = {
    "repository_path": r"%USERPROFILE%\Documents\GitHub\The-Library",
    "output_directory": "review-later",
    "commit_message": "Update Anki Review Later",
    "git_publish": True,
    "auto_publish_after_sync": True,
    "history_days": 45,
}
_LOCAL_MEDIA_ATTR_RE = re.compile(
    r'(?P<prefix>\s(?:src|href)=["\'])(?P<url>[^"\']+)(?P<suffix>["\'])',
    re.IGNORECASE,
)
_PUBLISH_RUNNING = False
_AUTO_PENDING = False
_AUTO_TIMER: QTimer | None = None
_INSTALLED = False


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}-{time.time_ns()}")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _append_log(message: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        with LOG_PATH.open("a", encoding="utf-8") as stream:
            stream.write(f"{timestamp} {message.rstrip()}\n")
    except Exception:
        pass


def _load_config() -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config.update(loaded)
        except Exception as exc:
            _append_log(f"Could not read config; defaults used: {exc}")
    else:
        try:
            _atomic_json(CONFIG_PATH, config)
        except Exception as exc:
            _append_log(f"Could not create config: {exc}")
    return config


def _load_status() -> dict[str, Any]:
    try:
        value = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _save_status(**updates: Any) -> None:
    status = _load_status()
    status.update(updates)
    status["last_attempt_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        _atomic_json(STATUS_PATH, status)
    except Exception as exc:
        _append_log(f"Could not save status: {exc}")


def _repository_and_output(config: dict[str, Any]) -> tuple[Path, Path, str]:
    raw_repository = os.path.expandvars(str(config.get("repository_path", "") or "").strip())
    if not raw_repository:
        raise RuntimeError(f"Set repository_path in {CONFIG_PATH}.")
    repository = Path(raw_repository).expanduser().resolve()
    if not (repository / ".git").exists():
        raise RuntimeError(f"Configured repository is not a Git checkout: {repository}")

    relative_text = str(config.get("output_directory", "review-later") or "review-later").strip()
    relative = Path(relative_text)
    if relative.is_absolute() or not relative.parts:
        raise RuntimeError("output_directory must be a non-empty path inside the repository.")
    output = (repository / relative).resolve()
    try:
        output.relative_to(repository)
    except ValueError as exc:
        raise RuntimeError("output_directory must stay inside repository_path.") from exc
    if output == repository:
        raise RuntimeError("Refusing to use the repository root as the generated output directory.")
    return repository, output, relative.as_posix()


def _collection_media_directory() -> str:
    media = getattr(getattr(mw, "col", None), "media", None)
    if media is None:
        return ""
    for name in ("dir", "dir_path"):
        candidate = getattr(media, name, None)
        try:
            value = candidate() if callable(candidate) else candidate
        except Exception:
            continue
        if value:
            return str(value)
    return ""


def _snapshot() -> dict[str, Any]:
    source = fetch_current_review_later()
    if not PROMPT_PATH.exists():
        raise RuntimeError(f"Missing standing-instructions template: {PROMPT_PATH}")
    source["standing_instructions"] = PROMPT_PATH.read_text(encoding="utf-8").strip()
    source["media_directory"] = _collection_media_directory()
    source["config"] = _load_config()
    return source


def _media_source(raw_url: str, media_directory: Path | None) -> Path | None:
    raw = unescape(str(raw_url or "").strip())
    if not raw:
        return None
    parsed = urlparse(raw)
    if parsed.scheme and parsed.scheme.casefold() not in {"file"}:
        return None
    path_text = unquote(parsed.path or raw).strip()
    if not path_text:
        return None
    if sys.platform.startswith("win") and re.match(r"^/[A-Za-z]:/", path_text):
        path_text = path_text[1:]
    path = Path(path_text)
    if not path.is_absolute():
        if media_directory is None:
            return None
        path = media_directory / path.name
    try:
        resolved = path.resolve()
    except Exception:
        return None
    return resolved if resolved.is_file() else None


def _publishable_media_name(path: Path) -> str:
    name = path.name
    if name in {".", "..", ""}:
        raise RuntimeError(f"Invalid media filename: {path}")
    return name


def _rewrite_card_media(
    card: dict[str, Any],
    *,
    media_directory: Path | None,
    media_output: Path,
    referenced_names: set[str],
) -> dict[str, Any]:
    rewritten = dict(card)
    card_media: set[str] = set()

    def rewrite_html(value: Any) -> str:
        def replace(match: re.Match[str]) -> str:
            source = _media_source(match.group("url"), media_directory)
            if source is None:
                return match.group(0)
            name = _publishable_media_name(source)
            target = media_output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            source_stat = source.stat()
            target_stat = target.stat() if target.exists() else None
            if (
                target_stat is None
                or target_stat.st_size != source_stat.st_size
                or target_stat.st_mtime_ns != source_stat.st_mtime_ns
            ):
                shutil.copy2(source, target)
            referenced_names.add(name)
            card_media.add(name)
            url = f"media/{quote(name)}"
            return f"{match.group('prefix')}{html_escape(url, quote=True)}{match.group('suffix')}"

        return _LOCAL_MEDIA_ATTR_RE.sub(replace, str(value or ""))

    rewritten["front_html"] = rewrite_html(card.get("front_html", ""))
    rewritten["back_html"] = rewrite_html(card.get("back_html", ""))
    rewritten["media"] = sorted(card_media)
    return rewritten


def _prune_generated_media(media_output: Path, referenced_names: set[str]) -> None:
    if not media_output.exists():
        return
    media_root = media_output.resolve()
    for child in media_output.iterdir():
        try:
            resolved = child.resolve()
            resolved.relative_to(media_root)
        except Exception:
            continue
        if not child.is_file() or child.name in referenced_names:
            continue
        child.unlink()


def _existing_document(output: Path) -> dict[str, Any]:
    try:
        value = json.loads((output / "data.json").read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _local_datetime(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or ""))
        return parsed.astimezone() if parsed.tzinfo is not None else parsed.astimezone()
    except Exception:
        return None


def _recent_cards(cards: list[dict[str, Any]], history_days: int) -> list[dict[str, Any]]:
    today = datetime.now().astimezone().date()
    cutoff = today - timedelta(days=max(1, int(history_days or 1)) - 1)
    return [
        card
        for card in cards
        if (seen := _local_datetime(card.get("last_seen_at"))) is not None
        and cutoff <= seen.date() <= today
    ]


def _today_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    today = datetime.now().astimezone().date()
    result = [
        card
        for card in cards
        if (seen := _local_datetime(card.get("last_seen_at"))) is not None and seen.date() == today
    ]
    return sorted(result, key=lambda card: str(card.get("last_seen_at", "") or ""), reverse=True)


def _generate(snapshot: dict[str, Any], output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    media_output = output / "media"
    media_dir_text = str(snapshot.get("media_directory", "") or "")
    media_directory = Path(media_dir_text) if media_dir_text else None
    referenced_names: set[str] = set()
    source_cards = _recent_cards(
        [dict(card) for card in snapshot.get("cards", [])],
        int(dict(snapshot.get("config", {}) or {}).get("history_days", 45) or 45),
    )
    cards = [
        _rewrite_card_media(
            card,
            media_directory=media_directory,
            media_output=media_output,
            referenced_names=referenced_names,
        )
        for card in source_cards
    ]
    _prune_generated_media(media_output, referenced_names)
    default_cards = _today_cards(cards)

    instructions = str(snapshot.get("standing_instructions", "") or "").strip()
    source_addon = str(snapshot.get("source_addon", "") or "")
    flag = int(snapshot.get("review_later_flag", 0) or 0)
    digest = content_hash(
        cards,
        instructions,
        source_addon=source_addon,
        review_later_flag=flag,
    )
    existing = _existing_document(output)
    required_files = [output / "index.html", output / "chat.md", output / "data.json"]
    unchanged = existing.get("content_hash") == digest and all(path.exists() for path in required_files)
    if unchanged:
        return {
            "generated_changed": False,
            "count": len(default_cards),
            "retained_count": len(cards),
            "content_hash": digest,
            "updated_at": str(existing.get("updated_at", "") or ""),
        }

    updated_at = display_timestamp()
    cards_only = cards_markdown(default_cards, updated_at)
    chat = chat_markdown(instructions, cards_only)
    document = data_document(
        cards,
        updated_at=updated_at,
        digest=digest,
        source_addon=source_addon,
        review_later_flag=flag,
    )
    _atomic_text(
        output / "index.html",
        page_html(cards, updated_at=updated_at, standing_instructions=instructions),
    )
    _atomic_text(output / "chat.md", chat)
    _atomic_text(output / "data.json", data_json(document))
    return {
        "generated_changed": True,
        "count": len(default_cards),
        "retained_count": len(cards),
        "content_hash": digest,
        "updated_at": updated_at,
    }


def _run_git(repository: Path, *args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["GCM_INTERACTIVE"] = "Never"
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform.startswith("win") else 0
    result = subprocess.run(
        ["git", *args],
        cwd=str(repository),
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=creationflags,
        check=False,
    )
    return result


def _git_error(action: str, result: subprocess.CompletedProcess[str]) -> RuntimeError:
    detail = (result.stderr or result.stdout or "unknown Git error").strip()
    return RuntimeError(f"{action} failed ({result.returncode}): {detail}")


def _git_publish(repository: Path, relative_output: str, config: dict[str, Any]) -> dict[str, Any]:
    add = _run_git(repository, "add", "--", relative_output)
    if add.returncode != 0:
        raise _git_error("git add", add)

    diff = _run_git(repository, "diff", "--cached", "--quiet", "--", relative_output)
    if diff.returncode not in {0, 1}:
        raise _git_error("git diff", diff)

    committed = False
    if diff.returncode == 1:
        message = str(config.get("commit_message", "Update Anki Review Later") or "Update Anki Review Later")
        commit = _run_git(
            repository,
            "commit",
            "--only",
            "-m",
            message,
            "--",
            relative_output,
        )
        if commit.returncode != 0:
            raise _git_error("git commit", commit)
        committed = True

    status = _load_status()
    push_pending = bool(status.get("push_pending", False))
    pushed = False
    if committed or push_pending:
        # The first publish may include the full active queue's media. Subsequent
        # pushes are normally small, but allow enough time for that initial pack.
        push = _run_git(repository, "push", timeout=10 * 60)
        if push.returncode != 0:
            _save_status(push_pending=True, last_error=(push.stderr or push.stdout or "git push failed").strip())
            raise _git_error("git push", push)
        pushed = True
        _save_status(push_pending=False, last_error="")
    return {"committed": committed, "pushed": pushed}


def _publish_worker(snapshot: dict[str, Any]) -> dict[str, Any]:
    config = dict(snapshot.get("config", {}) or {})
    repository, output, relative_output = _repository_and_output(config)
    result = _generate(snapshot, output)
    result.update({"repository": str(repository), "output": str(output)})
    if bool(config.get("git_publish", True)):
        result.update(_git_publish(repository, relative_output, config))
    else:
        result.update({"committed": False, "pushed": False})
    return result


def _publish_done(future: Future[dict[str, Any]], *, manual: bool) -> None:
    global _PUBLISH_RUNNING
    _PUBLISH_RUNNING = False
    try:
        result = future.result()
    except Exception as exc:
        message = str(exc)
        _append_log(f"Publish failed: {message}")
        _save_status(last_success=False, last_error=message)
        if manual:
            QMessageBox.warning(mw, "Review Later Publishing", f"Publishing failed.\n\n{message}\n\nLog: {LOG_PATH}")
    else:
        count = int(result.get("count", 0) or 0)
        changed = bool(result.get("generated_changed", False))
        committed = bool(result.get("committed", False))
        pushed = bool(result.get("pushed", False))
        summary = f"Published {count} Review Later cards"
        if not changed and not committed and not pushed:
            summary = f"Review Later is already current ({count} cards)"
        _append_log(
            f"Publish succeeded: count={count} generated_changed={changed} committed={committed} pushed={pushed}"
        )
        _save_status(
            last_success=True,
            last_error="",
            last_count=count,
            last_content_hash=str(result.get("content_hash", "") or ""),
            last_output=str(result.get("output", "") or ""),
        )
        if manual:
            tooltip(summary, parent=mw, period=5000)
    if _AUTO_PENDING:
        _schedule_auto_publish(1500)


def _start_publish(*, manual: bool) -> None:
    global _PUBLISH_RUNNING, _AUTO_PENDING
    if _PUBLISH_RUNNING:
        if not manual:
            _AUTO_PENDING = True
        elif manual:
            tooltip("Review Later publishing is already running.", parent=mw)
        return
    if not getattr(mw, "col", None):
        if manual:
            QMessageBox.information(mw, "Review Later Publishing", "Open an Anki profile first.")
        return
    try:
        snapshot = _snapshot()
    except Exception as exc:
        message = str(exc)
        _append_log(f"Could not prepare publish snapshot: {message}")
        if manual:
            QMessageBox.warning(mw, "Review Later Publishing", message)
        return
    _AUTO_PENDING = False
    _PUBLISH_RUNNING = True
    mw.taskman.run_in_background(
        lambda: _publish_worker(snapshot),
        lambda future: _publish_done(future, manual=manual),
    )


def publish_review_later_manual(*_args: Any) -> None:
    _start_publish(manual=True)


def _schedule_auto_publish(delay_ms: int = 1500) -> None:
    global _AUTO_TIMER
    if not bool(_load_config().get("auto_publish_after_sync", True)):
        return
    if _AUTO_TIMER is None:
        _AUTO_TIMER = QTimer(mw)
        _AUTO_TIMER.setSingleShot(True)
        _AUTO_TIMER.timeout.connect(lambda: _start_publish(manual=False))
    _AUTO_TIMER.start(max(0, int(delay_ms)))


def _on_sync_did_finish() -> None:
    global _AUTO_PENDING
    if not bool(_load_config().get("auto_publish_after_sync", True)):
        return
    _AUTO_PENDING = True
    media_syncer = getattr(mw, "media_syncer", None)
    try:
        if media_syncer is not None and media_syncer.is_syncing():
            return
    except Exception:
        pass
    _schedule_auto_publish()


def _on_media_sync_state_changed(running: bool) -> None:
    if not running and _AUTO_PENDING:
        _schedule_auto_publish(500)


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _load_config()
    sync_finished = getattr(gui_hooks, "sync_did_finish", None)
    if sync_finished is not None:
        sync_finished.append(_on_sync_did_finish)
    media_state = getattr(gui_hooks, "media_sync_did_start_or_stop", None)
    if media_state is not None:
        media_state.append(_on_media_sync_state_changed)
    _INSTALLED = True
