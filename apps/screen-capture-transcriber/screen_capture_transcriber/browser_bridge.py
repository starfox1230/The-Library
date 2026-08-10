from __future__ import annotations

import json
import secrets
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from PySide6.QtCore import QObject, Signal


BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 43129
BRIDGE_TOKEN = "sct-medality-local-v1-9f63d2c7"
BRIDGE_VERSION = 1


def browser_source_title(
    player: dict[str, Any] | None,
    transcript: dict[str, Any] | None = None,
) -> str:
    """Return the best title reported for the browser video currently in view."""
    player = player or {}
    player_url = str(player.get("top_url") or "").strip().rstrip("/")
    transcript = transcript or {}
    transcript_url = str(
        transcript.get("top_url") or transcript.get("url") or ""
    ).strip().rstrip("/")
    transcript_matches = (
        not player_url
        or not transcript_url
        or player_url == transcript_url
    )
    candidates = (
        transcript.get("title") if transcript_matches else "",
        player.get("top_title"),
        player.get("frame_title"),
    )
    for candidate in candidates:
        title = " ".join(str(candidate or "").split())
        if title:
            return title
    return ""


class BrowserBridge(QObject):
    player_event = Signal(object)
    transcript_received = Signal(object)
    sources_changed = Signal(object)
    server_error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        # A page content script can outlive the desktop process.  Give each
        # process a new identity so the page knows to resend cached lesson
        # metadata and its transcript after the recorder is restarted.
        self._instance_id = secrets.token_hex(8)
        self._lock = threading.Lock()
        self._commands: deque[dict[str, Any]] = deque()
        self._next_command_id = 1
        self._app_state: dict[str, Any] = {
            "linked_session_active": False,
            "recorder_state": "idle",
            "selected_source_tab_id": None,
        }
        self._last_player: dict[str, Any] | None = None
        self._last_transcript: dict[str, Any] | None = None
        self._players_by_tab: dict[int, dict[str, Any]] = {}
        self._transcripts_by_tab: dict[int, dict[str, Any]] = {}
        self._selected_tab_id: int | None = None
        self._sources_signature: tuple[tuple[object, ...], ...] = ()
        self._last_transcript_seen_monotonic = 0.0
        self._last_seen_monotonic = 0.0
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        if self._server is not None:
            return True
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def do_OPTIONS(self) -> None:  # noqa: N802
                self.send_response(204)
                self._cors_headers()
                self.end_headers()

            def do_GET(self) -> None:  # noqa: N802
                if self.path.rstrip("/") == "/v1/health":
                    self._write_json(
                        200,
                        {
                            "ok": True,
                            "version": BRIDGE_VERSION,
                            "app": "Screen Capture Transcriber",
                        },
                    )
                    return
                self._write_json(404, {"ok": False, "error": "Not found"})

            def do_POST(self) -> None:  # noqa: N802
                if self.headers.get("X-SCT-Bridge-Token", "") != BRIDGE_TOKEN:
                    self._write_json(403, {"ok": False, "error": "Forbidden"})
                    return
                try:
                    length = min(
                        256 * 1024,
                        max(0, int(self.headers.get("Content-Length", "0"))),
                    )
                    payload = json.loads(self.rfile.read(length) or b"{}")
                    if not isinstance(payload, dict):
                        raise ValueError("The request body must be an object.")
                except (ValueError, json.JSONDecodeError) as exc:
                    self._write_json(400, {"ok": False, "error": str(exc)})
                    return

                if self.path.rstrip("/") == "/v1/poll":
                    bridge._receive_payload(payload, heartbeat=True)
                    self._write_json(200, bridge._poll_response(payload))
                    return
                if self.path.rstrip("/") == "/v1/page-poll":
                    self._write_json(200, bridge._page_poll_response(payload))
                    return
                if self.path.rstrip("/") == "/v1/event":
                    if payload.get("event") == "source_transcript":
                        bridge._receive_transcript(payload)
                    else:
                        bridge._receive_payload(payload, heartbeat=False)
                    self._write_json(200, {"ok": True})
                    return
                self._write_json(404, {"ok": False, "error": "Not found"})

            def _write_json(self, status: int, payload: object) -> None:
                encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self._cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def _cors_headers(self) -> None:
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header(
                    "Access-Control-Allow-Headers",
                    "Content-Type, X-SCT-Bridge-Token",
                )
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Cache-Control", "no-store")

            def log_message(self, _format: str, *_args: object) -> None:
                return

        try:
            self._server = ThreadingHTTPServer((BRIDGE_HOST, BRIDGE_PORT), Handler)
            self._server.daemon_threads = True
        except OSError as exc:
            self.server_error.emit(
                f"Browser link could not listen on {BRIDGE_HOST}:{BRIDGE_PORT}: {exc}"
            )
            self._server = None
            return False

        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="screen-capture-browser-bridge",
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        server = self._server
        self._server = None
        if server is not None:
            server.shutdown()
            server.server_close()
        thread = self._thread
        self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)

    def enqueue_command(self, action: str, **payload: object) -> int:
        with self._lock:
            command_id = self._next_command_id
            self._next_command_id += 1
            target_tab_id = self._selected_tab_id
            if target_tab_id is None and self._last_player is not None:
                target_tab_id = self._coerce_tab_id(
                    self._last_player.get("tab_id")
                )
            self._commands.append(
                {
                    "id": command_id,
                    "action": action,
                    "_target_tab_id": target_tab_id,
                    **payload,
                }
            )
        return command_id

    def set_app_state(self, **state: object) -> None:
        with self._lock:
            self._app_state = {
                **self._app_state,
                **state,
            }

    @staticmethod
    def _coerce_tab_id(value: object) -> int | None:
        try:
            tab_id = int(value)
        except (TypeError, ValueError):
            return None
        return tab_id if tab_id >= 0 else None

    def select_source(self, tab_id: object | None) -> dict[str, Any] | None:
        selected = self._coerce_tab_id(tab_id)
        player: dict[str, Any] | None = None
        with self._lock:
            self._selected_tab_id = selected
            self._app_state["selected_source_tab_id"] = selected
            if selected is not None:
                player = self._players_by_tab.get(selected)
                transcript = self._transcripts_by_tab.get(selected)
                if player is not None:
                    self._last_player = dict(player)
                    self._last_seen_monotonic = time.monotonic()
                if transcript is not None:
                    self._last_transcript = dict(transcript)
                    self._last_transcript_seen_monotonic = time.monotonic()
            else:
                player = self._last_player
        return dict(player) if player is not None else None

    @property
    def selected_tab_id(self) -> int | None:
        with self._lock:
            return self._selected_tab_id

    def available_players(
        self,
        max_age_seconds: float = 10.0,
    ) -> list[dict[str, Any]]:
        now = time.monotonic()
        with self._lock:
            players = [
                dict(player)
                for player in self._players_by_tab.values()
                if now - float(player.get("received_monotonic") or 0.0)
                <= max_age_seconds
            ]
            selected = self._selected_tab_id
        players.sort(
            key=lambda player: (
                self._coerce_tab_id(player.get("tab_id")) != selected,
                bool(player.get("paused", True)),
                not bool(player.get("tab_active", False)),
                -float(player.get("received_monotonic") or 0.0),
            )
        )
        return players

    def _emit_sources_if_changed(self) -> None:
        players = self.available_players()
        signature = tuple(
            (
                player.get("tab_id"),
                player.get("top_title"),
                player.get("top_url"),
                player.get("provider"),
                bool(player.get("paused", True)),
            )
            for player in players
        )
        with self._lock:
            if signature == self._sources_signature:
                return
            self._sources_signature = signature
        self.sources_changed.emit(players)

    def current_player(self, max_age_seconds: float = 3.0) -> dict[str, Any] | None:
        with self._lock:
            if self._selected_tab_id is not None:
                selected = self._players_by_tab.get(self._selected_tab_id)
                if selected is not None:
                    age = time.monotonic() - float(
                        selected.get("received_monotonic") or 0.0
                    )
                    return dict(selected) if age <= max_age_seconds else None
            if (
                self._last_player is None
                or time.monotonic() - self._last_seen_monotonic > max_age_seconds
            ):
                return None
            return dict(self._last_player)

    def connected(self, max_age_seconds: float = 3.0) -> bool:
        return self.current_player(max_age_seconds) is not None

    def current_transcript(
        self,
        max_age_seconds: float = 10 * 60,
    ) -> dict[str, Any] | None:
        with self._lock:
            desired_tab_id = self._selected_tab_id
            if desired_tab_id is None and self._last_player is not None:
                desired_tab_id = self._coerce_tab_id(
                    self._last_player.get("tab_id")
                )
            if desired_tab_id is not None:
                selected = self._transcripts_by_tab.get(desired_tab_id)
                if selected is not None:
                    age = time.monotonic() - float(
                        selected.get("received_monotonic") or 0.0
                    )
                    return dict(selected) if age <= max_age_seconds else None
                return None
            if (
                self._last_transcript is None
                or time.monotonic() - self._last_transcript_seen_monotonic
                > max_age_seconds
            ):
                return None
            return dict(self._last_transcript)

    def _receive_payload(self, payload: dict[str, Any], heartbeat: bool) -> None:
        player = payload.get("player")
        payload_tab_id = self._coerce_tab_id(payload.get("tab_id"))
        if (
            not isinstance(player, dict)
            and payload.get("event") == "learning_note_intent"
        ):
            with self._lock:
                player = (
                    self._players_by_tab.get(payload_tab_id)
                    if payload_tab_id is not None
                    else self._last_player
                )
        if not isinstance(player, dict):
            return
        normalized = {
            **player,
            "event": str(payload.get("event") or ("heartbeat" if heartbeat else "")),
            "event_reason": str(payload.get("reason") or ""),
            "top_url": str(payload.get("top_url") or ""),
            "top_title": str(payload.get("top_title") or ""),
            "tab_id": payload.get("tab_id"),
            "frame_id": payload.get("frame_id"),
            "tab_active": bool(payload.get("tab_active", False)),
            "window_id": payload.get("window_id"),
            "received_monotonic": time.monotonic(),
        }
        tab_id = self._coerce_tab_id(normalized.get("tab_id"))
        with self._lock:
            if tab_id is not None:
                previous = self._players_by_tab.get(tab_id)
                previous_url = str(
                    (previous or {}).get("top_url") or ""
                ).rstrip("/")
                next_url = str(normalized.get("top_url") or "").rstrip("/")
                if previous_url and next_url and previous_url != next_url:
                    self._transcripts_by_tab.pop(tab_id, None)
                    if (
                        self._last_transcript is not None
                        and self._coerce_tab_id(
                            self._last_transcript.get("tab_id")
                        )
                        == tab_id
                    ):
                        self._last_transcript = None
                        self._last_transcript_seen_monotonic = 0.0
                self._players_by_tab[tab_id] = normalized
            selected = self._selected_tab_id
            current = self._last_player
            current_paused = bool(current.get("paused", True)) if current else True
            should_activate = (
                selected == tab_id
                or (
                    selected is None
                    and (
                        current is None
                        or self._coerce_tab_id(current.get("tab_id")) == tab_id
                        or (
                            not bool(normalized.get("paused", True))
                            and current_paused
                        )
                        or (
                            bool(normalized.get("tab_active", False))
                            and str(normalized.get("event") or "")
                            in {"play", "play_intent", "player_detected"}
                        )
                    )
                )
            )
            if should_activate:
                self._last_player = normalized
                self._last_seen_monotonic = time.monotonic()
        if tab_id is not None:
            self._emit_sources_if_changed()
        if should_activate:
            self.player_event.emit(normalized)

    def _receive_transcript(self, payload: dict[str, Any]) -> None:
        transcript = payload.get("transcript")
        if not isinstance(transcript, dict):
            return
        cues = transcript.get("cues")
        if not isinstance(cues, list) or not cues:
            return
        normalized = {
            **transcript,
            "top_url": str(payload.get("top_url") or ""),
            "top_title": str(payload.get("top_title") or ""),
            "tab_id": payload.get("tab_id"),
            "received_monotonic": time.monotonic(),
        }
        tab_id = self._coerce_tab_id(normalized.get("tab_id"))
        with self._lock:
            if tab_id is not None:
                self._transcripts_by_tab[tab_id] = normalized
            active_tab_id = self._selected_tab_id
            if active_tab_id is None and self._last_player is not None:
                active_tab_id = self._coerce_tab_id(
                    self._last_player.get("tab_id")
                )
            should_activate = active_tab_id is None or active_tab_id == tab_id
            if should_activate:
                self._last_transcript = normalized
                self._last_transcript_seen_monotonic = time.monotonic()
        if should_activate:
            self.transcript_received.emit(normalized)

    def _poll_response(
        self,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        caller_tab_id = self._coerce_tab_id((payload or {}).get("tab_id"))
        with self._lock:
            commands: list[dict[str, Any]] = []
            remaining: deque[dict[str, Any]] = deque()
            for command in self._commands:
                target = self._coerce_tab_id(
                    command.get("_target_tab_id")
                )
                if (
                    caller_tab_id is None
                    or target is None
                    or target == caller_tab_id
                ):
                    commands.append(
                        {
                            key: value
                            for key, value in command.items()
                            if key != "_target_tab_id"
                        }
                    )
                else:
                    remaining.append(command)
            self._commands = remaining
            state = dict(self._app_state)
            selected = self._selected_tab_id
            if selected is None and self._last_player is not None:
                selected = self._coerce_tab_id(
                    self._last_player.get("tab_id")
                )
        state["source_selected"] = (
            selected is None
            or caller_tab_id is None
            or caller_tab_id == selected
        )
        return {
            "ok": True,
            "version": BRIDGE_VERSION,
            "bridge_instance_id": self._instance_id,
            "commands": commands,
            "app_state": state,
        }

    def _page_poll_response(
        self,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        caller_tab_id = self._coerce_tab_id((payload or {}).get("tab_id"))
        with self._lock:
            state = dict(self._app_state)
            selected = self._selected_tab_id
            if selected is None and self._last_player is not None:
                selected = self._coerce_tab_id(
                    self._last_player.get("tab_id")
                )
        state["source_selected"] = (
            selected is None
            or caller_tab_id is None
            or caller_tab_id == selected
        )
        return {
            "ok": True,
            "version": BRIDGE_VERSION,
            "bridge_instance_id": self._instance_id,
            "app_state": state,
        }
