from __future__ import annotations

import json
import logging
import stat
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional

from .feedback_catalog import HAPTIC_PATTERN_LIBRARY

LOGGER = logging.getLogger(__name__)
MAC_HAPTICS_PROTOCOL_VERSION = 1


class MacHapticsBridge:
    """Automatic macOS GameController helper transport.

    A packaged helper is allowed to start even when no controller is attached so
    controller-free diagnostics can validate the native delivery path. Native
    output is selected only after the helper completes the protocol handshake
    and Apple's GameController framework reports a haptics-capable controller.
    The physical-test marker is retained as diagnostic evidence, not a launch
    gate.
    """

    def __init__(
        self,
        addon_root: Path,
        *,
        process_factory: Callable[..., subprocess.Popen[str]] = subprocess.Popen,
    ) -> None:
        self._root = Path(addon_root)
        self._process_factory = process_factory
        self._process: Optional[subprocess.Popen[str]] = None
        self._write_lock = threading.Lock()
        self._state_lock = threading.RLock()
        self._ready = threading.Event()
        self._status_received = threading.Event()
        self._launch_attempted = False
        self._shutdown_requested = False
        self._restart_pending = False
        self._restart_timestamps: List[float] = []
        self._hardware_validated = False
        self._validation_payload: Dict[str, Any] = {}
        self._controller_count = 0
        self._haptic_controller_count = 0
        self._controllers: List[Dict[str, Any]] = []
        self._last_error = ""
        self._stderr_tail: List[str] = []
        self._message_tail: List[Dict[str, Any]] = []
        self._ready_payload: Dict[str, Any] = {}
        self._last_status_payload: Dict[str, Any] = {}
        self._last_play_result: Dict[str, Any] = {}
        self._started_at = 0.0
        self._hardware_validated, self._validation_payload = self._read_hardware_validation()
        self._start_if_present()

    @property
    def available(self) -> bool:
        with self._state_lock:
            return bool(self.transport_ready and self._haptic_controller_count > 0)

    @property
    def transport_ready(self) -> bool:
        with self._state_lock:
            return bool(
                self._process is not None
                and self._process.poll() is None
                and self._ready.is_set()
            )

    @property
    def backend_name(self) -> str:
        if not sys.platform.startswith("darwin"):
            return "not-macos"
        if self.available:
            return "native-macos-gamecontroller"
        if self.transport_ready:
            return "browser-fallback-native-monitoring"
        return "browser-fallback-native-unavailable"

    @property
    def diagnostics(self) -> Dict[str, Any]:
        executable = self._helper_executable()
        bundle = self._helper_bundle()
        with self._state_lock:
            process_running = self._process is not None and self._process.poll() is None
            return {
                "backend": self.backend_name,
                "automaticSelection": True,
                "nativeOutputActive": bool(self.available),
                "hardwareValidated": bool(self._hardware_validated),
                "hardwareValidation": dict(self._validation_payload),
                "helperBundlePath": str(bundle),
                "helperPath": str(executable),
                "helperBundleExists": bool(bundle.is_dir()),
                "helperExists": bool(executable.is_file()),
                "launchAttempted": bool(self._launch_attempted),
                "helperRunning": bool(process_running),
                "protocolReady": bool(self._ready.is_set()),
                "statusReceived": bool(self._status_received.is_set()),
                "controllerCount": int(self._controller_count),
                "hapticControllerCount": int(self._haptic_controller_count),
                "controllers": [dict(controller) for controller in self._controllers],
                "readyPayload": dict(self._ready_payload),
                "lastStatus": dict(self._last_status_payload),
                "lastPlayResult": dict(self._last_play_result),
                "lastError": self._last_error,
                "stderrTail": list(self._stderr_tail),
                "messageTail": [dict(message) for message in self._message_tail],
                "automaticRestartCount": len(self._restart_timestamps),
                "helperUptimeSeconds": (
                    max(0.0, time.monotonic() - self._started_at)
                    if process_running and self._started_at
                    else 0.0
                ),
            }

    def refresh_status(self, timeout: float = 1.25) -> bool:
        """Request a fresh status event and wait briefly for diagnostics."""

        if not self.transport_ready:
            return False
        self._status_received.clear()
        request_id = f"diagnostic-status-{uuid.uuid4()}"
        if not self._send({"command": "status", "id": request_id}):
            return False
        return self._status_received.wait(timeout=max(0.0, min(5.0, float(timeout))))

    def play_pattern(self, pattern_key: str) -> bool:
        meta = HAPTIC_PATTERN_LIBRARY.get(str(pattern_key or "").strip())
        if not isinstance(meta, Mapping):
            return False
        raw_steps = meta.get("sequence", [])
        if not isinstance(raw_steps, list):
            return False
        return self.play_sequence(raw_steps)

    def play_sequence(self, raw_steps: List[Mapping[str, Any]]) -> bool:
        if not self.available:
            return False
        steps: List[Dict[str, float]] = []
        for raw_step in raw_steps:
            try:
                duration = max(0.0, min(10_000.0, float(raw_step.get("duration", 0) or 0)))
                weak = max(0.0, min(1.0, float(raw_step.get("weak", 0) or 0)))
                strong = max(0.0, min(1.0, float(raw_step.get("strong", 0) or 0)))
            except (TypeError, ValueError):
                continue
            steps.append({"duration": duration, "weak": weak, "strong": strong})
        if not steps:
            return False
        return self._send(
            {
                "command": "play",
                "id": str(uuid.uuid4()),
                "steps": steps,
            }
        )

    def stop(self) -> None:
        self._send({"command": "stop", "id": str(uuid.uuid4())})

    def shutdown(self) -> None:
        process = self._process
        if process is None:
            return
        self._shutdown_requested = True
        try:
            self._send({"command": "shutdown", "id": str(uuid.uuid4())})
            process.wait(timeout=1.5)
        except Exception:
            try:
                process.terminate()
            except Exception:
                pass
        finally:
            with self._state_lock:
                self._process = None
                self._controller_count = 0
                self._haptic_controller_count = 0
                self._ready.clear()
                self._status_received.clear()

    def _start_if_present(self) -> None:
        if not sys.platform.startswith("darwin"):
            return

        executable = self._helper_executable()
        if not executable.is_file():
            self._set_error(
                "Native macOS helper is not packaged. Browser haptics remain the automatic fallback."
            )
            return

        self._launch_attempted = True
        self._shutdown_requested = False
        try:
            # Anki's add-on extraction may not preserve the executable bit. This
            # is automatic and does not require an administrator or user command.
            current_mode = executable.stat().st_mode
            executable.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            process = self._process_factory(
                [str(executable)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            self._set_error(f"Could not launch native macOS haptics helper: {exc}")
            return

        with self._state_lock:
            self._process = process
            self._started_at = time.monotonic()
        threading.Thread(target=self._read_stdout, args=(process,), daemon=True).start()
        threading.Thread(target=self._read_stderr, args=(process,), daemon=True).start()
        self._send({"command": "status", "id": "startup-status"})

    def _read_hardware_validation(self) -> tuple[bool, Dict[str, Any]]:
        marker = self._root / "mac_haptics" / "POC_VALIDATED.json"
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except Exception:
            return False, {}
        if not isinstance(payload, Mapping):
            return False, {}
        normalized = dict(payload)
        validated = bool(normalized.get("validated")) and int(
            normalized.get("protocolVersion", 0) or 0
        ) == MAC_HAPTICS_PROTOCOL_VERSION
        return validated, normalized

    def _helper_bundle(self) -> Path:
        return self._root / "mac_haptics" / "SpeedStreakHaptics.app"

    def _helper_executable(self) -> Path:
        return self._helper_bundle() / "Contents" / "MacOS" / "SpeedStreakHaptics"

    def _send(self, payload: Mapping[str, Any]) -> bool:
        process = self._process
        if process is None or process.poll() is not None or process.stdin is None:
            return False
        try:
            line = json.dumps(dict(payload), separators=(",", ":"), ensure_ascii=True)
            with self._write_lock:
                process.stdin.write(line + "\n")
                process.stdin.flush()
            return True
        except Exception as exc:
            self._set_error(f"Native helper IPC write failed: {exc}")
            return False

    def _read_stdout(self, process: subprocess.Popen[str]) -> None:
        if process.stdout is None:
            return
        try:
            for line in process.stdout:
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    self._set_error("Native helper emitted invalid JSON.")
                    continue
                self._handle_message(payload)
        except Exception as exc:
            self._set_error(f"Native helper stdout failed: {exc}")
        finally:
            return_code = process.poll()
            should_restart = False
            with self._state_lock:
                self._controller_count = 0
                self._haptic_controller_count = 0
                self._ready.clear()
                should_restart = not self._shutdown_requested and return_code is not None
                if should_restart:
                    self._last_error = f"Native helper exited unexpectedly with status {return_code}."
            if should_restart:
                self._schedule_restart(process)
            elif not self._shutdown_requested:
                self._schedule_exit_check(process)

    def _read_stderr(self, process: subprocess.Popen[str]) -> None:
        if process.stderr is None:
            return
        try:
            for line in process.stderr:
                text = line.strip()
                if not text:
                    continue
                with self._state_lock:
                    self._stderr_tail = (self._stderr_tail + [text])[-20:]
        except Exception:
            return

    def _handle_message(self, payload: Any) -> None:
        if not isinstance(payload, Mapping):
            return
        normalized = dict(payload)
        event = str(normalized.get("event", ""))
        with self._state_lock:
            self._message_tail = (self._message_tail + [normalized])[-20:]
        if event == "ready":
            version = int(normalized.get("protocolVersion", 0) or 0)
            if version != MAC_HAPTICS_PROTOCOL_VERSION:
                self._set_error(
                    f"Native helper protocol mismatch: expected {MAC_HAPTICS_PROTOCOL_VERSION}, got {version}."
                )
                return
            with self._state_lock:
                self._ready_payload = normalized
                self._last_error = ""
            self._ready.set()
            return
        if event == "status":
            controllers = normalized.get("controllers", [])
            with self._state_lock:
                self._controller_count = max(0, int(normalized.get("controllerCount", 0) or 0))
                self._haptic_controller_count = max(
                    0, int(normalized.get("hapticControllerCount", 0) or 0)
                )
                self._controllers = [
                    dict(controller)
                    for controller in controllers
                    if isinstance(controller, Mapping)
                ]
                self._last_status_payload = normalized
            self._status_received.set()
            return
        if event == "playResult":
            with self._state_lock:
                self._last_play_result = normalized
            return
        if event == "error":
            self._set_error(
                str(normalized.get("message") or normalized.get("code") or "Unknown helper error")
            )

    def _schedule_restart(self, failed_process: subprocess.Popen[str]) -> None:
        with self._state_lock:
            if self._shutdown_requested or self._restart_pending:
                return
            now = time.monotonic()
            self._restart_timestamps = [
                stamp for stamp in self._restart_timestamps if now - stamp < 60.0
            ]
            if len(self._restart_timestamps) >= 3:
                self._last_error = "Native helper restart limit reached after three failures in one minute."
                return
            self._restart_timestamps.append(now)
            self._restart_pending = True

        def restart() -> None:
            with self._state_lock:
                self._restart_pending = False
                if self._shutdown_requested:
                    return
                if self._process is failed_process:
                    self._process = None
                self._status_received.clear()
            self._start_if_present()

        timer = threading.Timer(1.0, restart)
        timer.daemon = True
        timer.start()

    def _schedule_exit_check(self, process: subprocess.Popen[str]) -> None:
        """Cover the short race where stdout closes just before process exit."""

        def check() -> None:
            return_code = process.poll()
            if self._shutdown_requested or return_code is None:
                return
            self._set_error(f"Native helper exited unexpectedly with status {return_code}.")
            self._schedule_restart(process)

        timer = threading.Timer(0.3, check)
        timer.daemon = True
        timer.start()

    def _set_error(self, message: str) -> None:
        with self._state_lock:
            self._last_error = str(message)
        LOGGER.debug("Speed Streak macOS haptics: %s", message)
