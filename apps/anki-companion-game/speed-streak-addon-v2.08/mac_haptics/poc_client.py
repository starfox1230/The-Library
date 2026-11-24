from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any


PATTERNS = (
    (
        "strong-left / weak-right pulse",
        [{"duration": 250, "weak": 0.35, "strong": 1.0}],
    ),
    (
        "balanced double pulse",
        [
            {"duration": 140, "weak": 0.7, "strong": 0.7},
            {"duration": 90, "weak": 0.0, "strong": 0.0},
            {"duration": 180, "weak": 0.8, "strong": 0.8},
        ],
    ),
    (
        "weak-right / strong-left contrast",
        [
            {"duration": 220, "weak": 1.0, "strong": 0.2},
            {"duration": 100, "weak": 0.0, "strong": 0.0},
            {"duration": 220, "weak": 0.2, "strong": 1.0},
        ],
    ),
)


def _reader(process: subprocess.Popen[str], messages: list[dict[str, Any]]) -> None:
    assert process.stdout is not None
    for line in process.stdout:
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            print(f"helper output: {line.rstrip()}")
            continue
        messages.append(message)
        print(json.dumps(message, indent=2, sort_keys=True))


def _send(process: subprocess.Popen[str], payload: dict[str, Any]) -> None:
    assert process.stdin is not None
    process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
    process.stdin.flush()


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: poc_client.py /path/to/SpeedStreakHaptics", file=sys.stderr)
        return 2

    executable = Path(sys.argv[1]).resolve()
    if not executable.is_file():
        print(f"Helper executable not found: {executable}", file=sys.stderr)
        return 2

    process = subprocess.Popen(
        [str(executable)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    messages: list[dict[str, Any]] = []
    reader = threading.Thread(target=_reader, args=(process, messages), daemon=True)
    reader.start()

    try:
        time.sleep(0.75)
        _send(process, {"command": "status", "id": "poc-status"})
        time.sleep(0.5)
        statuses = [message for message in messages if message.get("event") == "status"]
        if not statuses or int(statuses[-1].get("hapticControllerCount", 0)) < 1:
            print(
                "No haptics-capable controller is visible to Apple's GameController framework.",
                file=sys.stderr,
            )
            return 1

        for label, steps in PATTERNS:
            print(f"\nPlaying: {label}")
            _send(
                process,
                {
                    "command": "play",
                    "id": str(uuid.uuid4()),
                    "steps": steps,
                },
            )
            duration = sum(float(step["duration"]) for step in steps) / 1_000.0
            time.sleep(duration + 0.7)
        return 0
    finally:
        if process.poll() is None:
            try:
                _send(process, {"command": "shutdown", "id": "poc-shutdown"})
                process.wait(timeout=2)
            except Exception:
                process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
