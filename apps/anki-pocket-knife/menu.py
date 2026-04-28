from __future__ import annotations

from pathlib import Path

from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QCheckBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSpinBox,
    Qt,
    QVBoxLayout,
    QWidget,
)

from .ai_tools import is_ai_tools_enabled, open_ai_settings_dialog, show_ai_key_source
from .auto_scroll import is_auto_scroll_enabled, set_auto_scroll_enabled
from .clipboard_json_cards import (
    ACTION_LABEL as CLIPBOARD_JSON_ACTION_LABEL,
    import_cards_from_clipboard_json,
)
from .early_review import (
    EARLY_REVIEW_DEFAULT_COUNT,
    EARLY_REVIEW_SHORTCUT,
    build_early_review_filtered_deck,
)
from .f3_blocker import is_default_f3_shortcut_disabled, set_default_f3_shortcut_disabled
from .hard_cards import open_hard_cards_dialog
from .lightning_mode import (
    build_lightning_mode_filtered_deck_for_current_deck,
    lightning_answer_seconds,
    lightning_card_limit,
    lightning_question_seconds,
    set_lightning_answer_seconds,
    set_lightning_card_limit,
    set_lightning_question_seconds,
)
from .missed_today import (
    copy_missed_today_text,
    export_missed_today_text_file,
    make_missed_today_filtered_deck,
    open_missed_today_html_viewer,
    summarize_missed_today,
)
from .no_image_today import open_no_image_today_dialog
from .recent_leeches import (
    is_recent_leech_banner_enabled,
    open_recent_leeches_browser,
    recent_leeches_summary,
    set_recent_leech_banner_enabled,
)
from .recent_new_cards import open_recent_new_cards_dialog
from .review_image_overlay import (
    EXIT_SHORTCUT,
    is_review_image_overlay_enabled,
    is_review_image_overlay_remember_position_enabled,
    NEXT_SHORTCUT,
    PREVIOUS_SHORTCUT,
    set_review_image_overlay_enabled,
    set_review_image_overlay_remember_position_enabled,
)
from .return_non_new import open_return_non_new_dialog
from .suspended_browser import open_suspended_cards_browser
from .tts_audio import is_tts_audio_enabled, set_tts_audio_enabled
from .underline_trailing_spaces import (
    is_underline_trailing_spaces_fix_enabled,
    set_underline_trailing_spaces_fix_enabled,
)
from .visual_card_multitude import (
    is_add_cards_auto_deck_enabled,
    is_add_cards_diagnosis_button_enabled,
    is_add_cards_multi_image_counter_enabled,
    is_add_cards_sticky_fields_default_on_enabled,
    is_add_cards_tab_cycles_clozes_enabled,
    is_visual_card_multitude_add_button_enabled,
    is_visual_card_multitude_auto_visual_deck_enabled,
    set_add_cards_auto_deck_enabled,
    set_add_cards_diagnosis_button_enabled,
    set_add_cards_multi_image_counter_enabled,
    set_add_cards_sticky_fields_default_on_enabled,
    set_add_cards_tab_cycles_clozes_enabled,
    set_visual_card_multitude_add_button_enabled,
    set_visual_card_multitude_auto_visual_deck_enabled,
)
from .settings import get_setting, set_setting


ADDON_NAME = "Anki Pocket Knife"
LAUNCHER_SHORTCUT = "Ctrl+Shift+Q"
LEGACY_EARLY_REVIEW_PACKAGE = "early_review_deck"
_HOOK_REGISTERED = False
_MENU_REGISTERED_FLAG = "_anki_pocket_knife_menu_registered"
_dialog: "PocketKnifeLauncherDialog | None" = None
_auto_scroll_action: QAction | None = None
_review_image_overlay_action: QAction | None = None
_review_image_overlay_remember_position_action: QAction | None = None
_recent_leech_banner_action: QAction | None = None
_tts_audio_action: QAction | None = None
_disable_f3_action: QAction | None = None
_underline_trailing_spaces_action: QAction | None = None
_add_cards_auto_deck_action: QAction | None = None
_add_cards_diagnosis_action: QAction | None = None
_add_cards_multi_image_counter_action: QAction | None = None
_add_cards_sticky_fields_action: QAction | None = None
_add_cards_tab_cycles_clozes_action: QAction | None = None
_visual_card_multitude_action: QAction | None = None
_visual_card_multitude_auto_visual_deck_action: QAction | None = None
_ai_tools_action: QAction | None = None


def _shortcut_taken(shortcut_text: str) -> bool:
    wanted = shortcut_text.strip()
    if not wanted:
        return False

    for action in mw.findChildren(QAction):
        try:
            existing = action.shortcut().toString().strip()
        except Exception:
            existing = ""
        if existing and existing.casefold() == wanted.casefold():
            return True

    return False


def _addon_package_exists(package_name: str) -> bool:
    manager = getattr(mw, "addonManager", None)
    if manager is None:
        return False

    folder_fn = getattr(manager, "addonsFolder", None)
    folder_path = None
    if callable(folder_fn):
        try:
            folder_path = folder_fn()
        except Exception:
            folder_path = None
    elif folder_fn:
        folder_path = folder_fn

    if folder_path is None:
        folder_path = getattr(manager, "addons_folder", None)

    try:
        addons_root = Path(str(folder_path))
    except Exception:
        return False

    return (addons_root / package_name).exists()


def _assign_shortcut_if_available(
    action: QAction,
    shortcut_text: str,
    *,
    skip_if_package_exists: str | None = None,
) -> None:
    if skip_if_package_exists and _addon_package_exists(skip_if_package_exists):
        return
    if _shortcut_taken(shortcut_text):
        return
    action.setShortcut(shortcut_text)


class PocketKnifeLauncherDialog(QDialog):
    def __init__(self) -> None:
        super().__init__(mw)
        self.setWindowTitle(ADDON_NAME)
        self.resize(620, 690)
        self._build_ui()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget(scroll)
        layout = QVBoxLayout(content)
        layout.setSpacing(14)

        intro = QLabel(
            "Quick actions for your Anki pocket knife. The early-review shortcut stays available here, "
            "and the missed-today tools are all one click away."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        early_review_box = QGroupBox("Early Review")
        early_review_layout = QVBoxLayout(early_review_box)
        early_review_copy = QLabel(
            "Build a filtered deck from tomorrow's review cards, prioritizing the longest intervals first."
        )
        early_review_copy.setWordWrap(True)
        early_review_layout.addWidget(early_review_copy)

        early_review_row = QHBoxLayout()
        early_review_row.addWidget(QLabel("Cards to pull:"))
        self.early_review_count = QSpinBox()
        self.early_review_count.setRange(1, 5000)
        self.early_review_count.setValue(EARLY_REVIEW_DEFAULT_COUNT)
        early_review_row.addWidget(self.early_review_count)
        early_review_row.addStretch(1)
        self.early_review_button = QPushButton("Build Early Review Deck")
        early_review_row.addWidget(self.early_review_button)
        early_review_layout.addLayout(early_review_row)
        layout.addWidget(early_review_box)

        study_repair_box = QGroupBox("Study Repair")
        study_repair_layout = QVBoxLayout(study_repair_box)
        study_repair_copy = QLabel(
            "Rank recently reviewed cards that still look unstable or not truly learned, then open that exact set "
            "in Browser or copy clean note content for a tutor workflow."
        )
        study_repair_copy.setWordWrap(True)
        study_repair_layout.addWidget(study_repair_copy)
        self.study_repair_button = QPushButton("Open Study Repair")
        study_repair_layout.addWidget(self.study_repair_button)
        layout.addWidget(study_repair_box)

        missed_today_box = QGroupBox("Missed Today")
        missed_today_layout = QVBoxLayout(missed_today_box)
        self.missed_today_summary = QLabel()
        self.missed_today_summary.setWordWrap(True)
        missed_today_layout.addWidget(self.missed_today_summary)

        missed_today_grid = QGridLayout()
        self.copy_button = QPushButton("Copy Text")
        self.export_button = QPushButton("Save Text File")
        self.html_button = QPushButton("Open HTML Viewer")
        self.deck_button = QPushButton("Make Filtered Deck")
        self.refresh_button = QPushButton("Refresh Count")
        missed_today_grid.addWidget(self.copy_button, 0, 0)
        missed_today_grid.addWidget(self.export_button, 0, 1)
        missed_today_grid.addWidget(self.html_button, 1, 0)
        missed_today_grid.addWidget(self.deck_button, 1, 1)
        missed_today_grid.addWidget(self.refresh_button, 2, 0, 1, 2)
        missed_today_layout.addLayout(missed_today_grid)
        layout.addWidget(missed_today_box)

        no_image_box = QGroupBox("No-Image Today")
        no_image_layout = QVBoxLayout(no_image_box)
        no_image_copy = QLabel(
            "Build a scheduling-affecting filtered deck from today's surfaced cards whose question side has no image."
        )
        no_image_copy.setWordWrap(True)
        no_image_layout.addWidget(no_image_copy)
        self.no_image_button = QPushButton("Build No-Image Today Deck")
        no_image_layout.addWidget(self.no_image_button)
        layout.addWidget(no_image_box)

        lightning_box = QGroupBox("Lightning Mode")
        lightning_layout = QVBoxLayout(lightning_box)
        lightning_copy = QLabel(
            "Build a rescheduling filtered deck from the most recent still-new cards in the current deck tree, even if "
            "some of those cards are already sitting in other filtered decks. Lightning decks force auto-advance, show "
            "the answer after the question timer expires, and bury cards that still time out on the answer side."
        )
        lightning_copy.setWordWrap(True)
        lightning_layout.addWidget(lightning_copy)

        lightning_grid = QGridLayout()
        lightning_grid.addWidget(QLabel("Cards to pull:"), 0, 0)
        self.lightning_card_limit_spin = QSpinBox()
        self.lightning_card_limit_spin.setRange(1, 1000)
        self.lightning_card_limit_spin.setValue(lightning_card_limit())
        lightning_grid.addWidget(self.lightning_card_limit_spin, 0, 1)
        lightning_grid.addWidget(QLabel("Question seconds:"), 1, 0)
        self.lightning_question_seconds_spin = QSpinBox()
        self.lightning_question_seconds_spin.setRange(1, 60)
        self.lightning_question_seconds_spin.setValue(lightning_question_seconds())
        lightning_grid.addWidget(self.lightning_question_seconds_spin, 1, 1)
        lightning_grid.addWidget(QLabel("Answer seconds:"), 2, 0)
        self.lightning_answer_seconds_spin = QSpinBox()
        self.lightning_answer_seconds_spin.setRange(1, 60)
        self.lightning_answer_seconds_spin.setValue(lightning_answer_seconds())
        lightning_grid.addWidget(self.lightning_answer_seconds_spin, 2, 1)
        lightning_grid.setColumnStretch(2, 1)
        lightning_layout.addLayout(lightning_grid)

        self.lightning_button = QPushButton("Build Lightning Mode For Current Deck")
        lightning_layout.addWidget(self.lightning_button)
        layout.addWidget(lightning_box)

        recent_new_box = QGroupBox("Recent New Cards")
        recent_new_layout = QVBoxLayout(recent_new_box)
        recent_new_copy = QLabel(
            "Build a rescheduling filtered deck from cards that are still new and were created today or in the past few days."
        )
        recent_new_copy.setWordWrap(True)
        recent_new_layout.addWidget(recent_new_copy)
        self.recent_new_button = QPushButton("Build Recent New Cards Deck")
        recent_new_layout.addWidget(self.recent_new_button)
        layout.addWidget(recent_new_box)

        browser_box = QGroupBox("Browser Tools")
        browser_layout = QVBoxLayout(browser_box)
        browser_copy = QLabel(
            "Open recent leeches or all suspended cards in the Browser, and optionally show a recent-leeches banner "
            "above the main deck list."
        )
        browser_copy.setWordWrap(True)
        browser_layout.addWidget(browser_copy)
        self.recent_leeches_summary = QLabel()
        self.recent_leeches_summary.setWordWrap(True)
        browser_layout.addWidget(self.recent_leeches_summary)
        self.recent_leeches_button = QPushButton("Open Recent Leeches In Browser")
        browser_layout.addWidget(self.recent_leeches_button)
        self.suspended_browser_button = QPushButton("Open Suspended Cards In Browser")
        browser_layout.addWidget(self.suspended_browser_button)
        self.recent_leech_banner_checkbox = QCheckBox(
            "Show a recent-leeches banner above the main deck list"
        )
        self.recent_leech_banner_checkbox.setChecked(is_recent_leech_banner_enabled())
        browser_layout.addWidget(self.recent_leech_banner_checkbox)
        layout.addWidget(browser_box)

        keyboard_box = QGroupBox("Keyboard Overrides")
        keyboard_layout = QVBoxLayout(keyboard_box)
        keyboard_copy = QLabel(
            "Optional shortcut override: disable Anki's built-in plain F3 shortcut so that key is left unused."
        )
        keyboard_copy.setWordWrap(True)
        keyboard_layout.addWidget(keyboard_copy)
        self.disable_f3_checkbox = QCheckBox("Disable Anki's default F3 shortcut")
        self.disable_f3_checkbox.setChecked(is_default_f3_shortcut_disabled())
        keyboard_layout.addWidget(self.disable_f3_checkbox)
        layout.addWidget(keyboard_box)

        editor_formatting_box = QGroupBox("Editor Formatting")
        editor_formatting_layout = QVBoxLayout(editor_formatting_box)
        editor_formatting_copy = QLabel(
            "Default-on editor helper: keep spaces out of underline while they are currently trailing, "
            "but allow those spaces to join the underline automatically once you continue the underlined phrase."
        )
        editor_formatting_copy.setWordWrap(True)
        editor_formatting_layout.addWidget(editor_formatting_copy)
        self.underline_trailing_spaces_checkbox = QCheckBox(
            "Keep currently trailing spaces out of underline"
        )
        self.underline_trailing_spaces_checkbox.setChecked(
            is_underline_trailing_spaces_fix_enabled()
        )
        editor_formatting_layout.addWidget(self.underline_trailing_spaces_checkbox)
        layout.addWidget(editor_formatting_box)

        filtered_cleanup_box = QGroupBox("Filtered Deck Cleanup")
        filtered_cleanup_layout = QVBoxLayout(filtered_cleanup_box)
        filtered_cleanup_copy = QLabel(
            "Choose a filtered deck and send only its current non-new cards back to their original deck while keeping "
            "their current schedule. Cards that are still new stay in the filtered deck."
        )
        filtered_cleanup_copy.setWordWrap(True)
        filtered_cleanup_layout.addWidget(filtered_cleanup_copy)
        self.return_non_new_button = QPushButton("Send Non-New Cards Home")
        filtered_cleanup_layout.addWidget(self.return_non_new_button)
        layout.addWidget(filtered_cleanup_box)

        add_cards_box = QGroupBox("Add Cards")
        add_cards_layout = QVBoxLayout(add_cards_box)
        add_cards_copy = QLabel(
            "Default-on helper for the normal Add Cards screen: show a pink picture-frame button that converts the "
            "current cloze note into your Visual_Card_Multitude note type by splitting cloze text, question text, "
            "images, and Extra into their matching fields."
        )
        add_cards_copy.setWordWrap(True)
        add_cards_layout.addWidget(add_cards_copy)
        self.visual_card_multitude_checkbox = QCheckBox(
            "Pink picture-frame converter button on the Add Cards screen"
        )
        self.visual_card_multitude_checkbox.setChecked(is_visual_card_multitude_add_button_enabled())
        add_cards_layout.addWidget(self.visual_card_multitude_checkbox)
        self.add_cards_sticky_fields_checkbox = QCheckBox(
            "Default Add Cards field thumbtacks to on for new note types"
        )
        self.add_cards_sticky_fields_checkbox.setChecked(
            is_add_cards_sticky_fields_default_on_enabled()
        )
        add_cards_layout.addWidget(self.add_cards_sticky_fields_checkbox)
        self.add_cards_auto_deck_checkbox = QCheckBox(
            "Auto-switch cloze notes between .NEW::Audio and .New::Visual based on Text images"
        )
        self.add_cards_auto_deck_checkbox.setChecked(is_add_cards_auto_deck_enabled())
        add_cards_layout.addWidget(self.add_cards_auto_deck_checkbox)
        self.add_cards_diagnosis_checkbox = QCheckBox(
            "Dx diagnosis-template button on the Add Cards screen"
        )
        self.add_cards_diagnosis_checkbox.setChecked(is_add_cards_diagnosis_button_enabled())
        add_cards_layout.addWidget(self.add_cards_diagnosis_checkbox)
        self.add_cards_multi_image_counter_checkbox = QCheckBox(
            "Add a live 1/N counter above the first Text-field image when more than one image is present"
        )
        self.add_cards_multi_image_counter_checkbox.setChecked(
            is_add_cards_multi_image_counter_enabled()
        )
        add_cards_layout.addWidget(self.add_cards_multi_image_counter_checkbox)
        self.add_cards_tab_cycles_clozes_checkbox = QCheckBox(
            "Tab cycles through cloze deletions when you're in the Text field"
        )
        self.add_cards_tab_cycles_clozes_checkbox.setChecked(
            is_add_cards_tab_cycles_clozes_enabled()
        )
        add_cards_layout.addWidget(self.add_cards_tab_cycles_clozes_checkbox)
        self.visual_card_multitude_auto_visual_deck_checkbox = QCheckBox(
            "Auto-switch Visual_Card_Multitude notes to .New::Visual"
        )
        self.visual_card_multitude_auto_visual_deck_checkbox.setChecked(
            is_visual_card_multitude_auto_visual_deck_enabled()
        )
        add_cards_layout.addWidget(self.visual_card_multitude_auto_visual_deck_checkbox)
        layout.addWidget(add_cards_box)

        ai_box = QGroupBox("AI Card Tools")
        ai_layout = QVBoxLayout(ai_box)
        ai_copy = QLabel(
            "Default-on sparkle button for Add Cards, plus Browser actions for selected notes."
        )
        ai_copy.setWordWrap(True)
        ai_layout.addWidget(ai_copy)
        self.ai_tools_checkbox = QCheckBox("Show Pocket Knife AI tools")
        self.ai_tools_checkbox.setChecked(is_ai_tools_enabled())
        ai_layout.addWidget(self.ai_tools_checkbox)
        ai_model_row = QHBoxLayout()
        ai_model_row.addWidget(QLabel("Model:"))
        self.ai_model_input = QLineEdit()
        self.ai_model_input.setText(str(get_setting("ai_tools_model") or "gpt-4.1"))
        ai_model_row.addWidget(self.ai_model_input)
        self.ai_key_button = QPushButton("Set OpenAI API Key")
        ai_model_row.addWidget(self.ai_key_button)
        ai_layout.addLayout(ai_model_row)
        layout.addWidget(ai_box)

        review_box = QGroupBox("Review Behavior")
        review_layout = QVBoxLayout(review_box)
        review_copy = QLabel(
            "Optional reviewer helpers: jump back to the top when you reveal the answer, cycle card images in a fullscreen "
            f"overlay with {NEXT_SHORTCUT}, go backward with {PREVIOUS_SHORTCUT}, close it with {EXIT_SHORTCUT} while "
            "it's open or the top-left Close button, and optionally allow or suppress "
            "audio playback from TTS-enabled cards."
        )
        review_copy.setWordWrap(True)
        review_layout.addWidget(review_copy)
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll to the top when answer is revealed")
        self.auto_scroll_checkbox.setChecked(is_auto_scroll_enabled())
        review_layout.addWidget(self.auto_scroll_checkbox)
        self.review_image_overlay_checkbox = QCheckBox(
            f"Reviewer image overlay shortcuts ({NEXT_SHORTCUT} next, {PREVIOUS_SHORTCUT} previous, {EXIT_SHORTCUT} close)"
        )
        self.review_image_overlay_checkbox.setChecked(is_review_image_overlay_enabled())
        review_layout.addWidget(self.review_image_overlay_checkbox)
        self.review_image_overlay_remember_position_checkbox = QCheckBox(
            "Remember image position after closing the overlay"
        )
        self.review_image_overlay_remember_position_checkbox.setChecked(
            is_review_image_overlay_remember_position_enabled()
        )
        review_layout.addWidget(self.review_image_overlay_remember_position_checkbox)
        self.tts_audio_checkbox = QCheckBox("Play audio from TTS-enabled cards")
        self.tts_audio_checkbox.setChecked(is_tts_audio_enabled())
        review_layout.addWidget(self.tts_audio_checkbox)
        layout.addWidget(review_box)

        layout.addStretch(1)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QPushButton("Close")
        close_row.addWidget(self.close_button)
        outer_layout.addLayout(close_row)

        self.early_review_button.clicked.connect(self._build_early_review_deck)
        self.study_repair_button.clicked.connect(lambda *_args: open_hard_cards_dialog())
        self.copy_button.clicked.connect(self._run_and_refresh(copy_missed_today_text))
        self.export_button.clicked.connect(self._run_and_refresh(export_missed_today_text_file))
        self.html_button.clicked.connect(self._run_and_refresh(open_missed_today_html_viewer))
        self.deck_button.clicked.connect(self._run_and_refresh(make_missed_today_filtered_deck))
        self.no_image_button.clicked.connect(lambda *_args: open_no_image_today_dialog())
        self.lightning_button.clicked.connect(
            lambda *_args: build_lightning_mode_filtered_deck_for_current_deck(parent=self)
        )
        self.recent_new_button.clicked.connect(lambda *_args: open_recent_new_cards_dialog())
        self.recent_leeches_button.clicked.connect(lambda *_args: open_recent_leeches_browser())
        self.suspended_browser_button.clicked.connect(lambda *_args: open_suspended_cards_browser())
        self.return_non_new_button.clicked.connect(lambda *_args: open_return_non_new_dialog())
        self.refresh_button.clicked.connect(self.refresh_missed_today_summary)
        self.lightning_card_limit_spin.valueChanged.connect(self._set_lightning_card_limit)
        self.lightning_question_seconds_spin.valueChanged.connect(self._set_lightning_question_seconds)
        self.lightning_answer_seconds_spin.valueChanged.connect(self._set_lightning_answer_seconds)
        self.recent_leech_banner_checkbox.toggled.connect(self._set_recent_leech_banner_enabled)
        self.disable_f3_checkbox.toggled.connect(self._set_disable_f3_enabled)
        self.underline_trailing_spaces_checkbox.toggled.connect(
            self._set_underline_trailing_spaces_enabled
        )
        self.visual_card_multitude_checkbox.toggled.connect(self._set_visual_card_multitude_enabled)
        self.add_cards_sticky_fields_checkbox.toggled.connect(
            self._set_add_cards_sticky_fields_default_on_enabled
        )
        self.add_cards_auto_deck_checkbox.toggled.connect(self._set_add_cards_auto_deck_enabled)
        self.add_cards_diagnosis_checkbox.toggled.connect(self._set_add_cards_diagnosis_enabled)
        self.add_cards_multi_image_counter_checkbox.toggled.connect(
            self._set_add_cards_multi_image_counter_enabled
        )
        self.add_cards_tab_cycles_clozes_checkbox.toggled.connect(
            self._set_add_cards_tab_cycles_clozes_enabled
        )
        self.visual_card_multitude_auto_visual_deck_checkbox.toggled.connect(
            self._set_visual_card_multitude_auto_visual_deck_enabled
        )
        self.ai_tools_checkbox.toggled.connect(self._set_ai_tools_enabled)
        self.ai_model_input.editingFinished.connect(self._set_ai_model)
        self.ai_key_button.clicked.connect(lambda *_args: open_ai_settings_dialog())
        self.auto_scroll_checkbox.toggled.connect(self._set_auto_scroll_enabled)
        self.review_image_overlay_checkbox.toggled.connect(self._set_review_image_overlay_enabled)
        self.review_image_overlay_remember_position_checkbox.toggled.connect(
            self._set_review_image_overlay_remember_position_enabled
        )
        self.tts_audio_checkbox.toggled.connect(self._set_tts_audio_enabled)
        self.close_button.clicked.connect(self.close)

        self.refresh_missed_today_summary()

    def _run_and_refresh(self, action):
        def runner(*_args) -> None:
            action()
            self.refresh_missed_today_summary()

        return runner

    def _build_early_review_deck(self, *_args) -> None:
        build_early_review_filtered_deck(int(self.early_review_count.value()), prompt_if_missing=False)

    def refresh_missed_today_summary(self) -> None:
        self.missed_today_summary.setText(summarize_missed_today())
        if hasattr(self, "recent_leeches_summary"):
            self.recent_leeches_summary.setText(recent_leeches_summary())
        if hasattr(self, "recent_leech_banner_checkbox"):
            self.recent_leech_banner_checkbox.blockSignals(True)
            self.recent_leech_banner_checkbox.setChecked(is_recent_leech_banner_enabled())
            self.recent_leech_banner_checkbox.blockSignals(False)
        if hasattr(self, "auto_scroll_checkbox"):
            self.auto_scroll_checkbox.blockSignals(True)
            self.auto_scroll_checkbox.setChecked(is_auto_scroll_enabled())
            self.auto_scroll_checkbox.blockSignals(False)
        if hasattr(self, "review_image_overlay_checkbox"):
            self.review_image_overlay_checkbox.blockSignals(True)
            self.review_image_overlay_checkbox.setChecked(is_review_image_overlay_enabled())
            self.review_image_overlay_checkbox.blockSignals(False)
        if hasattr(self, "review_image_overlay_remember_position_checkbox"):
            self.review_image_overlay_remember_position_checkbox.blockSignals(True)
            self.review_image_overlay_remember_position_checkbox.setChecked(
                is_review_image_overlay_remember_position_enabled()
            )
            self.review_image_overlay_remember_position_checkbox.blockSignals(False)
        if hasattr(self, "tts_audio_checkbox"):
            self.tts_audio_checkbox.blockSignals(True)
            self.tts_audio_checkbox.setChecked(is_tts_audio_enabled())
            self.tts_audio_checkbox.blockSignals(False)
        if hasattr(self, "disable_f3_checkbox"):
            self.disable_f3_checkbox.blockSignals(True)
            self.disable_f3_checkbox.setChecked(is_default_f3_shortcut_disabled())
            self.disable_f3_checkbox.blockSignals(False)
        if hasattr(self, "underline_trailing_spaces_checkbox"):
            self.underline_trailing_spaces_checkbox.blockSignals(True)
            self.underline_trailing_spaces_checkbox.setChecked(
                is_underline_trailing_spaces_fix_enabled()
            )
            self.underline_trailing_spaces_checkbox.blockSignals(False)
        if hasattr(self, "lightning_card_limit_spin"):
            self.lightning_card_limit_spin.blockSignals(True)
            self.lightning_card_limit_spin.setValue(lightning_card_limit())
            self.lightning_card_limit_spin.blockSignals(False)
        if hasattr(self, "lightning_question_seconds_spin"):
            self.lightning_question_seconds_spin.blockSignals(True)
            self.lightning_question_seconds_spin.setValue(lightning_question_seconds())
            self.lightning_question_seconds_spin.blockSignals(False)
        if hasattr(self, "lightning_answer_seconds_spin"):
            self.lightning_answer_seconds_spin.blockSignals(True)
            self.lightning_answer_seconds_spin.setValue(lightning_answer_seconds())
            self.lightning_answer_seconds_spin.blockSignals(False)
        if hasattr(self, "visual_card_multitude_checkbox"):
            self.visual_card_multitude_checkbox.blockSignals(True)
            self.visual_card_multitude_checkbox.setChecked(is_visual_card_multitude_add_button_enabled())
            self.visual_card_multitude_checkbox.blockSignals(False)
        if hasattr(self, "add_cards_sticky_fields_checkbox"):
            self.add_cards_sticky_fields_checkbox.blockSignals(True)
            self.add_cards_sticky_fields_checkbox.setChecked(
                is_add_cards_sticky_fields_default_on_enabled()
            )
            self.add_cards_sticky_fields_checkbox.blockSignals(False)
        if hasattr(self, "add_cards_auto_deck_checkbox"):
            self.add_cards_auto_deck_checkbox.blockSignals(True)
            self.add_cards_auto_deck_checkbox.setChecked(is_add_cards_auto_deck_enabled())
            self.add_cards_auto_deck_checkbox.blockSignals(False)
        if hasattr(self, "add_cards_diagnosis_checkbox"):
            self.add_cards_diagnosis_checkbox.blockSignals(True)
            self.add_cards_diagnosis_checkbox.setChecked(is_add_cards_diagnosis_button_enabled())
            self.add_cards_diagnosis_checkbox.blockSignals(False)
        if hasattr(self, "add_cards_multi_image_counter_checkbox"):
            self.add_cards_multi_image_counter_checkbox.blockSignals(True)
            self.add_cards_multi_image_counter_checkbox.setChecked(
                is_add_cards_multi_image_counter_enabled()
            )
            self.add_cards_multi_image_counter_checkbox.blockSignals(False)
        if hasattr(self, "add_cards_tab_cycles_clozes_checkbox"):
            self.add_cards_tab_cycles_clozes_checkbox.blockSignals(True)
            self.add_cards_tab_cycles_clozes_checkbox.setChecked(
                is_add_cards_tab_cycles_clozes_enabled()
            )
            self.add_cards_tab_cycles_clozes_checkbox.blockSignals(False)
        if hasattr(self, "visual_card_multitude_auto_visual_deck_checkbox"):
            self.visual_card_multitude_auto_visual_deck_checkbox.blockSignals(True)
            self.visual_card_multitude_auto_visual_deck_checkbox.setChecked(
                is_visual_card_multitude_auto_visual_deck_enabled()
            )
            self.visual_card_multitude_auto_visual_deck_checkbox.blockSignals(False)

    def showEvent(self, event) -> None:
        self.refresh_missed_today_summary()
        super().showEvent(event)

    def _set_auto_scroll_enabled(self, checked: bool) -> None:
        set_auto_scroll_enabled(bool(checked))
        sync_settings_ui()

    def _set_review_image_overlay_enabled(self, checked: bool) -> None:
        set_review_image_overlay_enabled(bool(checked))
        sync_settings_ui()

    def _set_review_image_overlay_remember_position_enabled(self, checked: bool) -> None:
        set_review_image_overlay_remember_position_enabled(bool(checked))
        sync_settings_ui()

    def _set_recent_leech_banner_enabled(self, checked: bool) -> None:
        set_recent_leech_banner_enabled(bool(checked))
        sync_settings_ui()

    def _set_tts_audio_enabled(self, checked: bool) -> None:
        set_tts_audio_enabled(bool(checked))
        sync_settings_ui()

    def _set_disable_f3_enabled(self, checked: bool) -> None:
        set_default_f3_shortcut_disabled(bool(checked))
        sync_settings_ui()

    def _set_underline_trailing_spaces_enabled(self, checked: bool) -> None:
        set_underline_trailing_spaces_fix_enabled(bool(checked))
        sync_settings_ui()

    def _set_lightning_card_limit(self, value: int) -> None:
        set_lightning_card_limit(int(value))
        sync_settings_ui()

    def _set_lightning_question_seconds(self, value: int) -> None:
        set_lightning_question_seconds(int(value))
        sync_settings_ui()

    def _set_lightning_answer_seconds(self, value: int) -> None:
        set_lightning_answer_seconds(int(value))
        sync_settings_ui()

    def _set_visual_card_multitude_enabled(self, checked: bool) -> None:
        set_visual_card_multitude_add_button_enabled(bool(checked))
        sync_settings_ui()

    def _set_add_cards_sticky_fields_default_on_enabled(self, checked: bool) -> None:
        set_add_cards_sticky_fields_default_on_enabled(bool(checked))
        sync_settings_ui()

    def _set_add_cards_auto_deck_enabled(self, checked: bool) -> None:
        set_add_cards_auto_deck_enabled(bool(checked))
        sync_settings_ui()

    def _set_add_cards_diagnosis_enabled(self, checked: bool) -> None:
        set_add_cards_diagnosis_button_enabled(bool(checked))
        sync_settings_ui()

    def _set_add_cards_multi_image_counter_enabled(self, checked: bool) -> None:
        set_add_cards_multi_image_counter_enabled(bool(checked))
        sync_settings_ui()

    def _set_add_cards_tab_cycles_clozes_enabled(self, checked: bool) -> None:
        set_add_cards_tab_cycles_clozes_enabled(bool(checked))
        sync_settings_ui()

    def _set_visual_card_multitude_auto_visual_deck_enabled(self, checked: bool) -> None:
        set_visual_card_multitude_auto_visual_deck_enabled(bool(checked))
        sync_settings_ui()

    def _set_ai_tools_enabled(self, checked: bool) -> None:
        set_setting("ai_tools_enabled", bool(checked))
        sync_settings_ui()

    def _set_ai_model(self) -> None:
        set_setting("ai_tools_model", str(self.ai_model_input.text() or "").strip() or "gpt-4.1")
        sync_settings_ui()


def open_launcher() -> None:
    global _dialog

    if _dialog is None:
        _dialog = PocketKnifeLauncherDialog()

    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()
    _dialog.refresh_missed_today_summary()


def sync_settings_ui() -> None:
    global _auto_scroll_action
    global _review_image_overlay_action
    global _review_image_overlay_remember_position_action
    global _recent_leech_banner_action
    global _tts_audio_action
    global _disable_f3_action
    global _underline_trailing_spaces_action
    global _add_cards_auto_deck_action
    global _add_cards_diagnosis_action
    global _add_cards_multi_image_counter_action
    global _add_cards_sticky_fields_action
    global _add_cards_tab_cycles_clozes_action
    global _visual_card_multitude_action
    global _visual_card_multitude_auto_visual_deck_action
    global _ai_tools_action

    auto_scroll_enabled = is_auto_scroll_enabled()
    if _auto_scroll_action is not None:
        _auto_scroll_action.blockSignals(True)
        _auto_scroll_action.setChecked(auto_scroll_enabled)
        _auto_scroll_action.blockSignals(False)
    review_image_overlay_enabled = is_review_image_overlay_enabled()
    if _review_image_overlay_action is not None:
        _review_image_overlay_action.blockSignals(True)
        _review_image_overlay_action.setChecked(review_image_overlay_enabled)
        _review_image_overlay_action.blockSignals(False)
    review_image_overlay_remember_position_enabled = (
        is_review_image_overlay_remember_position_enabled()
    )
    if _review_image_overlay_remember_position_action is not None:
        _review_image_overlay_remember_position_action.blockSignals(True)
        _review_image_overlay_remember_position_action.setChecked(
            review_image_overlay_remember_position_enabled
        )
        _review_image_overlay_remember_position_action.blockSignals(False)
    recent_leech_banner_enabled = is_recent_leech_banner_enabled()
    if _recent_leech_banner_action is not None:
        _recent_leech_banner_action.blockSignals(True)
        _recent_leech_banner_action.setChecked(recent_leech_banner_enabled)
        _recent_leech_banner_action.blockSignals(False)
    tts_audio_enabled = is_tts_audio_enabled()
    if _tts_audio_action is not None:
        _tts_audio_action.blockSignals(True)
        _tts_audio_action.setChecked(tts_audio_enabled)
        _tts_audio_action.blockSignals(False)
    disable_f3_enabled = is_default_f3_shortcut_disabled()
    if _disable_f3_action is not None:
        _disable_f3_action.blockSignals(True)
        _disable_f3_action.setChecked(disable_f3_enabled)
        _disable_f3_action.blockSignals(False)
    underline_trailing_spaces_enabled = is_underline_trailing_spaces_fix_enabled()
    if _underline_trailing_spaces_action is not None:
        _underline_trailing_spaces_action.blockSignals(True)
        _underline_trailing_spaces_action.setChecked(underline_trailing_spaces_enabled)
        _underline_trailing_spaces_action.blockSignals(False)
    add_cards_sticky_fields_enabled = is_add_cards_sticky_fields_default_on_enabled()
    if _add_cards_sticky_fields_action is not None:
        _add_cards_sticky_fields_action.blockSignals(True)
        _add_cards_sticky_fields_action.setChecked(add_cards_sticky_fields_enabled)
        _add_cards_sticky_fields_action.blockSignals(False)
    add_cards_auto_deck_enabled = is_add_cards_auto_deck_enabled()
    if _add_cards_auto_deck_action is not None:
        _add_cards_auto_deck_action.blockSignals(True)
        _add_cards_auto_deck_action.setChecked(add_cards_auto_deck_enabled)
        _add_cards_auto_deck_action.blockSignals(False)
    add_cards_diagnosis_enabled = is_add_cards_diagnosis_button_enabled()
    if _add_cards_diagnosis_action is not None:
        _add_cards_diagnosis_action.blockSignals(True)
        _add_cards_diagnosis_action.setChecked(add_cards_diagnosis_enabled)
        _add_cards_diagnosis_action.blockSignals(False)
    add_cards_multi_image_counter_enabled = is_add_cards_multi_image_counter_enabled()
    if _add_cards_multi_image_counter_action is not None:
        _add_cards_multi_image_counter_action.blockSignals(True)
        _add_cards_multi_image_counter_action.setChecked(add_cards_multi_image_counter_enabled)
        _add_cards_multi_image_counter_action.blockSignals(False)
    add_cards_tab_cycles_clozes_enabled = is_add_cards_tab_cycles_clozes_enabled()
    if _add_cards_tab_cycles_clozes_action is not None:
        _add_cards_tab_cycles_clozes_action.blockSignals(True)
        _add_cards_tab_cycles_clozes_action.setChecked(add_cards_tab_cycles_clozes_enabled)
        _add_cards_tab_cycles_clozes_action.blockSignals(False)
    visual_card_enabled = is_visual_card_multitude_add_button_enabled()
    if _visual_card_multitude_action is not None:
        _visual_card_multitude_action.blockSignals(True)
        _visual_card_multitude_action.setChecked(visual_card_enabled)
        _visual_card_multitude_action.blockSignals(False)
    visual_card_auto_visual_enabled = is_visual_card_multitude_auto_visual_deck_enabled()
    if _visual_card_multitude_auto_visual_deck_action is not None:
        _visual_card_multitude_auto_visual_deck_action.blockSignals(True)
        _visual_card_multitude_auto_visual_deck_action.setChecked(visual_card_auto_visual_enabled)
        _visual_card_multitude_auto_visual_deck_action.blockSignals(False)
    ai_tools_enabled = is_ai_tools_enabled()
    if _ai_tools_action is not None:
        _ai_tools_action.blockSignals(True)
        _ai_tools_action.setChecked(ai_tools_enabled)
        _ai_tools_action.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "auto_scroll_checkbox"):
        _dialog.auto_scroll_checkbox.blockSignals(True)
        _dialog.auto_scroll_checkbox.setChecked(auto_scroll_enabled)
        _dialog.auto_scroll_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "review_image_overlay_checkbox"):
        _dialog.review_image_overlay_checkbox.blockSignals(True)
        _dialog.review_image_overlay_checkbox.setChecked(review_image_overlay_enabled)
        _dialog.review_image_overlay_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "review_image_overlay_remember_position_checkbox"):
        _dialog.review_image_overlay_remember_position_checkbox.blockSignals(True)
        _dialog.review_image_overlay_remember_position_checkbox.setChecked(
            review_image_overlay_remember_position_enabled
        )
        _dialog.review_image_overlay_remember_position_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "tts_audio_checkbox"):
        _dialog.tts_audio_checkbox.blockSignals(True)
        _dialog.tts_audio_checkbox.setChecked(tts_audio_enabled)
        _dialog.tts_audio_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "recent_leech_banner_checkbox"):
        _dialog.recent_leech_banner_checkbox.blockSignals(True)
        _dialog.recent_leech_banner_checkbox.setChecked(recent_leech_banner_enabled)
        _dialog.recent_leech_banner_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "recent_leeches_summary"):
        _dialog.recent_leeches_summary.setText(recent_leeches_summary())
    if _dialog is not None and hasattr(_dialog, "disable_f3_checkbox"):
        _dialog.disable_f3_checkbox.blockSignals(True)
        _dialog.disable_f3_checkbox.setChecked(disable_f3_enabled)
        _dialog.disable_f3_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "underline_trailing_spaces_checkbox"):
        _dialog.underline_trailing_spaces_checkbox.blockSignals(True)
        _dialog.underline_trailing_spaces_checkbox.setChecked(underline_trailing_spaces_enabled)
        _dialog.underline_trailing_spaces_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "add_cards_sticky_fields_checkbox"):
        _dialog.add_cards_sticky_fields_checkbox.blockSignals(True)
        _dialog.add_cards_sticky_fields_checkbox.setChecked(add_cards_sticky_fields_enabled)
        _dialog.add_cards_sticky_fields_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "add_cards_auto_deck_checkbox"):
        _dialog.add_cards_auto_deck_checkbox.blockSignals(True)
        _dialog.add_cards_auto_deck_checkbox.setChecked(add_cards_auto_deck_enabled)
        _dialog.add_cards_auto_deck_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "add_cards_diagnosis_checkbox"):
        _dialog.add_cards_diagnosis_checkbox.blockSignals(True)
        _dialog.add_cards_diagnosis_checkbox.setChecked(add_cards_diagnosis_enabled)
        _dialog.add_cards_diagnosis_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "add_cards_multi_image_counter_checkbox"):
        _dialog.add_cards_multi_image_counter_checkbox.blockSignals(True)
        _dialog.add_cards_multi_image_counter_checkbox.setChecked(add_cards_multi_image_counter_enabled)
        _dialog.add_cards_multi_image_counter_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "add_cards_tab_cycles_clozes_checkbox"):
        _dialog.add_cards_tab_cycles_clozes_checkbox.blockSignals(True)
        _dialog.add_cards_tab_cycles_clozes_checkbox.setChecked(add_cards_tab_cycles_clozes_enabled)
        _dialog.add_cards_tab_cycles_clozes_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "visual_card_multitude_checkbox"):
        _dialog.visual_card_multitude_checkbox.blockSignals(True)
        _dialog.visual_card_multitude_checkbox.setChecked(visual_card_enabled)
        _dialog.visual_card_multitude_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "visual_card_multitude_auto_visual_deck_checkbox"):
        _dialog.visual_card_multitude_auto_visual_deck_checkbox.blockSignals(True)
        _dialog.visual_card_multitude_auto_visual_deck_checkbox.setChecked(visual_card_auto_visual_enabled)
        _dialog.visual_card_multitude_auto_visual_deck_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "ai_tools_checkbox"):
        _dialog.ai_tools_checkbox.blockSignals(True)
        _dialog.ai_tools_checkbox.setChecked(ai_tools_enabled)
        _dialog.ai_tools_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "ai_model_input"):
        _dialog.ai_model_input.blockSignals(True)
        _dialog.ai_model_input.setText(str(get_setting("ai_tools_model") or "gpt-4.1"))
        _dialog.ai_model_input.blockSignals(False)


def _toggle_auto_scroll(checked: bool) -> None:
    set_auto_scroll_enabled(bool(checked))
    sync_settings_ui()


def _toggle_review_image_overlay(checked: bool) -> None:
    set_review_image_overlay_enabled(bool(checked))
    sync_settings_ui()


def _toggle_review_image_overlay_remember_position(checked: bool) -> None:
    set_review_image_overlay_remember_position_enabled(bool(checked))
    sync_settings_ui()


def _toggle_recent_leech_banner(checked: bool) -> None:
    set_recent_leech_banner_enabled(bool(checked))
    sync_settings_ui()


def _toggle_tts_audio(checked: bool) -> None:
    set_tts_audio_enabled(bool(checked))
    sync_settings_ui()


def _toggle_disable_f3(checked: bool) -> None:
    set_default_f3_shortcut_disabled(bool(checked))
    sync_settings_ui()


def _toggle_underline_trailing_spaces(checked: bool) -> None:
    set_underline_trailing_spaces_fix_enabled(bool(checked))
    sync_settings_ui()


def _toggle_visual_card_multitude_button(checked: bool) -> None:
    set_visual_card_multitude_add_button_enabled(bool(checked))
    sync_settings_ui()


def _toggle_add_cards_sticky_fields_default_on(checked: bool) -> None:
    set_add_cards_sticky_fields_default_on_enabled(bool(checked))
    sync_settings_ui()


def _toggle_add_cards_auto_deck(checked: bool) -> None:
    set_add_cards_auto_deck_enabled(bool(checked))
    sync_settings_ui()


def _toggle_add_cards_diagnosis(checked: bool) -> None:
    set_add_cards_diagnosis_button_enabled(bool(checked))
    sync_settings_ui()


def _toggle_add_cards_multi_image_counter(checked: bool) -> None:
    set_add_cards_multi_image_counter_enabled(bool(checked))
    sync_settings_ui()


def _toggle_add_cards_tab_cycles_clozes(checked: bool) -> None:
    set_add_cards_tab_cycles_clozes_enabled(bool(checked))
    sync_settings_ui()


def _toggle_visual_card_multitude_auto_visual_deck(checked: bool) -> None:
    set_visual_card_multitude_auto_visual_deck_enabled(bool(checked))
    sync_settings_ui()


def _toggle_ai_tools(checked: bool) -> None:
    set_setting("ai_tools_enabled", bool(checked))
    sync_settings_ui()


def _register_menu() -> None:
    global _auto_scroll_action
    global _review_image_overlay_action
    global _review_image_overlay_remember_position_action
    global _recent_leech_banner_action
    global _tts_audio_action
    global _disable_f3_action
    global _underline_trailing_spaces_action
    global _add_cards_auto_deck_action
    global _add_cards_diagnosis_action
    global _add_cards_multi_image_counter_action
    global _add_cards_sticky_fields_action
    global _add_cards_tab_cycles_clozes_action
    global _visual_card_multitude_action
    global _visual_card_multitude_auto_visual_deck_action
    if getattr(mw, _MENU_REGISTERED_FLAG, False):
        return

    tools_menu = mw.form.menuTools
    pocket_menu = QMenu(ADDON_NAME, mw)
    tools_menu.addMenu(pocket_menu)

    open_action = QAction("Open Pocket Knife Launcher", mw)
    _assign_shortcut_if_available(open_action, LAUNCHER_SHORTCUT)
    open_action.triggered.connect(lambda *_args: open_launcher())
    pocket_menu.addAction(open_action)

    pocket_menu.addSeparator()

    early_review_action = QAction("Build Early Review Deck", mw)
    _assign_shortcut_if_available(
        early_review_action,
        EARLY_REVIEW_SHORTCUT,
        skip_if_package_exists=LEGACY_EARLY_REVIEW_PACKAGE,
    )
    early_review_action.triggered.connect(lambda *_args: build_early_review_filtered_deck())
    pocket_menu.addAction(early_review_action)

    clipboard_json_action = QAction(CLIPBOARD_JSON_ACTION_LABEL, mw)
    clipboard_json_action.triggered.connect(lambda *_args: import_cards_from_clipboard_json())
    pocket_menu.addAction(clipboard_json_action)

    pocket_menu.addSeparator()

    copy_action = QAction("Copy Missed-Today Text", mw)
    copy_action.triggered.connect(lambda *_args: copy_missed_today_text())
    pocket_menu.addAction(copy_action)

    export_action = QAction("Save Missed-Today Text File", mw)
    export_action.triggered.connect(lambda *_args: export_missed_today_text_file())
    pocket_menu.addAction(export_action)

    html_action = QAction("Open Missed-Today HTML Viewer", mw)
    html_action.triggered.connect(lambda *_args: open_missed_today_html_viewer())
    pocket_menu.addAction(html_action)

    deck_action = QAction("Make Missed-Today Filtered Deck", mw)
    deck_action.triggered.connect(lambda *_args: make_missed_today_filtered_deck())
    pocket_menu.addAction(deck_action)

    no_image_action = QAction("Build No-Image Today Deck", mw)
    no_image_action.triggered.connect(lambda *_args: open_no_image_today_dialog())
    pocket_menu.addAction(no_image_action)

    lightning_action = QAction("Build Lightning Mode For Current Deck", mw)
    lightning_action.triggered.connect(
        lambda *_args: build_lightning_mode_filtered_deck_for_current_deck()
    )
    pocket_menu.addAction(lightning_action)

    recent_new_action = QAction("Build Recent New Cards Deck", mw)
    recent_new_action.triggered.connect(lambda *_args: open_recent_new_cards_dialog())
    pocket_menu.addAction(recent_new_action)

    study_repair_action = QAction("Open Study Repair", mw)
    study_repair_action.triggered.connect(lambda *_args: open_hard_cards_dialog())
    pocket_menu.addAction(study_repair_action)

    recent_leeches_action = QAction("Open Recent Leeches In Browser", mw)
    recent_leeches_action.triggered.connect(lambda *_args: open_recent_leeches_browser())
    pocket_menu.addAction(recent_leeches_action)

    suspended_browser_action = QAction("Open Suspended Cards In Browser", mw)
    suspended_browser_action.triggered.connect(lambda *_args: open_suspended_cards_browser())
    pocket_menu.addAction(suspended_browser_action)

    return_non_new_action = QAction("Send Filtered Deck Non-New Cards Home", mw)
    return_non_new_action.triggered.connect(lambda *_args: open_return_non_new_dialog())
    pocket_menu.addAction(return_non_new_action)

    pocket_menu.addSeparator()

    _disable_f3_action = QAction("Disable Anki's Default F3 Shortcut", mw)
    _disable_f3_action.setCheckable(True)
    _disable_f3_action.setChecked(is_default_f3_shortcut_disabled())
    _disable_f3_action.triggered.connect(_toggle_disable_f3)
    pocket_menu.addAction(_disable_f3_action)

    _underline_trailing_spaces_action = QAction("Keep Trailing Spaces Out Of Underline", mw)
    _underline_trailing_spaces_action.setCheckable(True)
    _underline_trailing_spaces_action.setChecked(is_underline_trailing_spaces_fix_enabled())
    _underline_trailing_spaces_action.triggered.connect(_toggle_underline_trailing_spaces)
    pocket_menu.addAction(_underline_trailing_spaces_action)

    _recent_leech_banner_action = QAction("Recent-Leech Banner On Deck List", mw)
    _recent_leech_banner_action.setCheckable(True)
    _recent_leech_banner_action.setChecked(is_recent_leech_banner_enabled())
    _recent_leech_banner_action.triggered.connect(_toggle_recent_leech_banner)
    pocket_menu.addAction(_recent_leech_banner_action)

    _add_cards_sticky_fields_action = QAction("Default Sticky Fields On In Add Cards", mw)
    _add_cards_sticky_fields_action.setCheckable(True)
    _add_cards_sticky_fields_action.setChecked(is_add_cards_sticky_fields_default_on_enabled())
    _add_cards_sticky_fields_action.triggered.connect(_toggle_add_cards_sticky_fields_default_on)
    pocket_menu.addAction(_add_cards_sticky_fields_action)

    _add_cards_auto_deck_action = QAction("Auto Deck For Cloze Add Cards", mw)
    _add_cards_auto_deck_action.setCheckable(True)
    _add_cards_auto_deck_action.setChecked(is_add_cards_auto_deck_enabled())
    _add_cards_auto_deck_action.triggered.connect(_toggle_add_cards_auto_deck)
    pocket_menu.addAction(_add_cards_auto_deck_action)

    _add_cards_diagnosis_action = QAction("Dx Diagnosis Button In Add Cards", mw)
    _add_cards_diagnosis_action.setCheckable(True)
    _add_cards_diagnosis_action.setChecked(is_add_cards_diagnosis_button_enabled())
    _add_cards_diagnosis_action.triggered.connect(_toggle_add_cards_diagnosis)
    pocket_menu.addAction(_add_cards_diagnosis_action)

    _add_cards_multi_image_counter_action = QAction("Live Multi-Image Counter In Add Cards", mw)
    _add_cards_multi_image_counter_action.setCheckable(True)
    _add_cards_multi_image_counter_action.setChecked(is_add_cards_multi_image_counter_enabled())
    _add_cards_multi_image_counter_action.triggered.connect(_toggle_add_cards_multi_image_counter)
    pocket_menu.addAction(_add_cards_multi_image_counter_action)

    _add_cards_tab_cycles_clozes_action = QAction("Tab Cycles Clozes In Add Cards", mw)
    _add_cards_tab_cycles_clozes_action.setCheckable(True)
    _add_cards_tab_cycles_clozes_action.setChecked(is_add_cards_tab_cycles_clozes_enabled())
    _add_cards_tab_cycles_clozes_action.triggered.connect(_toggle_add_cards_tab_cycles_clozes)
    pocket_menu.addAction(_add_cards_tab_cycles_clozes_action)

    _visual_card_multitude_action = QAction("Pink Picture-Frame Button In Add Cards", mw)
    _visual_card_multitude_action.setCheckable(True)
    _visual_card_multitude_action.setChecked(is_visual_card_multitude_add_button_enabled())
    _visual_card_multitude_action.triggered.connect(_toggle_visual_card_multitude_button)
    pocket_menu.addAction(_visual_card_multitude_action)

    _visual_card_multitude_auto_visual_deck_action = QAction(
        "Auto-Switch Visual_Card_Multitude To .New::Visual",
        mw,
    )
    _visual_card_multitude_auto_visual_deck_action.setCheckable(True)
    _visual_card_multitude_auto_visual_deck_action.setChecked(
        is_visual_card_multitude_auto_visual_deck_enabled()
    )
    _visual_card_multitude_auto_visual_deck_action.triggered.connect(
        _toggle_visual_card_multitude_auto_visual_deck
    )
    pocket_menu.addAction(_visual_card_multitude_auto_visual_deck_action)

    _ai_tools_action = QAction("AI Card Tools In Add Cards And Browser", mw)
    _ai_tools_action.setCheckable(True)
    _ai_tools_action.setChecked(is_ai_tools_enabled())
    _ai_tools_action.triggered.connect(_toggle_ai_tools)
    pocket_menu.addAction(_ai_tools_action)

    ai_key_action = QAction("Set OpenAI API Key For AI Card Tools", mw)
    ai_key_action.triggered.connect(lambda *_args: open_ai_settings_dialog())
    pocket_menu.addAction(ai_key_action)

    ai_key_source_action = QAction("Show AI Key Source", mw)
    ai_key_source_action.triggered.connect(lambda *_args: show_ai_key_source())
    pocket_menu.addAction(ai_key_source_action)

    _auto_scroll_action = QAction("Auto-Scroll To Top On Answer Reveal", mw)
    _auto_scroll_action.setCheckable(True)
    _auto_scroll_action.setChecked(is_auto_scroll_enabled())
    _auto_scroll_action.triggered.connect(_toggle_auto_scroll)
    pocket_menu.addAction(_auto_scroll_action)

    _review_image_overlay_action = QAction(
        f"Reviewer Image Overlay Shortcuts ({NEXT_SHORTCUT} / {PREVIOUS_SHORTCUT} / {EXIT_SHORTCUT})",
        mw,
    )
    _review_image_overlay_action.setCheckable(True)
    _review_image_overlay_action.setChecked(is_review_image_overlay_enabled())
    _review_image_overlay_action.triggered.connect(_toggle_review_image_overlay)
    pocket_menu.addAction(_review_image_overlay_action)

    _review_image_overlay_remember_position_action = QAction(
        "Remember Reviewer Image Position On Close",
        mw,
    )
    _review_image_overlay_remember_position_action.setCheckable(True)
    _review_image_overlay_remember_position_action.setChecked(
        is_review_image_overlay_remember_position_enabled()
    )
    _review_image_overlay_remember_position_action.triggered.connect(
        _toggle_review_image_overlay_remember_position
    )
    pocket_menu.addAction(_review_image_overlay_remember_position_action)

    _tts_audio_action = QAction("Play Audio From TTS-Enabled Cards", mw)
    _tts_audio_action.setCheckable(True)
    _tts_audio_action.setChecked(is_tts_audio_enabled())
    _tts_audio_action.triggered.connect(_toggle_tts_audio)
    pocket_menu.addAction(_tts_audio_action)

    sync_settings_ui()

    setattr(mw, _MENU_REGISTERED_FLAG, True)


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    gui_hooks.main_window_did_init.append(_register_menu)
    _HOOK_REGISTERED = True
