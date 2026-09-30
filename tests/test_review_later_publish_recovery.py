from concurrent.futures import Future
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest


@pytest.fixture
def publish_module(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1] / "apps/anki-pocket-knife"
    package = ModuleType("pocket_knife_test")
    package.__path__ = [str(root)]
    monkeypatch.setitem(sys.modules, package.__name__, package)
    hooks = SimpleNamespace(profile_did_open=[], sync_did_finish=[], media_sync_did_start_or_stop=[])
    aqt = ModuleType("aqt")
    aqt.gui_hooks = hooks
    aqt.mw = SimpleNamespace(col=object())
    monkeypatch.setitem(sys.modules, "aqt", aqt)
    qt = ModuleType("aqt.qt")
    qt.QMessageBox = SimpleNamespace(warning=lambda *args: None)
    qt.QTimer = object
    monkeypatch.setitem(sys.modules, "aqt.qt", qt)
    notices = []
    utils = ModuleType("aqt.utils")
    utils.tooltip = lambda message, **kwargs: notices.append(message)
    monkeypatch.setitem(sys.modules, "aqt.utils", utils)
    common = ModuleType("pocket_knife_test.common")
    common.addon_root = lambda: root
    common.user_files_dir = lambda: tmp_path
    monkeypatch.setitem(sys.modules, common.__name__, common)
    integration = ModuleType("pocket_knife_test.speed_streak_review_later")
    integration.fetch_current_review_later = lambda: {"cards": []}
    monkeypatch.setitem(sys.modules, integration.__name__, integration)
    spec = importlib.util.spec_from_file_location("pocket_knife_test.review_later_publish", root / "review_later_publish.py")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    scheduled = []
    monkeypatch.setattr(module, "_schedule_auto_publish", lambda delay_ms=1500: scheduled.append(delay_ms))
    return module, scheduled, notices, hooks


def test_automatic_failures_are_visible_and_retries_are_bounded(publish_module):
    module, scheduled, notices, _hooks = publish_module
    for _ in range(4):
        future = Future()
        future.set_exception(RuntimeError("offline"))
        module._PUBLISH_RUNNING = True
        module._publish_done(future, manual=False)
        assert not module._PUBLISH_RUNNING
    assert scheduled == [30000, 60000, 120000]
    assert len(notices) == 4
    assert "use Publish Review Later Website" in notices[-1]
    assert module._load_status()["last_success"] is False
    assert module._load_status()["last_error"] == "offline"


def test_timeout_is_marked_pending_before_network_call(publish_module, monkeypatch):
    module, _scheduled, _notices, _hooks = publish_module

    def fail(*args, **kwargs):
        assert module._load_status()["push_pending"] is True
        raise TimeoutError("upload timed out")

    monkeypatch.setattr(module, "publish_generated_files", fail)
    with pytest.raises(TimeoutError):
        module._git_publish(Path("."), "review-later", {})
    assert module._load_status()["push_pending"] is True


def test_verified_remote_clears_pending_and_records_success(publish_module, monkeypatch):
    module, _scheduled, _notices, _hooks = publish_module
    module._save_status(push_pending=True, last_error="old failure")
    monkeypatch.setattr(module, "publish_generated_files", lambda *args, **kwargs: {
        "committed": False, "pushed": False, "published_commit": "abc", "remote_current": True,
    })
    result = module._git_publish(Path("."), "review-later", {})
    assert module._load_status()["push_pending"] is False
    future = Future()
    future.set_result(dict(result, count=3, retained_count=12, updated_at="export time"))
    module._AUTO_RETRY_COUNT = 3
    module._publish_done(future, manual=False)
    status = module._load_status()
    assert status["last_success"] and status["last_success_at"]
    assert status["last_error"] == ""
    assert status["last_published_commit"] == "abc"
    assert status["last_retained_count"] == 12
    assert module._AUTO_RETRY_COUNT == 0


def test_snapshot_failure_is_recorded_and_retried(publish_module, monkeypatch):
    module, scheduled, notices, _hooks = publish_module
    monkeypatch.setattr(module, "_snapshot", lambda: (_ for _ in ()).throw(RuntimeError("Speed Streak not loaded")))
    module._start_publish(manual=False)
    assert scheduled == [30000]
    assert notices
    assert "Speed Streak not loaded" in module._load_status()["last_error"]
    assert not module._PUBLISH_RUNNING


def test_install_registers_startup_and_sync_recovery_once(publish_module):
    module, scheduled, _notices, hooks = publish_module
    module.install()
    module.install()
    assert hooks.profile_did_open == [module._on_profile_did_open]
    assert hooks.sync_did_finish == [module._on_sync_did_finish]
    hooks.profile_did_open[0]()
    assert scheduled == [3000]


def test_sync_waits_for_media_then_schedules_upload(publish_module):
    module, scheduled, _notices, _hooks = publish_module
    module.mw.media_syncer = SimpleNamespace(is_syncing=lambda: True)
    module._AUTO_RETRY_COUNT = 3
    module._on_sync_did_finish()
    assert not scheduled and module._AUTO_PENDING
    assert module._AUTO_RETRY_COUNT == 0
    module._on_media_sync_state_changed(False)
    assert scheduled == [500]
