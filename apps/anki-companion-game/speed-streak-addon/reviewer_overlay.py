from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer
from aqt.webview import AnkiWebView
from aqt.qt import QHBoxLayout, QKeySequence, QShortcut, QSizePolicy, Qt, QWidget

from .game_state import CompanionGameEngine
from .haptics import HapticsController
from .review_later import open_review_later_manager, sync_review_later_membership


ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__)
ADDON_ROOT = Path(__file__).resolve().parent


class ReviewerOverlayController:
    def __init__(self) -> None:
        self.engine = CompanionGameEngine()
        self.haptics = HapticsController()
        self._last_nonce_sent = -1
        self._wrapped = False
        self._timer = None
        self._sidebar_container = None
        self._sidebar_web = None
        self._pause_shortcut = None
        self._auto_paused_for_non_review = False
        self._last_reviewer_signature = ""
        self._load_persisted_settings()

    def install(self) -> None:
        gui_hooks.webview_did_receive_js_message.append(self.on_js_message)
        self._install_reviewer_wrappers()
        self._start_timer()
        self._install_shortcut()

    def on_js_message(self, handled: tuple[bool, Any], message: str, context: Any) -> tuple[bool, Any]:
        if message == "speed-streak:reset":
            self.engine.hard_reset()
            self._last_nonce_sent = -1
            self._push_state(only_if_changed=False)
            self.haptics.play_pattern("reset")
            return (True, None)
        if message == "speed-streak:toggle-pause":
            event = self.engine.toggle_pause()
            if event:
                self._push_state(only_if_changed=False)
            return (True, None)
        if message.startswith("speed-streak:update-settings:"):
            payload = message.split("speed-streak:update-settings:", 1)[1]
            try:
                data = json.loads(payload)
                question_seconds = float(data.get("questionSeconds", 12))
                answer_seconds = float(data.get("answerSeconds", 8))
                time_drain_flag = int(data.get("timeDrainFlag", 0))
                review_later_flag = int(data.get("reviewLaterFlag", 0))
            except Exception:
                return (True, None)
            self.engine.update_time_limits(
                question_seconds=question_seconds,
                answer_seconds=answer_seconds,
                time_drain_flag=time_drain_flag,
                review_later_flag=review_later_flag,
            )
            self._save_persisted_settings()
            self._push_state(only_if_changed=False)
            return (True, None)
        if message == "speed-streak:default-settings":
            self.engine.reset_settings_to_defaults()
            self._save_persisted_settings()
            self._push_state(only_if_changed=False)
            return (True, None)
        if message == "speed-streak:open-review-later-manager":
            open_review_later_manager(self.engine.state.review_later_flag)
            return (True, None)
        return handled

    def _install_shortcut(self) -> None:
        if self._pause_shortcut is not None:
            return
        self._pause_shortcut = QShortcut(QKeySequence("P"), mw)
        self._pause_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._pause_shortcut.activated.connect(self._on_pause_shortcut)

    def _install_reviewer_wrappers(self) -> None:
        if self._wrapped:
            return
        self._wrapped = True

        original_show_question = Reviewer._showQuestion
        original_show_answer = Reviewer._showAnswer
        original_answer_card = Reviewer._answerCard
        controller = self

        def wrapped_show_question(reviewer: Reviewer) -> Any:
            result = original_show_question(reviewer)
            return result

        def wrapped_show_answer(reviewer: Reviewer) -> Any:
            result = original_show_answer(reviewer)
            return result

        def wrapped_answer_card(reviewer: Reviewer, ease: int) -> Any:
            controller._handle_rate(reviewer, ease)
            result = original_answer_card(reviewer, ease)
            return result

        Reviewer._showQuestion = wrapped_show_question
        Reviewer._showAnswer = wrapped_show_answer
        Reviewer._answerCard = wrapped_answer_card

        for method_name in ("onBuryCard", "onBuryNote"):
            if not hasattr(Reviewer, method_name):
                continue
            original_method = getattr(Reviewer, method_name)

            def wrapped_bury(reviewer: Reviewer, _original=original_method) -> Any:
                previous_card_id = str(getattr(getattr(reviewer, "card", None), "id", ""))
                controller._handle_skip(reviewer)
                result = _original(reviewer)
                next_card = getattr(reviewer, "card", None)
                next_card_id = str(getattr(next_card, "id", ""))
                if controller.engine.state.skip_pending and next_card is not None and next_card_id and next_card_id != previous_card_id:
                    controller._handle_question_shown(reviewer)
                return result

            setattr(Reviewer, method_name, wrapped_bury)

    def _start_timer(self) -> None:
        self._timer = mw.progress.timer(100, self._on_tick, repeat=True)

    def _on_pause_shortcut(self) -> None:
        if getattr(mw, "state", "") != "review":
            return
        event = self.engine.toggle_pause()
        if event:
            self._push_state(only_if_changed=False)

    def _on_tick(self) -> None:
        if getattr(mw, "state", "") != "review":
            self._handle_non_review_state()
            return

        self._handle_review_state()
        self._sync_reviewer_surface()
        self._sync_live_flag_state()
        event = self.engine.check_timeout()
        if event:
            self.haptics.play_pattern("timeout")
            self._push_state(only_if_changed=False)
        else:
            self._push_state(only_if_changed=False)

    def _handle_non_review_state(self) -> None:
        self._set_sidebar_hidden(True)
        self._last_reviewer_signature = ""
        state = self.engine.state
        if (
            not self._auto_paused_for_non_review
            and state.synced
            and state.phase != "idle"
            and not state.paused
            and state.phase_limit_ms > 0
        ):
            event = self.engine.toggle_pause()
            if event:
                self._auto_paused_for_non_review = True
                self._push_state(only_if_changed=False)

    def _handle_review_state(self) -> None:
        self._set_sidebar_hidden(False)
        if self._auto_paused_for_non_review and self.engine.state.paused:
            event = self.engine.toggle_pause()
            self._auto_paused_for_non_review = False
            if event:
                self._push_state(only_if_changed=False)

    def _sync_live_flag_state(self) -> None:
        reviewer = getattr(mw, "reviewer", None)
        card = getattr(reviewer, "card", None) if reviewer else None
        if card is None:
            return
        next_flag = self._flag_for_card(card)
        previous_flag = int(self.engine.state.current_card_flag or 0)
        event = self.engine.on_flag_changed(card_flag=next_flag)
        if next_flag != previous_flag:
            sync_review_later_membership(
                card_id=int(getattr(card, "id", 0) or 0),
                note_id=self._note_id_for_card(card),
                current_flag=next_flag,
                review_later_flag=int(self.engine.state.review_later_flag or 0),
            )
        if event:
            self._push_state(only_if_changed=False)

    def _sync_reviewer_surface(self) -> None:
        reviewer = getattr(mw, "reviewer", None)
        card = getattr(reviewer, "card", None) if reviewer else None
        if reviewer is None or card is None:
            return

        card_id = str(getattr(card, "id", "") or "")
        if not card_id:
            return

        side = str(getattr(reviewer, "state", "") or "question").lower()
        if side not in {"question", "answer"}:
            side = "question"

        signature = f"{card_id}:{side}"
        if signature == self._last_reviewer_signature:
            return

        self._last_reviewer_signature = signature
        if side == "answer":
            self._handle_answer_shown(reviewer)
            return
        self._handle_question_shown(reviewer)

    def _handle_question_shown(self, reviewer: Reviewer) -> None:
        self._ensure_sidebar(reviewer)
        card = getattr(reviewer, "card", None)
        if card is None:
            return
        deck_name = self._deck_name_for_card(card)
        card_flag = self._flag_for_card(card)
        event = self.engine.sync_visible_question_surface(card_id=str(card.id), deck_name=deck_name, card_flag=card_flag)
        sync_review_later_membership(
            card_id=int(getattr(card, "id", 0) or 0),
            note_id=self._note_id_for_card(card),
            current_flag=card_flag,
            review_later_flag=int(self.engine.state.review_later_flag or 0),
        )
        if event == "sync":
            self.haptics.play_pattern("sync")
        self._push_state(only_if_changed=False)

    def _handle_answer_shown(self, reviewer: Reviewer) -> None:
        card = getattr(reviewer, "card", None)
        if card is None:
            return
        event = self.engine.sync_visible_answer_surface(
            card_id=str(card.id),
            deck_name=self._deck_name_for_card(card),
            card_flag=self._flag_for_card(card),
        )
        if event == "reveal":
            self.haptics.play_pattern("reveal")
            self._push_state(only_if_changed=False)

    def _handle_rate(self, reviewer: Reviewer, ease: int) -> None:
        event = self.engine.on_rate(ease)
        if not event:
            return
        if event == "again":
            self.haptics.play_pattern("again")
        elif event == "again-on-time":
            self.haptics.play_pattern("hard")
        elif event == "hard":
            self.haptics.play_pattern("hard")
        elif event == "good":
            self.haptics.play_pattern("good")
        elif event == "easy":
            self.haptics.play_pattern("easy")
        self._push_state(only_if_changed=False)

    def _handle_skip(self, reviewer: Reviewer) -> None:
        event = self.engine.on_skip()
        if event == "skip":
            self.haptics.play_pattern("skip")
            self._push_state(only_if_changed=False)

    def _push_state(self, *, only_if_changed: bool = True) -> None:
        if self._sidebar_web is None:
            return
        state = self.engine.export()
        nonce = state.get("eventNonce", -1)
        if only_if_changed and nonce == self._last_nonce_sent:
            return
        self._last_nonce_sent = nonce
        payload = json.dumps(
            {
                **state,
                "hapticsAvailable": int(self.haptics.available),
            }
        )
        self._sidebar_web.eval(f"window.SpeedStreak && window.SpeedStreak.receiveState({payload});")

    def _ensure_sidebar(self, reviewer: Reviewer) -> None:
        if self._sidebar_web is not None and self._sidebar_container is not None:
            return

        review_web = getattr(reviewer, "web", None)
        if review_web is None:
            return

        host = review_web.parentWidget()
        if host is None or host.layout() is None:
            return

        host_layout = host.layout()
        index = host_layout.indexOf(review_web)
        if index < 0:
            return

        host_layout.removeWidget(review_web)

        container = QWidget(host)
        container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        container.setMinimumHeight(0)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar_web = AnkiWebView(container)
        sidebar_web.setFixedWidth(380)
        sidebar_web.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        sidebar_web.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sidebar_web.setMinimumHeight(0)

        review_web.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        review_web.setMinimumHeight(0)
        sidebar_web.stdHtml(self._sidebar_html())

        layout.addWidget(sidebar_web, 0)
        layout.addWidget(review_web, 1)
        host_layout.insertWidget(index, container, 1)

        self._sidebar_container = container
        self._sidebar_web = sidebar_web

    def _set_sidebar_hidden(self, hidden: bool) -> None:
        if self._sidebar_web is None:
            return
        if self._sidebar_web is not None:
            self._sidebar_web.setVisible(not hidden)
            if not hidden:
                self._sidebar_web.setFixedWidth(380)
            else:
                self._sidebar_web.setFixedWidth(0)
        action = "add" if hidden else "remove"
        try:
            self._sidebar_web.eval(
                f"""
                (() => {{
                  const node = document.getElementById("speed-streak-sidebar");
                  if (node) {{
                    node.classList.{action}("hidden");
                  }}
                }})()
                """
            )
        except Exception:
            pass

    def _sidebar_html(self) -> str:
        css = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
        js = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    html, body {{
      margin: 0;
      width: 100%;
      height: 100vh;
      min-height: 100vh;
      overflow: hidden;
      background: #0b0b0b;
    }}
    body {{
      position: relative;
    }}
    {css}
  </style>
</head>
<body>
  <script>
    {js}
  </script>
</body>
</html>
"""

    def _deck_name_for_card(self, card: Any) -> str:
        did = getattr(card, "odid", 0) or getattr(card, "did", 0)
        try:
            return mw.col.decks.name(did)
        except Exception:
            return "Unknown Deck"

    def _note_id_for_card(self, card: Any) -> int:
        try:
            note = card.note()
            return int(getattr(note, "id", 0) or 0)
        except Exception:
            return 0

    def _load_persisted_settings(self) -> None:
        config = mw.addonManager.getConfig(ADDON_PACKAGE) or {}
        try:
            self.engine.update_time_limits(
                question_seconds=float(config.get("question_seconds", 12)),
                answer_seconds=float(config.get("answer_seconds", 8)),
                time_drain_flag=int(config.get("time_drain_flag", 0)),
                review_later_flag=int(config.get("review_later_flag", 0)),
            )
        except Exception:
            self.engine.update_time_limits(
                question_seconds=12,
                answer_seconds=8,
                time_drain_flag=0,
                review_later_flag=0,
            )

    def _save_persisted_settings(self) -> None:
        state = self.engine.state
        config = {
            "question_seconds": state.question_limit_ms / 1000,
            "answer_seconds": state.review_limit_ms / 1000,
            "time_drain_flag": state.time_drain_flag,
            "review_later_flag": state.review_later_flag,
        }
        mw.addonManager.writeConfig(ADDON_PACKAGE, config)

    def _flag_for_card(self, card: Any) -> int:
        try:
            user_flag = getattr(card, "userFlag", None)
            if callable(user_flag):
                return int(user_flag())
            if user_flag is not None:
                return int(user_flag)
        except Exception:
            pass

        try:
            user_flag = getattr(card, "user_flag", None)
            if callable(user_flag):
                return int(user_flag())
            if user_flag is not None:
                return int(user_flag)
        except Exception:
            pass

        try:
            flags = int(getattr(card, "flags", 0))
            return flags & 0b111
        except Exception:
            return 0


controller: Optional[ReviewerOverlayController] = None


def install() -> None:
    global controller
    if controller is None:
        controller = ReviewerOverlayController()
        controller.install()
