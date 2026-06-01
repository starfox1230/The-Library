from __future__ import annotations

import json
from typing import Any

from anki.utils import pointVersion
from aqt import gui_hooks, mw
from aqt.qt import QTimer
from aqt.reviewer import ReviewerBottomBar

from .settings import get_setting, set_setting


_HOOKS_REGISTERED = False
COLORS = {
    "again": "red",
    "hard": "orange",
    "good": "#30c257",
    "easy": "#61a8ff",
}
NIGHT_COLORS = {
    "again": "#ff6961",
    "hard": "#ffb861",
    "good": "#61ffb8",
    "easy": "#61a8ff",
}


def is_king_answer_buttons_enabled() -> bool:
    return bool(get_setting("king_answer_buttons_enabled"))


def set_king_answer_buttons_enabled(enabled: bool) -> None:
    set_setting("king_answer_buttons_enabled", bool(enabled))
    _refresh_bottom_bar_styles()


def is_king_answer_feedback_enabled() -> bool:
    return bool(get_setting("king_answer_feedback_enabled"))


def set_king_answer_feedback_enabled(enabled: bool) -> None:
    set_setting("king_answer_feedback_enabled", bool(enabled))


def king_answer_feedback_scale() -> int:
    try:
        value = int(get_setting("king_answer_feedback_scale"))
    except Exception:
        value = 100
    return max(50, min(220, value))


def set_king_answer_feedback_scale(value: int) -> None:
    set_setting("king_answer_feedback_scale", max(50, min(220, int(value))))


def king_answer_feedback_width() -> int:
    try:
        legacy_scale = int(get_setting("king_answer_feedback_scale"))
    except Exception:
        legacy_scale = 100
    try:
        value = int(get_setting("king_answer_feedback_width"))
    except Exception:
        value = int(530 * max(50, min(220, legacy_scale)) / 100)
    return max(120, min(900, value))


def set_king_answer_feedback_width(value: int) -> None:
    set_setting("king_answer_feedback_width", max(120, min(900, int(value))))


def king_answer_feedback_font_size() -> int:
    try:
        value = int(get_setting("king_answer_feedback_font_size"))
    except Exception:
        value = 24
    return max(10, min(48, value))


def set_king_answer_feedback_font_size(value: int) -> None:
    set_setting("king_answer_feedback_font_size", max(10, min(48, int(value))))


def king_answer_button_height() -> int:
    try:
        value = int(get_setting("king_answer_button_height"))
    except Exception:
        value = 47
    return max(20, min(120, value))


def set_king_answer_button_height(value: int) -> None:
    set_setting("king_answer_button_height", max(20, min(120, int(value))))
    _refresh_bottom_bar_styles()
    _apply_bottom_bar_container_height()


def _is_night_mode() -> bool:
    try:
        from aqt.theme import theme_manager

        return bool(theme_manager.night_mode)
    except Exception:
        return False


def _active_colors() -> dict[str, str]:
    return dict(NIGHT_COLORS if _is_night_mode() else COLORS)


def _button_color(name: str) -> str:
    return _active_colors().get(name, COLORS[name])


def bottom_bar_styles() -> str:
    if not is_king_answer_buttons_enabled():
        return ""

    border_radius = 15
    answer_width = 530
    width = 42
    height = king_answer_button_height()
    due_label_space = 34
    top_cushion = 8
    bottom_cushion = 12
    bottom_bar_min_height = height + due_label_space + top_cushion + bottom_cushion

    colors = _active_colors()
    hover_effect = """
        /* the "Good" button */
        #defease:hover {
            background-color: %(good)s!important;
            color: #3a3a3a!important;
        }
        button[onclick*="ease1"]:not(#defease):hover {
            background-color: %(again)s!important;
            color: #3a3a3a!important;
        }
        button[onclick*="ease2"]:not(#defease):hover {
            background-color: %(hard)s!important;
            color: #3a3a3a!important;
        }
        button[onclick*="ease3"]:not(#defease):hover,
        button[onclick*="ease4"]:not(#defease):hover {
            background-color: %(easy)s!important;
            color: #3a3a3a!important;
        }
        /* the "Edit", "More" and "Answer" buttons */
        button[onclick*="edit"]:hover,
        button[onclick*="more"]:hover,
        #ansbut:hover {
            background-color: %(background)s!important;
            color: %(text)s!important;
        }
        #ansbut:hover .nobold,
        #ansbut:hover .nobold * {
            color: var(--fg, var(--text-fg)) !important;
        }
    """ % {
        "good": colors["good"],
        "again": colors["again"],
        "hard": colors["hard"],
        "easy": colors["easy"],
        "background": "#c0c0c0" if _is_night_mode() else "#3a3a3a",
        "text": "#3a3a3a" if _is_night_mode() else "#c0c0c0",
    }

    css = """
    /* All buttons at the bottom of the review screen
    (including the "Edit" and "More" button) */
    button {
        height: %(height)spx;
        min-height: %(height)spx;
        box-sizing: border-box;
        line-height: %(button_line_height)spx !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        border: solid 1px rgba(100, 100, 100, 0.2)!important;
        border-top: solid 0.5px #878787!important;
        border-radius: %(border_radius)spx !important;
        -webkit-appearance: none;
        cursor: pointer;
        margin: 2px 6px 6px !important;
        box-shadow: 0px 0px 1.5px .2px #000000 !important;
        -webkit-box-shadow: 0px 0px 1.5px .2px #000000 !important;
    }
    .nightMode button {
        box-shadow: 0px 0px 1.5px .5px #000000 !important;
        -webkit-box-shadow: 0px 0px 2.5px .5px #000000 !important;
        background: #3a3a3a !important;
    }

    /* the "Show Answer" button */
    #ansbut {
        width: %(answer_width)spx !important;
        height: %(height)spx !important;
        min-height: %(height)spx !important;
        line-height: %(button_line_height)spx !important;
        text-align: center;
    }
    /* All rating buttons */
    #middle button {
        min-width: %(width)spx;
        height: %(height)spx !important;
        min-height: %(height)spx !important;
        line-height: %(button_line_height)spx !important;
        text-align: center !important;
    }

    /* the "Good" button */
    #defease {
        color: %(good_color)s !important;
        background: inherit !important;
        text-align: center;
    }

    /* the "Again" button */
    button[onclick*="ease1"]:not(#defease) {
        color: %(again_color)s !important;
        background: inherit !important;
        text-align: center;
    }

    /* the "Hard" button */
    button[onclick*="ease2"]:not(#defease) {
        color: %(hard_color)s !important;
        background: inherit !important;
        text-align: center;
    }

    /* the "Easy" button */
    button[onclick*="ease3"]:not(#defease),
    button[onclick*="ease4"]:not(#defease) {
        color: %(easy_color)s !important;
        background: inherit !important;
        text-align: center;
    }

    button[onclick*="edit"],
    button[onclick*="more"] {
        text-align: center;
    }

    %(hover_effect)s

    /* The times are nested inside the answer buttons in 2.1.55+,
    so the previous styles also apply to the text and it becomes unreadable in night mode */
    .nobold {
        color: var(--fg, var(--text-fg));
    }
    #ansbut .nobold,
    #ansbut .nobold * {
        color: var(--fg, var(--text-fg)) !important;
    }
    html,
    body {
        min-height: %(bottom_bar_min_height)spx !important;
        height: auto !important;
        overflow: hidden !important;
    }
    body {
        box-sizing: border-box;
        padding-top: %(top_cushion)spx !important;
        padding-bottom: 4px !important;
    }
    #middle {
        min-height: %(bottom_bar_min_height)spx !important;
    }
    .stat,
    #middle td[align=center] {
        padding-top: %(due_label_space)spx !important;
    }
    """ % {
        "height": height,
        "button_line_height": max(1, height - 2),
        "border_radius": border_radius,
        "answer_width": answer_width,
        "width": width,
        "bottom_bar_min_height": bottom_bar_min_height,
        "due_label_space": due_label_space,
        "top_cushion": top_cushion,
        "good_color": colors["good"],
        "again_color": colors["again"],
        "hard_color": colors["hard"],
        "easy_color": colors["easy"],
        "hover_effect": hover_effect,
    }

    if pointVersion() >= 57:
        css += """
    .stat {
        padding-top: 34px !important;
    }
    #middle td[align=center] {
        padding-top: 34px !important;
    }
    """

    return css


def _bottom_bar_container_height() -> int:
    height = king_answer_button_height()
    if not is_king_answer_buttons_enabled():
        return 0
    return max(79, height + 54)


def _apply_bottom_bar_container_height() -> None:
    bottom_web = getattr(mw, "bottomWeb", None)
    if bottom_web is None:
        return
    height = _bottom_bar_container_height()
    try:
        if height <= 0:
            bottom_web.setMinimumHeight(0)
            bottom_web.setMaximumHeight(16777215)
            return
        bottom_web.setMinimumHeight(height)
        bottom_web.setMaximumHeight(height)
    except Exception:
        pass


def _on_webview_will_set_content(web_content: Any, context: Any) -> None:
    if not isinstance(context, ReviewerBottomBar):
        return
    web_content.head += f"<style id='pocket-knife-king-answer-button-styles'>{bottom_bar_styles()}</style>"
    web_content.body += """
<script>
(() => {
  function savePocketKnifeShowAnswerAnchor() {
    const showAnswer = document.querySelector("#ansbut");
    if (!showAnswer) return;
    const rect = showAnswer.getBoundingClientRect();
    window.pocketKnifeShowAnswerAnchor = {
      centerX: rect.left + (rect.width / 2),
      top: rect.top
    };
  }
  savePocketKnifeShowAnswerAnchor();
  window.setTimeout(savePocketKnifeShowAnswerAnchor, 0);
  window.setTimeout(savePocketKnifeShowAnswerAnchor, 50);
})();
</script>
"""
    _apply_bottom_bar_container_height()
    QTimer.singleShot(0, _apply_bottom_bar_container_height)


def _refresh_bottom_bar_styles() -> None:
    bottom_web = getattr(mw, "bottomWeb", None)
    if bottom_web is None:
        return
    _apply_bottom_bar_container_height()
    try:
        bottom_web.eval(
            "(() => { const el = document.querySelector('#pocket-knife-king-answer-button-styles'); "
            "if (el) el.textContent = %s; })();" % json.dumps(bottom_bar_styles())
        )
    except Exception:
        pass


def _label_for_ease(ease: int) -> tuple[str, str]:
    if int(ease) == 1:
        return "Again", _button_color("again")
    if int(ease) == 2:
        return "Hard", _button_color("hard")
    if int(ease) == 4:
        return "Easy", _button_color("easy")
    return "Good", _button_color("good")


def _contrast_text_color(background: str) -> str:
    value = str(background or "").strip().lower()
    named = {"red": "#ff0000", "orange": "#ffa500"}
    if value in named:
        value = named[value]
    if not value.startswith("#") or len(value) != 7:
        return "#3a3a3a"
    try:
        red = int(value[1:3], 16)
        green = int(value[3:5], 16)
        blue = int(value[5:7], 16)
    except Exception:
        return "#3a3a3a"
    luminance = (0.299 * red) + (0.587 * green) + (0.114 * blue)
    return "#101010" if luminance > 150 else "#f7f7f7"


def show_feedback_preview(ease: int = 3, *, period_ms: int = 900) -> None:
    if not is_king_answer_feedback_enabled():
        return

    label, color = _label_for_ease(int(ease))
    bottom_web = getattr(mw, "bottomWeb", None)
    if bottom_web is None:
        return
    _apply_bottom_bar_container_height()

    payload = {
        "label": label,
        "background": color,
        "color": _contrast_text_color(color),
        "width": king_answer_feedback_width(),
        "height": king_answer_button_height(),
        "radius": 15,
        "fontSize": king_answer_feedback_font_size(),
        "period": int(period_ms),
        "showAnswerWidth": 530,
    }
    bottom_web.eval(
        """
        (() => {
          const data = %s;
          const old = document.getElementById("pocketKnifeAnswerFeedback");
          if (old) old.remove();
          const showAnswer = document.querySelector("#ansbut");
          const middle = document.querySelector("#middle");
          const firstButton = document.querySelector("#middle button");
          if (showAnswer) {
            const showRect = showAnswer.getBoundingClientRect();
            window.pocketKnifeShowAnswerAnchor = {
              centerX: showRect.left + (showRect.width / 2),
              top: showRect.top
            };
          }
          const savedAnchor = window.pocketKnifeShowAnswerAnchor || null;
          const fallbackAnchor = middle || firstButton || document.body;
          const fallbackRect = fallbackAnchor.getBoundingClientRect();
          const centerX = savedAnchor
            ? savedAnchor.centerX
            : fallbackRect.left + (fallbackRect.width / 2);
          const top = savedAnchor
            ? savedAnchor.top
            : Math.max(0, window.innerHeight - data.height - 6);
          const el = document.createElement("div");
          el.id = "pocketKnifeAnswerFeedback";
          el.textContent = data.label;
          Object.assign(el.style, {
            position: "fixed",
            left: `${centerX}px`,
            top: `${top}px`,
            transform: "translateX(-50%%)",
            width: `${data.width}px`,
            maxWidth: "calc(100vw - 24px)",
            height: `${data.height}px`,
            lineHeight: `${data.height}px`,
            boxSizing: "border-box",
            textAlign: "center",
            pointerEvents: "none",
            zIndex: "2147483647",
            border: "solid 1px rgba(100, 100, 100, 0.2)",
            borderTop: "solid 0.5px #878787",
            borderRadius: `${data.radius}px`,
            background: data.background,
            color: data.color,
            fontSize: `${data.fontSize}px`,
            fontWeight: "700",
            boxShadow: "0px 0px 1.5px .2px #000000",
            webkitBoxShadow: "0px 0px 1.5px .2px #000000",
            overflow: "hidden",
            whiteSpace: "nowrap",
            textOverflow: "ellipsis"
          });
          document.body.appendChild(el);
          window.clearTimeout(window.pocketKnifeAnswerFeedbackTimer);
          window.pocketKnifeAnswerFeedbackTimer = window.setTimeout(() => el.remove(), data.period);
        })();
        """
        % json.dumps(payload)
    )


def _on_reviewer_did_answer_card(_reviewer: Any, _card: Any, ease: int) -> None:
    show_feedback_preview(int(ease))


def _on_theme_did_change() -> None:
    _refresh_bottom_bar_styles()


def install() -> None:
    global _HOOKS_REGISTERED
    if _HOOKS_REGISTERED:
        return
    gui_hooks.webview_will_set_content.append(_on_webview_will_set_content)
    if hasattr(gui_hooks, "theme_did_change"):
        gui_hooks.theme_did_change.append(_on_theme_did_change)
    if hasattr(gui_hooks, "reviewer_did_answer_card"):
        gui_hooks.reviewer_did_answer_card.append(_on_reviewer_did_answer_card)
    _HOOKS_REGISTERED = True
