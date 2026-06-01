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

  const URL_RE = /^(https?:\\/\\/|ftp:\\/\\/)[^\\s<>'"]+$/i;
  const TRAILING_PUNCT_RE = /[.,;:!?\\])}}]+$/;

  function normalizeUrl(raw) {{
    let url = String(raw || "").trim();
    if (!url) {{
      return "";
    }}
    url = url.replace(TRAILING_PUNCT_RE, "");
    if (URL_RE.test(url)) {{
      return url;
    }}
    return "";
  }}

  function hrefFromAnchor(target) {{
    const anchor = target && target.closest ? target.closest("a[href]") : null;
    if (!anchor) {{
      return "";
    }}
    return normalizeUrl(anchor.getAttribute("href") || anchor.href || "");
  }}

  function textNodeAtPoint(x, y) {{
    if (document.caretPositionFromPoint) {{
      const pos = document.caretPositionFromPoint(x, y);
      return pos ? {{ node: pos.offsetNode, offset: pos.offset }} : null;
    }}
    if (document.caretRangeFromPoint) {{
      const range = document.caretRangeFromPoint(x, y);
      return range ? {{ node: range.startContainer, offset: range.startOffset }} : null;
    }}
    return null;
  }}

  function linkFromPlainText(x, y) {{
    const point = textNodeAtPoint(x, y);
    if (!point || !point.node || point.node.nodeType !== Node.TEXT_NODE) {{
      return "";
    }}

    const text = point.node.nodeValue || "";
    let offset = Math.max(0, Math.min(point.offset || 0, text.length));
    const left = text.slice(0, offset).search(/\\S+$/);
    const rightMatch = text.slice(offset).match(/^\\S+/);
    if (left < 0 && !rightMatch) {{
      return "";
    }}

    const start = left < 0 ? offset : left;
    const end = rightMatch ? offset + rightMatch[0].length : offset;
    return normalizeUrl(text.slice(start, end));
  }}

  document.addEventListener("click", function(event) {{
    if (!window[configKey] || !event.ctrlKey || event.button !== 0) {{
      return;
    }}

    const url = hrefFromAnchor(event.target) || linkFromPlainText(event.clientX, event.clientY);
    if (!url || typeof pycmd !== "function") {{
      return;
    }}

    event.preventDefault();
    event.stopPropagation();
    pycmd(bridgePrefix + encodeURIComponent(url));
  }}, true);
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
