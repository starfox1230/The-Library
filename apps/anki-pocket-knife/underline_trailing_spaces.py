from __future__ import annotations

import json
import weakref

from aqt import gui_hooks
from aqt.editor import Editor

from .settings import get_setting, set_setting


SETTING_NAME = "underline_trailing_spaces_fix"
_HOOK_REGISTERED = False
_OPEN_EDITORS: "weakref.WeakSet[Editor]" = weakref.WeakSet()


def is_underline_trailing_spaces_fix_enabled() -> bool:
    return bool(get_setting(SETTING_NAME))


def set_underline_trailing_spaces_fix_enabled(enabled: bool) -> bool:
    value = bool(set_setting(SETTING_NAME, bool(enabled)))
    sync_open_editor_js()
    return value


def _register_editor(editor: Editor) -> None:
    try:
        _OPEN_EDITORS.add(editor)
    except Exception:
        pass


def _eval_editor_js(editor: Editor, body: str) -> None:
    web = getattr(editor, "web", None)
    if web is None:
        return
    web.eval(
        """
(() => {
  const run = () => {
%s
  };
  if (typeof require === "function") {
    try {
      require("anki/ui").loaded.then(run);
      return;
    } catch (_error) {}
  }
  run();
})();
"""
        % body
    )


def _sync_editor_js(editor: Editor) -> None:
    _register_editor(editor)
    _eval_editor_js(
        editor,
        _build_sync_script(is_underline_trailing_spaces_fix_enabled()),
    )


def sync_open_editor_js() -> None:
    for editor in list(_OPEN_EDITORS):
        try:
            _sync_editor_js(editor)
        except Exception:
            continue


def _build_sync_script(enabled: bool) -> str:
    enabled_js = json.dumps(bool(enabled))
    return """
const enabled = %s;
const globalKey = "__ankiPocketKnifeUnderlineTrailingSpaces";
const globalObject = window[globalKey] || (window[globalKey] = (() => {
  const pendingSelector = '[data-pocket-knife-pending-underline="true"]';
  const trailingWhitespacePattern = /[\\s\\u00a0]+$/;
  const hasVisibleTextPattern = /[^\\s\\u00a0]/;
  const editableStates = new WeakMap();
  const attachedEditables = new Set();

  function isElement(node) {
    return Boolean(node) && node.nodeType === Node.ELEMENT_NODE;
  }

  function isUnderlineElement(node) {
    if (!(node instanceof HTMLElement)) {
      return false;
    }
    if (node.matches(pendingSelector)) {
      return false;
    }
    if (node.closest(pendingSelector)) {
      return false;
    }
    if (node.tagName === "U") {
      return true;
    }
    const style = String(node.getAttribute("style") || "");
    return /text-decoration(?:-line)?\\s*:[^;]*underline/i.test(style);
  }

  function stripUnderlineStyle(styleText) {
    return styleText
      .split(";")
      .map((part) => part.trim())
      .filter(Boolean)
      .filter((part) => !/^text-decoration(?:-line)?\\s*:/i.test(part))
      .join("; ");
  }

  function cloneWithoutUnderline(element) {
    let clone;
    if (element.tagName === "U") {
      clone = document.createElement("span");
      for (const attribute of Array.from(element.attributes)) {
        clone.setAttribute(attribute.name, attribute.value);
      }
    } else {
      clone = element.cloneNode(false);
    }

    const style = stripUnderlineStyle(String(clone.getAttribute("style") || ""));
    if (style) {
      clone.setAttribute("style", style);
    } else {
      clone.removeAttribute("style");
    }

    clone.removeAttribute("data-pocket-knife-pending-underline");
    return clone;
  }

  function collectEditables(root, found) {
    const selector = "anki-editable[contenteditable='true']";
    if (root instanceof ShadowRoot || root instanceof Document || root instanceof HTMLElement) {
      if (typeof root.querySelectorAll === "function") {
        for (const editable of root.querySelectorAll(selector)) {
          found.add(editable);
        }
      }
      if (typeof root.querySelectorAll === "function") {
        for (const element of root.querySelectorAll("*")) {
          if (element.shadowRoot) {
            collectEditables(element.shadowRoot, found);
          }
        }
      }
    }
  }

  function saveSelectionOffsets(editable) {
    const selection = document.getSelection();
    if (!selection || selection.rangeCount === 0) {
      return null;
    }
    const range = selection.getRangeAt(0);
    if (!editable.contains(range.startContainer) || !editable.contains(range.endContainer)) {
      return null;
    }

    const startRange = document.createRange();
    startRange.selectNodeContents(editable);
    startRange.setEnd(range.startContainer, range.startOffset);

    const endRange = document.createRange();
    endRange.selectNodeContents(editable);
    endRange.setEnd(range.endContainer, range.endOffset);

    return {
      start: startRange.toString().length,
      end: endRange.toString().length,
    };
  }

  function findBoundary(editable, targetOffset) {
    const walker = document.createTreeWalker(editable, NodeFilter.SHOW_TEXT);
    let remaining = Math.max(0, Number(targetOffset) || 0);
    let lastText = null;

    while (walker.nextNode()) {
      const textNode = walker.currentNode;
      lastText = textNode;
      const length = textNode.data.length;
      if (remaining <= length) {
        return { node: textNode, offset: remaining };
      }
      remaining -= length;
    }

    if (lastText) {
      return { node: lastText, offset: lastText.data.length };
    }

    return { node: editable, offset: editable.childNodes.length };
  }

  function restoreSelectionOffsets(editable, saved) {
    if (!saved) {
      return;
    }

    const selection = document.getSelection();
    if (!selection) {
      return;
    }

    const start = findBoundary(editable, saved.start);
    const end = findBoundary(editable, saved.end);
    const range = document.createRange();
    range.setStart(start.node, start.offset);
    range.setEnd(end.node, end.offset);
    selection.removeAllRanges();
    selection.addRange(range);
  }

  function selectionIsCollapsedAtUnderlineEnd(underlineElement) {
    const selection = document.getSelection();
    if (!selection || selection.rangeCount === 0) {
      return false;
    }

    const range = selection.getRangeAt(0);
    if (!range.collapsed) {
      return false;
    }
    if (!underlineElement.contains(range.startContainer)) {
      return false;
    }

    const endRange = document.createRange();
    endRange.selectNodeContents(underlineElement);
    endRange.collapse(false);

    return (
      range.compareBoundaryPoints(Range.START_TO_START, endRange) === 0
      && range.compareBoundaryPoints(Range.END_TO_END, endRange) === 0
    );
  }

  function placeCaretAtEnd(node) {
    const selection = document.getSelection();
    if (!selection) {
      return;
    }
    const range = document.createRange();
    range.selectNodeContents(node);
    range.collapse(false);
    selection.removeAllRanges();
    selection.addRange(range);
  }

  function buildPendingElement(underlineElement, textParent, whitespace) {
    const pendingRoot = cloneWithoutUnderline(underlineElement);
    pendingRoot.dataset.pocketKnifePendingUnderline = "true";
    pendingRoot.replaceChildren();

    const path = [];
    let current = textParent;
    while (current && current !== underlineElement) {
      path.unshift(current);
      current = current.parentNode;
    }

    let cursor = pendingRoot;
    for (const element of path) {
      const clone = element.cloneNode(false);
      cursor.appendChild(clone);
      cursor = clone;
    }
    cursor.appendChild(document.createTextNode(whitespace));

    return pendingRoot;
  }

  function pruneEmptyBranch(node, stopElement) {
    let current = node;
    while (current && current !== stopElement) {
      if (current.nodeType === Node.TEXT_NODE) {
        if (current.data.length > 0) {
          break;
        }
        const parent = current.parentNode;
        current.remove();
        current = parent;
        continue;
      }

      if (!isElement(current) || current.childNodes.length > 0) {
        break;
      }

      const parent = current.parentNode;
      current.remove();
      current = parent;
    }
  }

  function appendPendingAfterUnderline(underlineElement, pendingElement) {
    const nextSibling = underlineElement.nextSibling;
    if (nextSibling && nextSibling.nodeType === Node.ELEMENT_NODE && nextSibling.matches(pendingSelector)) {
      while (pendingElement.firstChild) {
        nextSibling.insertBefore(pendingElement.firstChild, nextSibling.firstChild);
      }
      return;
    }
    underlineElement.parentNode.insertBefore(pendingElement, underlineElement.nextSibling);
  }

  function extractTrailingWhitespace(underlineElement) {
    const walker = document.createTreeWalker(underlineElement, NodeFilter.SHOW_TEXT);
    let lastText = null;
    while (walker.nextNode()) {
      lastText = walker.currentNode;
    }
    if (!lastText) {
      return false;
    }

    const match = String(lastText.data || "").match(trailingWhitespacePattern);
    if (!match) {
      return false;
    }

    const whitespace = match[0];
    if (!whitespace) {
      return null;
    }

    const shouldPlaceCaretAfterPending = selectionIsCollapsedAtUnderlineEnd(underlineElement);
    lastText.data = lastText.data.slice(0, lastText.data.length - whitespace.length);
    const pendingElement = buildPendingElement(underlineElement, lastText.parentNode, whitespace);
    appendPendingAfterUnderline(underlineElement, pendingElement);
    pruneEmptyBranch(lastText, underlineElement);
    return shouldPlaceCaretAfterPending ? pendingElement : true;
  }

  function restorePendingUnderline(pendingElement) {
    const text = String(pendingElement.textContent || "");
    if (!text) {
      pendingElement.remove();
      return true;
    }
    if (!hasVisibleTextPattern.test(text)) {
      return false;
    }

    let previous = pendingElement.previousSibling;
    while (previous && previous.nodeType === Node.TEXT_NODE && previous.textContent === "") {
      previous = previous.previousSibling;
    }

    if (previous && previous.nodeType === Node.ELEMENT_NODE && isUnderlineElement(previous)) {
      while (pendingElement.firstChild) {
        previous.appendChild(pendingElement.firstChild);
      }
      pendingElement.remove();
      return true;
    }

    pendingElement.removeAttribute("data-pocket-knife-pending-underline");
    return true;
  }

  function normalizeEditable(editable) {
    const state = editableStates.get(editable);
    if (!state || state.normalizing || state.composing || !api.enabled) {
      return;
    }

    state.normalizing = true;
    const selection = saveSelectionOffsets(editable);
    let changed = false;
    let preferredCaretTarget = null;

    try {
      for (let iteration = 0; iteration < 10; iteration += 1) {
        let iterationChanged = false;

        for (const pendingElement of Array.from(editable.querySelectorAll(pendingSelector))) {
          if (!(pendingElement instanceof HTMLElement) || !pendingElement.isConnected) {
            continue;
          }
          if (restorePendingUnderline(pendingElement)) {
            iterationChanged = true;
          }
        }

        const underlineElements = [];
        const walker = document.createTreeWalker(editable, NodeFilter.SHOW_ELEMENT);
        while (walker.nextNode()) {
          const element = walker.currentNode;
          if (element instanceof HTMLElement && isUnderlineElement(element)) {
            underlineElements.push(element);
          }
        }

        for (const underlineElement of underlineElements.reverse()) {
          if (!(underlineElement instanceof HTMLElement) || !underlineElement.isConnected) {
            continue;
          }
          const extracted = extractTrailingWhitespace(underlineElement);
          if (extracted) {
            if (extracted instanceof HTMLElement) {
              preferredCaretTarget = extracted;
            }
            iterationChanged = true;
          }
        }

        for (const pendingElement of Array.from(editable.querySelectorAll(pendingSelector))) {
          if (pendingElement.textContent === "") {
            pendingElement.remove();
            iterationChanged = true;
          }
        }

        changed = changed || iterationChanged;
        if (!iterationChanged) {
          break;
        }
      }

      if (changed) {
        if (preferredCaretTarget instanceof HTMLElement && preferredCaretTarget.isConnected) {
          placeCaretAtEnd(preferredCaretTarget);
        } else {
          restoreSelectionOffsets(editable, selection);
        }
      }
    } finally {
      state.normalizing = false;
    }
  }

  function scheduleNormalize(editable) {
    const state = editableStates.get(editable);
    if (!state || state.scheduled || state.composing) {
      return;
    }
    state.scheduled = true;
    queueMicrotask(() => {
      state.scheduled = false;
      normalizeEditable(editable);
    });
  }

  function attachEditable(editable) {
    if (!(editable instanceof HTMLElement) || editableStates.has(editable)) {
      return;
    }

    const state = {
      composing: false,
      normalizing: false,
      scheduled: false,
    };

    const observer = new MutationObserver(() => scheduleNormalize(editable));
    observer.observe(editable, {
      attributes: true,
      characterData: true,
      childList: true,
      subtree: true,
    });

    editable.addEventListener("compositionstart", () => {
      state.composing = true;
    });
    editable.addEventListener("compositionend", () => {
      state.composing = false;
      scheduleNormalize(editable);
    });
    editable.addEventListener("blur", () => scheduleNormalize(editable));

    state.observer = observer;
    editableStates.set(editable, state);
    attachedEditables.add(editable);
    scheduleNormalize(editable);
  }

  const api = {
    enabled: true,
    scan() {
      const editables = new Set();
      collectEditables(document, editables);
      for (const editable of editables) {
        attachEditable(editable);
      }
    },
    normalizeAll() {
      for (const editable of Array.from(attachedEditables)) {
        scheduleNormalize(editable);
      }
    },
  };

  return api;
})());
globalObject.enabled = enabled;
globalObject.scan();
globalObject.normalizeAll();
""" % enabled_js


def _on_editor_did_load_note(editor: Editor) -> None:
    _sync_editor_js(editor)


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    gui_hooks.editor_did_load_note.append(_on_editor_did_load_note)
    _HOOK_REGISTERED = True
