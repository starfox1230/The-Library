from __future__ import annotations

import json
import re
import weakref
from urllib.parse import urlparse

from aqt import gui_hooks
from aqt.editor import Editor
from aqt.utils import openLink

from .settings import get_setting, set_setting


SETTING_NAME = "editor_ctrl_click_open_links"
_BRIDGE_PREFIX = "pocket_knife_ctrl_click_open_link:"
_HOOK_REGISTERED = False
_BRIDGE_PATCHED = False
_OPEN_EDITORS: "weakref.WeakSet[Editor]" = weakref.WeakSet()
_URL_RE = re.compile(r"^(?:https?|ftp)://[^\s<>'\"]+$", re.IGNORECASE)


def is_ctrl_click_open_links_enabled() -> bool:
    return bool(get_setting(SETTING_NAME))


def set_ctrl_click_open_links_enabled(enabled: bool) -> bool:
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
    eval_method = getattr(web, "eval", None)
    if callable(eval_method):
        eval_method(body)


def _sync_editor_js(editor: Editor) -> None:
    _register_editor(editor)
    _eval_editor_js(editor, _build_editor_script(is_ctrl_click_open_links_enabled()))


def sync_open_editor_js() -> None:
    for editor in list(_OPEN_EDITORS):
        try:
            _sync_editor_js(editor)
        except Exception:
            pass


def _build_editor_script(enabled: bool) -> str:
    enabled_js = json.dumps(bool(enabled))
    prefix_js = json.dumps(_BRIDGE_PREFIX)
    return f"""
(function() {{
  const enabled = {enabled_js};
  const bridgePrefix = {prefix_js};
  const stateKey = "__pocketKnifeCtrlClickLinksInstalled";
  const configKey = "__pocketKnifeCtrlClickLinksEnabled";
  window[configKey] = enabled;

  if (window[stateKey]) {{
    return;
  }}
  window[stateKey] = true;

  const URL_RE = /(?:https?:\\/\\/|ftp:\\/\\/)[^\\s<>'"]+/ig;
  const FULL_URL_RE = /^(https?:\\/\\/|ftp:\\/\\/)[^\\s<>'"]+$/i;
  const TRAILING_PUNCT_RE = /[.,;:!?\\])}}]+$/;
  let lastOpened = {{ url: "", time: 0 }};

  function normalizeUrl(raw) {{
    let url = String(raw || "").trim();
    if (!url) {{
      return "";
    }}
    url = url.replace(TRAILING_PUNCT_RE, "");
    if (FULL_URL_RE.test(url)) {{
      return url;
    }}
    return "";
  }}

  function eventPath(event) {{
    if (typeof event.composedPath === "function") {{
      return event.composedPath();
    }}
    return [];
  }}

  function hrefFromAnchor(event) {{
    for (const node of eventPath(event)) {{
      if (node && node.nodeType === Node.ELEMENT_NODE && node.matches && node.matches("a[href]")) {{
        return normalizeUrl(node.getAttribute("href") || node.href || "");
      }}
      if (node && node.closest) {{
        const anchor = node.closest("a[href]");
        if (anchor) {{
          return normalizeUrl(anchor.getAttribute("href") || anchor.href || "");
        }}
      }}
    }}
    return "";
  }}

  function editableFromEvent(event) {{
    for (const node of eventPath(event)) {{
      if (node && node.nodeType === Node.ELEMENT_NODE) {{
        if (node.matches && node.matches("anki-editable, [contenteditable='true']")) {{
          return node;
        }}
        if (node.closest) {{
          const editable = node.closest("anki-editable, [contenteditable='true']");
          if (editable) {{
            return editable;
          }}
        }}
      }}
    }}
    return null;
  }}

  function pointInRect(x, y, rect) {{
    return x >= rect.left - 1 && x <= rect.right + 1 && y >= rect.top - 1 && y <= rect.bottom + 1;
  }}

  function pointInRange(x, y, range) {{
    for (const rect of Array.from(range.getClientRects())) {{
      if (pointInRect(x, y, rect)) {{
        return true;
      }}
    }}
    return false;
  }}

  function textNodesUnder(root) {{
    const nodes = [];
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {{
      nodes.push(walker.currentNode);
    }}
    return nodes;
  }}

  function linkFromPlainText(event) {{
    const editable = editableFromEvent(event);
    if (!editable) {{
      return "";
    }}

    for (const node of textNodesUnder(editable)) {{
      const text = node.nodeValue || "";
      URL_RE.lastIndex = 0;
      let match = URL_RE.exec(text);
      while (match) {{
        const raw = match[0];
        const url = normalizeUrl(raw);
        if (url) {{
          const range = document.createRange();
          range.setStart(node, match.index);
          range.setEnd(node, match.index + raw.length);
          if (pointInRange(event.clientX, event.clientY, range)) {{
            return url;
          }}
        }}
        match = URL_RE.exec(text);
      }}
    }}
    return "";
  }}

  function handlePointer(event) {{
    if (!window[configKey] || !event.ctrlKey || event.button !== 0) {{
      return;
    }}

    const url = hrefFromAnchor(event) || linkFromPlainText(event);
    if (!url || typeof pycmd !== "function") {{
      return;
    }}

    event.preventDefault();
    event.stopPropagation();
    const now = Date.now();
    if (lastOpened.url === url && now - lastOpened.time < 500) {{
      return;
    }}
    lastOpened = {{ url: url, time: now }};
    pycmd(bridgePrefix + encodeURIComponent(url));
  }}

  document.addEventListener("pointerdown", handlePointer, true);
  document.addEventListener("mousedown", handlePointer, true);
  document.addEventListener("click", handlePointer, true);
}})();
"""


def _is_safe_external_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme.lower() in {"http", "https", "ftp"} and bool(parsed.netloc)


def _handle_bridge_command(cmd: str) -> bool:
    if not cmd.startswith(_BRIDGE_PREFIX):
        return False
    if not is_ctrl_click_open_links_enabled():
        return True

    from urllib.parse import unquote

    url = unquote(cmd[len(_BRIDGE_PREFIX) :]).strip()
    if _URL_RE.match(url) and _is_safe_external_url(url):
        openLink(url)
    return True


def _patch_editor_bridge() -> None:
    global _BRIDGE_PATCHED
    if _BRIDGE_PATCHED:
        return

    original = getattr(Editor, "onBridgeCmd", None)
    if not callable(original):
        return

    def wrapped(editor: Editor, cmd: str):
        if _handle_bridge_command(cmd):
            return None
        return original(editor, cmd)

    Editor.onBridgeCmd = wrapped
    _BRIDGE_PATCHED = True


def _on_editor_did_load_note(editor: Editor) -> None:
    _sync_editor_js(editor)


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    gui_hooks.editor_did_init.append(_sync_editor_js)
    gui_hooks.editor_did_load_note.append(_on_editor_did_load_note)
    _patch_editor_bridge()
    _HOOK_REGISTERED = True
