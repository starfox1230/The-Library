"""Owns a hidden Windows loopback helper; never records or uploads audio."""
import json
import subprocess
import threading
import time
from pathlib import Path
from .beat import BeatTracker


class AudioListener:
    def __init__(self):
        self._stop = threading.Event()
        self._thread = None
        self._process = None
        self._lock = threading.Lock()
        self._state = {"status": "Not listening", "energy": 0, "bass": 0}
        self._tracker = BeatTracker()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="Afterglow audio")
        self._thread.start()

    def stop(self):
        self._stop.set()
        process = self._process
        if process:
            try:
                process.terminate()
            except OSError:
                pass
        if self._thread:
            self._thread.join(timeout=1)
        with self._lock:
            self._state = {"status": "Not listening", "energy": 0, "bass": 0}
            self._tracker = BeatTracker()

    def snapshot(self, lead_ms):
        with self._lock:
            return dict(self._state, **self._tracker.snapshot(time.monotonic(), lead_ms))

    def _run(self):
        helper = Path(__file__).parent / "loopback.exe"
        if not helper.exists():
            with self._lock:
                self._state["status"] = "Audio helper missing — run install_to_anki.ps1"
            return
        while not self._stop.is_set():
            try:
                process = subprocess.Popen([str(helper)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                           text=True, creationflags=0x08000000)
                self._process = process
                if self._stop.is_set():
                    process.terminate()
                for line in process.stdout:
                    if self._stop.is_set():
                        break
                    item = json.loads(line)
                    now = time.monotonic()
                    with self._lock:
                        if "error" in item:
                            self._state = {"status": item["error"], "energy": 0, "bass": 0}
                        else:
                            self._tracker.feed(now, item["energy"], item["bass"])
                            self._state = dict(item, status="Listening to system audio")
                process.wait(timeout=2)
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                with self._lock:
                    self._state = {"status": "Audio unavailable: " + str(exc)[:120], "energy": 0, "bass": 0}
            finally:
                if self._process:
                    try:
                        self._process.kill()
                        self._process.wait(timeout=1)
                    except (OSError, subprocess.SubprocessError):
                        pass
                    self._process = None
            self._stop.wait(2)
