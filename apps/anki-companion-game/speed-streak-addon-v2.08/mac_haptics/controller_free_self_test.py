from __future__ import annotations

import json
import platform
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _send(process: subprocess.Popen[str], payload: dict[str, Any]) -> None:
    assert process.stdin is not None
    process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
    process.stdin.flush()


def _probe(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
        output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
        return {"returnCode": result.returncode, "output": output[:6000]}
    except FileNotFoundError:
        return {"returnCode": 127, "output": "Command is not installed."}
    except Exception as exc:
        return {"returnCode": 1, "output": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("Usage: controller_free_self_test.py /path/to/SpeedStreakHaptics [report.json]", file=sys.stderr)
        return 2

    executable = Path(sys.argv[1]).resolve()
    report_path = Path(sys.argv[2]).resolve() if len(sys.argv) == 3 else executable.parents[3] / "SpeedStreakHaptics-diagnostic.json"
    if not executable.is_file():
        print(f"Helper executable not found: {executable}", file=sys.stderr)
        return 2

    bundle = executable.parents[2]
    process = subprocess.Popen(
        [str(executable)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    messages: list[dict[str, Any]] = []
    stderr_lines: list[str] = []
    message_event = threading.Event()

    def read_stdout() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                messages.append({"event": "invalidJson", "raw": line.rstrip()})
            else:
                messages.append(payload)
            message_event.set()

    def read_stderr() -> None:
        assert process.stderr is not None
        for line in process.stderr:
            stderr_lines.append(line.rstrip())

    threading.Thread(target=read_stdout, daemon=True).start()
    threading.Thread(target=read_stderr, daemon=True).start()

    def wait_for(event_name: str, timeout: float) -> dict[str, Any] | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            matches = [message for message in messages if message.get("event") == event_name]
            if matches:
                return matches[-1]
            message_event.clear()
            message_event.wait(timeout=min(0.2, max(0.0, deadline - time.monotonic())))
        return None

    ready = wait_for("ready", 3.0)
    if process.poll() is None:
        _send(process, {"command": "status", "id": "controller-free-status"})
    status = wait_for("status", 3.0)

    if process.poll() is None:
        try:
            _send(process, {"command": "shutdown", "id": "controller-free-shutdown"})
            process.wait(timeout=3)
        except Exception:
            process.kill()
            process.wait(timeout=2)

    passed = bool(
        ready
        and int(ready.get("protocolVersion", 0) or 0) == 1
        and status
        and process.returncode == 0
    )
    report = {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "macOS": platform.mac_ver()[0],
        "machine": platform.machine(),
        "python": platform.python_version(),
        "helper": str(executable),
        "ready": ready,
        "status": status,
        "processExitCode": process.returncode,
        "stderr": stderr_lines[-30:],
        "messages": messages[-30:],
        "probes": {
            "architectures": _probe(["lipo", "-archs", str(executable)]),
            "codeSignature": _probe(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(bundle)]),
            "signatureDetails": _probe(["codesign", "-dv", "--verbose=4", str(bundle)]),
            "gatekeeper": _probe(["spctl", "--assess", "--type", "execute", "--verbose=2", str(bundle)]),
            "swiftCompiler": _probe(["xcrun", "swiftc", "--version"]),
        },
        "limits": [
            "This test does not confirm physical vibration.",
            "A Gatekeeper rejection is expected for the ad-hoc local development build.",
        ],
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Controller-free native integration: {'PASS' if passed else 'FAIL'}")
    if status:
        print(f"Controllers: {status.get('controllerCount', 0)}")
        print(f"Haptics-capable controllers: {status.get('hapticControllerCount', 0)}")
    print(f"Diagnostic report: {report_path}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
