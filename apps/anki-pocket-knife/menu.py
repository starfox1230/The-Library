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
    QMenu,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from .auto_scroll import is_auto_scroll_enabled, set_auto_scroll_enabled
from .early_review import (
    EARLY_REVIEW_DEFAULT_COUNT,
    EARLY_REVIEW_SHORTCUT,
    build_early_review_filtered_deck,
)
from .missed_today import (
    copy_missed_today_text,
    export_missed_today_text_file,
    make_missed_today_filtered_deck,
    open_missed_today_html_viewer,
    summarize_missed_today,
)
from .no_image_today import open_no_image_today_dialog
from .recent_new_cards import open_recent_new_cards_dialog
from .return_non_new import open_return_non_new_dialog
from .suspended_browser import open_suspended_cards_browser
from .visual_card_multitude import (
    is_add_cards_auto_deck_enabled,
    is_visual_card_multitude_add_button_enabled,
    is_visual_card_multitude_auto_visual_deck_enabled,
    set_add_cards_auto_deck_enabled,
    set_visual_card_multitude_add_button_enabled,
    set_visual_card_multitude_auto_visual_deck_enabled,
)


ADDON_NAME = "Anki Pocket Knife"
LAUNCHER_SHORTCUT = "Ctrl+Shift+Q"
LEGACY_EARLY_REVIEW_PACKAGE = "early_review_deck"
_HOOK_REGISTERED = False
_MENU_REGISTERED_FLAG = "_anki_pocket_knife_menu_registered"
_dialog: "PocketKnifeLauncherDialog | None" = None
_auto_scroll_action: QAction | None = None
_add_cards_auto_deck_action: QAction | None = None
_visual_card_multitude_action: QAction | None = None
_visual_card_multitude_auto_visual_deck_action: QAction | None = None


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
        layout = QVBoxLayout(self)
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
            "Open all currently suspended cards in the Browser with the most recently suspended cards first."
        )
        browser_copy.setWordWrap(True)
        browser_layout.addWidget(browser_copy)
        self.suspended_browser_button = QPushButton("Open Suspended Cards In Browser")
        browser_layout.addWidget(self.suspended_browser_button)
        layout.addWidget(browser_box)

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
        self.add_cards_auto_deck_checkbox = QCheckBox(
            "Auto-switch cloze notes between .New::Audio and .New::Visual based on Text images"
        )
        self.add_cards_auto_deck_checkbox.setChecked(is_add_cards_auto_deck_enabled())
        add_cards_layout.addWidget(self.add_cards_auto_deck_checkbox)
        self.visual_card_multitude_auto_visual_deck_checkbox = QCheckBox(
            "Auto-switch Visual_Card_Multitude notes to .New::Visual"
        )
        self.visual_card_multitude_auto_visual_deck_checkbox.setChecked(
            is_visual_card_multitude_auto_visual_deck_enabled()
        )
        add_cards_layout.addWidget(self.visual_card_multitude_auto_visual_deck_checkbox)
        layout.addWidget(add_cards_box)

        review_box = QGroupBox("Review Behavior")
        review_layout = QVBoxLayout(review_box)
        review_copy = QLabel(
            "Optional reviewer helper: when enabled, revealing the answer jumps back to the top of the card automatically."
        )
        review_copy.setWordWrap(True)
        review_layout.addWidget(review_copy)
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll to the top when answer is revealed")
        self.auto_scroll_checkbox.setChecked(is_auto_scroll_enabled())
        review_layout.addWidget(self.auto_scroll_checkbox)
        layout.addWidget(review_box)

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QPushButton("Close")
        close_row.addWidget(self.close_button)
        layout.addLayout(close_row)

        self.early_review_button.clicked.connect(self._build_early_review_deck)
        self.copy_button.clicked.connect(self._run_and_refresh(copy_missed_today_text))
        self.export_button.clicked.connect(self._run_and_refresh(export_missed_today_text_file))
        self.html_button.clicked.connect(self._run_and_refresh(open_missed_today_html_viewer))
        self.deck_button.clicked.connect(self._run_and_refresh(make_missed_today_filtered_deck))
        self.no_image_button.clicked.connect(lambda *_args: open_no_image_today_dialog())
        self.recent_new_button.clicked.connect(lambda *_args: open_recent_new_cards_dialog())
        self.suspended_browser_button.clicked.connect(lambda *_args: open_suspended_cards_browser())
        self.return_non_new_button.clicked.connect(lambda *_args: open_return_non_new_dialog())
        self.refresh_button.clicked.connect(self.refresh_missed_today_summary)
        self.visual_card_multitude_checkbox.toggled.connect(self._set_visual_card_multitude_enabled)
        self.add_cards_auto_deck_checkbox.toggled.connect(self._set_add_cards_auto_deck_enabled)
        self.visual_card_multitude_auto_visual_deck_checkbox.toggled.connect(
            self._set_visual_card_multitude_auto_visual_deck_enabled
        )
        self.auto_scroll_checkbox.toggled.connect(self._set_auto_scroll_enabled)
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
        if hasattr(self, "auto_scroll_checkbox"):
            self.auto_scroll_checkbox.blockSignals(True)
            self.auto_scroll_checkbox.setChecked(is_auto_scroll_enabled())
            self.auto_scroll_checkbox.blockSignals(False)
        if hasattr(self, "visual_card_multitude_checkbox"):
            self.visual_card_multitude_checkbox.blockSignals(True)
            self.visual_card_multitude_checkbox.setChecked(is_visual_card_multitude_add_button_enabled())
            self.visual_card_multitude_checkbox.blockSignals(False)
        if hasattr(self, "add_cards_auto_deck_checkbox"):
            self.add_cards_auto_deck_checkbox.blockSignals(True)
            self.add_cards_auto_deck_checkbox.setChecked(is_add_cards_auto_deck_enabled())
            self.add_cards_auto_deck_checkbox.blockSignals(False)
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

    def _set_visual_card_multitude_enabled(self, checked: bool) -> None:
        set_visual_card_multitude_add_button_enabled(bool(checked))
        sync_settings_ui()

    def _set_add_cards_auto_deck_enabled(self, checked: bool) -> None:
        set_add_cards_auto_deck_enabled(bool(checked))
        sync_settings_ui()

    def _set_visual_card_multitude_auto_visual_deck_enabled(self, checked: bool) -> None:
        set_visual_card_multitude_auto_visual_deck_enabled(bool(checked))
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
    global _add_cards_auto_deck_action
    global _visual_card_multitude_action
    global _visual_card_multitude_auto_visual_deck_action

    auto_scroll_enabled = is_auto_scroll_enabled()
    if _auto_scroll_action is not None:
        _auto_scroll_action.blockSignals(True)
        _auto_scroll_action.setChecked(auto_scroll_enabled)
        _auto_scroll_action.blockSignals(False)
    add_cards_auto_deck_enabled = is_add_cards_auto_deck_enabled()
    if _add_cards_auto_deck_action is not None:
        _add_cards_auto_deck_action.blockSignals(True)
        _add_cards_auto_deck_action.setChecked(add_cards_auto_deck_enabled)
        _add_cards_auto_deck_action.blockSignals(False)
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
    if _dialog is not None and hasattr(_dialog, "auto_scroll_checkbox"):
        _dialog.auto_scroll_checkbox.blockSignals(True)
        _dialog.auto_scroll_checkbox.setChecked(auto_scroll_enabled)
        _dialog.auto_scroll_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "add_cards_auto_deck_checkbox"):
        _dialog.add_cards_auto_deck_checkbox.blockSignals(True)
        _dialog.add_cards_auto_deck_checkbox.setChecked(add_cards_auto_deck_enabled)
        _dialog.add_cards_auto_deck_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "visual_card_multitude_checkbox"):
        _dialog.visual_card_multitude_checkbox.blockSignals(True)
        _dialog.visual_card_multitude_checkbox.setChecked(visual_card_enabled)
        _dialog.visual_card_multitude_checkbox.blockSignals(False)
    if _dialog is not None and hasattr(_dialog, "visual_card_multitude_auto_visual_deck_checkbox"):
        _dialog.visual_card_multitude_auto_visual_deck_checkbox.blockSignals(True)
        _dialog.visual_card_multitude_auto_visual_deck_checkbox.setChecked(visual_card_auto_visual_enabled)
        _dialog.visual_card_multitude_auto_visual_deck_checkbox.blockSignals(False)


def _toggle_auto_scroll(checked: bool) -> None:
    set_auto_scroll_enabled(bool(checked))
    sync_settings_ui()


def _toggle_visual_card_multitude_button(checked: bool) -> None:
    set_visual_card_multitude_add_button_enabled(bool(checked))
    sync_settings_ui()


def _toggle_add_cards_auto_deck(checked: bool) -> None:
    set_add_cards_auto_deck_enabled(bool(checked))
    sync_settings_ui()


def _toggle_visual_card_multitude_auto_visual_deck(checked: bool) -> None:
    set_visual_card_multitude_auto_visual_deck_enabled(bool(checked))
    sync_settings_ui()


def _register_menu() -> None:
    global _auto_scroll_action
    global _add_cards_auto_deck_action
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

    recent_new_action = QAction("Build Recent New Cards Deck", mw)
    recent_new_action.triggered.connect(lambda *_args: open_recent_new_cards_dialog())
    pocket_menu.addAction(recent_new_action)

    suspended_browser_action = QAction("Open Suspended Cards In Browser", mw)
    suspended_browser_action.triggered.connect(lambda *_args: open_suspended_cards_browser())
    pocket_menu.addAction(suspended_browser_action)

    return_non_new_action = QAction("Send Filtered Deck Non-New Cards Home", mw)
    return_non_new_action.triggered.connect(lambda *_args: open_return_non_new_dialog())
    pocket_menu.addAction(return_non_new_action)

    pocket_menu.addSeparator()

    _add_cards_auto_deck_action = QAction("Auto Deck For Cloze Add Cards", mw)
    _add_cards_auto_deck_action.setCheckable(True)
    _add_cards_auto_deck_action.setChecked(is_add_cards_auto_deck_enabled())
    _add_cards_auto_deck_action.triggered.connect(_toggle_add_cards_auto_deck)
    pocket_menu.addAction(_add_cards_auto_deck_action)

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

    _auto_scroll_action = QAction("Auto-Scroll To Top On Answer Reveal", mw)
    _auto_scroll_action.setCheckable(True)
    _auto_scroll_action.setChecked(is_auto_scroll_enabled())
    _auto_scroll_action.triggered.connect(_toggle_auto_scroll)
    pocket_menu.addAction(_auto_scroll_action)

    sync_settings_ui()

    setattr(mw, _MENU_REGISTERED_FLAG, True)


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    gui_hooks.main_window_did_init.append(_register_menu)
    _HOOK_REGISTERED = True
