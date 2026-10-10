from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "diagnostic_logging.py"
spec = importlib.util.spec_from_file_location("diagnostic_test", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RecordingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_abrupt_process_exit_preserves_previous_session(self):
        script = """import importlib.util, os, sys
s=importlib.util.spec_from_file_location('d',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
r=m.SessionRecorder(sys.argv[2],'published-diagnostic');r.record('last_haptic_request');os._exit(42)
"""
        result = subprocess.run([sys.executable, "-B", "-c", script, str(SOURCE), str(self.root)])
        self.assertEqual(result.returncode, 42)
        current = module.SessionRecorder(self.root, "new-launch")
        report = current.report()
        self.assertIn("last_haptic_request", report)
        self.assertIn('"stage": "running"', report)
        self.assertIn("not a crash diagnosis", report)
        self.assertIn("published-diagnostic", report)
        self.assertIn("new-launch", report)

    def test_rotation_keeps_last_events_and_session_metadata(self):
        recorder = module.SessionRecorder(self.root, "build-a", max_bytes=1000)
        for number in range(30):
            recorder.record("event", number=number)
        self.assertTrue(Path(str(recorder.path) + ".1").exists())
        recorder.mark("python_exit_observed")
        report = module.SessionRecorder(self.root, "build-b").report()
        self.assertIn('"number":29', report)
        self.assertIn("python_exit_observed", report)
        self.assertIn("build-a", report)

    def test_pruning_retains_four_sessions_and_never_removes_live_sessions(self):
        with patch.object(module, "_pid_alive", return_value=False):
            for _ in range(7):
                recorder = module.SessionRecorder(self.root, "build")
                recorder.mark("python_exit_observed")
            self.assertEqual(len(list(self.root.glob("*.state.json"))), 4)
        paths = set(self.root.glob("*.state.json"))
        with patch.object(module, "_pid_alive", return_value=True):
            for path in paths:
                data = json.loads(path.read_text()); data["stage"] = "running"
                path.write_text(json.dumps(data))
            module.SessionRecorder(self.root, "concurrent")
        self.assertTrue(all(path.exists() for path in paths))

    def test_logger_failure_never_raises_into_review(self):
        blocked = self.root / "file"
        blocked.write_text("not a directory")
        recorder = module.SessionRecorder(blocked, "build")
        recorder.record("review")
        recorder.mark("qt_about_to_quit")
        self.assertTrue(recorder.last_error)
        self.assertIn("error", recorder.report().lower())

    def test_multiple_threads_write_complete_json_records(self):
        recorder = module.SessionRecorder(self.root, "build", max_bytes=100000)
        threads = [threading.Thread(target=lambda: [recorder.record("event") for _ in range(20)]) for _ in range(4)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        entries = [json.loads(line) for line in recorder.path.read_text().splitlines()]
        self.assertEqual(len(entries), 81)
        self.assertEqual(len({entry["seq"] for entry in entries}), 81)

    def test_browser_payload_filters_content_and_limits_messages(self):
        recorder = module.SessionRecorder(self.root, "build")
        for _ in range(80):
            recorder.browser_event(dict(event="script_error", error="TypeError", card="private text",
                                        url="/Users/patient/private.mp3", channel="private text"))
        recorder.browser_event(dict(event="private card text"))
        report = recorder.report()
        self.assertNotIn("private", report)
        self.assertLessEqual(report.count('"event":"browser:script_error"'), 30)

    def test_operation_wrapper_preserves_returns_and_original_exception(self):
        class Target:
            def run(self, value):
                if value is None: raise ValueError("original")
                return value
        target = Target()
        events = []
        with patch.object(module, "record", side_effect=lambda event, **kw: events.append(event)):
            module._wrap(target, "run", "operation")
            sentinel = object()
            self.assertIs(target.run(sentinel), sentinel)
            with self.assertRaisesRegex(ValueError, "original"):
                target.run(None)
        self.assertEqual(events, ["operation:request", "operation:returned", "operation:request", "operation:exception"])

    def test_current_pid_probe_does_not_terminate_process(self):
        self.assertTrue(module._pid_alive(os.getpid()))


if __name__ == "__main__":
    unittest.main()
