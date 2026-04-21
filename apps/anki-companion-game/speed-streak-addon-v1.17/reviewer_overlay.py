from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import unquote
from typing import Any, Optional

from anki.cards import Card
from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer
from aqt.webview import AnkiWebView
from aqt.qt import QAction, QApplication, QByteArray, QEvent, QHBoxLayout, QMenu, QMessageBox, QObject, QSizePolicy, Qt, QTimer, QVBoxLayout, QWidget

from .addon_meta import ensure_meta_json
from .anki_flag_colors import get_anki_flag_palette
from .audio_feedback import AudioFeedbackController
from .data_paths import speed_streak_data_root
from .display_mode import (
    DISPLAY_MODE_COMPATIBILITY,
    DISPLAY_MODE_INLINE,
    normalize_display_mode,
)
from .feedback_catalog import (
    AUDIO_TRIMMED_DIRECTORY_NAME,
    DEFAULT_AUDIO_ENABLED,
    DEFAULT_AUDIO_FILE,
    default_audio_event_files,
    default_haptic_event_patterns,
    haptic_pattern_sequences,
    normalize_audio_event_files,
    normalize_haptic_event_patterns,
)
from .game_state import CompanionGameEngine
from .haptics import HapticsController
from .review_later import (
    REVIEW_LATER_TODAY_OPEN_MESSAGE,
    build_review_later_today_button_html,
    inject_shared_deck_action_html,
    open_review_later_manager,
    review_later_today_count,
    sync_review_later_membership,
)
from .render_mode import (
    RENDER_MODE_CLASSIC,
    RENDER_MODE_ULTRA_LOW_RESOURCE,
    normalize_render_mode,
)
from .settings_dialog import open_settings_dialog
from .shortcuts import default_shortcut_bindings, normalize_shortcut_bindings
from .sphere_mode import SPHERE_MODE_CLASSIC, normalize_sphere_mode
from .stats_dialog import open_stats_dialog
from .stats_store import StatsStore
from .visual_mode import VISUAL_MODE_LIGHTWEIGHT_ROWS, VISUAL_MODE_SPHERE, normalize_visual_mode
from .web_assets import WEB_ASSETS


ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__)
ADDON_ROOT = Path(__file__).resolve().parent
ADDON_DISPLAY_NAME = "Speed Streak v1.17"
SIDEBAR_EXPANDED_WIDTH = 316
SIDEBAR_COLLAPSED_WIDTH = 36
INLINE_CONTAINER_OBJECT_NAME = "speedStreakInlineContainer"
INLINE_SIDEBAR_OBJECT_NAME = "speedStreakInlineSidebar"
BROWSER_HAPTIC_PATTERN_SEQUENCES = haptic_pattern_sequences()
SYNC_AUDIO_SUPPRESSION_SECONDS = 0.4
WEBVIEW_AUDIO_EVENT_KEYS = {"again", "hard", "good", "easy"}
COMPATIBILITY_LAYOUT_VERSION = 3
TIME_DRAIN_FETCH_BATCH_SIZES = (32, 128, 512, 2048, 8192, 32768)
def _export_widget_geometry(widget: QWidget) -> str:
    try:
        encoded = widget.saveGeometry().toBase64()
        return bytes(encoded).decode("ascii") if encoded else ""
    except Exception:
        return ""


def _restore_widget_geometry(widget: QWidget, encoded: str) -> bool:
    text = str(encoded or "").strip()
    if not text:
        return False
    try:
        geometry = QByteArray.fromBase64(text.encode("ascii"))
        return bool(geometry) and widget.restoreGeometry(geometry)
    except Exception:
        return False


def _frame_margins(widget: QWidget) -> tuple[int, int, int, int]:
    try:
        geometry = widget.geometry()
        frame = widget.frameGeometry()
        left = max(0, int(geometry.x() - frame.x()))
        top = max(0, int(geometry.y() - frame.y()))
        right = max(0, int(frame.right() - geometry.right()))
        bottom = max(0, int(frame.bottom() - geometry.bottom()))
        return left, top, right, bottom
    except Exception:
        return 0, 0, 0, 0


def _ensure_window_frame_metrics(widget: QWidget) -> None:
    if widget.isVisible():
        return
    try:
        widget.show()
        QApplication.processEvents()
    except Exception:
        return


def _set_window_frame_geometry(widget: QWidget, x: int, y: int, width: int, height: int) -> None:
    left, top, right, bottom = _frame_margins(widget)
    min_width = max(1, int(getattr(widget, "minimumWidth", lambda: 0)() or 0))
    min_height = max(1, int(getattr(widget, "minimumHeight", lambda: 0)() or 0))
    content_width = max(min_width, int(width) - left - right)
    content_height = max(min_height, int(height) - top - bottom)
    widget.setGeometry(int(x) + left, int(y) + top, content_width, content_height)


class WindowGeometryTracker(QObject):
    def __init__(self, widget: QWidget, on_geometry_changed: Any) -> None:
        super().__init__(widget)
        self._widget = widget
        self._on_geometry_changed = on_geometry_changed
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emit_geometry_changed)
        widget.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: Any) -> bool:
        if watched is self._widget and event is not None:
            if event.type() in (
                QEvent.Type.Move,
                QEvent.Type.Resize,
                QEvent.Type.WindowStateChange,
            ):
                self._timer.start(200)
        return False

    def _emit_geometry_changed(self) -> None:
        if callable(self._on_geometry_changed):
            self._on_geometry_changed()


class FloatingSidebarWindow(QWidget):
    def __init__(self, on_geometry_changed: Any, on_request_review_focus: Any) -> None:
        super().__init__(mw, Qt.WindowType.Window)
        self._on_geometry_changed = on_geometry_changed
        self._on_request_review_focus = on_request_review_focus
        self._geometry_timer = QTimer(self)
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.timeout.connect(self._emit_geometry_changed)
        self.setWindowTitle(ADDON_DISPLAY_NAME)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setWindowFlag(Qt.WindowType.WindowTitleHint, True)
        self.setWindowFlag(Qt.WindowType.WindowSystemMenuHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        try:
            self.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, True)
        except AttributeError:
            pass
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMinimumSize(260, 420)
        self.resize(340, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web = AnkiWebView(self)
        self.web.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.web.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.web, 1)

    def export_geometry(self) -> str:
        return _export_widget_geometry(self)

    def restore_exported_geometry(self, encoded: str) -> bool:
        return _restore_widget_geometry(self, encoded)

    def moveEvent(self, event: Any) -> None:
        super().moveEvent(event)
        self._schedule_geometry_emit()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._schedule_geometry_emit()

    def _schedule_geometry_emit(self) -> None:
        self._geometry_timer.start(200)

    def _emit_geometry_changed(self) -> None:
        if callable(self._on_geometry_changed):
            self._on_geometry_changed(self.export_geometry())

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
        self._request_review_focus_soon()

    def focusInEvent(self, event: Any) -> None:
        super().focusInEvent(event)
        self._request_review_focus_soon()

    def mousePressEvent(self, event: Any) -> None:
        super().mousePressEvent(event)
        self._request_review_focus_soon()

    def _request_review_focus_soon(self) -> None:
        if callable(self._on_request_review_focus):
            QTimer.singleShot(0, self._on_request_review_focus)


def _read_web_asset(*parts: str) -> str:
    asset_path = ADDON_ROOT.joinpath(*parts)
    try:
        return asset_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        asset_name = "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
        fallback = WEB_ASSETS.get(str(parts[-1]))
        if fallback is not None:
            print(f"{ADDON_DISPLAY_NAME}: using embedded fallback asset for {asset_name}")
            return fallback
        print(f"{ADDON_DISPLAY_NAME}: missing web asset {asset_path}")
        return ""


def _web_asset_exists(*parts: str) -> bool:
    return ADDON_ROOT.joinpath(*parts).exists()


def _web_asset_url(*parts: str) -> str:
    return f"/_addons/{ADDON_PACKAGE}/{'/'.join(parts)}"


def _is_deck_browser_context(context: Any) -> bool:
    if context is getattr(mw, "deckBrowser", None):
        return True
    return getattr(getattr(context, "__class__", None), "__name__", "") == "DeckBrowser"


class ReviewerOverlayController:
    def __init__(self) -> None:
        self.engine = CompanionGameEngine()
        self.haptics = HapticsController()
        self.data_root = speed_streak_data_root(ADDON_ROOT)
        self.audio_feedback = AudioFeedbackController(
            ADDON_ROOT / AUDIO_TRIMMED_DIRECTORY_NAME,
            self.data_root,
        )
        self.stats_store = StatsStore(self.data_root)
        self.display_mode = DISPLAY_MODE_INLINE
        self.visual_mode = VISUAL_MODE_SPHERE
        self.sphere_mode = SPHERE_MODE_CLASSIC
        self.render_mode = RENDER_MODE_CLASSIC
        self._last_nonce_sent = -1
        self._wrapped = False
        self._timer = None
        self._sidebar_container = None
        self._floating_window: Optional[FloatingSidebarWindow] = None
        self._floating_geometry = ""
        self._compatibility_main_geometry = ""
        self._pre_compatibility_main_geometry = ""
        self._compatibility_review_layout_active = False
        self._geometry_persistence_suspended = False
        self._menu: Optional[QMenu] = None
        self._settings_action: Optional[QAction] = None
        self._review_later_action: Optional[QAction] = None
        self._sidebar_web = None
        self._review_web = None
        self._auto_paused_for_non_review = False
        self._last_reviewer_signature = ""
        self._recorded_review_event_ids: list[int] = []
        self._pending_review_undo_snapshot = None
        self._pending_review_card_id = 0
        self._display_mode_prompt_pending = False
        self._display_mode_prompt_scheduled = False
        self._display_mode_prompt_open = False
        self._pending_review_later_sync: Optional[dict[str, int]] = None
        self._last_reduced_live_update_bucket: Optional[int] = None
        self._card_timer_bootstrap = self._build_card_timer_bootstrap()
        self._sidebar_background = self._default_sidebar_background()
        self._last_audio_feedback_started_at = 0.0
        self._last_audio_feedback_event = ""
        self._pending_answer_feedback_event = ""
        self.shortcut_bindings = default_shortcut_bindings()
        self._last_timer_display_signature = ""
        self._last_timer_display_remaining_ms = -1
        self._last_timer_display_anchor_ms = 0
        self._non_review_surface_applied = False
        self._deferred_time_drain_card_ids: list[int] = []
        self.review_later_today_deck_button_enabled = False
        self._deck_browser_refresh_pending = False
        self._persist_settings_timer = QTimer(mw)
        self._persist_settings_timer.setSingleShot(True)
        self._persist_settings_timer.timeout.connect(self._flush_scheduled_persisted_settings_save)
        self._last_saved_config_signature = ""
        self._main_window_geometry_tracker = WindowGeometryTracker(mw, self._on_main_window_geometry_changed)
        self._load_persisted_settings()

    def install(self) -> None:
        self._install_reviewer_queue_wrapper()
        self._register_web_exports()
        self._install_menu()
        gui_hooks.webview_did_receive_js_message.append(self.on_js_message)
        gui_hooks.webview_will_set_content.append(self.on_webview_will_set_content)
        deck_browser_hook = getattr(gui_hooks, "deck_browser_will_render_content", None)
        if deck_browser_hook is not None:
            deck_browser_hook.append(self.on_deck_browser_will_render_content)
        gui_hooks.reviewer_did_show_question.append(self.on_reviewer_did_show_question)
        gui_hooks.reviewer_did_show_answer.append(self.on_reviewer_did_show_answer)
        gui_hooks.reviewer_will_answer_card.append(self.on_reviewer_will_answer_card)
        gui_hooks.reviewer_did_answer_card.append(self.on_reviewer_did_answer_card)
        gui_hooks.reviewer_will_bury_card.append(self.on_reviewer_will_bury_card)
        gui_hooks.reviewer_will_bury_note.append(self.on_reviewer_will_bury_note)
        gui_hooks.state_did_undo.append(self.on_state_did_undo)
        gui_hooks.state_shortcuts_will_change.append(self.on_state_shortcuts_will_change)
        self._start_timer()

    def _install_reviewer_queue_wrapper(self) -> None:
        if self._wrapped:
            return
        original = getattr(Reviewer, "_get_next_v3_card", None)
        if not callable(original) or getattr(original, "__speed_streak_time_drain_wrapper__", False):
            self._wrapped = True
            return

        def wrapped(reviewer: Reviewer) -> None:
            active_controller = controller
            if active_controller is None:
                original(reviewer)
                return
            active_controller._get_next_v3_card_with_time_drain_reordering(reviewer, original)

        setattr(wrapped, "__speed_streak_time_drain_wrapper__", True)
        Reviewer._get_next_v3_card = wrapped
        self._wrapped = True

    def _get_next_v3_card_with_time_drain_reordering(self, reviewer: Reviewer, original: Any) -> None:
        if not self._time_drain_review_last_enabled():
            self._restore_deferred_time_drain_cards()
            original(reviewer)
            return

        for _attempt in range(512):
            if not self._defer_top_time_drain_card_if_needed(reviewer):
                break

        original(reviewer)

    def _time_drain_review_last_enabled(self) -> bool:
        state = self.engine.state
        return bool(getattr(state, "time_drain_review_last", False)) and int(
            getattr(state, "time_drain_flag", 0) or 0
        ) > 0

    def _defer_top_time_drain_card_if_needed(self, reviewer: Reviewer) -> bool:
        if not self._time_drain_review_last_enabled():
            return False

        state = self.engine.state
        time_drain_flag = int(getattr(state, "time_drain_flag", 0) or 0)
        scheduler = getattr(getattr(getattr(reviewer, "mw", None), "col", None), "sched", None)
        get_queued_cards = getattr(scheduler, "get_queued_cards", None)
        bury_cards = getattr(scheduler, "bury_cards", None)
        if not callable(get_queued_cards) or not callable(bury_cards):
            return False

        for fetch_limit in TIME_DRAIN_FETCH_BATCH_SIZES:
            output = get_queued_cards(fetch_limit=fetch_limit)
            cards = list(getattr(output, "cards", []))
            if not cards:
                return self._restore_deferred_time_drain_cards()
            if self._flag_for_queued_card(reviewer, cards[0]) != time_drain_flag:
                return False
            first_non_time_drain_index = next(
                (
                    index
                    for index, queued_card in enumerate(cards)
                    if self._flag_for_queued_card(reviewer, queued_card) != time_drain_flag
                ),
                None,
            )
            if first_non_time_drain_index is None:
                if len(cards) < fetch_limit:
                    return False
                continue
            if first_non_time_drain_index == 0:
                return False
            return self._bury_queued_time_drain_card(bury_cards, cards[0])
        return False

    def _queued_card_id(self, queued_card: Any) -> int:
        backend_card = getattr(queued_card, "card", None)
        if backend_card is None:
            return 0
        try:
            return int(getattr(backend_card, "id", 0) or 0)
        except Exception:
            return 0

    def _bury_queued_time_drain_card(self, bury_cards: Any, queued_card: Any) -> bool:
        card_id = self._queued_card_id(queued_card)
        if card_id <= 0:
            return False
        try:
            bury_cards([card_id], manual=False)
        except TypeError:
            try:
                bury_cards([card_id])
            except Exception:
                return False
        except Exception:
            return False
        self._remember_deferred_time_drain_card(card_id)
        return True

    def _remember_deferred_time_drain_card(self, card_id: int) -> None:
        if int(card_id or 0) <= 0:
            return
        target_id = int(card_id)
        self._deferred_time_drain_card_ids = [
            existing_id
            for existing_id in self._deferred_time_drain_card_ids
            if int(existing_id or 0) != target_id
        ]
        self._deferred_time_drain_card_ids.append(target_id)

    def _restore_deferred_time_drain_cards(self) -> bool:
        if not self._deferred_time_drain_card_ids:
            return False
        scheduler = getattr(getattr(mw, "col", None), "sched", None)
        unbury_cards = getattr(scheduler, "unbury_cards", None)
        if not callable(unbury_cards):
            return False

        deferred_ids = [
            int(card_id)
            for card_id in dict.fromkeys(int(card_id or 0) for card_id in self._deferred_time_drain_card_ids)
            if int(card_id) > 0
        ]
        self._deferred_time_drain_card_ids = []
        restored = False
        for card_id in deferred_ids:
            try:
                unbury_cards([card_id])
                restored = True
            except Exception:
                continue
        return restored

    def _flag_for_queued_card(self, reviewer: Reviewer, queued_card: Any) -> int:
        backend_card = getattr(queued_card, "card", None)
        if backend_card is None:
            return 0
        try:
            return int(getattr(backend_card, "flags", 0) or 0) & 0b111
        except Exception:
            pass
        try:
            probe_card = Card(reviewer.mw.col, backend_card=backend_card)
        except TypeError:
            try:
                probe_card = Card(reviewer.mw.col)
                probe_card._load_from_backend_card(backend_card)
            except Exception:
                return 0
        except Exception:
            return 0
        return self._flag_for_card(probe_card)

    def available_audio_feedback_files(self) -> list[str]:
        return self.audio_feedback.available_files()

    def available_audio_feedback_options(self) -> list[tuple[str, str]]:
        return [(option.label, option.key) for option in self.audio_feedback.available_options()]

    def available_audio_feedback_groups(self, query: str = "") -> list[tuple[str, list[tuple[str, str]]]]:
        return [
            (category, [(option.file_label, option.key) for option in options])
            for category, options in self.audio_feedback.grouped_options(query)
        ]

    def normalize_audio_feedback_file(self, file_name: str) -> str:
        return self.audio_feedback.normalize_file(file_name)

    def audio_feedback_label(self, file_name: str) -> str:
        return self.audio_feedback.display_label(file_name)

    def import_audio_feedback_file(self, source_path: str) -> str:
        return self.audio_feedback.import_file(source_path)

    def preview_audio_feedback(self, file_name: str) -> bool:
        return self.audio_feedback.play(self.audio_feedback.normalize_file(file_name))

    def preview_haptic_pattern(self, pattern_key: str) -> bool:
        return self.haptics.preview_pattern(pattern_key)

    def current_shortcut_bindings(self) -> dict[str, str]:
        return dict(normalize_shortcut_bindings(self.shortcut_bindings))

    def shortcut_label(self, shortcut_key: str) -> str:
        return self.current_shortcut_bindings().get(shortcut_key, default_shortcut_bindings().get(shortcut_key, ""))

    def pause_shortcut_display(self) -> str:
        return self.shortcut_label("pause")

    def _normalize_feedback_preferences(self) -> None:
        state = self.engine.state
        state.audio_event_files = self.audio_feedback.normalize_event_files(
            state.audio_event_files,
            legacy_file=state.selected_audio_file,
        )
        state.selected_audio_file = self._preferred_audio_file(state.audio_event_files)
        state.haptic_event_patterns = normalize_haptic_event_patterns(state.haptic_event_patterns)

    def _preferred_audio_file(self, audio_event_files: dict[str, str] | None) -> str:
        for file_name in dict(audio_event_files or {}).values():
            normalized = self.audio_feedback.normalize_file(file_name)
            if normalized:
                return normalized
        return self.audio_feedback.default_file()

    def _audio_file_for_event(self, event_key: str) -> str:
        audio_event_files = dict(self.engine.state.audio_event_files or {})
        defaults = default_audio_event_files()
        selected = self.audio_feedback.normalize_file(
            audio_event_files.get(event_key, defaults.get(event_key, self.engine.state.selected_audio_file))
        )
        if selected:
            return selected
        legacy = self.audio_feedback.normalize_file(self.engine.state.selected_audio_file)
        if legacy:
            return legacy
        return self.audio_feedback.default_file()

    def _haptic_pattern_for_event(self, event_key: str) -> str:
        patterns = self.engine.state.haptic_event_patterns or default_haptic_event_patterns()
        pattern_key = str(patterns.get(event_key, "") or "").strip()
        if pattern_key:
            return pattern_key
        return default_haptic_event_patterns().get(event_key, "")

    def _play_audio_feedback(self, event_key: str) -> None:
        if not self.engine.state.audio_enabled:
            return
        now = time.monotonic()
        if (
            event_key == "sync"
            and self._last_audio_feedback_event
            and self._last_audio_feedback_event != "sync"
            and (now - self._last_audio_feedback_started_at) < SYNC_AUDIO_SUPPRESSION_SECONDS
        ):
            return
        selected = self._audio_file_for_event(event_key)
        if selected:
            played = False
            if event_key in WEBVIEW_AUDIO_EVENT_KEYS:
                played = self._play_review_web_audio_feedback(selected, interrupt=True)
            if not played:
                played = self.audio_feedback.play(selected, interrupt=(event_key != "sync"))
            if played:
                self._last_audio_feedback_started_at = now
                self._last_audio_feedback_event = event_key

    def _play_review_web_audio_feedback(self, file_name: str, *, interrupt: bool) -> bool:
        web = self._review_web or getattr(getattr(mw, "reviewer", None), "web", None)
        if web is None:
            return False
        relative_path = self.audio_feedback.export_relative_path(file_name)
        if not relative_path:
            return False
        try:
            web.setPlaybackRequiresGesture(False)
        except Exception:
            pass
        try:
            audio_url = _web_asset_url(*Path(relative_path).parts)
            interrupt_js = "true" if interrupt else "false"
            web.eval(
                f"""
                (() => {{
                  if (!window.SpeedStreakCardTimer) {{
                    {self._card_timer_bootstrap}
                  }}
                  if (window.SpeedStreakCardTimer && window.SpeedStreakCardTimer.playFeedbackAudio) {{
                    window.SpeedStreakCardTimer.playFeedbackAudio({json.dumps(audio_url)}, {interrupt_js});
                  }}
                }})()
                """
            )
            return True
        except Exception:
            return False

    def _play_haptic_feedback(self, event_key: str) -> None:
        self.haptics.play_pattern(self._haptic_pattern_for_event(event_key))

    def _play_feedback_event(self, event_key: str) -> None:
        self._play_audio_feedback(event_key)
        self._play_haptic_feedback(event_key)

    def _refresh_deck_browser(self) -> None:
        if getattr(mw, "state", "") != "deckBrowser":
            return
        deck_browser = getattr(mw, "deckBrowser", None)
        if deck_browser is None:
            return
        refresh = getattr(deck_browser, "refresh", None)
        if callable(refresh):
            try:
                refresh()
                return
            except Exception:
                pass
        show = getattr(deck_browser, "show", None)
        if callable(show):
            try:
                show()
            except Exception:
                pass

    def _request_deck_browser_refresh(self) -> None:
        self._deck_browser_refresh_pending = True

    def _flush_requested_deck_browser_refresh(self) -> None:
        if not self._deck_browser_refresh_pending:
            return
        if getattr(mw, "state", "") != "deckBrowser":
            return
        self._deck_browser_refresh_pending = False
        self._refresh_deck_browser()

    def set_review_later_today_deck_button_enabled(self, enabled: bool) -> bool:
        next_enabled = bool(enabled)
        if next_enabled == self.review_later_today_deck_button_enabled:
            self._request_deck_browser_refresh()
            return next_enabled
        self.review_later_today_deck_button_enabled = next_enabled
        self._save_persisted_settings()
        self._request_deck_browser_refresh()
        return next_enabled

    def on_js_message(self, handled: tuple[bool, Any], message: str, context: Any) -> tuple[bool, Any]:
        if message == "speed-streak:reset":
            self.engine.hard_reset()
            self._normalize_feedback_preferences()
            self._last_nonce_sent = -1
            self._push_state(only_if_changed=False)
            self._play_feedback_event("reset")
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
            self._open_settings_dialog()
            return (True, None)
        if message.startswith("speed-streak:update-settings:"):
            payload = message.split("speed-streak:update-settings:", 1)[1]
            try:
                previous_time_drain_flag = int(self.engine.state.time_drain_flag or 0)
                previous_time_drain_review_last = bool(self.engine.state.time_drain_review_last)
                data = json.loads(payload)
                question_seconds = float(data.get("questionSeconds", 12))
                answer_seconds = float(data.get("answerSeconds", 8))
                time_drain_flag = int(data.get("timeDrainFlag", 0))
                time_drain_review_last = bool(data.get("timeDrainReviewLast", self.engine.state.time_drain_review_last))
                review_later_flag = int(data.get("reviewLaterFlag", 0))
                audio_enabled = bool(data.get("audioEnabled", self.engine.state.audio_enabled))
                selected_audio_file = str(data.get("selectedAudioFile", self.engine.state.selected_audio_file or DEFAULT_AUDIO_FILE))
                raw_audio_event_files = data.get("audioEventFiles")
                if raw_audio_event_files is None:
                    if "selectedAudioFile" in data:
                        raw_audio_event_files = {event_key: selected_audio_file for event_key in default_audio_event_files()}
                    else:
                        raw_audio_event_files = self.engine.state.audio_event_files
                audio_event_files = normalize_audio_event_files(
                    raw_audio_event_files,
                    fallback_file=selected_audio_file,
                )
                haptics_enabled = bool(data.get("hapticsEnabled", self.engine.state.haptics_enabled))
                haptic_event_patterns = normalize_haptic_event_patterns(
                    data.get("hapticEventPatterns", self.engine.state.haptic_event_patterns)
                )
                visuals_enabled = bool(data.get("visualsEnabled", True))
                show_card_timer = bool(data.get("showCardTimer", True))
                orbit_animation_enabled = bool(data.get("orbitAnimationEnabled", True))
                reduced_motion_enabled = bool(data.get("reducedMotion", self.engine.state.reduced_motion_enabled))
                custom_timer_colors = bool(data.get("customTimerColors", False))
                custom_timer_color_level = float(data.get("customTimerColorLevel", 0))
                appearance_mode = str(data.get("appearanceMode", "midnight"))
                custom_colors = dict(data.get("customColors", {}) or {})
                display_mode = normalize_display_mode(data.get("displayMode", self.display_mode))
                visual_mode = normalize_visual_mode(data.get("visualMode", self.visual_mode))
                sphere_mode = normalize_sphere_mode(data.get("sphereMode", self.sphere_mode))
                render_mode = normalize_render_mode(data.get("renderMode", self.render_mode))
                if visual_mode == VISUAL_MODE_LIGHTWEIGHT_ROWS:
                    render_mode = RENDER_MODE_ULTRA_LOW_RESOURCE
                    reduced_motion_enabled = True
            except Exception:
                return (True, None)
            previous_visuals_enabled = bool(self.engine.state.visuals_enabled)
            self.engine.update_time_limits(
                question_seconds=question_seconds,
                answer_seconds=answer_seconds,
                time_drain_flag=time_drain_flag,
                time_drain_review_last=time_drain_review_last,
                review_later_flag=review_later_flag,
                audio_enabled=audio_enabled,
                selected_audio_file=selected_audio_file,
                audio_event_files=audio_event_files,
                haptics_enabled=haptics_enabled,
                haptic_event_patterns=haptic_event_patterns,
                visuals_enabled=visuals_enabled,
                show_card_timer=show_card_timer,
                orbit_animation_enabled=orbit_animation_enabled,
                reduced_motion_enabled=reduced_motion_enabled,
                custom_timer_colors=custom_timer_colors,
                custom_timer_color_level=custom_timer_color_level,
                appearance_mode=appearance_mode,
                custom_colors=custom_colors,
            )
            self._normalize_feedback_preferences()
            display_mode_changed = display_mode != self.display_mode or self._display_mode_prompt_pending
            self.set_display_mode(display_mode, persist=False, reconfigure=display_mode_changed)
            self.visual_mode = visual_mode
            self.sphere_mode = sphere_mode
            self.render_mode = render_mode
            if (
                previous_time_drain_flag != int(self.engine.state.time_drain_flag or 0)
                or previous_time_drain_review_last != bool(self.engine.state.time_drain_review_last)
            ):
                self._restore_deferred_time_drain_cards()
            self.haptics.set_enabled(self.engine.state.haptics_enabled)
            self._save_persisted_settings()
            self._request_deck_browser_refresh()
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
                time_drain_review_last=state.time_drain_review_last,
                review_later_flag=state.review_later_flag,
                audio_enabled=state.audio_enabled,
                selected_audio_file=state.selected_audio_file,
                audio_event_files=dict(state.audio_event_files),
                haptics_enabled=state.haptics_enabled,
                haptic_event_patterns=dict(state.haptic_event_patterns),
                visuals_enabled=state.visuals_enabled,
                show_card_timer=state.show_card_timer,
                orbit_animation_enabled=state.orbit_animation_enabled,
                reduced_motion_enabled=state.reduced_motion_enabled,
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
        if message == "speed-streak:toggle-display-mode":
            next_mode = DISPLAY_MODE_COMPATIBILITY if self.display_mode == DISPLAY_MODE_INLINE else DISPLAY_MODE_INLINE
            self.set_display_mode(next_mode, persist=True, reconfigure=True)
            self._push_state(only_if_changed=False)
            return (True, None)
        if message == "speed-streak:default-settings":
            self.engine.reset_settings_to_defaults()
            self._restore_deferred_time_drain_cards()
            self._normalize_feedback_preferences()
            self.visual_mode = VISUAL_MODE_SPHERE
            self.sphere_mode = SPHERE_MODE_CLASSIC
            self.render_mode = RENDER_MODE_CLASSIC
            self.review_later_today_deck_button_enabled = False
            self.haptics.set_enabled(self.engine.state.haptics_enabled)
            self._save_persisted_settings()
            self._request_deck_browser_refresh()
            self._apply_sidebar_width()
            self._push_state(only_if_changed=False)
            return (True, None)
        if message == "speed-streak:open-review-later-manager":
            self.open_review_later_manager_from_dialog()
            return (True, None)
        if message == REVIEW_LATER_TODAY_OPEN_MESSAGE and _is_deck_browser_context(context):
            self.open_review_later_manager_from_deck_browser()
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
        time_drain_review_last: bool,
        review_later_flag: int,
        audio_enabled: bool,
        selected_audio_file: str,
        audio_event_files: dict[str, str],
        haptics_enabled: bool,
        haptic_event_patterns: dict[str, str],
        show_card_timer: bool,
        display_mode: str,
        visual_mode: str,
        sphere_mode: str,
        render_mode: str,
        orbit_animation_enabled: bool,
        reduced_motion_enabled: bool,
        visuals_enabled: bool,
        custom_timer_colors: bool,
        custom_timer_color_level: float,
        appearance_mode: str,
        custom_colors: dict[str, str] | None = None,
        shortcut_bindings: dict[str, str] | None = None,
    ) -> None:
        previous_visuals_enabled = bool(self.engine.state.visuals_enabled)
        self.engine.update_time_limits(
            question_seconds=question_seconds,
            answer_seconds=answer_seconds,
            time_drain_flag=time_drain_flag,
            time_drain_review_last=time_drain_review_last,
            review_later_flag=review_later_flag,
            audio_enabled=audio_enabled,
            selected_audio_file=selected_audio_file,
            audio_event_files=audio_event_files,
            haptics_enabled=haptics_enabled,
            haptic_event_patterns=haptic_event_patterns,
            visuals_enabled=visuals_enabled,
            show_card_timer=show_card_timer,
            orbit_animation_enabled=orbit_animation_enabled,
            reduced_motion_enabled=reduced_motion_enabled,
            custom_timer_colors=custom_timer_colors,
            custom_timer_color_level=custom_timer_color_level,
            appearance_mode=appearance_mode,
            custom_colors=custom_colors,
        )
        self.shortcut_bindings = normalize_shortcut_bindings(shortcut_bindings)
        self._normalize_feedback_preferences()
        display_mode_changed = normalize_display_mode(display_mode) != self.display_mode or self._display_mode_prompt_pending
        self.set_display_mode(display_mode, persist=False, reconfigure=display_mode_changed)
        self.visual_mode = normalize_visual_mode(visual_mode)
        self.sphere_mode = normalize_sphere_mode(sphere_mode)
        self.render_mode = normalize_render_mode(render_mode)
        if self.visual_mode == VISUAL_MODE_LIGHTWEIGHT_ROWS:
            self.render_mode = RENDER_MODE_ULTRA_LOW_RESOURCE
            self.engine.state.reduced_motion_enabled = True
        self.haptics.set_enabled(self.engine.state.haptics_enabled)
        self._save_persisted_settings()
        self._request_deck_browser_refresh()
        if previous_visuals_enabled != self.engine.state.visuals_enabled and getattr(mw, "state", "") == "review":
            self._last_reviewer_signature = ""
            self._sync_reviewer_surface()
        self._push_state(only_if_changed=False)

    def open_review_later_manager_from_dialog(self) -> None:
        open_review_later_manager(
            self.engine.state.review_later_flag,
            review_later_today_button_enabled=self.review_later_today_deck_button_enabled,
            on_review_later_today_button_changed=self.set_review_later_today_deck_button_enabled,
        )

    def open_review_later_manager_from_deck_browser(self) -> None:
        self.open_review_later_manager_from_dialog()

    def open_stats_from_dialog(self) -> None:
        open_stats_dialog(self.engine, self.stats_store)

    def reset_defaults_from_dialog(self) -> None:
        self.engine.reset_settings_to_defaults()
        self.shortcut_bindings = default_shortcut_bindings()
        self._normalize_feedback_preferences()
        self.visual_mode = VISUAL_MODE_SPHERE
        self.sphere_mode = SPHERE_MODE_CLASSIC
        self.render_mode = RENDER_MODE_CLASSIC
        self.review_later_today_deck_button_enabled = False
        self.haptics.set_enabled(self.engine.state.haptics_enabled)
        self._save_persisted_settings()
        self._request_deck_browser_refresh()
        self._apply_sidebar_width()
        self._push_state(only_if_changed=False)

    def on_deck_browser_will_render_content(self, deck_browser: Any, content: Any) -> None:
        del deck_browser
        if not self.review_later_today_deck_button_enabled:
            return
        review_later_flag = int(self.engine.state.review_later_flag or 0)
        if review_later_flag <= 0:
            return
        count = review_later_today_count(review_later_flag)
        if count <= 0:
            return
        button_html = build_review_later_today_button_html(count)
        current_tree = getattr(content, "tree", None)
        if isinstance(current_tree, str):
            content.tree = inject_shared_deck_action_html(current_tree, button_html)
            return
        current_stats = getattr(content, "stats", None)
        if isinstance(current_stats, str):
            content.stats = inject_shared_deck_action_html(current_stats, button_html)

    def reset_game_from_dialog(self) -> None:
        self.engine.hard_reset()
        self._normalize_feedback_preferences()
        self._last_nonce_sent = -1
        self._push_state(only_if_changed=False)
        self._play_feedback_event("reset")

    def _register_web_exports(self) -> None:
        try:
            mw.addonManager.setWebExports(
                __name__,
                r"(web|Audio_trimmed|user_files/audio_uploads)/.*\.(aac|css|flac|js|m4a|mp3|oga|ogg|opus|wav)",
            )
        except Exception:
            pass

    def _install_menu(self) -> None:
        menubar = getattr(getattr(mw, "form", None), "menubar", None)
        if menubar is None:
            return

        existing_menu = None
        for action in menubar.actions():
            menu = action.menu()
            if menu is not None and menu.objectName() == "speedStreakMenu":
                existing_menu = menu
                break

        menu = existing_menu or menubar.addMenu("Speed Streak")
        menu.setObjectName("speedStreakMenu")
        menu.clear()

        review_later_action = menu.addAction("Review Later Manager")
        review_later_action.setMenuRole(QAction.MenuRole.NoRole)
        review_later_action.triggered.connect(self.open_review_later_manager_from_dialog)

        menu.addSeparator()
        action = menu.addAction("Settings")
        action.setMenuRole(QAction.MenuRole.NoRole)
        action.triggered.connect(self._open_settings_dialog)

        self._menu = menu
        self._review_later_action = review_later_action
        self._settings_action = action

    def _open_settings_dialog(self) -> None:
        if not self.engine.state.paused and self.engine.state.visuals_enabled:
            self.engine.toggle_pause()
            self._push_state(only_if_changed=False)
        open_settings_dialog(self)

    def on_webview_will_set_content(self, web_content: Any, context: object | None) -> None:
        if not isinstance(context, Reviewer):
            return
        for part in ("card_timer.css", "card_timer.js"):
            if _web_asset_exists("web", part):
                target = getattr(web_content, "css" if part.endswith(".css") else "js", None)
                if isinstance(target, list):
                    url = _web_asset_url("web", part)
                    if url not in target:
                        target.append(url)

    def on_reviewer_did_show_question(self, card: Any) -> None:
        reviewer = getattr(mw, "reviewer", None)
        if reviewer is None:
            return
        self._last_reviewer_signature = f"{getattr(card, 'id', '')}:question"
        self._handle_question_shown(reviewer)

    def on_reviewer_did_show_answer(self, card: Any) -> None:
        reviewer = getattr(mw, "reviewer", None)
        if reviewer is None:
            return
        self._last_reviewer_signature = f"{getattr(card, 'id', '')}:answer"
        self._handle_answer_shown(reviewer)

    def on_reviewer_will_answer_card(self, ease_tuple: tuple[bool, int], reviewer: Reviewer, card: Any) -> tuple[bool, int]:
        should_continue, ease = ease_tuple
        if should_continue:
            self._pending_review_undo_snapshot = self.engine.capture_review_undo_snapshot()
            self._pending_review_card_id = int(getattr(card, "id", 0) or 0)
            self._pending_answer_feedback_event = ""
            if self.engine.state.enabled and self.engine.state.phase == "answer" and not self.engine.state.paused:
                event_key = self._feedback_event_for_ease(ease)
                if event_key:
                    self._pending_answer_feedback_event = event_key
                    self._play_feedback_event(event_key)
        else:
            self._pending_review_undo_snapshot = None
            self._pending_review_card_id = 0
            self._pending_answer_feedback_event = ""
        return ease_tuple

    def on_reviewer_did_answer_card(self, reviewer: Reviewer, card: Any, ease: int) -> None:
        event = self.engine.on_rate(int(ease))
        self._queue_review_later_sync_for_card(card)
        self._flush_pending_review_later_sync_for_card(int(getattr(card, "id", 0) or 0))
        if not event:
            self._pending_review_undo_snapshot = None
            self._pending_review_card_id = 0
            self._pending_answer_feedback_event = ""
            return
        card_id = int(getattr(card, "id", 0) or 0)
        if self._pending_review_undo_snapshot is not None and card_id == self._pending_review_card_id:
            self.engine.commit_review_undo_snapshot(self._pending_review_undo_snapshot)
        self._pending_review_undo_snapshot = None
        self._pending_review_card_id = 0
        self._finalize_rate(event)

    def on_reviewer_will_bury_card(self, card_id: int) -> None:
        reviewer = getattr(mw, "reviewer", None)
        self._queue_review_later_sync_for_card(getattr(reviewer, "card", None) if reviewer is not None else None)
        self._flush_pending_review_later_sync_for_card(card_id)
        self._handle_skip()

    def on_reviewer_will_bury_note(self, note_id: int) -> None:
        reviewer = getattr(mw, "reviewer", None)
        self._queue_review_later_sync_for_card(getattr(reviewer, "card", None) if reviewer is not None else None)
        self._flush_pending_review_later_sync()
        self._handle_skip()

    def on_state_did_undo(self, changes: Any) -> None:
        self._apply_anki_undo_to_speed_streak()

    def on_state_shortcuts_will_change(self, state: Any, shortcuts: list[tuple[str, Any]]) -> None:
        if str(state) != "review":
            return
        shortcuts.append((self.pause_shortcut_display(), self._on_pause_shortcut))

    def _start_timer(self) -> None:
        self._timer = mw.progress.timer(100, self._on_tick, repeat=True)

    def _on_pause_shortcut(self) -> None:
        if getattr(mw, "state", "") != "review":
            return
        event = self.engine.toggle_pause()
        if event:
            self._push_state(only_if_changed=False)

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
        self._sync_live_flag_state()
        event = self.engine.check_timeout()
        if event:
            self._play_feedback_event("timeout")
            self._push_state(only_if_changed=False)

    def _handle_non_review_state(self) -> None:
        self._restore_deferred_time_drain_cards()
        self._flush_pending_review_later_sync()
        self._flush_requested_deck_browser_refresh()
        if not self._non_review_surface_applied:
            self._set_sidebar_hidden(True)
            if self.display_mode == DISPLAY_MODE_COMPATIBILITY and self._compatibility_review_layout_active:
                self._restore_pre_compatibility_main_geometry()
                self._compatibility_review_layout_active = False
            self._hide_card_timer()
            self._last_reviewer_signature = ""
            self._last_reduced_live_update_bucket = None
            self._non_review_surface_applied = True
        state = self.engine.state
        self.engine.set_pause_stat_tracking_active(False)
        if (
            not self._auto_paused_for_non_review
            and state.synced
            and state.phase != "idle"
            and not state.paused
            and state.phase_limit_ms > 0
            and state.visuals_enabled
        ):
            event = self.engine.toggle_pause(count_in_stats=False)
            if event:
                self._auto_paused_for_non_review = True
                self._push_state(only_if_changed=False)

    def _handle_review_state(self) -> None:
        self._non_review_surface_applied = False
        self._schedule_display_mode_prompt_if_needed()
        self._set_sidebar_hidden(False)
        # If review re-entry or question sync already cleared the paused state, the
        # non-review auto-pause marker is stale and should not consume the user's
        # next manual pause action.
        if self._auto_paused_for_non_review and not self.engine.state.paused:
            self._auto_paused_for_non_review = False
        if self._auto_paused_for_non_review and self.engine.state.paused:
            if not self.engine.state.enabled or not self.engine.state.visuals_enabled:
                return
            event = self.engine.toggle_pause()
            self._auto_paused_for_non_review = False
            if event:
                self._push_state(only_if_changed=False)
            return
        self.engine.set_pause_stat_tracking_active(True)

    def _sync_live_flag_state(self) -> None:
        reviewer = getattr(mw, "reviewer", None)
        card = getattr(reviewer, "card", None) if reviewer else None
        if card is None:
            return
        next_flag = self._flag_for_card(card)
        previous_flag = int(self.engine.state.current_card_flag or 0)
        event = self.engine.on_flag_changed(card_flag=next_flag)
        if next_flag != previous_flag:
            self._queue_review_later_sync_for_card(card, current_flag=next_flag)
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
        self._schedule_display_mode_prompt_if_needed()
        self._ensure_display_surface(reviewer)
        card = getattr(reviewer, "card", None)
        if card is None:
            return
        self._queue_review_later_sync_for_card(card)
        deck_name = self._deck_name_for_card(card)
        card_flag = self._flag_for_card(card)
        event = self.engine.sync_visible_question_surface(card_id=str(card.id), deck_name=deck_name, card_flag=card_flag)
        if event == "sync":
            self._play_feedback_event("sync")
        self._push_state(only_if_changed=False)
        self._restore_review_focus()

    def _handle_answer_shown(self, reviewer: Reviewer) -> None:
        self._ensure_display_surface(reviewer)
        card = getattr(reviewer, "card", None)
        if card is None:
            return
        event = self.engine.sync_visible_answer_surface(
            card_id=str(card.id),
            deck_name=self._deck_name_for_card(card),
            card_flag=self._flag_for_card(card),
        )
        if event == "reveal":
            self._play_feedback_event("reveal")
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
        resolved_event_key = self._resolved_feedback_event_key(event)
        if resolved_event_key and resolved_event_key != self._pending_answer_feedback_event:
            self._play_feedback_event(resolved_event_key)
        self._pending_answer_feedback_event = ""
        self._push_state(only_if_changed=False)

    def _handle_skip(self) -> None:
        event = self.engine.on_skip()
        if event == "skip":
            self._play_feedback_event("skip")
            self._push_state(only_if_changed=False)

    def _feedback_event_for_ease(self, ease: int) -> str:
        return {1: "again", 2: "hard", 3: "good", 4: "easy"}.get(int(ease or 0), "")

    def _resolved_feedback_event_key(self, event: str) -> str:
        if event == "again-on-time":
            return "hard"
        if event in {"again", "hard", "good", "easy"}:
            return event
        return ""

    def _queue_review_later_sync_for_card(self, card: Any, *, current_flag: int | None = None) -> None:
        if card is None:
            return
        card_id = int(getattr(card, "id", 0) or 0)
        if card_id <= 0:
            return
        pending = self._pending_review_later_sync
        if pending is not None and int(pending.get("card_id", 0) or 0) != card_id:
            self._flush_pending_review_later_sync()
        self._pending_review_later_sync = {
            "card_id": card_id,
            "note_id": self._note_id_for_card(card),
            "card_ord": self._card_ord_for_card(card),
            "current_flag": int(self._flag_for_card(card) if current_flag is None else current_flag),
            "review_later_flag": int(self.engine.state.review_later_flag or 0),
        }

    def _flush_pending_review_later_sync_for_card(self, card_id: int) -> None:
        pending = self._pending_review_later_sync
        if pending is None:
            return
        if int(pending.get("card_id", 0) or 0) != int(card_id or 0):
            return
        self._flush_pending_review_later_sync()

    def _flush_pending_review_later_sync(self) -> None:
        pending = self._pending_review_later_sync
        if pending is None:
            return
        self._pending_review_later_sync = None
        try:
            sync_review_later_membership(
                card_id=int(pending.get("card_id", 0) or 0),
                note_id=int(pending.get("note_id", 0) or 0),
                card_ord=int(pending.get("card_ord", 0) or 0),
                current_flag=int(pending.get("current_flag", 0) or 0),
                review_later_flag=int(pending.get("review_later_flag", 0) or 0),
            )
            self._request_deck_browser_refresh()
        except Exception:
            pass

    def _push_state(self, *, only_if_changed: bool = True) -> None:
        if self._sidebar_web is None and self._review_web is None:
            return
        state = self.engine.export()
        nonce = state.get("eventNonce", -1)
        if only_if_changed and nonce == self._last_nonce_sent:
            return
        self._last_nonce_sent = nonce
        timer_display = self._build_timer_display_payload()
        payload = json.dumps(
            {
                **state,
                "flagPalette": get_anki_flag_palette(),
                "hapticsAvailable": int(self.haptics.available),
                "hapticPatternSequences": BROWSER_HAPTIC_PATTERN_SEQUENCES,
                "sidebarBackground": self._sidebar_background or self._default_sidebar_background(),
                "displayMode": self.display_mode,
                "visualMode": self.visual_mode,
                "sphereMode": self.sphere_mode,
                "renderMode": self.render_mode,
                "shortcutBindings": self.current_shortcut_bindings(),
                "pauseShortcut": self.pause_shortcut_display(),
                **timer_display,
            }
        )
        if self._sidebar_web is not None:
            self._sidebar_web.eval(f"window.SpeedStreak && window.SpeedStreak.receiveState({payload});")
        self._push_card_timer_state(payload)
        if self._uses_reduced_render_timing():
            self._last_reduced_live_update_bucket = self._current_reduced_live_update_bucket()
        else:
            self._last_reduced_live_update_bucket = None

    def _uses_reduced_render_timing(self) -> bool:
        return self.visual_mode == VISUAL_MODE_LIGHTWEIGHT_ROWS or self.render_mode == RENDER_MODE_ULTRA_LOW_RESOURCE

    def _current_reduced_live_update_bucket(self) -> int:
        return int(time.monotonic() / 0.5)

    def _should_push_live_update(self) -> bool:
        return False

    def _timer_display_step_ms(self) -> int:
        if self.visual_mode == VISUAL_MODE_LIGHTWEIGHT_ROWS:
            return 100
        return 500 if self.render_mode == RENDER_MODE_ULTRA_LOW_RESOURCE else 100

    def _raw_timer_remaining_ms(self, now_ms: int) -> int:
        state = self.engine.state
        if (
            not state.enabled
            or not state.visuals_enabled
            or state.phase == "idle"
            or state.phase_start_epoch_ms <= 0
            or state.phase_limit_ms <= 0
            or (state.phase == "question" and state.first_card_free)
        ):
            return 0
        if state.paused:
            return max(0, int(state.paused_remaining_ms))
        return max(0, int(state.phase_limit_ms) - max(0, now_ms - int(state.phase_start_epoch_ms)))

    def _snap_timer_remaining_ms(self, remaining_ms: int, step_ms: int) -> int:
        remaining = max(0, int(remaining_ms))
        step = max(1, int(step_ms))
        if remaining <= 0:
            return 0
        return ((remaining + step - 1) // step) * step

    def _build_timer_display_payload(self) -> dict[str, Any]:
        state = self.engine.state
        now_ms = int(time.time() * 1000)
        step_ms = self._timer_display_step_ms()
        remaining_ms = self._snap_timer_remaining_ms(self._raw_timer_remaining_ms(now_ms), step_ms)
        signature = "|".join(
            (
                str(state.phase or "idle"),
                str(int(state.phase_start_epoch_ms or 0)),
                str(int(state.phase_limit_ms or 0)),
                str(int(bool(state.paused))),
                str(int(bool(state.first_card_free))),
                str(int(step_ms)),
            )
        )
        anchor_ms = now_ms
        if signature == self._last_timer_display_signature and remaining_ms == self._last_timer_display_remaining_ms:
            anchor_ms = self._last_timer_display_anchor_ms or now_ms
        else:
            self._last_timer_display_signature = signature
            self._last_timer_display_remaining_ms = remaining_ms
            self._last_timer_display_anchor_ms = now_ms
        return {
            "timerDisplayNowEpochMs": anchor_ms,
            "timerDisplayRemainingMs": remaining_ms,
            "timerDisplayStepMs": step_ms,
            "timerDisplaySecondsText": f"{remaining_ms / 1000:.1f}",
        }

    def _ensure_display_surface(self, reviewer: Reviewer) -> None:
        if self.display_mode == DISPLAY_MODE_COMPATIBILITY:
            self._ensure_floating_sidebar(reviewer)
            return
        self._ensure_inline_sidebar(reviewer)

    def _ensure_inline_sidebar(self, reviewer: Reviewer) -> None:
        review_web = getattr(reviewer, "web", None)
        if review_web is None:
            return

        existing_parent = review_web.parentWidget()
        if existing_parent is not None and existing_parent.objectName() == INLINE_CONTAINER_OBJECT_NAME:
            existing_sidebar = existing_parent.findChild(AnkiWebView, INLINE_SIDEBAR_OBJECT_NAME)
            self._sidebar_container = existing_parent
            self._sidebar_web = existing_sidebar
            self._review_web = review_web
            self._apply_sidebar_width()
            self._restore_review_focus()
            return

        if self._sidebar_web is not None and self._sidebar_container is not None:
            if self._sidebar_container.parentWidget() is not None:
                return
            self._sidebar_container = None
            self._sidebar_web = None

        if self._floating_window is not None:
            self._floating_window.hide()

        host = review_web.parentWidget()
        if host is None or host.layout() is None:
            return

        host_layout = host.layout()
        index = host_layout.indexOf(review_web)
        if index < 0:
            return

        host_layout.removeWidget(review_web)

        container = QWidget(host)
        container.setObjectName(INLINE_CONTAINER_OBJECT_NAME)
        container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        container.setMinimumHeight(0)
        container.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar_web = AnkiWebView(container)
        sidebar_web.setObjectName(INLINE_SIDEBAR_OBJECT_NAME)
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
        self._schedule_sidebar_state_push()
        self._restore_review_focus()

    def _ensure_floating_sidebar(self, reviewer: Reviewer) -> None:
        review_web = getattr(reviewer, "web", None)
        if review_web is None:
            return

        existing_parent = review_web.parentWidget()
        if existing_parent is not None and existing_parent.objectName() == INLINE_CONTAINER_OBJECT_NAME:
            self._sidebar_container = existing_parent
            self._sidebar_web = existing_parent.findChild(AnkiWebView, INLINE_SIDEBAR_OBJECT_NAME)
            self._review_web = review_web

        if self._sidebar_container is not None:
            self._detach_inline_sidebar()

        self._review_web = review_web
        entering_review_layout = not self._compatibility_review_layout_active
        if entering_review_layout:
            self._remember_pre_compatibility_main_geometry()

        if self._floating_window is None:
            window = FloatingSidebarWindow(self._on_floating_geometry_changed, self._restore_main_window_focus)
            window.web.stdHtml(self._sidebar_html())
            self._floating_window = window
        if self._floating_window is not None and entering_review_layout:
            self._restore_or_place_floating_window()
            self._compatibility_review_layout_active = True
        if self._floating_window is not None:
            self._sidebar_web = self._floating_window.web
            if self._floating_window.isMinimized():
                self._floating_window.showNormal()
            if not self._floating_window.isVisible():
                self._floating_window.show()
            self._schedule_sidebar_state_push()

    def _set_sidebar_hidden(self, hidden: bool) -> None:
        if self.display_mode == DISPLAY_MODE_COMPATIBILITY:
            self._set_floating_sidebar_hidden(hidden)
            return
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

    def _set_floating_sidebar_hidden(self, hidden: bool) -> None:
        if self._floating_window is None:
            return
        if hidden:
            self._floating_geometry = self._floating_window.export_geometry() or self._floating_geometry
            self._floating_window.hide()
            return
        if self._floating_window.isMinimized():
            self._floating_window.showNormal()
        if not self._floating_window.isVisible():
            self._floating_window.show()

    def _sidebar_html(self) -> str:
        css_link = (
            f'<link rel="stylesheet" href="{_web_asset_url("web", "overlay.css")}">'
            if _web_asset_exists("web", "overlay.css")
            else ""
        )
        js_tag = (
            f'<script src="{_web_asset_url("web", "overlay.js")}"></script>'
            if _web_asset_exists("web", "overlay.js")
            else ""
        )
        inline_css = "" if css_link else _read_web_asset("web", "overlay.css")
        inline_js = "" if js_tag else _read_web_asset("web", "overlay.js")
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {css_link}
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
    {inline_css}
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
  {js_tag}
  <script>
    {inline_js}
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
            raw_render_mode = str(config.get("render_mode", RENDER_MODE_CLASSIC) or RENDER_MODE_CLASSIC)
            raw_visual_mode = str(config.get("visual_mode", "") or "")
            self.display_mode = normalize_display_mode(config.get("display_mode", DISPLAY_MODE_INLINE))
            if raw_visual_mode:
                self.visual_mode = normalize_visual_mode(raw_visual_mode)
            elif raw_render_mode in {"lightweight_rows", "rows"}:
                self.visual_mode = VISUAL_MODE_LIGHTWEIGHT_ROWS
            else:
                self.visual_mode = VISUAL_MODE_SPHERE
            self.sphere_mode = normalize_sphere_mode(config.get("sphere_mode", SPHERE_MODE_CLASSIC))
            self.render_mode = normalize_render_mode(raw_render_mode)
            if self.visual_mode == VISUAL_MODE_LIGHTWEIGHT_ROWS:
                self.render_mode = RENDER_MODE_ULTRA_LOW_RESOURCE
            self._display_mode_prompt_pending = not bool(config.get("display_mode_prompted", False))
            self._floating_geometry = str(config.get("floating_geometry", "") or "")
            compatibility_layout_version = int(config.get("compatibility_layout_version", 0) or 0)
            self._compatibility_main_geometry = (
                str(config.get("compatibility_main_geometry", "") or "")
                if compatibility_layout_version >= COMPATIBILITY_LAYOUT_VERSION
                else ""
            )
            raw_shortcut_bindings = config.get("shortcut_bindings")
            if raw_shortcut_bindings is None and config.get("pause_shortcut") is not None:
                raw_shortcut_bindings = {"pause": config.get("pause_shortcut")}
            self.shortcut_bindings = normalize_shortcut_bindings(raw_shortcut_bindings)
            self.review_later_today_deck_button_enabled = bool(
                config.get("review_later_today_deck_button_enabled", False)
            )
            reduced_motion_enabled = config.get("reduced_motion")
            if reduced_motion_enabled is None:
                reduced_motion_enabled = self.visual_mode == VISUAL_MODE_LIGHTWEIGHT_ROWS
            elif self.visual_mode == VISUAL_MODE_LIGHTWEIGHT_ROWS:
                reduced_motion_enabled = True
            selected_audio_file = str(config.get("selected_audio_file", DEFAULT_AUDIO_FILE))
            raw_audio_event_files = config.get("audio_event_files")
            if raw_audio_event_files is None:
                raw_audio_event_files = {event_key: selected_audio_file for event_key in default_audio_event_files()}
            # Re-arm haptics on every Anki launch so an accidental toggle-off does
            # not silently persist across sessions.
            startup_haptics_enabled = True
            self.engine.update_time_limits(
                question_seconds=float(config.get("question_seconds", 12)),
                answer_seconds=float(config.get("answer_seconds", 8)),
                time_drain_flag=int(config.get("time_drain_flag", 2)),
                time_drain_review_last=bool(config.get("time_drain_review_last", False)),
                review_later_flag=int(config.get("review_later_flag", 4)),
                audio_enabled=bool(config.get("audio_enabled", DEFAULT_AUDIO_ENABLED)),
                selected_audio_file=selected_audio_file,
                audio_event_files=raw_audio_event_files,
                haptics_enabled=startup_haptics_enabled,
                haptic_event_patterns=normalize_haptic_event_patterns(config.get("haptic_event_patterns", {})),
                visuals_enabled=bool(config.get("visuals_enabled", True)),
                show_card_timer=bool(config.get("show_card_timer", True)),
                orbit_animation_enabled=bool(config.get("orbit_animation_enabled", True)),
                reduced_motion_enabled=bool(reduced_motion_enabled),
                custom_timer_colors=bool(config.get("custom_timer_colors", False)),
                custom_timer_color_level=float(config.get("custom_timer_color_level", 0)),
                sidebar_collapsed=bool(config.get("sidebar_collapsed", False)),
                appearance_mode=str(config.get("appearance_mode", "midnight")),
                custom_colors=dict(config.get("custom_colors", {}) or {}),
            )
            self._normalize_feedback_preferences()
            self.engine.state.enabled = bool(config.get("enabled", True))
            self.haptics.set_enabled(self.engine.state.haptics_enabled)
        except Exception:
            self.display_mode = DISPLAY_MODE_INLINE
            self.visual_mode = VISUAL_MODE_SPHERE
            self.sphere_mode = SPHERE_MODE_CLASSIC
            self.render_mode = RENDER_MODE_CLASSIC
            self._display_mode_prompt_pending = True
            self._floating_geometry = ""
            self._compatibility_main_geometry = ""
            self.shortcut_bindings = default_shortcut_bindings()
            self.review_later_today_deck_button_enabled = False
            self.engine.update_time_limits(
                question_seconds=12,
                answer_seconds=8,
                time_drain_flag=2,
                time_drain_review_last=False,
                review_later_flag=4,
                audio_enabled=DEFAULT_AUDIO_ENABLED,
                selected_audio_file=DEFAULT_AUDIO_FILE,
                audio_event_files=default_audio_event_files(),
                haptics_enabled=True,
                haptic_event_patterns=default_haptic_event_patterns(),
                visuals_enabled=True,
                show_card_timer=True,
                orbit_animation_enabled=True,
                reduced_motion_enabled=False,
                custom_timer_colors=False,
                custom_timer_color_level=0,
                sidebar_collapsed=False,
                appearance_mode="midnight",
                custom_colors={},
            )
            self._normalize_feedback_preferences()
            self.engine.state.enabled = True
            self.haptics.set_enabled(self.engine.state.haptics_enabled)
        try:
            self._last_saved_config_signature = json.dumps(
                self._build_persisted_settings_config(),
                sort_keys=True,
                separators=(",", ":"),
            )
        except Exception:
            self._last_saved_config_signature = ""

    def _build_persisted_settings_config(self) -> dict[str, Any]:
        state = self.engine.state
        if self._floating_window is not None:
            self._floating_geometry = self._floating_window.export_geometry() or self._floating_geometry
        return {
            "enabled": bool(state.enabled),
            "display_mode": self.display_mode,
            "visual_mode": self.visual_mode,
            "sphere_mode": self.sphere_mode,
            "render_mode": self.render_mode,
            "display_mode_prompted": not self._display_mode_prompt_pending,
            "floating_geometry": self._floating_geometry,
            "compatibility_layout_version": COMPATIBILITY_LAYOUT_VERSION,
            "compatibility_main_geometry": self._compatibility_main_geometry,
            "shortcut_bindings": self.current_shortcut_bindings(),
            "audio_enabled": bool(state.audio_enabled),
            "selected_audio_file": str(state.selected_audio_file),
            "audio_event_files": dict(state.audio_event_files),
            "haptics_enabled": bool(state.haptics_enabled),
            "haptic_event_patterns": dict(state.haptic_event_patterns),
            "visuals_enabled": bool(state.visuals_enabled),
            "show_card_timer": bool(state.show_card_timer),
            "orbit_animation_enabled": bool(state.orbit_animation_enabled),
            "reduced_motion": bool(state.reduced_motion_enabled),
            "custom_timer_colors": bool(state.custom_timer_colors),
            "custom_timer_color_level": float(state.custom_timer_color_level),
            "sidebar_collapsed": bool(state.sidebar_collapsed),
            "appearance_mode": str(state.appearance_mode),
            "custom_colors": dict(state.custom_colors),
            "question_seconds": state.question_limit_ms / 1000,
            "answer_seconds": state.review_limit_ms / 1000,
            "time_drain_flag": state.time_drain_flag,
            "time_drain_review_last": bool(state.time_drain_review_last),
            "review_later_flag": state.review_later_flag,
            "review_later_today_deck_button_enabled": bool(self.review_later_today_deck_button_enabled),
        }

    def _flush_scheduled_persisted_settings_save(self) -> None:
        self._save_persisted_settings()

    def _schedule_persisted_settings_save(self, delay_ms: int = 900) -> None:
        if self._persist_settings_timer.isActive():
            self._persist_settings_timer.stop()
        self._persist_settings_timer.start(max(0, int(delay_ms)))

    def _save_persisted_settings(self) -> None:
        ensure_meta_json(ADDON_ROOT)
        config = self._build_persisted_settings_config()
        signature = json.dumps(config, sort_keys=True, separators=(",", ":"))
        if signature == self._last_saved_config_signature:
            return
        self._last_saved_config_signature = signature
        mw.addonManager.writeConfig(ADDON_PACKAGE, config)

    def _apply_sidebar_width(self) -> None:
        if self.display_mode != DISPLAY_MODE_INLINE:
            return
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

    def _restore_main_window_focus(self) -> None:
        try:
            mw.activateWindow()
            mw.raise_()
        except Exception:
            pass
        self._restore_review_focus()

    def _current_main_window_bounds(self) -> dict[str, int]:
        try:
            geometry = mw.geometry()
            return {
                "x": int(geometry.x()),
                "y": int(geometry.y()),
                "width": int(geometry.width()),
                "height": int(geometry.height()),
            }
        except Exception:
            return {}

    def _remember_pre_compatibility_main_geometry(self) -> None:
        self._pre_compatibility_main_geometry = _export_widget_geometry(mw)

    def _restore_pre_compatibility_main_geometry(self) -> None:
        if not self._pre_compatibility_main_geometry:
            return
        self._geometry_persistence_suspended = True
        try:
            _restore_widget_geometry(mw, self._pre_compatibility_main_geometry)
        finally:
            self._geometry_persistence_suspended = False

    def _compatibility_sidebar_width(self) -> int:
        return SIDEBAR_EXPANDED_WIDTH

    def _place_floating_window_on_right(self, width: int | None = None) -> None:
        if self._floating_window is None:
            return

        _ensure_window_frame_metrics(self._floating_window)
        sidebar_width = max(self._floating_window.minimumWidth(), int(width or self._compatibility_sidebar_width()))
        try:
            main_frame = mw.frameGeometry()
            main_x = int(main_frame.x())
            main_y = int(main_frame.y())
            main_width = int(main_frame.width())
            main_height = int(main_frame.height())
        except Exception:
            return

        height = max(self._floating_window.minimumHeight(), main_height)
        x = main_x + main_width
        y = main_y

        screen = mw.screen() or self._floating_window.screen()
        if screen is not None:
            available = screen.availableGeometry()
            x = max(available.left(), min(x, available.left() + available.width() - sidebar_width))
            y = max(available.top(), min(y, available.top() + available.height() - height))

        _set_window_frame_geometry(self._floating_window, x, y, sidebar_width, height)
        self._floating_geometry = self._floating_window.export_geometry() or self._floating_geometry

    def _apply_default_compatibility_layout(self, sidebar_width: int | None = None) -> None:
        if self._floating_window is None:
            return

        try:
            if mw.isMinimized() or mw.isMaximized() or mw.isFullScreen():
                mw.showNormal()
        except Exception:
            pass

        _ensure_window_frame_metrics(self._floating_window)
        min_main_width = max(1, int(getattr(mw, "minimumWidth", lambda: 0)() or 0))
        min_main_height = max(1, int(getattr(mw, "minimumHeight", lambda: 0)() or 0))
        sidebar_width = max(
            self._floating_window.minimumWidth(),
            int(sidebar_width or self._compatibility_sidebar_width()),
        )
        current = self._current_main_window_bounds()
        if not current:
            return

        screen = mw.screen() or self._floating_window.screen()
        if screen is not None:
            available = screen.availableGeometry()
            max_sidebar_width = max(self._floating_window.minimumWidth(), available.width() - min_main_width)
            sidebar_width = min(sidebar_width, max_sidebar_width)
            target_width = max(min_main_width, available.width() - sidebar_width)
            target_height = max(min_main_height, available.height())
            _set_window_frame_geometry(
                mw,
                available.left(),
                available.top(),
                target_width,
                target_height,
            )
            _set_window_frame_geometry(
                self._floating_window,
                available.left() + target_width,
                available.top(),
                sidebar_width,
                target_height,
            )
            self._floating_geometry = self._floating_window.export_geometry() or self._floating_geometry
        else:
            target_width = max(min_main_width, current["width"] - sidebar_width)
            target_height = max(min_main_height, current["height"])
            mw.setGeometry(current["x"], current["y"], target_width, target_height)
            self._place_floating_window_on_right(sidebar_width)
        bounds = self._current_main_window_bounds()
        if bounds:
            self._compatibility_main_geometry = _export_widget_geometry(mw)

    def _detach_inline_sidebar(self) -> None:
        if self._sidebar_container is None or self._review_web is None:
            reviewer = getattr(mw, "reviewer", None)
            review_web = getattr(reviewer, "web", None) if reviewer else None
            if review_web is not None:
                self._review_web = review_web
            self._sidebar_container = None
            self._sidebar_web = None
            return

        container = self._sidebar_container
        review_web = self._review_web
        host = container.parentWidget()
        host_layout = host.layout() if host is not None else None
        index = host_layout.indexOf(container) if host_layout is not None else -1
        container_layout = container.layout()

        if container_layout is not None:
            container_layout.removeWidget(review_web)
        if host_layout is not None:
            host_layout.removeWidget(container)
            review_web.setParent(host)
            review_web.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            review_web.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            review_web.setMinimumHeight(0)
            insert_at = index if index >= 0 else host_layout.count()
            host_layout.insertWidget(insert_at, review_web, 1)

        if self._sidebar_web is not None:
            self._sidebar_web.deleteLater()
        container.hide()
        container.setParent(None)
        container.deleteLater()
        if host_layout is not None:
            try:
                host_layout.invalidate()
                host_layout.activate()
            except Exception:
                pass
        if host is not None:
            try:
                host.updateGeometry()
                host.update()
            except Exception:
                pass

        self._sidebar_container = None
        self._sidebar_web = None
        self._review_web = review_web
        self._restore_review_focus()

    def _deactivate_floating_sidebar(self) -> None:
        if self._floating_window is not None:
            self._floating_geometry = self._floating_window.export_geometry() or self._floating_geometry
            self._floating_window.hide()
        self._sidebar_web = None

    def _on_main_window_geometry_changed(self) -> None:
        if (
            self._geometry_persistence_suspended
            or self.display_mode != DISPLAY_MODE_COMPATIBILITY
            or getattr(mw, "state", "") != "review"
        ):
            return
        geometry = _export_widget_geometry(mw)
        if geometry:
            self._compatibility_main_geometry = geometry
            self._schedule_persisted_settings_save()

    def _on_floating_geometry_changed(self, geometry: str) -> None:
        if self._geometry_persistence_suspended or getattr(mw, "state", "") != "review":
            return
        if geometry:
            self._floating_geometry = geometry
            self._schedule_persisted_settings_save()

    def _restore_or_place_floating_window(self) -> None:
        if self._floating_window is None:
            return

        needs_save = False
        self._geometry_persistence_suspended = True
        try:
            has_saved_main_geometry = bool(self._compatibility_main_geometry)
            restored_main = _restore_widget_geometry(mw, self._compatibility_main_geometry) if has_saved_main_geometry else False
            restored_floating = self._floating_window.restore_exported_geometry(self._floating_geometry)

            if has_saved_main_geometry and restored_main and restored_floating:
                return
            if has_saved_main_geometry and restored_main:
                if not restored_floating:
                    self._place_floating_window_on_right()
                needs_save = True
                return

            preferred_sidebar_width = (
                max(self._floating_window.minimumWidth(), self._floating_window.width())
                if restored_floating
                else None
            )
            self._apply_default_compatibility_layout(preferred_sidebar_width)
            needs_save = True
        finally:
            self._geometry_persistence_suspended = False
            if needs_save:
                self._compatibility_main_geometry = _export_widget_geometry(mw) or self._compatibility_main_geometry
                self._floating_geometry = self._floating_window.export_geometry() or self._floating_geometry
                self._save_persisted_settings()

    def _schedule_sidebar_state_push(self) -> None:
        if self._sidebar_web is None:
            return
        QTimer.singleShot(0, lambda: self._push_state(only_if_changed=False))
        QTimer.singleShot(140, lambda: self._push_state(only_if_changed=False))
        QTimer.singleShot(320, lambda: self._push_state(only_if_changed=False))

    def set_display_mode(self, display_mode: str, *, persist: bool = True, reconfigure: bool = True) -> None:
        normalized = normalize_display_mode(display_mode)
        changed = normalized != self.display_mode or self._display_mode_prompt_pending
        self.display_mode = normalized
        self._display_mode_prompt_pending = False
        if changed and reconfigure:
            if normalized == DISPLAY_MODE_COMPATIBILITY:
                self._detach_inline_sidebar()
                self._compatibility_review_layout_active = False
            else:
                self._deactivate_floating_sidebar()
                if self._compatibility_review_layout_active:
                    self._restore_pre_compatibility_main_geometry()
                self._compatibility_review_layout_active = False
            self._last_reviewer_signature = ""
            if getattr(mw, "state", "") == "review":
                self._sync_reviewer_surface()
                self._schedule_sidebar_state_push()
        if persist:
            self._save_persisted_settings()

    def _schedule_display_mode_prompt_if_needed(self) -> None:
        if (
            not self._display_mode_prompt_pending
            or self._display_mode_prompt_scheduled
            or self._display_mode_prompt_open
            or getattr(mw, "state", "") != "review"
        ):
            return
        self._display_mode_prompt_scheduled = True
        mw.progress.timer(1, self._prompt_for_display_mode, repeat=False)

    def _prompt_for_display_mode(self) -> None:
        self._display_mode_prompt_scheduled = False
        if (
            not self._display_mode_prompt_pending
            or self._display_mode_prompt_open
            or getattr(mw, "state", "") != "review"
        ):
            return
        self._display_mode_prompt_open = True
        try:
            choice = self._choose_display_mode()
            self.set_display_mode(choice, persist=True, reconfigure=True)
        finally:
            self._display_mode_prompt_open = False

    def _choose_display_mode(self) -> str:
        dialog = QMessageBox(mw)
        dialog.setWindowTitle(f"{ADDON_DISPLAY_NAME} Display Mode")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setText("Choose where Speed Streak should appear while you review.")
        dialog.setInformativeText(
            "External Window is recommended. It usually renders more smoothly and plays better with add-ons like "
            "AnkiHub and AMBOSS because it leaves Anki's review layout alone.\n\n"
            "Inline Side Pane keeps Speed Streak docked inside the review screen as a left column."
        )
        inline_button = dialog.addButton("Inline Side Pane", QMessageBox.ButtonRole.ActionRole)
        compatibility_button = dialog.addButton(
            "External Window (Recommended)",
            QMessageBox.ButtonRole.AcceptRole,
        )
        dialog.setDefaultButton(compatibility_button)
        dialog.exec()
        if dialog.clickedButton() is compatibility_button:
            return DISPLAY_MODE_COMPATIBILITY
        return DISPLAY_MODE_INLINE

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
