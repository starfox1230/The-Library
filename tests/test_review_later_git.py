from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "apps/anki-pocket-knife/review_later_git.py"
spec = importlib.util.spec_from_file_location("review_later_git", MODULE_PATH)
assert spec and spec.loader
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


def git(path: Path, *args: str) -> str:
    environment = dict(os.environ)
    for key in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE"):
        environment.pop(key, None)
    return subprocess.check_output(["git", *args], cwd=path, env=environment, text=True).strip()


def write(path: Path, name: str, content: str) -> None:
    target = path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def commit(path: Path, message: str) -> None:
    git(path, "add", "-A")
    git(path, "commit", "-m", message)


@pytest.fixture
def repositories(tmp_path: Path):
    remote = tmp_path / "remote.git"
    local = tmp_path / "local"
    other = tmp_path / "other"
    remote.mkdir()
    git(remote, "init", "--bare", "--initial-branch=main")
    git(tmp_path, "clone", str(remote), str(local))
    for repository in (local,):
        git(repository, "config", "user.name", "Test Publisher")
        git(repository, "config", "user.email", "publisher@example.test")
        git(repository, "config", "core.autocrlf", "false")
    write(local, "review-later/data.json", "old")
    write(local, "review-later/media/old.png", "old media")
    write(local, "unrelated.txt", "original")
    commit(local, "Initial")
    git(local, "push", "origin", "main")
    git(tmp_path, "clone", str(remote), str(other))
    git(other, "config", "user.name", "Other Publisher")
    git(other, "config", "user.email", "other@example.test")
    git(other, "config", "core.autocrlf", "false")
    return remote, local, other


def test_remote_ahead_dirty_diverged_checkout_and_real_index_are_preserved(repositories):
    remote, local, other = repositories
    write(other, "unrelated.txt", "remote change")
    commit(other, "Remote edit")
    git(other, "push", "origin", "main")
    remote_parent = git(remote, "rev-parse", "main")
    write(local, "local-only.txt", "local committed work")
    commit(local, "Local-only commit")
    write(local, "unrelated.txt", "staged local edit")
    git(local, "add", "unrelated.txt")
    write(local, "unrelated.txt", "unstaged local edit")
    write(local, "untracked.txt", "untracked")
    write(local, "review-later/data.json", "new export")
    (local / "review-later/media/old.png").unlink()
    write(local, "review-later/media/new.png", "new media")
    head_before = git(local, "rev-parse", "HEAD")
    status_before = git(local, "status", "--porcelain")
    index_before = (local / ".git/index").read_bytes()

    result = publisher.publish_generated_files(local, "review-later", message="Publish")

    assert result["pushed"]
    assert git(remote, "show", "main:review-later/data.json") == "new export"
    assert git(remote, "show", "main:unrelated.txt") == "remote change"
    assert git(remote, "rev-parse", "main^") == remote_parent
    assert git(remote, "diff", "--name-only", "main^", "main").splitlines() == [
        "review-later/data.json", "review-later/media/new.png", "review-later/media/old.png",
    ]
    assert git(local, "rev-parse", "HEAD") == head_before
    assert (local / ".git/index").read_bytes() == index_before
    assert git(local, "status", "--porcelain") == status_before
    assert git(local, "for-each-ref", "refs/pocket-knife") == ""


def test_unchanged_remote_is_verified_without_pushing_local_commits(repositories):
    remote, local, _other = repositories
    remote_before = git(remote, "rev-parse", "main")
    write(local, "local-only.txt", "must not be uploaded")
    commit(local, "Unrelated work")
    result = publisher.publish_generated_files(local, "review-later", message="Publish")
    assert result["remote_current"]
    assert not result["committed"] and not result["pushed"]
    assert git(remote, "rev-parse", "main") == remote_before


def test_competing_push_is_retried_on_new_remote_tip(repositories, monkeypatch):
    remote, local, other = repositories
    write(local, "review-later/data.json", "new export")
    original = publisher._run_git
    pushes = []

    def run(repository, *args, **kwargs):
        if args[0] == "push":
            pushes.append(args)
            if len(pushes) == 1:
                write(other, "unrelated.txt", "concurrent remote edit")
                commit(other, "Concurrent edit")
                git(other, "push", "origin", "main")
        return original(repository, *args, **kwargs)

    monkeypatch.setattr(publisher, "_run_git", run)
    result = publisher.publish_generated_files(local, "review-later", message="Publish")
    assert result["pushed"] and len(pushes) == 2
    assert git(remote, "show", "main:unrelated.txt") == "concurrent remote edit"
    assert git(remote, "show", "main:review-later/data.json") == "new export"


def test_network_failure_keeps_export_and_index_for_next_attempt(repositories, monkeypatch):
    remote, local, _other = repositories
    write(local, "review-later/data.json", "new export")
    index_before = (local / ".git/index").read_bytes()
    original = publisher._run_git

    def run(repository, *args, **kwargs):
        if args[0] == "push":
            raise subprocess.TimeoutExpired("git push", 600)
        return original(repository, *args, **kwargs)

    monkeypatch.setattr(publisher, "_run_git", run)
    with pytest.raises(subprocess.TimeoutExpired):
        publisher.publish_generated_files(local, "review-later", message="Publish")
    assert (local / "review-later/data.json").read_text() == "new export"
    assert (local / ".git/index").read_bytes() == index_before
    assert git(remote, "show", "main:review-later/data.json") == "old"
    assert git(local, "for-each-ref", "refs/pocket-knife") == ""
    monkeypatch.setattr(publisher, "_run_git", original)
    assert publisher.publish_generated_files(local, "review-later", message="Retry")["pushed"]


def test_permanent_push_rejection_is_not_retried(repositories, monkeypatch):
    _remote, local, _other = repositories
    write(local, "review-later/data.json", "new export")
    original = publisher._run_git
    pushes = []

    def run(repository, *args, **kwargs):
        if args[0] == "push":
            pushes.append(args)
            return subprocess.CompletedProcess(args, 1, "", "Permission denied")
        return original(repository, *args, **kwargs)

    monkeypatch.setattr(publisher, "_run_git", run)
    with pytest.raises(RuntimeError, match="Permission denied"):
        publisher.publish_generated_files(local, "review-later", message="Publish")
    assert len(pushes) == 1


def test_output_cannot_escape_repository(repositories):
    _remote, local, _other = repositories
    with pytest.raises(ValueError):
        publisher.publish_generated_files(local, "../other", message="Publish")
    with pytest.raises(RuntimeError, match="directory inside"):
        publisher.publish_generated_files(local, ".", message="Publish")
