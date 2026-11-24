"""Bounded, local evidence collection; never controls audio or haptics."""
from __future__ import annotations

import atexit
from collections import deque
from datetime import datetime, timezone
import functools
import json
import os
from pathlib import Path
import platform
import re
import signal
import sys
import threading
import time
import uuid


SCHEMA = 1
MAX_BYTES = 256 * 1024
KEEP_SESSIONS = 4
REPORT_LINES = 160
TOKEN = re.compile(r"^[a-zA-Z0-9_.:+-]{1,100}$")
_recorder = None
_attached = False


def _pid_alive(pid):
    if os.name == "nt":
        # os.kill(..., 0) is NOT a safe liveness probe on Windows.
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return ctypes.get_last_error() not in {87, 1168}
        try:
            code = wintypes.DWORD()
            return not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except OSError:
        return True


class SessionRecorder:
    def __init__(self, directory, build, *, max_bytes=MAX_BYTES):
        self.directory = Path(directory)
        self.build = str(build)
        self.session = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:12]
        self.path = self.directory / ("session-" + self.session + ".jsonl")
        self.meta_path = self.path.with_suffix(".state.json")
        self.max_bytes = max_bytes
        self.started = time.monotonic()
        self.lock = threading.RLock()
        self.last_error = ""
        self.stage = "running"
        self.browser_window = 0.0
        self.browser_count = 0
        self.sequence = 0
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            self._prune()
            self._metadata()
        except Exception as error:
            self.last_error = type(error).__name__
        self.record("session_start", python=platform.python_version(), os=platform.system(),
                    os_release=platform.release(), machine=platform.machine(),
                    sigpipe_disposition=("ignored" if signal.getsignal(signal.SIGPIPE) == signal.SIG_IGN
                                         else "default" if signal.getsignal(signal.SIGPIPE) == signal.SIG_DFL
                                         else "custom") if hasattr(signal, "SIGPIPE") else "not-applicable")

    def _prune(self):
        metadata = sorted(self.directory.glob("session-*.state.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for path in metadata[KEEP_SESSIONS - 1:]:
            try:
                meta = json.loads(path.read_text(encoding="utf-8"))
                # Never remove another live Anki session's files.
                pid = int(meta.get("pid", 0))
                if pid > 0 and meta.get("stage") != "python_exit_observed" and _pid_alive(pid):
                    continue
                stem = path.name.removesuffix(".state.json")
                for suffix in (".jsonl", ".jsonl.1", ".state.json"):
                    (self.directory / (stem + suffix)).unlink(missing_ok=True)
            except Exception:
                continue

    def _metadata(self):
        payload = dict(schema=SCHEMA, session=self.session, build=self.build, pid=os.getpid(),
                       stage=self.stage, started_utc=self.session.split("-")[0])
        temporary = self.meta_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload), encoding="utf-8")
        temporary.replace(self.meta_path)

    def record(self, event, **details):
        """Close/flush each append; failures never propagate into Anki."""
        try:
            with self.lock:
                self.sequence += 1
                payload = dict(schema=SCHEMA, utc=datetime.now(timezone.utc).isoformat(),
                               elapsed_ms=round((time.monotonic() - self.started) * 1000),
                               pid=os.getpid(), thread=threading.get_ident(), build=self.build,
                               session=self.session, seq=self.sequence, event=event, details=details)
                line = json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n"
                if len(line.encode()) > 4096:
                    return
                if self.path.exists() and self.path.stat().st_size + len(line) > self.max_bytes:
                    self.path.replace(Path(str(self.path) + ".1"))
                with self.path.open("a", encoding="utf-8") as stream:
                    stream.write(line)
                self.last_error = ""
        except Exception as error:
            self.last_error = type(error).__name__

    def mark(self, stage):
        with self.lock:
            self.stage = stage
            self.record(stage)
            try:
                self._metadata()
            except Exception as error:
                self.last_error = type(error).__name__

    def browser_event(self, payload):
        # Browser data is untrusted. Only short enum-like tokens/numbers survive.
        if not isinstance(payload, dict):
            return
        event = payload.get("event")
        if not isinstance(event, str) or not TOKEN.fullmatch(event):
            return
        with self.lock:
            now = time.monotonic()
            if now - self.browser_window > 1:
                self.browser_window, self.browser_count = now, 0
            self.browser_count += 1
            if self.browser_count > 30:
                return
            allowed = {}
            for key in ("page", "hidden", "connected", "count", "index", "duration", "result", "error", "channel"):
                value = payload.get(key)
                if isinstance(value, (bool, int, float)):
                    allowed[key] = value
                elif isinstance(value, str) and TOKEN.fullmatch(value):
                    allowed[key] = value
            self.record("browser:" + event, **allowed)

    def report(self):
        with self.lock:
            heading = ["Speed Streak support report v1", "Build: " + self.build,
                       "Current session: " + self.session,
                       "This is diagnostic evidence, not a crash diagnosis.",
                       "Missing exit markers can mean a crash, force quit, power loss, or logging failure.",
                       "Shutdown/exit markers show callbacks ran; they do not prove the process exited normally.",
                       "Requests/accepted results do not confirm audible sound or physical vibration.",
                       "Logging error: " + (self.last_error or "none"), ""]
            try:
                metadata = sorted(self.directory.glob("session-*.state.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                current = self.meta_path
                previous = next((p for p in metadata if p != current), None)
                # Previous session comes first so copying soon after a restart preserves its tail.
                for meta in ([previous] if previous else []) + [current]:
                    data = json.loads(meta.read_text(encoding="utf-8"))
                    heading.append("SESSION " + json.dumps(data, sort_keys=True))
                    base = self.directory / (meta.name.removesuffix(".state.json") + ".jsonl")
                    tail = deque(maxlen=REPORT_LINES)
                    for path in (Path(str(base) + ".1"), base):
                        if path.exists():
                            with path.open(encoding="utf-8") as stream:
                                tail.extend(line.rstrip() for line in stream)
                    retained = deque()
                    size = 0
                    for line in reversed(tail):
                        if size + len(line) > 40000:
                            break
                        retained.appendleft(line)
                        size += len(line)
                    heading.extend(retained)
            except Exception as error:
                heading.append("Report read error: " + type(error).__name__)
            return "\n".join(heading)


def record(event, **details):
    if _recorder is not None:
        _recorder.record(event, **details)


def start(build):
    global _recorder
    if _recorder is not None:
        return
    try:
        from aqt import mw
        base = getattr(getattr(mw, "pm", None), "base", None)
        if not base:
            # Avoid putting evidence in addons21 where reinstalling replaces it.
            if sys.platform == "darwin":
                base = Path.home() / "Library/Application Support/Anki2"
            elif sys.platform.startswith("win"):
                base = Path(os.environ.get("APPDATA", str(Path.home()))) / "Anki2"
            else:
                base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "Anki2"
        _recorder = SessionRecorder(Path(base) / "addons-data/speed_streak/diagnostics", build)
        atexit.register(lambda: _recorder.mark("python_exit_observed"))
    except Exception:
        pass


def support_report():
    if _recorder is None:
        return "Speed Streak diagnostic logging did not initialize."
    return _recorder.report()


def copy_support_report(*_args):
    from aqt.qt import QApplication
    from aqt.utils import tooltip
    QApplication.clipboard().setText(support_report())
    tooltip("Speed Streak support report copied. Paste it into your bug report.")


def _state(controller):
    state = controller.engine.state
    bridge = getattr(controller.haptics, "_mac", None)
    process = getattr(bridge, "_process", None)
    return dict(phase=str(getattr(state, "phase", "idle")),
                haptics_enabled=bool(state.haptics_enabled), audio_enabled=bool(state.audio_enabled),
                countdown_enabled=bool(state.countdown_audio_enabled),
                display_mode=str(controller.display_mode), visual_mode=str(controller.visual_mode),
                audio_policy="browser-only" if sys.platform == "darwin" else "native-and-browser",
                helper_pid=getattr(process, "pid", None),
                pyobjc_enabled=bool(getattr(getattr(controller.haptics, "_mac_pyobjc", None), "_native_backend_enabled", False)),
                audio_backend=str(controller.audio_feedback.last_playback_backend))


def _wrap(instance, method, event, details=None):
    original = getattr(instance, method, None)
    if not callable(original):
        return
    @functools.wraps(original)
    def observed(*args, **kwargs):
        try:
            info = details(args, kwargs) if details else {}
        except Exception:
            info = {}
        record(event + ":request", **info)
        try:
            result = original(*args, **kwargs)
        except BaseException as error:
            record(event + ":exception", error=type(error).__name__)
            raise
        record(event + ":returned", result=result if isinstance(result, (bool, int)) else "returned")
        return result
    setattr(instance, method, observed)


def attach(controller):
    """Observe existing operations and official hooks without changing sequencing."""
    global _attached
    if _attached or _recorder is None:
        return
    _attached = True
    try:
        from aqt import gui_hooks, mw
        from aqt.qt import QApplication, QAction, QTimer
        from aqt.reviewer import Reviewer
        from anki import version as anki_version
        from aqt.qt import qVersion
        record("controller_attached", anki=str(anki_version), qt=qVersion(),
               **_state(controller))
        script = Path(__file__).with_name("diagnostic_browser.js").read_text(encoding="utf-8")
        bootstrap = controller._audio_feedback_bootstrap.replace(
            "const audio = new Audio();",
            "const audio = new Audio(); window.SpeedStreakDiagnostic.observeAudio(audio);")
        controller._audio_feedback_bootstrap = script + "\n" + bootstrap
        original_html = controller._sidebar_html
        def sidebar_html():
            html = original_html()
            # Insert before overlay startup, preserving its original script order.
            return html.replace("<head>", "<head><script>" + script + "</script>", 1)
        controller._sidebar_html = sidebar_html
        def web_content(content, context):
            if isinstance(context, Reviewer):
                content.head += "<script>" + script + "</script>"
        gui_hooks.webview_will_set_content.append(web_content)

        prefix = "speed-streak:diagnostic:"
        def browser_message(handled, message, context):
            if not isinstance(message, str) or not message.startswith(prefix):
                return handled
            if len(message) <= 2048:
                try:
                    _recorder.browser_event(json.loads(message[len(prefix):]))
                except Exception:
                    pass
            return (True, None)
        gui_hooks.webview_did_receive_js_message.append(browser_message)

        for method, event in (("_play_review_web_audio_feedback", "browser_audio"),
                              ("_stop_web_audio_feedback", "browser_audio_stop"),
                              ("_play_haptic_feedback", "haptics"),
                              ("preview_haptic_pattern", "haptics_preview")):
            def details(args, kwargs, name=event):
                # No source paths, uploaded filenames, card text, or deck names.
                data = {"channel": str(kwargs.get("channel", "feedback"))}
                if name in {"haptics", "haptics_preview"} and args:
                    data["pattern"] = str(args[0]) if TOKEN.fullmatch(str(args[0])) else "custom"
                return data
            _wrap(controller, method, event, details)

        def snapshot(event, *_args):
            try:
                record(event, **_state(controller))
            except Exception as error:
                record("snapshot_failure", error=type(error).__name__)
        for hook, event in (("profile_did_open", "profile_open"), ("profile_will_close", "profile_close"),
                            ("reviewer_did_show_question", "question_shown"),
                            ("reviewer_did_show_answer", "answer_shown"),
                            ("reviewer_did_answer_card", "card_answered")):
            target = getattr(gui_hooks, hook, None)
            if target is not None:
                target.append(functools.partial(snapshot, event))
        gui_hooks.state_did_change.append(lambda new, old: record("navigation", new=str(new), old=str(old)))
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(lambda: _recorder.mark("qt_about_to_quit"))
            app.applicationStateChanged.connect(lambda state: record("app_state", state=str(state)))
        timer = QTimer(mw)
        timer.setInterval(30000)
        timer.timeout.connect(functools.partial(snapshot, "heartbeat"))
        timer.start()
        controller._diagnostic_timer = timer
        menu = getattr(controller, "_menu", None)
        if menu is not None:
            menu.addSeparator()
            action = menu.addAction("Copy Support Report")
            action.setMenuRole(QAction.MenuRole.NoRole)
            action.triggered.connect(copy_support_report)
        record("diagnostics_ready")
    except Exception as error:
        record("diagnostic_setup_failure", error=type(error).__name__)
