from __future__ import annotations

from typing import Any

from anki.notes import Note
from aqt import gui_hooks, mw
from aqt.qt import QAction, QApplication, QMenu
from aqt.utils import showInfo, showWarning

from .clipboard_json_cards_core import ClipboardJsonCard, parse_clipboard_json_cards


ACTION_LABEL = "Make New Cards From Clipboard JSON"
NOTETYPE_NAME = "saCloze++"
TEXT_FIELD_NAME = "Text"
_HOOK_REGISTERED = False


def _main_window_state() -> str:
    state = getattr(mw, "state", "")
    if callable(state):
        try:
            state = state()
        except Exception:
            state = ""
    return str(state or "")


def _is_deck_browser_context(webview: Any) -> bool:
    return webview is getattr(mw, "web", None) and _main_window_state() == "deckBrowser"


def _actual_model_field_name(model: dict[str, Any], wanted_name: str) -> str | None:
    wanted = str(wanted_name).casefold()
    for field in model.get("flds", []):
        name = str(field.get("name") or "")
        if name.casefold() == wanted:
            return name
    return None


def _deck_name(deck_id: int) -> str:
    decks = getattr(mw.col, "decks", None)
    if decks is None:
        return "Current Deck"

    name_method = getattr(decks, "name", None)
    if callable(name_method):
        try:
            return str(name_method(int(deck_id)))
        except Exception:
            pass

    get_method = getattr(decks, "get", None)
    if callable(get_method):
        try:
            deck = get_method(int(deck_id)) or {}
        except Exception:
            deck = {}
        if isinstance(deck, dict) and deck.get("name"):
            return str(deck.get("name"))

    return "Current Deck"


def _current_deck_info() -> tuple[int, str, bool] | None:
    decks = getattr(mw.col, "decks", None)
    if decks is None:
        return None

    current_method = getattr(decks, "current", None)
    if callable(current_method):
        try:
            deck = current_method() or {}
        except Exception:
            deck = {}
        if isinstance(deck, dict) and deck.get("id") is not None:
            try:
                deck_id = int(deck["id"])
            except Exception:
                deck_id = None
            if deck_id is not None:
                return (
                    deck_id,
                    str(deck.get("name") or _deck_name(deck_id)),
                    bool(deck.get("dyn", False)),
                )

    selected_method = getattr(decks, "selected", None)
    if callable(selected_method):
        try:
            deck_id = int(selected_method())
        except Exception:
            deck_id = None
        if deck_id is not None:
            deck = {}
            get_method = getattr(decks, "get", None)
            if callable(get_method):
                try:
                    deck = get_method(deck_id) or {}
                except Exception:
                    deck = {}
            return (deck_id, _deck_name(deck_id), bool(deck.get("dyn", False)))

    return None


def _target_model() -> dict[str, Any] | None:
    models = getattr(mw.col, "models", None)
    if models is None:
        return None

    by_name = getattr(models, "by_name", None)
    if callable(by_name):
        try:
            model = by_name(NOTETYPE_NAME)
        except Exception:
            model = None
        if isinstance(model, dict):
            return model

    all_method = getattr(models, "all", None)
    if callable(all_method):
        try:
            raw_models = all_method()
        except Exception:
            raw_models = []
        if isinstance(raw_models, dict):
            raw_models = list(raw_models.values())
        for model in raw_models or []:
            if not isinstance(model, dict):
                continue
            if str(model.get("name") or "").casefold() == NOTETYPE_NAME.casefold():
                return model

    return None


def _clipboard_text() -> str:
    clipboard = QApplication.clipboard()
    if clipboard is None:
        return ""
    try:
        return str(clipboard.text() or "")
    except Exception:
        return ""


def _build_note(
    model: dict[str, Any],
    *,
    text_field_name: str,
    card: ClipboardJsonCard,
) -> Note:
    note = Note(mw.col, model)
    note[text_field_name] = card.html
    note.tags = list(card.tags)
    return note


def import_cards_from_clipboard_json() -> None:
    try:
        cards = parse_clipboard_json_cards(_clipboard_text())
    except Exception as exc:
        showWarning(
            "Could not import cards from the clipboard JSON.\n\n"
            "Expected a JSON array of objects with an 'html' string and optional 'tags'.\n\n"
            f"{exc}"
        )
        return

    if not cards:
        showInfo("Clipboard JSON did not contain any cards to import.")
        return

    deck_info = _current_deck_info()
    if deck_info is None:
        showWarning("Could not determine the current deck for importing notes.")
        return

    deck_id, deck_name, is_filtered = deck_info
    if is_filtered:
        showWarning(
            "The current deck is a filtered deck.\n\n"
            "Switch to a normal deck on the deck list first, then run the import again."
        )
        return

    model = _target_model()
    if model is None:
        showWarning(
            f"Could not find the '{NOTETYPE_NAME}' note type in this Anki collection."
        )
        return

    text_field_name = _actual_model_field_name(model, TEXT_FIELD_NAME)
    if not text_field_name:
        showWarning(
            f"The '{NOTETYPE_NAME}' note type is missing the required '{TEXT_FIELD_NAME}' field."
        )
        return

    imported_count = 0
    errors: list[str] = []

    for index, card in enumerate(cards, start=1):
        try:
            note = _build_note(
                model,
                text_field_name=text_field_name,
                card=card,
            )
            mw.col.add_note(note, deck_id)
        except Exception as exc:
            errors.append(f"Card {index}: {exc}")
            continue
        imported_count += 1

    try:
        mw.reset()
    except Exception:
        pass

    refresh = getattr(getattr(mw, "deckBrowser", None), "refresh", None)
    if callable(refresh):
        try:
            refresh()
        except Exception:
            pass

    if imported_count > 0 and not errors:
        showInfo(
            f"Imported {imported_count} new '{NOTETYPE_NAME}' note(s) into '{deck_name}'."
        )
        return

    if imported_count <= 0:
        detail = "\n".join(errors[:8]) if errors else "Unknown import failure."
        showWarning(
            f"No cards were imported into '{deck_name}'.\n\n{detail}"
        )
        return

    shown_errors = "\n".join(errors[:8])
    extra_error_count = len(errors) - min(len(errors), 8)
    more_text = f"\n...and {extra_error_count} more." if extra_error_count > 0 else ""
    showWarning(
        f"Imported {imported_count} note(s) into '{deck_name}', but {len(errors)} card(s) failed.\n\n"
        f"{shown_errors}{more_text}"
    )


def build_import_cards_action(parent) -> QAction:
    action = QAction(ACTION_LABEL, parent)
    action.triggered.connect(lambda *_args: import_cards_from_clipboard_json())
    return action


def _on_webview_will_show_context_menu(webview: Any, menu: QMenu) -> None:
    if not _is_deck_browser_context(webview):
        return

    if menu.actions():
        menu.addSeparator()
    menu.addAction(build_import_cards_action(menu))


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    hook = getattr(gui_hooks, "webview_will_show_context_menu", None)
    if hook is not None:
        hook.append(_on_webview_will_show_context_menu)

    _HOOK_REGISTERED = True
