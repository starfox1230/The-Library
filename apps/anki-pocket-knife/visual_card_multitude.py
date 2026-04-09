from __future__ import annotations

import json
import re
import weakref
from dataclasses import dataclass

from anki.consts import MODEL_CLOZE
from anki.notes import Note
from aqt import gui_hooks, mw
from aqt.addcards import AddCards
from aqt.editor import Editor
from aqt.qt import QTimer
from aqt.theme import theme_manager
from aqt.utils import showWarning, tooltip

from .common import addon_root
from .settings import get_setting, set_setting


SETTING_NAME = "visual_card_multitude_add_button"
DIAGNOSIS_BUTTON_SETTING_NAME = "add_cards_diagnosis_button"
AUTO_DECK_SETTING_NAME = "add_cards_cloze_auto_deck"
VISUAL_DECK_SETTING_NAME = "visual_card_multitude_auto_visual_deck"
MULTI_IMAGE_COUNTER_SETTING_NAME = "add_cards_multi_image_counter"
TARGET_NOTETYPE_NAME = "Visual_Card_Multitude"
REVERSE_TARGET_NOTETYPE_NAME = "saCloze++"
BUTTON_COMMAND = "pocket_knife_visual_card_multitude"
BUTTON_TOOLTIP = "Convert between saCloze++ and Visual_Card_Multitude"
BUTTON_ICON_PATH = addon_root() / "assets" / "pink_picture_frame.svg"
BUTTON_ID = "pocket-knife-visual-card-multitude"
DIAGNOSIS_BUTTON_COMMAND = "pocket_knife_diagnosis_template"
DIAGNOSIS_BUTTON_ID = "pocket-knife-diagnosis-template"
AUTO_DECK_BUTTON_COMMAND = "pocket_knife_toggle_add_cards_auto_deck"
AUTO_DECK_BUTTON_ID = "pocket-knife-auto-deck-toggle"
AUTO_DECK_AUDIO_NAME = ".NEW::Audio"
AUTO_DECK_VISUAL_NAME = ".New::Visual"
_HOOK_REGISTERED = False
_BRIDGE_PATCHED = False
_OPEN_ADD_CARDS_EDITORS: "weakref.WeakSet[Editor]" = weakref.WeakSet()

_CLOZE_RE = re.compile(r"\{\{c\d+::(.*?)(?:::(.*?))?\}\}", re.IGNORECASE | re.DOTALL)
_IMAGE_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_BR_RUN_RE = re.compile(r"(?:\s*<br\s*/?>\s*){3,}", re.IGNORECASE)
_EDGE_BRS_RE = re.compile(
    r"^(?:\s*<br\s*/?>\s*)+|(?:\s*<br\s*/?>\s*)+$",
    re.IGNORECASE,
)
_MULTI_IMAGE_COUNTER_RE = re.compile(
    r"<div\b[^>]*data-pocket-knife-image-counter=(['\"])true\1[^>]*>.*?</div>",
    re.IGNORECASE | re.DOTALL,
)
_DIAGNOSIS_CURSOR_MARKERS_RE = re.compile(
    r"<span\b[^>]*data-pocket-knife-dx-marker=(['\"])(?:start|end)\1[^>]*></span>",
    re.IGNORECASE,
)
_MULTI_IMAGE_COUNTER_HTML = (
    '<div data-pocket-knife-image-counter="true">{label}</div>'
)
_DIAGNOSIS_TEMPLATE_PREFIX = "Most likely diagnosis?<br><br>"
_DIAGNOSIS_TEMPLATE_SUFFIX = "<br><br>"
_DIAGNOSIS_CLOZE_PREFIX = "{{c1::"
_DIAGNOSIS_CLOZE_SUFFIX = "}}"
_DIAGNOSIS_CURSOR_START_MARKER = '<span data-pocket-knife-dx-marker="start"></span>'
_DIAGNOSIS_CURSOR_END_MARKER = '<span data-pocket-knife-dx-marker="end"></span>'


@dataclass(frozen=True)
class ConvertedVisualFields:
    question_html: str
    english_html: str
    images_html: str


def is_visual_card_multitude_add_button_enabled() -> bool:
    return bool(get_setting(SETTING_NAME))


def set_visual_card_multitude_add_button_enabled(enabled: bool) -> bool:
    return bool(set_setting(SETTING_NAME, bool(enabled)))


def is_add_cards_diagnosis_button_enabled() -> bool:
    return bool(get_setting(DIAGNOSIS_BUTTON_SETTING_NAME))


def set_add_cards_diagnosis_button_enabled(enabled: bool) -> bool:
    value = bool(set_setting(DIAGNOSIS_BUTTON_SETTING_NAME, bool(enabled)))
    sync_open_add_cards_editor_ui()
    return value


def is_add_cards_auto_deck_enabled() -> bool:
    return bool(get_setting(AUTO_DECK_SETTING_NAME))


def set_add_cards_auto_deck_enabled(enabled: bool) -> bool:
    value = bool(set_setting(AUTO_DECK_SETTING_NAME, bool(enabled)))
    sync_open_add_cards_editor_ui()
    return value


def is_visual_card_multitude_auto_visual_deck_enabled() -> bool:
    return bool(get_setting(VISUAL_DECK_SETTING_NAME))


def set_visual_card_multitude_auto_visual_deck_enabled(enabled: bool) -> bool:
    value = bool(set_setting(VISUAL_DECK_SETTING_NAME, bool(enabled)))
    sync_open_add_cards_editor_ui()
    return value


def is_add_cards_multi_image_counter_enabled() -> bool:
    return bool(get_setting(MULTI_IMAGE_COUNTER_SETTING_NAME))


def set_add_cards_multi_image_counter_enabled(enabled: bool) -> bool:
    value = bool(set_setting(MULTI_IMAGE_COUNTER_SETTING_NAME, bool(enabled)))
    sync_open_add_cards_editor_ui()
    return value


def _actual_note_field_name(note, wanted_name: str) -> str | None:
    wanted = str(wanted_name).casefold()
    for field_name in note.keys():
        if str(field_name).casefold() == wanted:
            return str(field_name)
    return None


def _actual_model_field_name(model: dict, wanted_name: str) -> str | None:
    wanted = str(wanted_name).casefold()
    for field in model.get("flds", []):
        name = field.get("name")
        if str(name or "").casefold() == wanted:
            return str(name)
    return None


def _clean_html_fragment(html: str) -> str:
    cleaned = str(html or "").replace("\r", "").replace("\n", "")
    cleaned = _BR_RUN_RE.sub("<br><br>", cleaned)
    cleaned = _EDGE_BRS_RE.sub("", cleaned)
    return cleaned.strip()


def _strip_multi_image_counter(html: str) -> str:
    return _MULTI_IMAGE_COUNTER_RE.sub("", str(html or ""))


def _strip_diagnosis_cursor_markers(html: str) -> str:
    return _DIAGNOSIS_CURSOR_MARKERS_RE.sub("", str(html or ""))


def _apply_multi_image_counter_html(html: str) -> str:
    base_html = _strip_multi_image_counter(html)
    matches = list(_IMAGE_RE.finditer(base_html))
    if len(matches) <= 1:
        return base_html

    first = matches[0]
    label = f"1/{len(matches)}"
    marker = _MULTI_IMAGE_COUNTER_HTML.format(label=label)
    return f"{base_html[:first.start()]}{marker}{base_html[first.start():]}"


def _extract_images_html(html: str) -> str:
    return "".join(match.group(0) for match in _IMAGE_RE.finditer(str(html or "")))


def _remove_images(html: str) -> str:
    return _IMAGE_RE.sub("", str(html or ""))


def _join_html_sections(*sections: str) -> str:
    kept: list[str] = []
    for section in sections:
        raw = str(section or "")
        if raw.strip():
            kept.append(raw)
    return "<br><br>".join(kept)


def _convert_text_field_html(text_html: str) -> ConvertedVisualFields:
    source_html = _strip_multi_image_counter(text_html)
    cloze_segments = [
        _clean_html_fragment(_remove_images(match.group(1)))
        for match in _CLOZE_RE.finditer(source_html)
    ]
    english_html = "<br><br>".join(segment for segment in cloze_segments if segment)
    question_html = _clean_html_fragment(_remove_images(_CLOZE_RE.sub("", source_html)))
    images_html = _extract_images_html(source_html)
    return ConvertedVisualFields(
        question_html=question_html,
        english_html=english_html,
        images_html=images_html,
    )


def _selected_deck_id(add_cards: AddCards) -> int | None:
    chooser = _deck_chooser(add_cards)
    deck_id = getattr(chooser, "selected_deck_id", None)
    if deck_id is None:
        return None
    try:
        return int(deck_id)
    except Exception:
        return None


def _deck_chooser(add_cards: AddCards):
    for attr in ("deck_chooser", "deckChooser"):
        chooser = getattr(add_cards, attr, None)
        if chooser is not None:
            return chooser
    return None


def _sync_menu_settings_ui() -> None:
    try:
        from .menu import sync_settings_ui
    except Exception:
        return
    try:
        sync_settings_ui()
    except Exception:
        pass


def _register_add_cards_editor(editor: Editor) -> None:
    if not isinstance(getattr(editor, "parentWindow", None), AddCards):
        return
    try:
        _OPEN_ADD_CARDS_EDITORS.add(editor)
    except Exception:
        pass


def _run_toolbar_js(editor: Editor, js: str) -> None:
    web = getattr(editor, "web", None)
    if web is None:
        return
    web.eval(
        f"""
require("anki/ui").loaded.then(() => {{
{js}
}});
"""
    )


def _sync_auto_deck_toggle_button(editor: Editor) -> None:
    if not isinstance(getattr(editor, "parentWindow", None), AddCards):
        return

    night_mode = bool(getattr(theme_manager, "night_mode", False))
    enabled = is_add_cards_auto_deck_enabled()
    note = getattr(editor, "note", None)
    diagnosis_enabled = _note_is_cloze(note)
    button_text = "AD"
    button_title = (
        "Automatically switch cloze notes between .NEW::Audio and .New::Visual based on images in Text"
    )
    if night_mode:
        background = "rgba(244, 114, 182, 0.24)" if enabled else "rgba(71, 85, 105, 0.38)"
        border = "#f9a8d4" if enabled else "#94a3b8"
        text_color = "#fff1f7" if enabled else "#e2e8f0"
        frame_background = "rgba(244, 114, 182, 0.18)"
        frame_border = "#f9a8d4"
        diagnosis_background = "rgba(56, 189, 248, 0.24)" if diagnosis_enabled else "rgba(71, 85, 105, 0.38)"
        diagnosis_border = "#7dd3fc" if diagnosis_enabled else "#94a3b8"
        diagnosis_text = "#e0f2fe" if diagnosis_enabled else "#94a3b8"
    else:
        background = "rgba(244, 114, 182, 0.18)" if enabled else "rgba(148, 163, 184, 0.14)"
        border = "#ec4899" if enabled else "#94a3b8"
        text_color = "#9d174d" if enabled else "#334155"
        frame_background = "rgba(244, 114, 182, 0.10)"
        frame_border = "#f472b6"
        diagnosis_background = "rgba(56, 189, 248, 0.14)" if diagnosis_enabled else "rgba(148, 163, 184, 0.14)"
        diagnosis_border = "#0284c7" if diagnosis_enabled else "#94a3b8"
        diagnosis_text = "#0f4c81" if diagnosis_enabled else "#64748b"
    _run_toolbar_js(
        editor,
        f"""
const button = document.getElementById({json.dumps(AUTO_DECK_BUTTON_ID)});
if (button) {{
  button.textContent = {json.dumps(button_text)};
  button.title = {json.dumps(button_title)};
  button.style.background = {json.dumps(background)};
  button.style.borderColor = {json.dumps(border)};
  button.style.color = {json.dumps(text_color)};
  button.style.fontWeight = "600";
  button.style.whiteSpace = "nowrap";
  button.style.margin = "";
  button.style.marginInlineStart = "";
  button.style.marginInlineEnd = "";
}}
const frameButton = document.getElementById({json.dumps(BUTTON_ID)});
if (frameButton) {{
  frameButton.title = {json.dumps(_frame_button_tooltip(getattr(editor, "note", None)))}; 
  frameButton.style.background = {json.dumps(frame_background)};
  frameButton.style.borderColor = {json.dumps(frame_border)};
  frameButton.style.borderRadius = "8px";
  frameButton.style.paddingInline = "6px";
  frameButton.style.margin = "";
  frameButton.style.marginInlineStart = "";
  frameButton.style.marginInlineEnd = "";
}}
const diagnosisButton = document.getElementById({json.dumps(DIAGNOSIS_BUTTON_ID)});
if (diagnosisButton) {{
  diagnosisButton.textContent = "Dx";
  diagnosisButton.title = {json.dumps(_diagnosis_button_tooltip(note))};
  diagnosisButton.disabled = {json.dumps(not diagnosis_enabled)};
  diagnosisButton.style.background = {json.dumps(diagnosis_background)};
  diagnosisButton.style.borderColor = {json.dumps(diagnosis_border)};
  diagnosisButton.style.color = {json.dumps(diagnosis_text)};
  diagnosisButton.style.fontWeight = "700";
  diagnosisButton.style.whiteSpace = "nowrap";
  diagnosisButton.style.margin = "";
  diagnosisButton.style.marginInlineStart = "";
  diagnosisButton.style.marginInlineEnd = "";
  diagnosisButton.style.opacity = diagnosisButton.disabled ? "0.62" : "1";
  diagnosisButton.style.cursor = diagnosisButton.disabled ? "not-allowed" : "";
}}
""",
    )


def sync_open_add_cards_editor_ui() -> None:
    for editor in list(_OPEN_ADD_CARDS_EDITORS):
        try:
            _apply_multi_image_counter_rules(editor)
            _sync_auto_deck_toggle_button(editor)
        except Exception:
            continue
    _sync_menu_settings_ui()


def _note_type_name(note) -> str:
    try:
        note_type = note.note_type() or {}
    except Exception:
        return ""
    return str(note_type.get("name", ""))


def _note_is_visual_card_multitude(note) -> bool:
    return _note_type_name(note).casefold() == TARGET_NOTETYPE_NAME.casefold()


def _note_is_cloze(note) -> bool:
    try:
        note_type = note.note_type() or {}
    except Exception:
        note_type = {}
    try:
        if int(note_type.get("type", -1)) == int(MODEL_CLOZE):
            return True
    except Exception:
        pass
    return _note_type_name(note).casefold().startswith("sacloze")


def _field_ord(note, wanted_name: str) -> int | None:
    try:
        note_type = note.note_type() or {}
    except Exception:
        note_type = {}
    wanted = str(wanted_name).casefold()
    for index, field in enumerate(note_type.get("flds", [])):
        name = str(field.get("name") or "")
        if name.casefold() == wanted:
            return index
    return None


def _frame_button_tooltip(note) -> str:
    if _note_is_visual_card_multitude(note):
        return f"Convert the current {TARGET_NOTETYPE_NAME} note into {REVERSE_TARGET_NOTETYPE_NAME}"
    if _note_is_cloze(note):
        return f"Convert the current cloze note into {TARGET_NOTETYPE_NAME}"
    return BUTTON_TOOLTIP


def _diagnosis_button_tooltip(note) -> str:
    if _note_is_cloze(note):
        return "Replace Text-field text with a Diagnosis cloze template and keep any images below it"
    return "Dx template is only available when the current note type is cloze"


def _text_field_html(note) -> str:
    text_field_name = _actual_note_field_name(note, "Text")
    if not text_field_name:
        return ""
    return str(note[text_field_name] or "")


def _text_field_has_image(note) -> bool:
    return bool(_IMAGE_RE.search(_text_field_html(note)))


def _normalize_text_field_for_multi_image_counter(note) -> bool:
    text_field_name = _actual_note_field_name(note, "Text")
    if not text_field_name:
        return False

    current_html = str(note[text_field_name] or "")
    if _note_is_cloze(note) and is_add_cards_multi_image_counter_enabled():
        desired_html = _apply_multi_image_counter_html(current_html)
    else:
        desired_html = _strip_multi_image_counter(current_html)

    if desired_html == current_html:
        return False

    note[text_field_name] = desired_html
    return True


def _build_diagnosis_text_html(text_html: str) -> str:
    source_html = _strip_diagnosis_cursor_markers(_strip_multi_image_counter(text_html))
    first_cloze_match = _CLOZE_RE.search(source_html)
    preserved_cloze_html = ""
    if first_cloze_match:
        preserved_cloze_html = _clean_html_fragment(_remove_images(first_cloze_match.group(1)))
    cloze_contents = (
        f"{_DIAGNOSIS_CURSOR_START_MARKER}"
        f"{preserved_cloze_html}"
        f"{_DIAGNOSIS_CURSOR_END_MARKER}"
    )
    images_html = _extract_images_html(source_html)
    combined = (
        f"{_DIAGNOSIS_TEMPLATE_PREFIX}"
        f"{_DIAGNOSIS_CLOZE_PREFIX}{cloze_contents}{_DIAGNOSIS_CLOZE_SUFFIX}"
        f"{_DIAGNOSIS_TEMPLATE_SUFFIX}"
        f"{images_html}"
    )
    if is_add_cards_multi_image_counter_enabled():
        return _apply_multi_image_counter_html(combined)
    return _strip_multi_image_counter(combined)


def _target_deck_name_for_note(note) -> str | None:
    if note is None:
        return None
    if is_visual_card_multitude_auto_visual_deck_enabled() and _note_is_visual_card_multitude(note):
        return AUTO_DECK_VISUAL_NAME
    if is_add_cards_auto_deck_enabled() and _note_is_cloze(note):
        return AUTO_DECK_VISUAL_NAME if _text_field_has_image(note) else AUTO_DECK_AUDIO_NAME
    return None


def _deck_id_for_name(deck_name: str) -> int | None:
    decks = mw.col.decks
    by_name = getattr(decks, "by_name", None)
    if callable(by_name):
        try:
            deck = by_name(deck_name)
        except Exception:
            deck = None
        if isinstance(deck, dict) and deck.get("id") is not None:
            try:
                return int(deck["id"])
            except Exception:
                pass

    id_for_name = getattr(decks, "id_for_name", None)
    if callable(id_for_name):
        try:
            deck_id = id_for_name(deck_name)
        except Exception:
            deck_id = None
        if deck_id is not None:
            try:
                return int(deck_id)
            except Exception:
                pass

    legacy_id = getattr(decks, "id", None)
    if callable(legacy_id):
        try:
            deck_id = legacy_id(deck_name)
        except Exception:
            deck_id = None
        if deck_id is not None:
            try:
                return int(deck_id)
            except Exception:
                pass

    return None


def _set_selected_deck_id(add_cards: AddCards, deck_id: int) -> bool:
    chooser = _deck_chooser(add_cards)
    if chooser is None:
        return False

    current_id = _selected_deck_id(add_cards)
    if current_id == int(deck_id):
        return False

    for attr in ("selected_deck_id", "selectedDeckId"):
        if hasattr(chooser, attr):
            try:
                setattr(chooser, attr, int(deck_id))
                return True
            except Exception:
                continue
    return False


def _apply_auto_deck_rules(editor: Editor) -> None:
    if not isinstance(getattr(editor, "parentWindow", None), AddCards):
        return
    note = getattr(editor, "note", None)
    desired_deck_name = _target_deck_name_for_note(note)
    if not desired_deck_name:
        return
    desired_deck_id = _deck_id_for_name(desired_deck_name)
    if desired_deck_id is None:
        return
    _set_selected_deck_id(editor.parentWindow, desired_deck_id)


def _refresh_editor_after_text_change(editor: Editor) -> None:
    load_note_keeping_focus = getattr(editor, "loadNoteKeepingFocus", None)
    if callable(load_note_keeping_focus):
        load_note_keeping_focus()
        return

    load_note = getattr(editor, "loadNote", None)
    if callable(load_note):
        try:
            load_note(getattr(editor, "currentField", None))
        except TypeError:
            load_note()


def _place_diagnosis_cursor(editor: Editor, field_ord: int | None = None) -> None:
    _run_toolbar_js(
        editor,
        f"""
const fieldOrd = {json.dumps(field_ord)};
let attempts = 0;
const startSelector = '[data-pocket-knife-dx-marker="start"]';
const endSelector = '[data-pocket-knife-dx-marker="end"]';
const isElementNode = (node) => !!node && node.nodeType === 1;
const isDocumentLike = (node) => !!node && (node.nodeType === 9 || node.nodeType === 11);
const isEditable = (node) => {{
  if (!isElementNode(node)) {{
    return false;
  }}
  if (node.isContentEditable) {{
    return true;
  }}
  const raw = String(node.getAttribute?.("contenteditable") || "").toLowerCase();
  return raw === "" || raw === "true";
}};
const iframeDocument = (node) => {{
  if (!isElementNode(node) || String(node.tagName || "").toUpperCase() !== "IFRAME") {{
    return null;
  }}
  try {{
    return node.contentDocument || node.contentWindow?.document || null;
  }} catch (_error) {{
    return null;
  }}
}};
const findMarker = (root, selector) => {{
  if (!root) {{
    return null;
  }}
  const frameDoc = iframeDocument(root);
  if (frameDoc) {{
    return findMarker(frameDoc, selector);
  }}
  if (isDocumentLike(root)) {{
    const direct = root.querySelector?.(selector) || null;
    if (direct) {{
      return direct;
    }}
    const active = root.activeElement || null;
    if (active) {{
      const activeFound = findMarker(active, selector);
      if (activeFound) {{
        return activeFound;
      }}
    }}
    const nested = root.querySelectorAll?.("iframe, [contenteditable]") || [];
    for (const node of nested) {{
      const found = findMarker(node, selector);
      if (found) {{
        return found;
      }}
    }}
    return null;
  }}
  if (!isElementNode(root)) {{
    return null;
  }}
  if (root.matches?.(selector)) {{
    return root;
  }}
  if (root.shadowRoot) {{
    const shadowFound = findMarker(root.shadowRoot, selector);
    if (shadowFound) {{
      return shadowFound;
    }}
  }}
  return root.querySelector?.(selector) || null;
}};
const editableAncestor = (node) => {{
  let current = node;
  while (current) {{
    if (isEditable(current)) {{
      return current;
    }}
    current = current.parentElement || current.parentNode || null;
  }}
  return null;
}};
const placeCursor = () => {{
  attempts += 1;
  if (typeof focusField === "function" && typeof fieldOrd === "number") {{
    try {{
      focusField(fieldOrd);
    }} catch (_error) {{
      // ignore
    }}
  }}
  const startMarker = findMarker(document, startSelector);
  const endMarker = findMarker(document, endSelector);
  if (!startMarker || !endMarker) {{
    if (attempts < 40) {{
      setTimeout(placeCursor, 50);
    }}
    return;
  }}
  const host = editableAncestor(startMarker) || editableAncestor(endMarker);
  if (!host) {{
    if (attempts < 40) {{
      setTimeout(placeCursor, 50);
    }}
    return;
  }}
  try {{
    host.focus({{ preventScroll: true }});
  }} catch (_error) {{
    host.focus();
  }}
  host.scrollIntoView({{ block: "nearest" }});
  const applySelection = () => {{
    const liveStart = findMarker(document, startSelector) || startMarker;
    const liveEnd = findMarker(document, endSelector) || endMarker;
    if (!liveStart || !liveEnd) {{
      return;
    }}
    const liveHost = editableAncestor(liveStart) || editableAncestor(liveEnd) || host;
    if (liveHost) {{
      try {{
        liveHost.focus({{ preventScroll: true }});
      }} catch (_error) {{
        liveHost.focus();
      }}
    }}
    const ownerDoc = (liveHost && liveHost.ownerDocument) || document;
    const ownerWin = ownerDoc.defaultView || window;
    const range = ownerDoc.createRange();
    const selection = ownerDoc.getSelection ? ownerDoc.getSelection() : ownerWin.getSelection?.();
    range.setStartAfter(liveStart);
    range.setEndBefore(liveEnd);
    if (range.toString() === "") {{
      range.collapse(true);
    }}
    if (selection) {{
      selection.removeAllRanges();
      selection.addRange(range);
    }}
  }};
  applySelection();
  setTimeout(applySelection, 120);
  setTimeout(() => {{
    applySelection();
    if (startMarker.isConnected) {{
      startMarker.remove();
    }}
    if (endMarker.isConnected) {{
      endMarker.remove();
    }}
  }}, 240);
}};
placeCursor();
""",
    )


def _apply_pending_diagnosis_cursor(editor: Editor) -> None:
    field_ord = getattr(editor, "_anki_pocket_knife_pending_diagnosis_cursor_ord", None)
    if field_ord is None:
        return
    setattr(editor, "_anki_pocket_knife_pending_diagnosis_cursor_ord", None)
    QTimer.singleShot(50, lambda: _place_diagnosis_cursor(editor, int(field_ord)))


def _apply_multi_image_counter_rules(editor: Editor) -> None:
    if not isinstance(getattr(editor, "parentWindow", None), AddCards):
        return
    if getattr(editor, "_anki_pocket_knife_syncing_multi_image_counter", False):
        return

    note = getattr(editor, "note", None)
    if note is None:
        return

    if not _normalize_text_field_for_multi_image_counter(note):
        return

    setattr(editor, "_anki_pocket_knife_syncing_multi_image_counter", True)
    try:
        _refresh_editor_after_text_change(editor)
    finally:
        setattr(editor, "_anki_pocket_knife_syncing_multi_image_counter", False)


def _toggle_add_cards_auto_deck(editor: Editor) -> None:
    enabled = set_add_cards_auto_deck_enabled(not is_add_cards_auto_deck_enabled())
    _sync_auto_deck_toggle_button(editor)
    if enabled:
        _apply_auto_deck_rules(editor)
    tooltip(f"Add Cards auto deck {'enabled' if enabled else 'disabled'}.")


def apply_diagnosis_template(editor: Editor) -> None:
    if not isinstance(getattr(editor, "parentWindow", None), AddCards):
        return

    source_note = getattr(editor, "note", None)
    if source_note is None:
        showWarning("No Add Cards note is currently loaded.")
        return
    if not _note_is_cloze(source_note):
        tooltip("Dx is only available for cloze note types.")
        return

    text_field_name = _actual_note_field_name(source_note, "Text")
    text_field_ord = _field_ord(source_note, "Text")
    if text_field_name is None or text_field_ord is None:
        showWarning("This note does not have a usable Text field.")
        return

    source_note[text_field_name] = _build_diagnosis_text_html(source_note[text_field_name])
    setattr(editor, "_anki_pocket_knife_pending_diagnosis_cursor_ord", int(text_field_ord))
    load_note = getattr(editor, "loadNote", None)
    if callable(load_note):
        load_note(int(text_field_ord))
    source_note[text_field_name] = _strip_diagnosis_cursor_markers(source_note[text_field_name])
    QTimer.singleShot(50, lambda: _place_diagnosis_cursor(editor, int(text_field_ord)))
    _apply_auto_deck_rules(editor)
    tooltip("Diagnosis template inserted.")


def _build_visual_target_note(source_note, *, converted: ConvertedVisualFields) -> Note | None:
    target_model = mw.col.models.by_name(TARGET_NOTETYPE_NAME)
    if target_model is None:
        showWarning(
            f"Could not find the '{TARGET_NOTETYPE_NAME}' note type in this Anki collection."
        )
        return None

    field_map = {
        "question": _actual_model_field_name(target_model, "Question"),
        "english": _actual_model_field_name(target_model, "English"),
        "images": _actual_model_field_name(target_model, "Images"),
        "more_info": _actual_model_field_name(target_model, "More Info"),
    }
    missing = [label for label, name in field_map.items() if not name]
    if missing:
        pretty_missing = ", ".join(
            label.replace("_", " ").title() for label in missing
        )
        showWarning(
            f"The '{TARGET_NOTETYPE_NAME}' note type is missing required field(s): {pretty_missing}."
        )
        return None

    target_note = Note(mw.col, target_model)
    if getattr(source_note, "tags", None):
        target_note.tags = list(source_note.tags)

    extra_field_name = _actual_note_field_name(source_note, "Extra")
    more_info_html = source_note[extra_field_name] if extra_field_name else ""

    target_note[field_map["question"]] = converted.question_html
    target_note[field_map["english"]] = converted.english_html
    target_note[field_map["images"]] = converted.images_html
    target_note[field_map["more_info"]] = str(more_info_html or "")
    return target_note


def _build_reverse_cloze_target_note(source_note) -> Note | None:
    target_model = mw.col.models.by_name(REVERSE_TARGET_NOTETYPE_NAME)
    if target_model is None:
        showWarning(
            f"Could not find the '{REVERSE_TARGET_NOTETYPE_NAME}' note type in this Anki collection."
        )
        return None

    text_field_name = _actual_model_field_name(target_model, "Text")
    extra_field_name = _actual_model_field_name(target_model, "Extra")
    missing_fields = []
    if not text_field_name:
        missing_fields.append("Text")
    if not extra_field_name:
        missing_fields.append("Extra")
    if missing_fields:
        showWarning(
            f"The '{REVERSE_TARGET_NOTETYPE_NAME}' note type is missing required field(s): "
            + ", ".join(missing_fields)
            + "."
        )
        return None

    question_field_name = _actual_note_field_name(source_note, "Question")
    english_field_name = _actual_note_field_name(source_note, "English")
    images_field_name = _actual_note_field_name(source_note, "Images")
    more_info_field_name = _actual_note_field_name(source_note, "More Info")

    question_html = _clean_html_fragment(source_note[question_field_name]) if question_field_name else ""
    english_html = _clean_html_fragment(source_note[english_field_name]) if english_field_name else ""
    images_html = str(source_note[images_field_name] or "") if images_field_name else ""
    more_info_html = str(source_note[more_info_field_name] or "") if more_info_field_name else ""

    text_html = _join_html_sections(
        question_html,
        f"{{{{c1::{english_html}}}}}" if english_html else "",
        images_html,
    )
    if is_add_cards_multi_image_counter_enabled():
        text_html = _apply_multi_image_counter_html(text_html)
    else:
        text_html = _strip_multi_image_counter(text_html)

    target_note = Note(mw.col, target_model)
    if getattr(source_note, "tags", None):
        target_note.tags = list(source_note.tags)

    target_note[text_field_name] = text_html
    target_note[extra_field_name] = more_info_html
    return target_note


def _set_add_cards_note(add_cards: AddCards, target_note: Note) -> None:
    desired_deck_name = _target_deck_name_for_note(target_note)
    deck_id = _deck_id_for_name(desired_deck_name) if desired_deck_name else _selected_deck_id(add_cards)
    if deck_id is None:
        deck_id = _selected_deck_id(add_cards)
    try:
        add_cards.set_note(target_note, deck_id=deck_id)
    except TypeError:
        add_cards.set_note(target_note)


def convert_current_add_note(editor: Editor) -> None:
    if not isinstance(getattr(editor, "parentWindow", None), AddCards):
        return

    add_cards = editor.parentWindow
    source_note = editor.note
    if source_note is None:
        showWarning("No Add Cards note is currently loaded.")
        return

    if _note_is_visual_card_multitude(source_note):
        target_note = _build_reverse_cloze_target_note(source_note)
        if target_note is None:
            return
        _set_add_cards_note(add_cards, target_note)
        _apply_auto_deck_rules(editor)
        tooltip(f"Converted note to {REVERSE_TARGET_NOTETYPE_NAME}.")
        return

    text_field_name = _actual_note_field_name(source_note, "Text")
    if text_field_name is None:
        showWarning(
            "This note does not have a 'Text' field, so Pocket Knife could not convert it."
        )
        return

    text_html = str(source_note[text_field_name] or "")
    if not _CLOZE_RE.search(text_html):
        showWarning(
            "No cloze deletions were found in the current Text field."
        )
        return

    converted = _convert_text_field_html(text_html)
    target_note = _build_visual_target_note(source_note, converted=converted)
    if target_note is None:
        return

    _set_add_cards_note(add_cards, target_note)
    _apply_auto_deck_rules(editor)
    tooltip(f"Converted note to {TARGET_NOTETYPE_NAME}.")


def _on_setup_editor_buttons(buttons: list[str], editor: Editor) -> list[str]:
    if not isinstance(getattr(editor, "parentWindow", None), AddCards):
        return buttons

    _register_add_cards_editor(editor)

    auto_deck_button = editor.addButton(
        None,
        AUTO_DECK_BUTTON_COMMAND,
        _toggle_add_cards_auto_deck,
        tip="Toggle automatic .NEW::Audio / .New::Visual deck switching for cloze notes",
        label="AD",
        id=AUTO_DECK_BUTTON_ID,
        disables=False,
    )
    buttons.append(auto_deck_button)

    if is_visual_card_multitude_add_button_enabled():
        button = editor.addButton(
            str(BUTTON_ICON_PATH),
            BUTTON_COMMAND,
            convert_current_add_note,
            tip=BUTTON_TOOLTIP,
            label="",
            id=BUTTON_ID,
            disables=False,
        )
        buttons.append(button)
    if is_add_cards_diagnosis_button_enabled():
        diagnosis_button = editor.addButton(
            None,
            DIAGNOSIS_BUTTON_COMMAND,
            apply_diagnosis_template,
            tip="Replace Text with a Diagnosis cloze template and keep images",
            label="Dx",
            id=DIAGNOSIS_BUTTON_ID,
            disables=False,
        )
        buttons.append(diagnosis_button)
    return buttons


def _on_editor_did_load_note(editor: Editor) -> None:
    if not isinstance(getattr(editor, "parentWindow", None), AddCards):
        return
    _register_add_cards_editor(editor)
    _apply_multi_image_counter_rules(editor)
    _sync_auto_deck_toggle_button(editor)
    _apply_auto_deck_rules(editor)
    _apply_pending_diagnosis_cursor(editor)


def _patch_editor_bridge() -> None:
    global _BRIDGE_PATCHED
    if _BRIDGE_PATCHED:
        return

    original = getattr(Editor, "onBridgeCmd", None)
    if not callable(original):
        return

    def wrapped(editor: Editor, cmd: str):
        result = original(editor, cmd)
        try:
            if isinstance(getattr(editor, "parentWindow", None), AddCards):
                _register_add_cards_editor(editor)
                _apply_multi_image_counter_rules(editor)
                _sync_auto_deck_toggle_button(editor)
                _apply_auto_deck_rules(editor)
        except Exception:
            pass
        return result

    Editor.onBridgeCmd = wrapped
    _BRIDGE_PATCHED = True


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    gui_hooks.editor_did_init_buttons.append(_on_setup_editor_buttons)
    gui_hooks.editor_did_load_note.append(_on_editor_did_load_note)
    if hasattr(gui_hooks, "theme_did_change"):
        gui_hooks.theme_did_change.append(sync_open_add_cards_editor_ui)
    _patch_editor_bridge()
    _HOOK_REGISTERED = True
