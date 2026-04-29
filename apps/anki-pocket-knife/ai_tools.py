from __future__ import annotations

from collections.abc import Callable
import re
from typing import Any

from aqt import gui_hooks, mw
from aqt.addcards import AddCards
from aqt.browser import Browser
from aqt.editor import Editor
from aqt.qt import QAction, QApplication, QCheckBox, QCursor, QDialog, QHBoxLayout, QInputDialog, QLabel, QMenu, QPushButton, QTimer, QVBoxLayout, QWidget
from aqt.utils import showInfo, showWarning, tooltip
from aqt.operations import QueryOp

from .ai_preview import BatchPreviewDialog, GeneratedCardsDialog, ReplacementPreviewDialog
from .ai_prompts import (
    api_key_source,
    has_api_key,
    make_card_briefer,
    make_card_even_more_concise,
    make_card_unambiguous,
    convert_to_sentence,
    make_contrasting_card,
    split_card_into_multiple,
    make_cards_uniform,
    spellcheck_card_text,
)
from .settings import get_setting, set_setting


SETTING_NAME = "ai_tools_enabled"
BUTTON_COMMAND = "pocket_knife_ai_tools"
SPELLCHECK_COMMAND = "pocket_knife_ai_spellcheck"
SPELLCHECK_SETTINGS_COMMAND = "pocket_knife_ai_spellcheck_settings"
BUTTON_ID = "pocket-knife-ai-tools"
SPELLCHECK_BUTTON_ID = "pocket-knife-ai-spellcheck"
SPELLCHECK_SETTINGS_BUTTON_ID = "pocket-knife-ai-spellcheck-settings"
BUTTON_LABEL = "✦"
SPELLCHECK_LABEL = "✔"
SPELLCHECK_SETTINGS_LABEL = "⚙"
AI_MENU_LABEL = "AI Tools"
_BROWSER_TOOLBAR_FLAG = "_anki_pocket_knife_ai_toolbar_added"
_SPELLCHECK_SHORTCUT_FLAG = "_anki_pocket_knife_spellcheck_shortcut_added"
_SPELLCHECK_BOTTOM_BUTTONS_FLAG = "_anki_pocket_knife_spellcheck_bottom_buttons_added"
_CLOZE_BOTTOM_BUTTONS_FLAG = "_anki_pocket_knife_cloze_bottom_buttons_added"
_CLOZE_BUTTON_PROPERTY = "ankiPocketKnifeClozeButton"
_HOOK_REGISTERED = False
_ADD_CARDS_PATCHED = False
_LAST_BRIEF_BY_EDITOR: dict[int, tuple[str, str]] = {}
_OPEN_GENERATED_CARD_DIALOGS: list[GeneratedCardsDialog] = []
_CLOZE_RE = re.compile(r"\{\{c(\d+)::(.*?)(?:::(.*?))?\}\}", re.IGNORECASE | re.DOTALL)


def is_ai_tools_enabled() -> bool:
    return bool(get_setting(SETTING_NAME))


def _note_field_names(note: Any) -> list[str]:
    try:
        return [str(field["name"]) for field in note.note_type()["flds"]]
    except Exception:
        try:
            return list(note.keys())
        except Exception:
            return []


def _preferred_text_field(note: Any) -> str | None:
    names = _note_field_names(note)
    for wanted in ("Text", "Front", "Question", "English", "Content"):
        for name in names:
            if name.casefold() == wanted.casefold():
                return name
    return names[0] if names else None


def _refresh_editor(editor: Editor) -> None:
    load_note_keeping_focus = getattr(editor, "loadNoteKeepingFocus", None)
    if callable(load_note_keeping_focus):
        load_note_keeping_focus()
        return
    load_note = getattr(editor, "loadNote", None)
    if callable(load_note):
        try:
            load_note()
        except TypeError:
            load_note(getattr(editor, "currentField", None))


def _run_ai(title: str, fn: Callable[[], Any], on_done: Callable[[Any], None]) -> None:
    if not has_api_key():
        showInfo(
            "Pocket Knife AI tools need an OpenAI API key before they can run.\n\n"
            "Set one with Tools > Anki Pocket Knife > Set OpenAI API Key For AI Card Tools, "
            "or set the OPENAI_API_KEY environment variable before starting Anki."
        )
        return

    def on_failed(exc: Any) -> None:
        showWarning(f"Pocket Knife AI could not complete '{title}'.\n\n{exc}")

    try:
        op = QueryOp(
            parent=mw,
            op=lambda _collection: fn(),
            success=lambda result: on_done(result),
        )
        failure_method = getattr(op, "failure", None)
        if callable(failure_method):
            configured = failure_method(on_failed)
            if configured is not None:
                op = configured
        progress_method = getattr(op, "with_progress", None)
        if callable(progress_method):
            try:
                configured = progress_method(label=f"{title}...")
            except TypeError:
                configured = progress_method(f"{title}...")
            if configured is not None:
                op = configured
        op.run_in_background()
    except Exception:
        try:
            on_done(fn())
        except Exception as exc:
            on_failed(exc)


def _editor_note_and_field(editor: Editor) -> tuple[Any, str | None]:
    note = getattr(editor, "note", None)
    return note, _preferred_text_field(note) if note is not None else None


def _apply_spellcheck_to_editor(
    editor: Editor,
    *,
    preview: bool | None = None,
    on_applied: Callable[[], None] | None = None,
    on_cancelled: Callable[[], None] | None = None,
) -> None:
    note, field = _editor_note_and_field(editor)
    if note is None or field is None:
        showWarning("Pocket Knife could not find a text field on this note.")
        if callable(on_cancelled):
            on_cancelled()
        return
    original = str(note[field] or "")
    if not original.strip():
        if callable(on_applied):
            on_applied()
        return
    should_preview = bool(get_setting("ai_spellcheck_preview")) if preview is None else bool(preview)

    def done(suggestion: str) -> None:
        if suggestion.strip() == original.strip():
            tooltip("No spelling or grammar changes found.")
            if callable(on_applied):
                on_applied()
            return
        if should_preview:
            dialog = ReplacementPreviewDialog(
                title="Spellcheck Card",
                original=original,
                suggestion=suggestion,
                parent=getattr(editor, "parentWindow", None),
                show_diff=True,
            )
            if not (dialog.exec() and dialog.accepted_replacement):
                if callable(on_cancelled):
                    on_cancelled()
                return
        note[field] = suggestion
        _refresh_editor(editor)
        tooltip("Spellcheck applied.")
        if callable(on_applied):
            on_applied()

    _run_ai("Spellcheck Card", lambda: spellcheck_card_text(original), done)


class SpellcheckSettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle("AI Spellcheck Settings")
        self.resize(460, 190)
        layout = QVBoxLayout(self)
        intro = QLabel("Choose how AI spellcheck behaves when creating cards.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.auto_checkbox = QCheckBox("Run spellcheck automatically before adding a card")
        self.auto_checkbox.setChecked(bool(get_setting("ai_spellcheck_auto_on_add")))
        layout.addWidget(self.auto_checkbox)
        self.preview_checkbox = QCheckBox("Preview spelling and grammar changes before applying")
        self.preview_checkbox.setChecked(bool(get_setting("ai_spellcheck_preview")))
        layout.addWidget(self.preview_checkbox)
        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton("Cancel", self)
        save = QPushButton("Save", self)
        save.setDefault(True)
        row.addWidget(cancel)
        row.addWidget(save)
        layout.addLayout(row)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._save)

    def _save(self) -> None:
        set_setting("ai_spellcheck_auto_on_add", bool(self.auto_checkbox.isChecked()))
        set_setting("ai_spellcheck_preview", bool(self.preview_checkbox.isChecked()))
        self.accept()


def _open_spellcheck_settings(parent: QWidget | None = None) -> None:
    SpellcheckSettingsDialog(parent).exec()


def _ensure_spellcheck_shortcut(editor: Editor) -> None:
    parent = getattr(editor, "parentWindow", None)
    if parent is None or getattr(parent, _SPELLCHECK_SHORTCUT_FLAG, False):
        return
    action = QAction("Pocket Knife Spellcheck", parent)
    action.setShortcut("Ctrl+R")
    action.triggered.connect(lambda *_args, ed=editor: _apply_spellcheck_to_editor(ed))
    try:
        parent.addAction(action)
        setattr(parent, _SPELLCHECK_SHORTCUT_FLAG, True)
    except Exception:
        pass


def _ensure_add_cards_bottom_buttons(add_cards: AddCards, editor: Editor) -> None:
    if getattr(add_cards, _SPELLCHECK_BOTTOM_BUTTONS_FLAG, False):
        return
    add_button = None
    for button in add_cards.findChildren(QPushButton):
        text = str(button.text() or "").replace("&", "").strip().casefold()
        if text == "add":
            add_button = button
            break
    if add_button is None:
        return
    layout = add_button.parentWidget().layout() if add_button.parentWidget() is not None else None
    if layout is None:
        return
    index = layout.indexOf(add_button)
    if index < 0:
        return

    settings_button = QPushButton(SPELLCHECK_SETTINGS_LABEL, add_cards)
    settings_button.setToolTip("AI spellcheck settings")
    settings_button.clicked.connect(lambda *_args: _open_spellcheck_settings(add_cards))
    spellcheck_button = QPushButton(SPELLCHECK_LABEL, add_cards)
    spellcheck_button.setToolTip("AI spelling, grammar, and punctuation check (Ctrl+R)")
    spellcheck_button.setStyleSheet("QPushButton { color: #22c55e; font-weight: 900; }")
    spellcheck_button.clicked.connect(lambda *_args, ed=editor: _apply_spellcheck_to_editor(ed))

    layout.insertWidget(index, spellcheck_button)
    layout.insertWidget(index, settings_button)
    setattr(add_cards, _SPELLCHECK_BOTTOM_BUTTONS_FLAG, True)


def _current_editor_text(editor: Editor) -> str:
    note, field = _editor_note_and_field(editor)
    if note is None or field is None:
        return ""
    return str(note[field] or "")


def _text_field_ord(note: Any) -> int | None:
    for index, name in enumerate(_note_field_names(note)):
        if name.casefold() == "text":
            return index
    return None


def _cloze_numbers(text: str) -> list[int]:
    return sorted({int(match.group(1)) for match in _CLOZE_RE.finditer(str(text or ""))})


def _refresh_note_field(editor: Editor, text: str) -> None:
    note, field = _editor_note_and_field(editor)
    if note is None or field is None:
        return
    note[field] = text
    _refresh_editor(editor)
    QTimer.singleShot(50, lambda ed=editor: _ensure_cloze_bottom_buttons(getattr(ed, "parentWindow", None), ed))


def _remove_all_clozes(editor: Editor) -> None:
    text = _current_editor_text(editor)
    _refresh_note_field(editor, _CLOZE_RE.sub(lambda match: match.group(2), text))
    tooltip("Removed all clozes.")


def _remove_cloze_number(editor: Editor, number: int) -> None:
    text = _current_editor_text(editor)
    target = int(number)

    def replace_target(match: re.Match[str]) -> str:
        num = int(match.group(1))
        if num == target:
            return match.group(2)
        if num > target:
            hint = f"::{match.group(3)}" if match.group(3) else ""
            return f"{{{{c{num - 1}::{match.group(2)}{hint}}}}}"
        return match.group(0)

    _refresh_note_field(editor, _CLOZE_RE.sub(replace_target, text))
    tooltip(f"Removed C{target} clozes.")


def _add_cloze_via_js(editor: Editor, number: int) -> None:
    web = getattr(editor, "web", None)
    if web is None:
        return
    prefix = f"{{{{c{int(number)}::"
    suffix = "}}"
    web.eval(
        f"""
(function() {{
  const prefix = {prefix!r};
  const suffix = {suffix!r};
  const selection = window.getSelection && window.getSelection();
  if (!selection || selection.rangeCount === 0) {{
    document.execCommand("insertText", false, prefix + suffix);
    return;
  }}
  const selected = selection.toString();
  if (!selected) {{
    document.execCommand("insertText", false, prefix + suffix);
    return;
  }}
  document.execCommand("insertText", false, prefix + selected + suffix);
}})();
"""
    )
    tooltip(f"Added C{int(number)} cloze.")
    QTimer.singleShot(250, lambda ed=editor: _ensure_cloze_bottom_buttons(getattr(ed, "parentWindow", None), ed))


def _ensure_cloze_bottom_buttons(add_cards: Any, editor: Editor) -> None:
    if not isinstance(add_cards, AddCards):
        return
    add_button = None
    for button in add_cards.findChildren(QPushButton):
        text = str(button.text() or "").replace("&", "").strip().casefold()
        if text == "add":
            add_button = button
            break
    if add_button is None:
        return
    layout = add_button.parentWidget().layout() if add_button.parentWidget() is not None else None
    if layout is None:
        return
    index = layout.indexOf(add_button)
    if index < 0:
        return
    for button in add_cards.findChildren(QPushButton):
        if bool(button.property(_CLOZE_BUTTON_PROPERTY)):
            layout.removeWidget(button)
            button.deleteLater()
    index = layout.indexOf(add_button)

    remove_all = QPushButton("Remove All Clozes", add_cards)
    remove_all.setProperty(_CLOZE_BUTTON_PROPERTY, True)
    remove_all.setToolTip("Remove all cloze deletion markup")
    remove_all.setStyleSheet(
        "QPushButton { background: #7f1d1d; color: #fee2e2; border: 1px solid #ef4444; font-weight: 700; }"
    )
    remove_all.clicked.connect(lambda *_args, ed=editor: _remove_all_clozes(ed))
    layout.insertWidget(index, remove_all)
    index += 1

    text = _current_editor_text(editor)
    numbers = _cloze_numbers(text)
    next_number = (max(numbers) + 1) if numbers else 1
    for number in [*numbers, next_number]:
        add_button_c = QPushButton(f"+C{number}", add_cards)
        add_button_c.setProperty(_CLOZE_BUTTON_PROPERTY, True)
        add_button_c.setToolTip(f"Add selected text as C{number}")
        add_button_c.setStyleSheet(
            "QPushButton { background: #064e3b; color: #d1fae5; border: 1px solid #10b981; font-weight: 700; }"
        )
        add_button_c.clicked.connect(lambda *_args, n=number, ed=editor: _add_cloze_via_js(ed, n))
        layout.insertWidget(index, add_button_c)
        index += 1
    for number in numbers:
        remove_button = QPushButton(f"-C{number}", add_cards)
        remove_button.setProperty(_CLOZE_BUTTON_PROPERTY, True)
        remove_button.setToolTip(f"Remove all C{number} clozes")
        remove_button.setStyleSheet(
            "QPushButton { background: #7f1d1d; color: #fee2e2; border: 1px solid #ef4444; font-weight: 700; }"
        )
        remove_button.clicked.connect(lambda *_args, n=number, ed=editor: _remove_cloze_number(ed, n))
        layout.insertWidget(index, remove_button)
        index += 1
    setattr(add_cards, _CLOZE_BOTTOM_BUTTONS_FLAG, True)


def _install_cloze_number_shortcuts(editor: Editor) -> None:
    web = getattr(editor, "web", None)
    if web is None:
        return
    web.eval(
        """
(function() {
  if (window.__ankiPocketKnifeClozeNumberShortcuts) return;
  window.__ankiPocketKnifeClozeNumberShortcuts = true;
  document.addEventListener("keydown", function(event) {
    if (!/^[1-9]$/.test(event.key)) return;
    if (event.ctrlKey || event.altKey || event.metaKey) return;
    const selection = window.getSelection && window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return;
    const selected = selection.toString();
    if (!selected || !selected.trim()) return;
    event.preventDefault();
    event.stopPropagation();
    document.execCommand("insertText", false, "{{c" + event.key + "::" + selected + "}}");
  }, true);
})();
"""
    )


def _install_text_field_cloze_toolbar(editor: Editor) -> None:
    note = getattr(editor, "note", None)
    if note is None:
        return
    field_ord = _text_field_ord(note)
    web = getattr(editor, "web", None)
    if web is None:
        return
    field_ord_js = "null" if field_ord is None else str(field_ord)
    web.eval(
        f"""
(function() {{
  const fieldOrd = {field_ord_js};
  const toolbarId = "anki-pocket-knife-text-cloze-toolbar";
  const styleId = "anki-pocket-knife-text-cloze-style";
  const clozeRe = /\\{{\\{{c(\\d+)::(.*?)(?:::(.*?))?\\}}\\}}/gis;

  function addStyle() {{
    if (document.getElementById(styleId)) return;
    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = `
      #${{toolbarId}} {{
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin: 6px 0 10px;
        align-items: center;
      }}
      #${{toolbarId}} button {{
        border-radius: 5px;
        border: 1px solid #475569;
        padding: 4px 9px;
        font: 700 12px system-ui, -apple-system, Segoe UI, sans-serif;
        line-height: 1.2;
        cursor: pointer;
      }}
      #${{toolbarId}} .apk-cloze-remove {{
        background: #7f1d1d;
        border-color: #ef4444;
        color: #fee2e2;
      }}
      #${{toolbarId}} .apk-cloze-all {{
        background: #991b1b;
        border-color: #f87171;
        color: #fff1f2;
      }}
    `;
    document.head.appendChild(style);
  }}

  function fieldBlock(editable) {{
    return editable.closest(".field, .field-container, .editor-field, .form-field, li, tr") ||
      editable.parentElement ||
      editable;
  }}

  function fieldLabelText(editable) {{
    const block = fieldBlock(editable);
    const labelledBy = editable.getAttribute("aria-labelledby");
    const explicitLabel = labelledBy && document.getElementById(labelledBy);
    const label = explicitLabel ||
      block.querySelector("label, .field-name, .field-label, .label, [class*='label'], [class*='name']");
    const text = [
      editable.getAttribute("aria-label"),
      editable.getAttribute("data-name"),
      editable.getAttribute("name"),
      block.getAttribute("data-name"),
      block.getAttribute("aria-label"),
      label && label.textContent
    ].filter(Boolean).join(" ");
    return String(text || "").trim().toLowerCase();
  }}

  function editableOrd(editable) {{
    const host = editable.closest("[data-field-ord], [data-ord], [data-field]");
    if (!host) return null;
    const value = host.getAttribute("data-field-ord") || host.getAttribute("data-ord") || host.getAttribute("data-field");
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }}

  function textEditable() {{
    const editables = Array.from(document.querySelectorAll('[contenteditable="true"]'))
      .filter(node => node.offsetParent !== null || node.getClientRects().length > 0);
    const byLabel = editables.find(node => /(^|\\b)text(\\b|:)/i.test(fieldLabelText(node)));
    if (byLabel) return byLabel;
    const byOrd = fieldOrd === null ? null : editables.find(node => editableOrd(node) === fieldOrd);
    if (byOrd) return byOrd;
    return fieldOrd === null ? null : (editables[fieldOrd] || null);
  }}

  function numbersFrom(text) {{
    const nums = new Set();
    String(text || "").replace(clozeRe, function(_match, num) {{
      nums.add(Number(num));
      return "";
    }});
    return Array.from(nums).filter(Number.isFinite).sort((a, b) => a - b);
  }}

  function notify(editable) {{
    try {{
      editable.dispatchEvent(new InputEvent("input", {{ bubbles: true, inputType: "insertText", data: null }}));
    }} catch (_error) {{
      editable.dispatchEvent(new Event("input", {{ bubbles: true }}));
    }}
    editable.dispatchEvent(new Event("change", {{ bubbles: true }}));
    setTimeout(rebuild, 0);
  }}

  function setPlainText(editable, text) {{
    editable.textContent = text;
    notify(editable);
  }}

  function removeAll(editable) {{
    setPlainText(editable, editable.innerText.replace(clozeRe, "$2"));
  }}

  function removeCnum(editable, number) {{
    const target = Number(number);
    const updated = editable.innerText.replace(clozeRe, function(match, num, body, hint) {{
      const current = Number(num);
      if (current === target) return body;
      if (current > target) return "{{{{c" + (current - 1) + "::" + body + (hint ? "::" + hint : "") + "}}}}";
      return match;
    }});
    setPlainText(editable, updated);
  }}

  function button(label, className, onClick) {{
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    b.className = className;
    b.addEventListener("mousedown", event => event.preventDefault());
    b.addEventListener("click", event => {{
      event.preventDefault();
      event.stopPropagation();
      onClick();
    }});
    return b;
  }}

  function rebuild() {{
    addStyle();
    const editable = textEditable();
    const existing = document.getElementById(toolbarId);
    if (!editable) {{
      if (existing) existing.remove();
      return;
    }}
    const block = fieldBlock(editable);
    const nums = numbersFrom(editable.innerText);
    let toolbar = existing;
    if (!nums.length) {{
      if (toolbar) toolbar.remove();
      return;
    }}
    if (!toolbar) {{
      toolbar = document.createElement("div");
      toolbar.id = toolbarId;
    }}
    toolbar.innerHTML = "";
    nums.forEach(number => {{
      toolbar.appendChild(button("-C" + number, "apk-cloze-remove", () => removeCnum(editable, number)));
    }});
    toolbar.appendChild(button("Remove All Clozes", "apk-cloze-all", () => removeAll(editable)));
    if (toolbar.parentElement !== block.parentElement || toolbar.previousElementSibling !== block) {{
      block.insertAdjacentElement("afterend", toolbar);
    }}
    if (!editable.__ankiPocketKnifeClozeListeners) {{
      editable.__ankiPocketKnifeClozeListeners = true;
      ["input", "keyup", "mouseup", "focus"].forEach(name => editable.addEventListener(name, () => setTimeout(rebuild, 0)));
    }}
  }}

  rebuild();
  if (!window.__ankiPocketKnifeTextClozeObserver) {{
    window.__ankiPocketKnifeTextClozeObserver = new MutationObserver(() => setTimeout(rebuild, 0));
    window.__ankiPocketKnifeTextClozeObserver.observe(document.body, {{ childList: true, subtree: true }});
  }}
}})();
"""
    )


def _replace_editor_text(editor: Editor, title: str, action: Callable[[str], str], *, remember_brief: bool = False) -> None:
    note = getattr(editor, "note", None)
    field = _preferred_text_field(note) if note is not None else None
    if note is None or field is None:
        showWarning("Pocket Knife could not find a text field on this note.")
        return
    original = str(note[field] or "")
    if not original.strip():
        showWarning("The selected note field is empty.")
        return

    def done(suggestion: str) -> None:
        dialog = ReplacementPreviewDialog(title=title, original=original, suggestion=suggestion, parent=getattr(editor, "parentWindow", None))
        if dialog.exec() and dialog.accepted_replacement:
            note[field] = suggestion
            if remember_brief:
                _LAST_BRIEF_BY_EDITOR[id(editor)] = (original, suggestion)
            _refresh_editor(editor)
            tooltip("AI change applied.")

    _run_ai(title, lambda: action(original), done)


def _more_concise_editor(editor: Editor) -> None:
    prior = _LAST_BRIEF_BY_EDITOR.get(id(editor))
    if prior is None:
        showWarning("Use Make Brief first, then Make More Brief.")
        return
    original, concise = prior

    def done(suggestion: str) -> None:
        dialog = ReplacementPreviewDialog(title="Make More Brief", original=concise, suggestion=suggestion, parent=getattr(editor, "parentWindow", None))
        if dialog.exec() and dialog.accepted_replacement:
            note = editor.note
            field = _preferred_text_field(note)
            if field:
                note[field] = suggestion
                _LAST_BRIEF_BY_EDITOR[id(editor)] = (original, suggestion)
                _refresh_editor(editor)
                tooltip("AI change applied.")

    _run_ai("Make More Brief", lambda: make_card_even_more_concise(original, concise), done)


def _generated_editor_cards(editor: Editor, title: str, action: Callable[[str], list[str]]) -> None:
    note = getattr(editor, "note", None)
    field = _preferred_text_field(note) if note is not None else None
    if note is None or field is None:
        showWarning("Pocket Knife could not find a text field on this note.")
        return
    original = str(note[field] or "")
    if not original.strip():
        showWarning("The selected note field is empty.")
        return

    def done(cards: list[str]) -> None:
        add_cards = getattr(editor, "parentWindow", None)
        dialog = GeneratedCardsDialog(title=title, cards=cards, parent=add_cards)

        def handle_action(action_name: str, selected: str) -> None:
            if not selected:
                return
            if action_name == "load":
                note[field] = selected
                _refresh_editor(editor)
                tooltip("Generated card loaded into the editor.")
            elif action_name == "add":
                if not isinstance(add_cards, AddCards):
                    QApplication.clipboard().setText(selected)
                    tooltip("Generated card copied. Add it as a new Browser note when ready.")
                    return
                note[field] = selected
                _refresh_editor(editor)
                add_method = getattr(add_cards, "addCards", None)
                if callable(add_method):
                    add_method()
                    tooltip("Generated card added.")
                else:
                    tooltip("Generated card loaded into the editor.")

        dialog.action_callback = handle_action
        _OPEN_GENERATED_CARD_DIALOGS.append(dialog)
        dialog.destroyed.connect(lambda *_args, d=dialog: _OPEN_GENERATED_CARD_DIALOGS.remove(d) if d in _OPEN_GENERATED_CARD_DIALOGS else None)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    _run_ai(title, lambda: action(original), done)


def _show_editor_menu(editor: Editor) -> None:
    if not is_ai_tools_enabled():
        return
    menu = QMenu(getattr(editor, "parentWindow", None))
    actions: list[tuple[str, Callable[[], None]]] = [
        ("Make Brief", lambda: _replace_editor_text(editor, "Make Brief", make_card_briefer, remember_brief=True)),
        ("Make More Brief", lambda: _more_concise_editor(editor)),
        ("Make Unambiguous", lambda: _replace_editor_text(editor, "Make Unambiguous", make_card_unambiguous)),
        ("Make Sentence", lambda: _replace_editor_text(editor, "Make Sentence", convert_to_sentence)),
        ("Add Contrasting Card", lambda: _generated_editor_cards(editor, "Add Contrasting Card", lambda text: [make_contrasting_card(text)])),
    ]
    for label, callback in actions:
        action = QAction(label, menu)
        action.triggered.connect(callback)
        menu.addAction(action)
    split_menu = menu.addMenu("Split Into Multiple Cards")
    for count in (2, 3, 4):
        action = QAction(f"{count} Cards", split_menu)
        action.triggered.connect(lambda _checked=False, c=count: _generated_editor_cards(editor, f"Split Into {c} Cards", lambda text, n=c: split_card_into_multiple(text, n)))
        split_menu.addAction(action)
    menu.exec(QCursor.pos())


def _install_shared_editor_tools(editor: Editor) -> None:
    parent = getattr(editor, "parentWindow", None)
    _ensure_spellcheck_shortcut(editor)
    if isinstance(parent, AddCards):
        QTimer.singleShot(0, lambda p=parent, ed=editor: _ensure_add_cards_bottom_buttons(p, ed))
    QTimer.singleShot(0, lambda ed=editor: _install_text_field_cloze_toolbar(ed))


def _on_setup_editor_buttons(buttons: list[str], editor: Editor) -> list[str]:
    if not is_ai_tools_enabled():
        return buttons
    _install_shared_editor_tools(editor)
    button = editor.addButton(
        None,
        BUTTON_COMMAND,
        _show_editor_menu,
        tip="AI card tools",
        label=BUTTON_LABEL,
        id=BUTTON_ID,
        disables=False,
    )
    buttons.append(button)
    return buttons


def _browser_selected_notes(browser: Browser) -> list[Any]:
    selected_notes = getattr(browser, "selectedNotes", None)
    note_ids = selected_notes() if callable(selected_notes) else []
    notes = []
    for note_id in note_ids:
        try:
            notes.append(mw.col.get_note(int(note_id)))
        except Exception:
            try:
                notes.append(mw.col.getNote(int(note_id)))
            except Exception:
                pass
    return notes


def _browser_cards_and_fields(browser: Browser) -> tuple[list[Any], list[str], list[str]]:
    notes = _browser_selected_notes(browser)
    fields = []
    texts = []
    usable_notes = []
    for note in notes:
        field = _preferred_text_field(note)
        if field is None:
            continue
        usable_notes.append(note)
        fields.append(field)
        texts.append(str(note[field] or ""))
    return usable_notes, fields, texts


def _flush_note(note: Any) -> None:
    flush = getattr(note, "flush", None)
    if callable(flush):
        flush()
        return
    update_note = getattr(mw.col, "update_note", None)
    if callable(update_note):
        update_note(note)
        return
    update_note = getattr(mw.col, "updateNote", None)
    if callable(update_note):
        update_note(note)


def _replace_browser_single(browser: Browser, title: str, action: Callable[[str], str]) -> None:
    notes, fields, texts = _browser_cards_and_fields(browser)
    if len(notes) != 1:
        showWarning("Select exactly one note for this AI action.")
        return
    original = texts[0]

    def done(suggestion: str) -> None:
        dialog = ReplacementPreviewDialog(title=title, original=original, suggestion=suggestion, parent=browser)
        if dialog.exec() and dialog.accepted_replacement:
            notes[0][fields[0]] = suggestion
            mw.checkpoint(f"Pocket Knife {title}")
            _flush_note(notes[0])
            mw.reset()
            tooltip("AI change applied.")

    _run_ai(title, lambda: action(original), done)


def _make_browser_uniform(browser: Browser) -> None:
    notes, fields, texts = _browser_cards_and_fields(browser)
    if len(notes) < 2:
        showWarning("Select at least two notes to make them uniform.")
        return

    def done(suggestions: list[str]) -> None:
        dialog = BatchPreviewDialog(title="Make Uniform Cards", originals=texts, suggestions=suggestions, parent=browser)
        if dialog.exec() and dialog.apply_changes:
            mw.checkpoint("Pocket Knife Make Uniform Cards")
            for note, field, suggestion in zip(notes, fields, suggestions):
                note[field] = suggestion
                _flush_note(note)
            mw.reset()
            tooltip(f"Applied AI to {len(suggestions)} notes.")

    _run_ai("Make Uniform Cards", lambda: make_cards_uniform(texts), done)


def _browser_generated(browser: Browser, title: str, action: Callable[[str], list[str]]) -> None:
    notes, fields, texts = _browser_cards_and_fields(browser)
    if len(texts) != 1:
        showWarning("Select exactly one note for this AI action.")
        return
    source_note = notes[0]
    source_field = fields[0]
    original = texts[0]

    def done(cards: list[str]) -> None:
        dialog = GeneratedCardsDialog(title=title, cards=cards, parent=browser)
        if not dialog.exec():
            return
        selected = dialog.selected_card()
        if dialog.selected_action == "add":
            try:
                model = source_note.note_type()
                new_note = mw.col.new_note(model)
                for field_name in _note_field_names(source_note):
                    new_note[field_name] = str(source_note[field_name] or "")
                new_note[source_field] = selected
                new_note.tags = list(getattr(source_note, "tags", []))
                deck_id = None
                cards_fn = getattr(source_note, "cards", None)
                if callable(cards_fn):
                    source_cards = cards_fn()
                    if source_cards:
                        deck_id = getattr(source_cards[0], "did", None)
                mw.checkpoint(f"Pocket Knife {title}")
                add_note = getattr(mw.col, "add_note", None)
                if callable(add_note):
                    add_note(new_note, int(deck_id) if deck_id else None)
                else:
                    add_note = getattr(mw.col, "addNote", None)
                    if callable(add_note):
                        add_note(new_note)
                    else:
                        raise RuntimeError("This Anki version cannot add a generated note.")
                mw.reset()
                tooltip("Generated card added.")
                return
            except Exception as exc:
                showWarning(str(exc))
                return
        QApplication.clipboard().setText(selected)
        tooltip("Generated card copied.")

    _run_ai(title, lambda: action(original), done)


def _populate_browser_ai_menu(menu: QMenu, browser: Browser) -> None:
    notes, _fields, _texts = _browser_cards_and_fields(browser)
    selected_count = len(notes)
    items: list[tuple[str, Callable[[], None]]] = [
        ("Spellcheck", lambda: _replace_browser_single(browser, "Spellcheck", spellcheck_card_text)),
        ("Make Brief", lambda: _replace_browser_single(browser, "Make Brief", make_card_briefer)),
        ("Make Unambiguous", lambda: _replace_browser_single(browser, "Make Unambiguous", make_card_unambiguous)),
        ("Make Sentence", lambda: _replace_browser_single(browser, "Make Sentence", convert_to_sentence)),
        ("Copy Contrasting Card", lambda: _browser_generated(browser, "Copy Contrasting Card", lambda text: [make_contrasting_card(text)])),
        ("Make Uniform From Selected", lambda: _make_browser_uniform(browser)),
    ]
    for label, callback in items:
        action = QAction(label, menu)
        if selected_count != 1 and label != "Make Uniform From Selected":
            action.setEnabled(False)
        if selected_count < 2 and label == "Make Uniform From Selected":
            action.setEnabled(False)
        action.triggered.connect(callback)
        menu.addAction(action)


def _show_browser_menu(browser: Browser) -> None:
    menu = QMenu(browser)
    _populate_browser_ai_menu(menu, browser)
    menu.exec(QCursor.pos())


def _add_browser_toolbar_button(browser: Browser) -> None:
    if getattr(browser, _BROWSER_TOOLBAR_FLAG, False):
        return
    ai_action = QAction(BUTTON_LABEL, browser)
    ai_action.setToolTip("Pocket Knife AI tools")
    ai_action.triggered.connect(lambda *_args: _show_browser_menu(browser))
    spellcheck_action = QAction(SPELLCHECK_LABEL, browser)
    spellcheck_action.setToolTip("AI spelling, grammar, and punctuation check")
    spellcheck_action.triggered.connect(
        lambda *_args: _replace_browser_single(browser, "Spellcheck", spellcheck_card_text)
    )
    for child in browser.findChildren(QWidget):
        add_action = getattr(child, "addAction", None)
        if not callable(add_action):
            continue
        if not child.__class__.__name__.endswith("ToolBar"):
            continue
        try:
            add_action(ai_action)
            add_action(spellcheck_action)
            setattr(browser, _BROWSER_TOOLBAR_FLAG, True)
            return
        except Exception:
            pass


def _on_browser_menus_did_init(browser: Browser) -> None:
    if not is_ai_tools_enabled():
        return
    _add_browser_toolbar_button(browser)
    action = QAction("Pocket Knife AI Tools", browser)
    action.triggered.connect(lambda *_args: _show_browser_menu(browser))
    try:
        browser.form.menuEdit.addAction(action)
    except Exception:
        try:
            browser.menuBar().addAction(action)
        except Exception:
            pass


def _on_editor_did_load_note(editor: Editor) -> None:
    if not is_ai_tools_enabled():
        return
    _install_shared_editor_tools(editor)


def _on_browser_will_show_context_menu(*args: Any) -> None:
    if not is_ai_tools_enabled():
        return
    browser = next((arg for arg in args if isinstance(arg, Browser)), None)
    menu = next((arg for arg in args if isinstance(arg, QMenu)), None)
    if browser is None or menu is None:
        return
    ai_menu = QMenu(AI_MENU_LABEL, menu)
    _populate_browser_ai_menu(ai_menu, browser)
    actions = menu.actions()
    if actions:
        menu.insertMenu(actions[0], ai_menu)
        menu.insertSeparator(actions[0])
    else:
        menu.addMenu(ai_menu)


def open_ai_settings_dialog() -> None:
    from .settings import set_setting

    key, ok = QInputDialog.getText(mw, "Pocket Knife AI Key", "OpenAI API key:")
    if ok:
        set_setting("ai_tools_api_key", str(key).strip())
        showInfo("Pocket Knife AI key saved in the add-on user files.")


def show_ai_key_source() -> None:
    showInfo(f"Pocket Knife AI key source: {api_key_source()}")


def _patch_add_cards_add() -> None:
    global _ADD_CARDS_PATCHED
    if _ADD_CARDS_PATCHED:
        return
    candidate_names = ("add_current_note", "addCards", "_addCards")
    patched_any = False

    def make_wrapper(method_name: str, original: Callable[..., Any]):
        def wrapped(add_cards: AddCards, *args: Any, **kwargs: Any):
            return _maybe_spellcheck_then_add(add_cards, original, args, kwargs, method_name)

        return wrapped

    for name in candidate_names:
        original = getattr(AddCards, name, None)
        if not callable(original):
            continue
        setattr(AddCards, name, make_wrapper(name, original))
        patched_any = True

    _ADD_CARDS_PATCHED = patched_any


def _maybe_spellcheck_then_add(
    add_cards: AddCards,
    original: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    method_name: str,
) -> Any:
    add_args: tuple[Any, ...] = ()
    add_kwargs: dict[str, Any] = {}
    if getattr(add_cards, "_anki_pocket_knife_spellcheck_continue", False):
        return original(add_cards, *add_args, **add_kwargs)
    if not bool(get_setting("ai_spellcheck_auto_on_add")):
        return original(add_cards, *add_args, **add_kwargs)
    if not has_api_key():
        return original(add_cards, *add_args, **add_kwargs)
    editor = getattr(add_cards, "editor", None)
    if not isinstance(editor, Editor):
        return original(add_cards, *add_args, **add_kwargs)

    def continue_add() -> None:
        setattr(add_cards, "_anki_pocket_knife_spellcheck_continue", True)
        try:
            getattr(add_cards, method_name)(*add_args, **add_kwargs)
        finally:
            setattr(add_cards, "_anki_pocket_knife_spellcheck_continue", False)

    _apply_spellcheck_to_editor(
        editor,
        preview=bool(get_setting("ai_spellcheck_preview")),
        on_applied=continue_add,
    )
    return None


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    gui_hooks.editor_did_init_buttons.append(_on_setup_editor_buttons)
    gui_hooks.editor_did_load_note.append(_on_editor_did_load_note)
    if hasattr(gui_hooks, "browser_menus_did_init"):
        gui_hooks.browser_menus_did_init.append(_on_browser_menus_did_init)
    for hook_name in (
        "browser_will_show_context_menu",
        "browser_will_show_context_menu_for_selected_notes",
        "browser_will_show_context_menu_for_selected_cards",
    ):
        hook = getattr(gui_hooks, hook_name, None)
        if hook is not None:
            try:
                hook.append(_on_browser_will_show_context_menu)
            except Exception:
                pass
    _patch_add_cards_add()
    _HOOK_REGISTERED = True
