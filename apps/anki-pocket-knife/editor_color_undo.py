from __future__ import annotations

from aqt import gui_hooks
from aqt.editor import Editor


_HOOK_REGISTERED = False


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
    _eval_editor_js(editor, _build_patch_script())


def _build_patch_script() -> str:
    return r"""
const globalKey = "__ankiPocketKnifeColorUndo";
if (!window[globalKey]) {
  window[globalKey] = true;

  function isColorInput(node) {
    return node instanceof HTMLInputElement && node.type === "color";
  }

  function colorInputs() {
    return Array.from(document.querySelectorAll("input[type='color']"));
  }

  function colorCommand(input) {
    const inputs = colorInputs();
    const index = inputs.indexOf(input);
    if (index === 0) {
      return { command: "foreColor", bridge: "lastTextColor" };
    }
    if (index === 1) {
      return { command: "hiliteColor", fallback: "backColor", bridge: "lastHighlightColor" };
    }
    return null;
  }

  function sendBridge(command) {
    if (typeof pycmd === "function") {
      pycmd(command);
    }
  }

  function applyColorWithEditorUndo(input) {
    const spec = colorCommand(input);
    if (!spec) {
      return false;
    }

    const color = input.value;
    sendBridge(`${spec.bridge}:${color}`);

    try {
      document.execCommand("styleWithCSS", false, true);
    } catch (_error) {}

    let changed = false;
    try {
      changed = document.execCommand(spec.command, false, color);
    } catch (_error) {
      changed = false;
    }

    if (!changed && spec.fallback) {
      try {
        changed = document.execCommand(spec.fallback, false, color);
      } catch (_error) {
        changed = false;
      }
    }

    if (changed) {
      document.dispatchEvent(new Event(spec.command, { bubbles: true }));
    }
    return changed;
  }

  document.addEventListener(
    "change",
    (event) => {
      const input = event.target;
      if (!isColorInput(input)) {
        return;
      }
      if (!colorCommand(input)) {
        return;
      }
      if (!applyColorWithEditorUndo(input)) {
        return;
      }

      event.preventDefault();
      event.stopImmediatePropagation();
    },
    true
  );
}
"""


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    gui_hooks.editor_did_init.append(_sync_editor_js)
    gui_hooks.editor_did_load_note.append(_sync_editor_js)
    _HOOK_REGISTERED = True
