from __future__ import annotations

import json
from typing import Any, Callable

from aqt import gui_hooks, mw
from aqt.qt import QKeySequence, QShortcut, Qt
from aqt.utils import tooltip

from .review_image_overlay_core import extract_image_sources, merge_image_sources
from .settings import get_setting, set_setting


SETTING_NAME = "review_image_overlay_shortcuts"
REMEMBER_POSITION_SETTING = "review_image_overlay_remember_position"
CYCLE_SHORTCUT = "Ctrl+Shift+5"
CLOSE_SHORTCUT = "Ctrl+Shift+4"
OVERLAY_JS_NAMESPACE = "PocketKnifeReviewImageOverlay"
OVERLAY_ROOT_ID = "pocket-knife-review-image-overlay"
_HOOK_REGISTERED = False
_CONTROLLER: "_ReviewerImageOverlayController | None" = None


def is_review_image_overlay_enabled() -> bool:
    return bool(get_setting(SETTING_NAME))


def set_review_image_overlay_enabled(enabled: bool) -> bool:
    value = bool(set_setting(SETTING_NAME, bool(enabled)))
    controller = _controller()
    if not value:
        controller.hide_overlay()
    return value


def is_review_image_overlay_remember_position_enabled() -> bool:
    return bool(get_setting(REMEMBER_POSITION_SETTING))


def set_review_image_overlay_remember_position_enabled(enabled: bool) -> bool:
    return bool(set_setting(REMEMBER_POSITION_SETTING, bool(enabled)))


def _reviewer_web():
    if getattr(mw, "state", "") != "review":
        return None
    reviewer = getattr(mw, "reviewer", None)
    return getattr(reviewer, "web", None) if reviewer is not None else None


def _card_id(card: Any) -> int:
    try:
        return int(getattr(card, "id", 0) or 0)
    except Exception:
        return 0


def _scroll_reviewer_to_top() -> None:
    web = _reviewer_web()
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


def _normalize_image_sources(raw_value: Any) -> list[str]:
    parsed = raw_value
    if isinstance(raw_value, str):
        text = raw_value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = [text]

    if not isinstance(parsed, list):
        return []

    cleaned = [str(value or "").strip() for value in parsed]
    return merge_image_sources(cleaned)


def _visible_images_query_script() -> str:
    return f"""
    (() => {{
      const overlayRootId = {json.dumps(OVERLAY_ROOT_ID)};
      const unique = [];
      const seen = new Set();
      const isHidden = (node) => {{
        if (!(node instanceof Element)) {{
          return false;
        }}
        const style = window.getComputedStyle(node);
        if (
          style.display === "none"
          || style.visibility === "hidden"
          || Number(style.opacity || "1") === 0
        ) {{
          return true;
        }}
        return false;
      }};
      const isVisibleImage = (img) => {{
        if (!(img instanceof HTMLImageElement)) {{
          return false;
        }}
        if (img.closest(`#${{overlayRootId}}`)) {{
          return false;
        }}
        const rect = img.getBoundingClientRect();
        if (rect.width <= 1 || rect.height <= 1) {{
          return false;
        }}
        let current = img;
        while (current instanceof Element) {{
          if (isHidden(current)) {{
            return false;
          }}
          current = current.parentElement;
        }}
        return true;
      }};

      for (const img of Array.from(document.querySelectorAll("img"))) {{
        if (!isVisibleImage(img)) {{
          continue;
        }}
        const source = String(
          img.currentSrc
          || img.getAttribute("src")
          || img.getAttribute("data-src")
          || img.src
          || ""
        ).trim();
        if (!source || seen.has(source)) {{
          continue;
        }}
        seen.add(source);
        unique.push(source);
      }}

      return JSON.stringify(unique);
    }})();
    """


def _overlay_bootstrap_script() -> str:
    return f"""
    (() => {{
      const namespace = "{OVERLAY_JS_NAMESPACE}";
      if (window[namespace]) {{
        return;
      }}

      const rootId = "{OVERLAY_ROOT_ID}";
      const styleId = "pocket-knife-review-image-overlay-style";
      const state = {{
        images: [],
        index: 0,
        open: false,
      }};

      function ensureStyle() {{
        if (document.getElementById(styleId)) {{
          return;
        }}
        const style = document.createElement("style");
        style.id = styleId;
        style.textContent = `
          #${{rootId}} {{
            position: fixed;
            inset: 0;
            z-index: 2147483647;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 20px;
            background: rgba(0, 0, 0, 0.985);
            pointer-events: auto;
          }}
          #${{rootId}}.is-open {{
            display: flex;
          }}
          #${{rootId}} .pkio-stage {{
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
          }}
          #${{rootId}} .pkio-image {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            user-select: none;
            -webkit-user-drag: none;
          }}
          #${{rootId}} .pkio-counter {{
            position: absolute;
            top: 14px;
            right: 16px;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.08);
            color: rgba(255, 255, 255, 0.92);
            font: 600 14px/1.2 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            letter-spacing: 0.02em;
          }}
        `;
        document.head.appendChild(style);
      }}

      function ensureRoot() {{
        let root = document.getElementById(rootId);
        if (root) {{
          return root;
        }}

        root = document.createElement("div");
        root.id = rootId;
        root.setAttribute("aria-hidden", "true");
        root.innerHTML = `
          <div class="pkio-stage">
            <img class="pkio-image" alt="Current card image" />
            <div class="pkio-counter" aria-live="polite"></div>
          </div>
        `;
        (document.body || document.documentElement).appendChild(root);
        return root;
      }}

      function currentImage() {{
        return state.images[state.index] || "";
      }}

      function render() {{
        ensureStyle();
        const root = ensureRoot();
        const image = root.querySelector(".pkio-image");
        const counter = root.querySelector(".pkio-counter");
        const hasImages = state.images.length > 0;
        const activeSource = currentImage();

        root.classList.toggle("is-open", state.open && hasImages);
        root.setAttribute("aria-hidden", state.open && hasImages ? "false" : "true");

        if (!hasImages) {{
          image.removeAttribute("src");
          counter.textContent = "";
          state.open = false;
          state.index = 0;
          return;
        }}

        image.src = activeSource;
        counter.textContent = `${{state.index + 1}} / ${{state.images.length}}`;
      }}

      function setImages(images, options = {{}}) {{
        const nextImages = Array.isArray(images)
          ? images.map((value) => String(value || "").trim()).filter(Boolean)
          : [];
        const previousImage = currentImage();

        state.images = nextImages;

        if (!nextImages.length) {{
          state.index = 0;
          state.open = false;
          render();
          return;
        }}

        if (options.reset) {{
          state.index = 0;
        }} else if (options.preserveCurrent && previousImage) {{
          const preservedIndex = nextImages.indexOf(previousImage);
          state.index = preservedIndex >= 0 ? preservedIndex : Math.min(state.index, nextImages.length - 1);
        }} else {{
          state.index = Math.min(state.index, nextImages.length - 1);
        }}

        if (options.close) {{
          state.open = false;
        }}

        render();
      }}

      function next() {{
        if (!state.images.length) {{
          state.open = false;
          render();
          return false;
        }}
        if (!state.open) {{
          state.open = true;
          render();
          return true;
        }}
        state.index = (state.index + 1) % state.images.length;
        render();
        return true;
      }}

      function hide() {{
        state.open = false;
        render();
      }}

      window[namespace] = {{
        setImages,
        next,
        hide,
      }};
      render();
    }})();
    """


def _command_script(
    *,
    images: list[str] | None = None,
    reset: bool = False,
    close: bool = False,
    preserve_current: bool = False,
    action: str | None = None,
) -> str:
    commands: list[str] = [_overlay_bootstrap_script()]
    if images is not None:
        commands.append(
            f"""
            window.{OVERLAY_JS_NAMESPACE}.setImages(
              {json.dumps(images)},
              {{
                reset: {str(bool(reset)).lower()},
                close: {str(bool(close)).lower()},
                preserveCurrent: {str(bool(preserve_current)).lower()},
              }}
            );
            """
        )
    if action == "next":
        commands.append(f"window.{OVERLAY_JS_NAMESPACE}.next();")
    elif action == "hide":
        commands.append(f"window.{OVERLAY_JS_NAMESPACE}.hide();")
    return "\n".join(commands)


class _ReviewerImageOverlayController:
    def __init__(self) -> None:
        self._cycle_shortcut: QShortcut | None = None
        self._close_shortcut: QShortcut | None = None
        self._question_images: list[str] = []
        self._active_images: list[str] = []
        self._current_card_id = 0

    def install(self) -> None:
        if self._cycle_shortcut is None:
            self._cycle_shortcut = QShortcut(QKeySequence(CYCLE_SHORTCUT), mw)
            self._cycle_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            self._cycle_shortcut.activated.connect(self.on_cycle_shortcut)

        if self._close_shortcut is None:
            self._close_shortcut = QShortcut(QKeySequence(CLOSE_SHORTCUT), mw)
            self._close_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            self._close_shortcut.activated.connect(self.on_close_shortcut)

    def on_reviewer_did_show_question(self, card: Any) -> None:
        self._current_card_id = _card_id(card)
        self._question_images = extract_image_sources(str(card.question() or ""))
        self._active_images = list(self._question_images)
        self._sync_overlay(reset=True, close=True, preserve_current=False)

    def on_reviewer_did_show_answer(self, card: Any) -> None:
        card_id = _card_id(card)
        if card_id != self._current_card_id:
            self._current_card_id = card_id
            self._question_images = extract_image_sources(str(card.question() or ""))
        answer_images = extract_image_sources(str(card.answer() or ""))
        self._active_images = merge_image_sources(self._question_images, answer_images)
        self._sync_overlay(reset=True, close=True, preserve_current=False)

    def on_reviewer_did_answer_card(self, reviewer: Any, card: Any, ease: int) -> None:
        del reviewer
        del card
        del ease
        self.hide_overlay()

    def on_cycle_shortcut(self) -> None:
        if not is_review_image_overlay_enabled():
            return
        if _reviewer_web() is None:
            return
        if self._refresh_active_images_from_dom(self._show_next_image):
            return
        self._show_next_image(list(self._active_images))

    def on_close_shortcut(self) -> None:
        if _reviewer_web() is None:
            return
        self.hide_overlay(scroll_to_top=True)

    def hide_overlay(self, *, scroll_to_top: bool = False) -> None:
        if self._active_images and not is_review_image_overlay_remember_position_enabled():
            self._eval(
                _command_script(
                    images=self._active_images,
                    reset=True,
                    close=True,
                    preserve_current=False,
                )
            )
        else:
            self._eval(_command_script(action="hide"))
        if scroll_to_top:
            _scroll_reviewer_to_top()

    def _show_next_image(self, images: list[str]) -> None:
        self._active_images = list(images)
        if not self._active_images:
            tooltip("No images found on the current card.")
            self.hide_overlay()
            return
        self._eval(
            _command_script(
                images=self._active_images,
                preserve_current=True,
                action="next",
            )
        )

    def _refresh_active_images_from_dom(
        self,
        callback: Callable[[list[str]], None],
    ) -> bool:
        web = _reviewer_web()
        if web is None:
            return False

        eval_with_callback = getattr(web, "evalWithCallback", None)
        if not callable(eval_with_callback):
            return False

        def on_result(value: Any) -> None:
            callback(_normalize_image_sources(value))

        eval_with_callback(_visible_images_query_script(), on_result)
        return True

    def _sync_overlay(self, *, reset: bool, close: bool, preserve_current: bool) -> None:
        if not is_review_image_overlay_enabled():
            self.hide_overlay()
            return
        self._eval(
            _command_script(
                images=self._active_images,
                reset=reset,
                close=close,
                preserve_current=preserve_current,
            )
        )

    def _eval(self, script: str) -> None:
        web = _reviewer_web()
        if web is None:
            return
        web.eval(script)


def _controller() -> _ReviewerImageOverlayController:
    global _CONTROLLER
    if _CONTROLLER is None:
        _CONTROLLER = _ReviewerImageOverlayController()
    return _CONTROLLER


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    controller = _controller()
    controller.install()

    reviewer_show_question = getattr(gui_hooks, "reviewer_did_show_question", None)
    if reviewer_show_question is not None:
        reviewer_show_question.append(controller.on_reviewer_did_show_question)

    reviewer_show_answer = getattr(gui_hooks, "reviewer_did_show_answer", None)
    if reviewer_show_answer is not None:
        reviewer_show_answer.append(controller.on_reviewer_did_show_answer)

    reviewer_answer = getattr(gui_hooks, "reviewer_did_answer_card", None)
    if reviewer_answer is not None:
        reviewer_answer.append(controller.on_reviewer_did_answer_card)

    _HOOK_REGISTERED = True
