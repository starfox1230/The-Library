from __future__ import annotations

import os
import time
from typing import Any, Sequence

from anki.cards import CardId
from anki.collection import (
    CardIdsLimit,
    Collection,
    ExportAnkiPackageOptions,
    Progress,
)
from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.errors import show_exception
from aqt.operations import QueryOp
from aqt.progress import ProgressUpdate
from aqt.qt import QAction, QMenu, qconnect
from aqt.utils import getSaveFile, showWarning, tooltip

from .selected_card_export_core import ExportCard, render_text_export


_HOOK_REGISTERED = False
_MENU_PROPERTY = "_anki_pocket_knife_selected_card_export"


def _selected_card_ids(browser: Browser) -> list[CardId]:
    getter = getattr(browser, "selected_cards", None)
    if not callable(getter):
        getter = getattr(browser, "selectedCards", None)
    return list(getter()) if callable(getter) else []


def _default_filename(extension: str) -> str:
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")
    return f"selected-cards-{timestamp}.{extension}"


def _choose_export_path(
    browser: Browser, *, extension: str, description: str
) -> str | None:
    while True:
        path = getSaveFile(
            browser,
            "Export Selected Cards",
            "export",
            description,
            f".{extension}",
            fname=_default_filename(extension),
        )
        if not path:
            return None
        path = os.path.normpath(path)
        try:
            profile_base = os.path.normcase(os.path.abspath(mw.pm.base))
            selected_path = os.path.normcase(os.path.abspath(path))
            if os.path.commonpath((profile_base, selected_path)) == profile_base:
                showWarning(
                    "Please choose a location outside Anki's profile folder.",
                    parent=browser,
                )
                continue
        except (AttributeError, ValueError):
            pass
        return path


def _export_progress_update(progress: Progress, update: ProgressUpdate) -> None:
    if progress.HasField("exporting"):
        update.label = progress.exporting
    if update.user_wants_abort:
        update.abort = True


def _show_failure(browser: Browser, exception: Exception) -> None:
    show_exception(parent=browser, exception=exception)


def export_selected_cards_as_apkg(
    browser: Browser, card_ids: Sequence[CardId]
) -> None:
    card_ids = list(card_ids)
    if not card_ids:
        showWarning("Select one or more cards first.", parent=browser)
        return
    path = _choose_export_path(
        browser,
        extension="apkg",
        description="Anki Deck Package",
    )
    if not path:
        return

    def export(col: Collection) -> int:
        return col.export_anki_package(
            out_path=path,
            limit=CardIdsLimit(card_ids),
            options=ExportAnkiPackageOptions(
                with_scheduling=False,
                with_deck_configs=False,
                with_media=True,
                legacy=False,
            ),
        )

    QueryOp(
        parent=browser,
        op=export,
        success=lambda _count: tooltip(
            f"Exported {len(card_ids)} selected card(s) to {path}",
            period=5000,
            parent=browser,
        ),
    ).failure(lambda exception: _show_failure(browser, exception)).with_backend_progress(
        _export_progress_update
    ).run_in_background()


def _deck_name(col: Collection, deck_id: int) -> str:
    try:
        return col.decks.name(deck_id)
    except Exception:
        return f"Deck {deck_id}"


def _collect_export_cards(
    col: Collection, card_ids: Sequence[CardId]
) -> list[ExportCard]:
    exported: list[ExportCard] = []
    for card_id in card_ids:
        card = col.get_card(card_id)
        note = card.note()
        note_type = note.note_type() or {}
        template = card.template()
        exported.append(
            ExportCard(
                card_id=int(card.id),
                note_id=int(note.id),
                deck_name=_deck_name(col, int(card.did)),
                original_deck_name=(
                    _deck_name(col, int(card.odid)) if int(card.odid) else ""
                ),
                note_type_name=str(note_type.get("name", "")) or "(unknown)",
                card_template_name=str(template.get("name", "")) or f"Card {card.ord + 1}",
                tags=tuple(note.tags),
                front_html=card.question(browser=True),
                back_html=card.answer(),
                fields=tuple(note.items()),
            )
        )
    return exported


def export_selected_cards_as_text(
    browser: Browser, card_ids: Sequence[CardId]
) -> None:
    card_ids = list(card_ids)
    if not card_ids:
        showWarning("Select one or more cards first.", parent=browser)
        return
    path = _choose_export_path(
        browser,
        extension="txt",
        description="Plain Text",
    )
    if not path:
        return

    def export(col: Collection) -> int:
        cards = _collect_export_cards(col, card_ids)
        with open(path, "w", encoding="utf-8", newline="\n") as output:
            output.write(render_text_export(cards))
        return len(cards)

    QueryOp(
        parent=browser,
        op=export,
        success=lambda count: tooltip(
            f"Exported {count} selected card(s) to {path}",
            period=5000,
            parent=browser,
        ),
    ).failure(lambda exception: _show_failure(browser, exception)).with_progress(
        "Exporting selected cards..."
    ).run_in_background()


def _on_browser_will_show_context_menu(*args: Any) -> None:
    browser = next((arg for arg in args if isinstance(arg, Browser)), None)
    menu = next((arg for arg in args if isinstance(arg, QMenu)), None)
    if browser is None or menu is None or bool(menu.property(_MENU_PROPERTY)):
        return
    menu.setProperty(_MENU_PROPERTY, True)

    card_ids = _selected_card_ids(browser)
    actions = menu.actions()
    if actions and not actions[-1].isSeparator():
        menu.addSeparator()

    export_menu = menu.addMenu(
        f"Pocket Knife: Export Selected Cards ({len(card_ids)})"
    )
    if export_menu is None:
        return
    export_menu.setEnabled(bool(card_ids))

    apkg_action = QAction("Anki Package (.apkg)", export_menu)
    qconnect(
        apkg_action.triggered,
        lambda: export_selected_cards_as_apkg(browser, card_ids),
    )
    export_menu.addAction(apkg_action)

    text_action = QAction("Text - Rendered Sides + Every Field (.txt)", export_menu)
    qconnect(
        text_action.triggered,
        lambda: export_selected_cards_as_text(browser, card_ids),
    )
    export_menu.addAction(text_action)


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    hook = getattr(gui_hooks, "browser_will_show_context_menu", None)
    if hook is not None:
        hook.append(_on_browser_will_show_context_menu)
        _HOOK_REGISTERED = True
