from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote
from typing import Any, Optional

from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer
from aqt.webview import AnkiWebView
from aqt.qt import QHBoxLayout, QKeySequence, QShortcut, QSizePolicy, Qt, QTimer, QWidget

from .game_state import CompanionGameEngine
from .haptics import HapticsController
from .review_later import open_review_later_manager, sync_review_later_membership
from .settings_dialog import open_settings_dialog
from .stats_dialog import open_stats_dialog
from .stats_store import StatsStore
from .web_assets import WEB_ASSETS


ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__)
ADDON_ROOT = Path(__file__).resolve().parent
SIDEBAR_EXPANDED_WIDTH = 316
SIDEBAR_COLLAPSED_WIDTH = 36


def _read_web_asset(*parts: str) -> str:
    asset_path = ADDON_ROOT.joinpath(*parts)
    try:
        return asset_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        asset_name = "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
        fallback = WEB_ASSETS.get(str(parts[-1]))
        if fallback is not None:
            print(f"Speed Streak v1.1: using embedded fallback asset for {asset_name}")
            return fallback
        print(f"Speed Streak v1.1: missing web asset {asset_path}")
        return ""


class ReviewerOverlayController:
    def __init__(self) -> None:
        self.engine = CompanionGameEngine()
        self.haptics = HapticsController()
        self.stats_store = StatsStore(ADDON_ROOT)
        self._last_nonce_sent = -1
        self._wrapped = False
        self._timer = None
        self._sidebar_container = None
        self._sidebar_web = None
        self._review_web = None
        self._pause_shortcut = None
        self._undo_action_connected = False
        self._auto_paused_for_non_review = False
        self._last_reviewer_signature = ""
        self._recorded_review_event_ids: list[int] = []
        self._card_timer_bootstrap = self._build_card_timer_bootstrap()
        self._sidebar_background = self._default_sidebar_background()
        self._load_persisted_settings()

    def install(self) -> None:
        gui_hooks.webview_did_receive_js_message.append(self.on_js_message)
        self._install_reviewer_wrappers()
        self._start_timer()
        self._install_shortcut()
        self._install_undo_listener()

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
        if message == "speed-streak:toggle-enabled":
            event = self.engine.set_enabled(not self.engine.state.enabled)
            self._save_persisted_settings()
            if self.engine.state.enabled and getattr(mw, "state", "") == "review":
                self._last_reviewer_signature = ""
                self._sync_reviewer_surface()
            if event:
                self._push_state(only_if_changed=False)
            return (True, None)
        if message.startswith("speed-streak:card-background:"):
            payload = message.split("speed-streak:card-background:", 1)[1]
            try:
                data = json.loads(unquote(payload))
                color = str(data.get("color", "") or "").strip()
            except Exception:
                color = ""
            self._sidebar_background = color or self._default_sidebar_background()
            self._push_state(only_if_changed=False)
            return (True, None)
        if message == "speed-streak:open-settings":
            if not self.engine.state.paused and self.engine.state.visuals_enabled:
                self.engine.toggle_pause()
                self._push_state(only_if_changed=False)
            open_settings_dialog(self)
            return (True, None)
        if message.startswith("speed-streak:update-settings:"):
            payload = message.split("speed-streak:update-settings:", 1)[1]
            try:
                data = json.loads(payload)
                question_seconds = float(data.get("questionSeconds", 12))
                answer_seconds = float(data.get("answerSeconds", 8))
                time_drain_flag = int(data.get("timeDrainFlag", 0))
                review_later_flag = int(data.get("reviewLaterFlag", 0))
                visuals_enabled = bool(data.get("visualsEnabled", True))
                show_card_timer = bool(data.get("showCardTimer", True))
                custom_timer_colors = bool(data.get("customTimerColors", False))
                custom_timer_color_level = float(data.get("customTimerColorLevel", 0))
                appearance_mode = str(data.get("appearanceMode", "midnight"))
                custom_colors = dict(data.get("customColors", {}) or {})
            except Exception:
                return (True, None)
            previous_visuals_enabled = bool(self.engine.state.visuals_enabled)
            self.engine.update_time_limits(
                question_seconds=question_seconds,
                answer_seconds=answer_seconds,
                time_drain_flag=time_drain_flag,
                review_later_flag=review_later_flag,
                visuals_enabled=visuals_enabled,
                show_card_timer=show_card_timer,
                custom_timer_colors=custom_timer_colors,
                custom_timer_color_level=custom_timer_color_level,
                appearance_mode=appearance_mode,
                custom_colors=custom_colors,
            )
            self._save_persisted_settings()
            if previous_visuals_enabled != self.engine.state.visuals_enabled and getattr(mw, "state", "") == "review":
                self._last_reviewer_signature = ""
                self._sync_reviewer_surface()
            self._push_state(only_if_changed=False)
            return (True, None)
        if message == "speed-streak:toggle-collapsed":
            state = self.engine.state
            self.engine.update_time_limits(
                question_seconds=state.question_limit_ms / 1000,
                answer_seconds=state.review_limit_ms / 1000,
                time_drain_flag=state.time_drain_flag,
                review_later_flag=state.review_later_flag,
                visuals_enabled=state.visuals_enabled,
                show_card_timer=state.show_card_timer,
                custom_timer_colors=state.custom_timer_colors,
                custom_timer_color_level=state.custom_timer_color_level,
                sidebar_collapsed=not state.sidebar_collapsed,
                appearance_mode=state.appearance_mode,
                custom_colors=dict(state.custom_colors),
            )
            self._save_persisted_settings()
            self._apply_sidebar_width()
            self._push_state(only_if_changed=False)
            return (True, None)
        if message == "speed-streak:default-settings":
            self.engine.reset_settings_to_defaults()
            self._save_persisted_settings()
            self._apply_sidebar_width()
            self._push_state(only_if_changed=False)
            return (True, None)
        if message == "speed-streak:open-review-later-manager":
            open_review_later_manager(self.engine.state.review_later_flag)
            return (True, None)
        if message == "speed-streak:open-stats":
            open_stats_dialog(self.engine, self.stats_store)
            return (True, None)
        return handled

    def apply_settings_from_dialog(
        self,
        *,
        question_seconds: float,
        answer_seconds: float,
        time_drain_flag: int,
        review_later_flag: int,
        show_card_timer: bool,
        visuals_enabled: bool,
        custom_timer_colors: bool,
        custom_timer_color_level: float,
        appearance_mode: str,
        custom_colors: dict[str, str] | None = None,
    ) -> None:
        previous_visuals_enabled = bool(self.engine.state.visuals_enabled)
        self.engine.update_time_limits(
            question_seconds=question_seconds,
            answer_seconds=answer_seconds,
            time_drain_flag=time_drain_flag,
            review_later_flag=review_later_flag,
            visuals_enabled=visuals_enabled,
            show_card_timer=show_card_timer,
            custom_timer_colors=custom_timer_colors,
            custom_timer_color_level=custom_timer_color_level,
            appearance_mode=appearance_mode,
            custom_colors=custom_colors,
        )
        self._save_persisted_settings()
        if previous_visuals_enabled != self.engine.state.visuals_enabled and getattr(mw, "state", "") == "review":
            self._last_reviewer_signature = ""
            self._sync_reviewer_surface()
        self._push_state(only_if_changed=False)

    def open_review_later_manager_from_dialog(self) -> None:
        open_review_later_manager(self.engine.state.review_later_flag)

    def open_stats_from_dialog(self) -> None:
        open_stats_dialog(self.engine, self.stats_store)

    def reset_defaults_from_dialog(self) -> None:
        self.engine.reset_settings_to_defaults()
        self._save_persisted_settings()
        self._apply_sidebar_width()
        self._push_state(only_if_changed=False)

    def reset_game_from_dialog(self) -> None:
        self.engine.hard_reset()
        self._last_nonce_sent = -1
        self._push_state(only_if_changed=False)
        self.haptics.play_pattern("reset")

    def _install_shortcut(self) -> None:
        if self._pause_shortcut is not None:
            return
        self._pause_shortcut = QShortcut(QKeySequence("P"), mw)
        self._pause_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._pause_shortcut.activated.connect(self._on_pause_shortcut)

    def _install_undo_listener(self) -> None:
        if self._undo_action_connected:
            return
        action = getattr(getattr(mw, "form", None), "actionUndo", None)
        if action is None:
            return
        try:
            action.triggered.connect(self._on_anki_undo_triggered)
            self._undo_action_connected = True
        except Exception:
            pass

    def _install_reviewer_wrappers(self) -> None:
        if self._wrapped:
            return
        self._wrapped = True

        original_answer_card = Reviewer._answerCard
        controller = self

        def wrapped_answer_card(reviewer: Reviewer, ease: int) -> Any:
            snapshot = controller.engine.capture_review_undo_snapshot()
            event = controller.engine.on_rate(ease)
            if not event:
                return original_answer_card(reviewer, ease)
            try:
                result = original_answer_card(reviewer, ease)
            except Exception:
                controller.engine.discard_review_undo_snapshot(snapshot)
                controller._push_state(only_if_changed=False)
                raise
            controller.engine.commit_review_undo_snapshot(snapshot)
            controller._finalize_rate(event)
            return result

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

    def _on_anki_undo_triggered(self) -> None:
        if getattr(mw, "state", "") != "review":
            return
        QTimer.singleShot(0, self._apply_anki_undo_to_speed_streak)

    def _apply_anki_undo_to_speed_streak(self) -> None:
        if not self.engine.undo_last_review():
            return
        if self._recorded_review_event_ids:
            self.stats_store.delete_review_event(self._recorded_review_event_ids.pop())
        self._last_nonce_sent = -1
        if getattr(mw, "state", "") == "review":
            self._last_reviewer_signature = ""
            self._sync_reviewer_surface()
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
        self._hide_card_timer()
        self._last_reviewer_signature = ""
        state = self.engine.state
        if (
            not self._auto_paused_for_non_review
            and state.synced
            and state.phase != "idle"
            and not state.paused
            and state.phase_limit_ms > 0
            and state.visuals_enabled
        ):
            event = self.engine.toggle_pause()
            if event:
                self._auto_paused_for_non_review = True
                self._push_state(only_if_changed=False)

    def _handle_review_state(self) -> None:
        self._set_sidebar_hidden(False)
        if self._auto_paused_for_non_review and self.engine.state.paused:
            if not self.engine.state.enabled or not self.engine.state.visuals_enabled:
                return
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
                card_ord=self._card_ord_for_card(card),
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
            card_ord=self._card_ord_for_card(card),
            current_flag=card_flag,
            review_later_flag=int(self.engine.state.review_later_flag or 0),
        )
        if event == "sync":
            self.haptics.play_pattern("sync")
        self._push_state(only_if_changed=False)
        self._restore_review_focus()

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
        self._restore_review_focus()

    def _finalize_rate(self, event: str) -> None:
        metrics = self.engine.take_last_review_metrics()
        if metrics:
            event_id = self.stats_store.record_review(
                card_id=int(metrics.get("card_id", 0) or 0),
                deck_name=str(metrics.get("deck_name", "") or ""),
                active_ms=int(metrics.get("active_ms", 0) or 0),
                ease=int(metrics.get("ease", 0) or 0),
                correct=int(metrics.get("correct", 0) or 0),
            )
            if event_id > 0:
                self._recorded_review_event_ids.append(event_id)
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
        if self._sidebar_web is None and self._review_web is None:
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
                "sidebarBackground": self._sidebar_background or self._default_sidebar_background(),
            }
        )
        if self._sidebar_web is not None:
            self._sidebar_web.eval(f"window.SpeedStreak && window.SpeedStreak.receiveState({payload});")
        self._push_card_timer_state(payload)

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
        container.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar_web = AnkiWebView(container)
        sidebar_web.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)
        sidebar_web.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        sidebar_web.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sidebar_web.setMinimumHeight(0)

        review_web.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        review_web.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        review_web.setMinimumHeight(0)
        sidebar_web.stdHtml(self._sidebar_html())

        layout.addWidget(sidebar_web, 0)
        layout.addWidget(review_web, 1)
        host_layout.insertWidget(index, container, 1)

        self._sidebar_container = container
        self._sidebar_web = sidebar_web
        self._review_web = review_web
        self._apply_sidebar_width()
        self._restore_review_focus()

    def _set_sidebar_hidden(self, hidden: bool) -> None:
        if self._sidebar_web is None:
            return
        if self._sidebar_web is not None:
            self._sidebar_web.setVisible(not hidden)
            if not hidden:
                self._apply_sidebar_width()
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
        css = _read_web_asset("web", "overlay.css")
        js = _read_web_asset("web", "overlay.js")
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
      background: transparent;
    }}
    body {{
      position: relative;
    }}
    {css}
  </style>
</head>
<body>
  <script>
    (() => {{
      const renderSidebarError = (message) => {{
        const existing = document.getElementById("speed-streak-bootstrap-error");
        if (existing) {{
          existing.textContent = message;
          return;
        }}
        const node = document.createElement("div");
        node.id = "speed-streak-bootstrap-error";
        node.style.cssText = "box-sizing:border-box;margin:12px;padding:12px;border-radius:12px;background:rgba(120,20,40,0.92);color:#fff3f5;font:12px/1.4 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;white-space:pre-wrap;";
        node.textContent = message;
        (document.body || document.documentElement).appendChild(node);
      }};
      window.addEventListener("error", (event) => {{
        const details = event && event.error && event.error.stack ? event.error.stack : (event && event.message ? event.message : "Unknown sidebar error");
        renderSidebarError(`Speed Streak sidebar error\\n${{details}}`);
      }});
      window.addEventListener("unhandledrejection", (event) => {{
        const reason = event && event.reason ? (event.reason.stack || String(event.reason)) : "Unknown sidebar rejection";
        renderSidebarError(`Speed Streak sidebar error\\n${{reason}}`);
      }});
    }})()
  </script>
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

    def _card_ord_for_card(self, card: Any) -> int:
        try:
            return int(getattr(card, "ord", 0) or 0)
        except Exception:
            return 0

    def _load_persisted_settings(self) -> None:
        config = mw.addonManager.getConfig(ADDON_PACKAGE) or {}
        try:
            self.engine.update_time_limits(
                question_seconds=float(config.get("question_seconds", 12)),
                answer_seconds=float(config.get("answer_seconds", 8)),
                time_drain_flag=int(config.get("time_drain_flag", 2)),
                review_later_flag=int(config.get("review_later_flag", 4)),
                visuals_enabled=bool(config.get("visuals_enabled", True)),
                show_card_timer=bool(config.get("show_card_timer", True)),
                custom_timer_colors=bool(config.get("custom_timer_colors", False)),
                custom_timer_color_level=float(config.get("custom_timer_color_level", 0)),
                sidebar_collapsed=bool(config.get("sidebar_collapsed", False)),
                appearance_mode=str(config.get("appearance_mode", "midnight")),
                custom_colors=dict(config.get("custom_colors", {}) or {}),
            )
            self.engine.state.enabled = bool(config.get("enabled", True))
        except Exception:
            self.engine.update_time_limits(
                question_seconds=12,
                answer_seconds=8,
                time_drain_flag=2,
                review_later_flag=4,
                visuals_enabled=True,
                show_card_timer=True,
                custom_timer_colors=False,
                custom_timer_color_level=0,
                sidebar_collapsed=False,
                appearance_mode="midnight",
                custom_colors={},
            )
            self.engine.state.enabled = True

    def _save_persisted_settings(self) -> None:
        state = self.engine.state
        config = {
            "enabled": bool(state.enabled),
            "visuals_enabled": bool(state.visuals_enabled),
            "show_card_timer": bool(state.show_card_timer),
            "custom_timer_colors": bool(state.custom_timer_colors),
            "custom_timer_color_level": float(state.custom_timer_color_level),
            "sidebar_collapsed": bool(state.sidebar_collapsed),
            "appearance_mode": str(state.appearance_mode),
            "custom_colors": dict(state.custom_colors),
            "question_seconds": state.question_limit_ms / 1000,
            "answer_seconds": state.review_limit_ms / 1000,
            "time_drain_flag": state.time_drain_flag,
            "review_later_flag": state.review_later_flag,
        }
        mw.addonManager.writeConfig(ADDON_PACKAGE, config)

    def _apply_sidebar_width(self) -> None:
        if self._sidebar_web is None or not self._sidebar_web.isVisible():
            return
        width = SIDEBAR_COLLAPSED_WIDTH if self.engine.state.sidebar_collapsed else SIDEBAR_EXPANDED_WIDTH
        self._sidebar_web.setFixedWidth(width)

    def _push_card_timer_state(self, payload: str) -> None:
        if self._review_web is None:
            return
        try:
            self._review_web.eval(
                f"""
                (() => {{
                  if (!window.SpeedStreakCardTimer) {{
                    {self._card_timer_bootstrap}
                  }}
                  if (window.SpeedStreakCardTimer) {{
                    window.SpeedStreakCardTimer.receiveState({payload});
                  }}
                }})()
                """
            )
        except Exception:
            pass

    def _hide_card_timer(self) -> None:
        if self._review_web is None:
            return
        try:
            self._review_web.eval(
                """
                (() => {
                  if (window.SpeedStreakCardTimer) {
                    window.SpeedStreakCardTimer.hide();
                  }
                })()
                """
            )
        except Exception:
            pass

    def _build_card_timer_bootstrap(self) -> str:
        css = _read_web_asset("web", "card_timer.css")
        js = _read_web_asset("web", "card_timer.js")
        css_json = json.dumps(css)
        return f"""
        const existingStyle = document.getElementById("speed-streak-card-timer-style");
        if (!existingStyle) {{
          const style = document.createElement("style");
          style.id = "speed-streak-card-timer-style";
          style.textContent = {css_json};
          document.head.appendChild(style);
        }}
        {js}
        """

    def _default_sidebar_background(self) -> str:
        try:
            color = mw.app.palette().base().color()
            return color.name()
        except Exception:
            return "#2f2f31"

    def _restore_review_focus(self) -> None:
        if self._review_web is None:
            return
        try:
            self._review_web.setFocus()
        except Exception:
            pass

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
