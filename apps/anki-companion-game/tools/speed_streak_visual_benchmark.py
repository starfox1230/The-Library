from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView


COLOR_SEQUENCE = ["green", "blue", "green", "yellow", "blue", "green", "red", "blue", "green", "yellow"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one reproducible Speed Streak visual benchmark case.")
    parser.add_argument("--addon-root", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--visual-mode", default="sphere")
    parser.add_argument("--sphere-mode", default="classic")
    parser.add_argument("--render-mode", default="webgl")
    parser.add_argument("--streak", type=int, default=50)
    parser.add_argument("--crystal-rotation", type=int, choices=(0, 1), default=1)
    parser.add_argument("--orbit-animation", type=int, choices=(0, 1), default=1)
    parser.add_argument("--visuals-enabled", type=int, choices=(0, 1), default=1)
    parser.add_argument("--timer-active", type=int, choices=(0, 1), default=0)
    parser.add_argument("--gameplay-mode", choices=("time_boost", "legacy_points"), default="time_boost")
    parser.add_argument("--effect", choices=("none", "milestone", "charge"), default="none")
    parser.add_argument("--warmup", type=float, default=3.0)
    parser.add_argument("--duration", type=float, default=6.0)
    parser.add_argument("--ready-file", type=Path, required=True)
    parser.add_argument("--result-file", type=Path, required=True)
    parser.add_argument("--width", type=int, default=336)
    parser.add_argument("--height", type=int, default=760)
    return parser.parse_args()


def build_state(args: argparse.Namespace) -> dict[str, object]:
    streak = max(0, args.streak)
    colors = [COLOR_SEQUENCE[index % len(COLOR_SEQUENCE)] for index in range(streak)]
    now_ms = int(time.time() * 1000)
    timer_active = bool(args.timer_active)
    return {
        "enabled": True,
        "displayMode": "compatibility",
        "visualMode": args.visual_mode,
        "sphereMode": args.sphere_mode,
        "renderMode": args.render_mode,
        "visualsEnabled": bool(args.visuals_enabled),
        "orbitAnimationEnabled": bool(args.orbit_animation),
        "crystalRotationEnabled": bool(args.crystal_rotation),
        "paused": False,
        "appearanceMode": "midnight",
        "sidebarBackground": "#08090c",
        "satelliteColors": colors,
        "customColors": {},
        "streak": streak,
        "score": 0,
        "streakMultiplier": 1,
        "gameplayMode": args.gameplay_mode,
        "boostCharges": 2,
        "maxBoostCharges": 3,
        "boostChargeProgress": 6,
        "cardsPerBoostCharge": 10,
        "boostSeconds": 10,
        "noPauseMode": False,
        "noUndoMode": False,
        "showFocusModeToggles": True,
        "shortcutBindings": {"pause": "P", "unpause": "U", "boost": "C"},
        "phase": "question" if timer_active else "idle",
        "phaseStartEpochMs": now_ms if timer_active else 0,
        "phaseLimitMs": 3_600_000 if timer_active else 0,
        "phaseBaseLimitMs": 3_600_000 if timer_active else 0,
        "timerDisplayRemainingMs": 3_000_000 if timer_active else 0,
        "timerDisplayNowEpochMs": now_ms,
        "timerPolicyMode": "normal",
        "firstCardFree": False,
        "eventNonce": 1,
        "lastEventType": "",
        "lastEventText": "",
        "lastSatelliteColor": colors[-1] if colors else "green",
        "audioEnabled": False,
        "hapticsEnabled": False,
        "sidePanelEnabled": True,
        "inlineSide": "left",
        "windowPositionPresets": [],
    }


def main() -> int:
    args = parse_args()
    addon_root = args.addon_root.resolve()
    css_path = addon_root / "web" / "overlay.css"
    js_path = addon_root / "web" / "overlay.js"
    if not css_path.exists() or not js_path.exists():
        raise FileNotFoundError(f"Missing overlay assets under {addon_root}")

    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-background-timer-throttling")
    app = QApplication(sys.argv)
    view = QWebEngineView()
    view.resize(args.width, args.height)
    view.setWindowTitle(f"Speed Streak benchmark — {args.case}")
    view.move(40, 40)

    css_url = QUrl.fromLocalFile(str(css_path)).toString()
    js_url = QUrl.fromLocalFile(str(js_path)).toString()
    state_json = json.dumps(build_state(args), separators=(",", ":"))
    html = f"""<!doctype html>
<html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<link rel=\"stylesheet\" href=\"{css_url}\">
<style>html,body{{width:100%;height:100%;margin:0;overflow:hidden;background:#08090c}}.speed-streak-sidebar{{inset:10px}}</style>
</head><body>
<script>
window.pycmd=function(){{}};
window.__benchmarkRafCallbacks=0;
window.__benchmarkRawRaf=window.requestAnimationFrame.bind(window);
window.requestAnimationFrame=function(callback){{
  return window.__benchmarkRawRaf(function(timestamp){{window.__benchmarkRafCallbacks+=1;callback(timestamp);}});
}};
</script>
<script src=\"{js_url}\"></script>
<script>window.SpeedStreak.receiveState({state_json});</script>
</body></html>"""

    result: dict[str, object] = {
        "case": args.case,
        "addon_root": str(addon_root),
        "visual_mode": args.visual_mode,
        "sphere_mode": args.sphere_mode,
        "render_mode": args.render_mode,
        "streak": args.streak,
        "duration_s": args.duration,
    }
    measurement_started = 0.0

    def write_failure(message: str) -> None:
        args.result_file.parent.mkdir(parents=True, exist_ok=True)
        args.result_file.write_text(json.dumps({**result, "error": message}, indent=2), encoding="utf-8")
        app.quit()

    def finish_measurement() -> None:
        elapsed = max(0.001, time.perf_counter() - measurement_started)
        script = """(() => {
          const glCanvas = document.querySelector('canvas');
          let gpu = {};
          if (glCanvas) {
            const gl = glCanvas.getContext('webgl') || glCanvas.getContext('experimental-webgl');
            if (gl) {
              const ext = gl.getExtension('WEBGL_debug_renderer_info');
              gpu = {
                vendor: ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR),
                renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
              };
            }
          }
          return {
            rafCallbacks: window.__benchmarkRafCallbacks || 0,
            canvases: document.querySelectorAll('canvas').length,
            domSatellites: document.querySelectorAll('.acg-satellite').length,
            milestoneRings: document.querySelectorAll('.acg-milestone-ring').length,
            fusionRows: document.querySelectorAll('.acg-fusion-live-ring').length,
            gpu,
          };
        })()"""

        def got_metrics(metrics: object) -> None:
            payload = metrics if isinstance(metrics, dict) else {}
            result.update(payload)
            result["elapsed_s"] = elapsed
            result["raf_callbacks_per_s"] = float(payload.get("rafCallbacks", 0) or 0) / elapsed
            args.result_file.parent.mkdir(parents=True, exist_ok=True)
            args.result_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
            app.quit()

        view.page().runJavaScript(script, got_metrics)

    def begin_measurement() -> None:
        nonlocal measurement_started
        measurement_started = time.perf_counter()
        next_state = build_state(args)
        if args.effect == "milestone":
            next_streak = max(50, ((max(0, args.streak) + 1 + 49) // 50) * 50)
            next_state["streak"] = next_streak
            next_state["satelliteColors"] = [
                COLOR_SEQUENCE[index % len(COLOR_SEQUENCE)] for index in range(next_streak)
            ]
            next_state["eventNonce"] = 2
            next_state["lastEventType"] = "good"
            next_state["lastEventText"] = f"Good: streak {next_streak}"
            next_state["lastSatelliteColor"] = next_state["satelliteColors"][-1]
        elif args.effect == "charge":
            next_state["eventNonce"] = 2
            next_state["lastEventType"] = "time-boost"
            next_state["lastEventText"] = "Time Boost: +10s | 1 charge left."
            next_state["boostCharges"] = 1

        command = "window.__benchmarkRafCallbacks=0;"
        if args.effect != "none":
            command += f"window.SpeedStreak.receiveState({json.dumps(next_state, separators=(',', ':'))});"

        def effect_started(_: object) -> None:
            args.ready_file.parent.mkdir(parents=True, exist_ok=True)
            args.ready_file.write_text(json.dumps({"pid": os.getpid(), "case": args.case}), encoding="utf-8")
            QTimer.singleShot(max(1, int(args.duration * 1000)), finish_measurement)

        view.page().runJavaScript(command, effect_started)

    def loaded(ok: bool) -> None:
        if not ok:
            write_failure("QWebEngine failed to load benchmark HTML")
            return
        QTimer.singleShot(max(1, int(args.warmup * 1000)), begin_measurement)

    view.loadFinished.connect(loaded)
    view.setHtml(html, QUrl.fromLocalFile(str(addon_root) + os.sep))
    view.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
