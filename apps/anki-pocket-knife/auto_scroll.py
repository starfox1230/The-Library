from __future__ import annotations

from typing import Any

from aqt import gui_hooks, mw

from .settings import get_setting, set_setting, toggle_setting


AUTO_SCROLL_SETTING = "scroll_to_top_on_answer"
_HOOK_REGISTERED = False


def is_auto_scroll_enabled() -> bool:
    return get_setting(AUTO_SCROLL_SETTING)


def set_auto_scroll_enabled(enabled: bool) -> bool:
    return set_setting(AUTO_SCROLL_SETTING, enabled)


def toggle_auto_scroll_enabled() -> bool:
    return toggle_setting(AUTO_SCROLL_SETTING)


def _scroll_reviewer_to_top() -> None:
    reviewer = getattr(mw, "reviewer", None)
    web = getattr(reviewer, "web", None) if reviewer is not None else None
    if web is None:
        return

    web.eval(
        """
        (() => {
          const scrollTop = () => {
            try {
              window.scrollTo({ top: 0, left: 0, behavior: "auto" });
            } catch (_error) {
              window.scrollTo(0, 0);
            }
            if (document.documentElement) {
              document.documentElement.scrollTop = 0;
            }
            if (document.body) {
              document.body.scrollTop = 0;
            }
            const scrollers = Array.from(document.querySelectorAll("*")).filter((node) => {
              if (!(node instanceof HTMLElement)) {
                return false;
              }
              return node.scrollHeight > node.clientHeight;
            });
            scrollers.forEach((node) => {
              node.scrollTop = 0;
            });
          };

          scrollTop();
          requestAnimationFrame(scrollTop);
          setTimeout(scrollTop, 0);
        })();
        """
    )


def on_reviewer_did_show_answer(_card: Any) -> None:
    if not is_auto_scroll_enabled():
        return
    _scroll_reviewer_to_top()


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    gui_hooks.reviewer_did_show_answer.append(on_reviewer_did_show_answer)
    _HOOK_REGISTERED = True
