from __future__ import annotations

from typing import Any

from anki.notes import Note
from aqt import gui_hooks, mw
from aqt.qt import QAction, QApplication, QMenu
from aqt.utils import showInfo, showWarning

from .clipboard_json_cards_core import ClipboardJsonCard, parse_clipboard_json_cards
from .saved_cards_audio import SOURCE_DECK_NAME


ACTION_LABEL = "Make New Cards From Clipboard"
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


def _deck_for_id(deck_id: int) -> dict[str, Any] | None:
    decks = getattr(mw.col, "decks", None)
    if decks is None:
        return None

    get_method = getattr(decks, "get", None)
    if not callable(get_method):
        return None

    try:
        deck = get_method(int(deck_id)) or {}
    except Exception:
        return None
    return deck if isinstance(deck, dict) and deck else None


def _deck_id_for_exact_name(deck_name: str) -> int | None:
    decks = getattr(mw.col, "decks", None)
    if decks is None:
        return None

    by_name = getattr(decks, "by_name", None)
    if callable(by_name):
        try:
            deck = by_name(deck_name)
        except Exception:
            deck = None
        if isinstance(deck, dict) and deck.get("id") is not None and str(deck.get("name", "")) == deck_name:
            return int(deck["id"])

    id_for_name = getattr(decks, "id_for_name", None)
    if callable(id_for_name):
        try:
            deck_id = id_for_name(deck_name)
        except Exception:
            deck_id = None
        if deck_id is not None:
            deck = _deck_for_id(int(deck_id))
            if deck and str(deck.get("name", "")) == deck_name:
                return int(deck_id)

    all_names_and_ids = getattr(decks, "all_names_and_ids", None)
    if callable(all_names_and_ids):
        try:
            raw_items = list(all_names_and_ids() or [])
        except Exception:
            raw_items = []
        for item in raw_items:
            raw_id = None
            raw_name = None
            if isinstance(item, dict):
                raw_id = item.get("id")
                raw_name = item.get("name")
            elif isinstance(item, (tuple, list)) and len(item) >= 2:
                first, second = item[0], item[1]
                if isinstance(first, int):
                    raw_id, raw_name = first, second
                else:
                    raw_name, raw_id = first, second
            if raw_id is None or raw_name != deck_name:
                continue
            return int(raw_id)

    return None


def _created_deck_id(raw_result: Any) -> int | None:
    try:
        if raw_result is None:
            return None
        if isinstance(raw_result, int):
            return int(raw_result)
        if isinstance(raw_result, dict) and raw_result.get("id") is not None:
            return int(raw_result["id"])
        raw_id = getattr(raw_result, "id", None)
        if raw_id is not None:
            return int(raw_id)
    except Exception:
        return None
    return None


def _ensure_saved_cards_deck() -> tuple[int, str]:
    deck_id = _deck_id_for_exact_name(SOURCE_DECK_NAME)
    decks = getattr(mw.col, "decks", None)
    if deck_id is None and decks is not None:
        create_method = getattr(decks, "add_normal_deck_with_name", None)
        if callable(create_method):
            try:
                deck_id = _created_deck_id(create_method(SOURCE_DECK_NAME))
            except Exception:
                deck_id = None
        if deck_id is None:
            legacy_id = getattr(decks, "id", None)
            if callable(legacy_id):
                try:
                    deck_id = _created_deck_id(legacy_id(SOURCE_DECK_NAME))
                except Exception:
                    deck_id = None

    if deck_id is None:
        raise RuntimeError(f"Could not find or create the '{SOURCE_DECK_NAME}' deck.")

    deck = _deck_for_id(deck_id)
    if not deck or str(deck.get("name", "")) != SOURCE_DECK_NAME:
        raise RuntimeError(f"Could not resolve the exact '{SOURCE_DECK_NAME}' deck.")
    if bool(deck.get("dyn", False)):
        raise RuntimeError(
            f"'{SOURCE_DECK_NAME}' exists as a filtered deck. Rename or remove it, then try again."
        )

    return int(deck_id), str(deck.get("name") or SOURCE_DECK_NAME)


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
            "Could not import cards from the clipboard.\n\n"
            "Expected either a JSON array of objects with an 'html' string and optional 'tags', "
            "or one cloze card per non-empty clipboard line.\n\n"
            f"{exc}"
        )
        return

    if not cards:
        showInfo("Clipboard JSON did not contain any cards to import.")
        return

    try:
        deck_id, deck_name = _ensure_saved_cards_deck()
    except Exception as exc:
        showWarning(f"Could not prepare the '{SOURCE_DECK_NAME}' deck.\n\n{exc}")
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
