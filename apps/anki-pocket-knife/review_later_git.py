"""Publish generated files without changing the checkout, branch, or real index."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any


def _run_git(
    repository: Path, *args: str, index: Path | None = None,
    input_text: str | None = None, timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment.update(GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
    # Do not inherit another process's temporary index or repository overrides.
    for name in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE"):
        environment.pop(name, None)
    if index is not None:
        environment["GIT_INDEX_FILE"] = str(index)
    return subprocess.run(
        ["git", *args], cwd=str(repository), env=environment,
        input=input_text, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=timeout, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform.startswith("win") else 0,
    )


def _checked(repository: Path, *args: str, **kwargs: Any) -> str:
    result = _run_git(repository, *args, **kwargs)
    if result.returncode:
        detail = (result.stderr or result.stdout or "unknown Git error").strip()
        raise RuntimeError(f"git {args[0]} failed ({result.returncode}): {detail}")
    return result.stdout.strip()


def publish_generated_files(
    repository: Path, relative_output: str, *, message: str,
    branch: str = "main", attempts: int = 3,
) -> dict[str, Any]:
    """Make a scoped commit based on the remote tip; retry competing pushes.

    A private index stages only the generated directory. No local commits,
    staged edits, or other worktree files can enter the published commit.
    """
    repository = repository.resolve()
    output = (repository / relative_output).resolve()
    output.relative_to(repository)
    if output == repository or not output.is_dir():
        raise RuntimeError("Generated output must be an existing directory inside the repository.")
    _checked(repository, "check-ref-format", f"refs/heads/{branch}")
    output_pathspec = f":(top,literal){output.relative_to(repository).as_posix()}"
    remote_ref = f"refs/pocket-knife/review-later/{os.getpid()}-{time.time_ns()}"
    target_ref = f"refs/heads/{branch}"
    try:
        with tempfile.TemporaryDirectory(prefix="pocket-knife-publish-") as temporary:
            index = Path(temporary) / "index"
            for _attempt in range(max(1, attempts)):
                _checked(repository, "fetch", "--no-tags", "origin", f"{target_ref}:{remote_ref}", timeout=600)
                parent = _checked(repository, "rev-parse", remote_ref)
                _checked(repository, "read-tree", parent, index=index)
                _checked(repository, "add", "-A", "--", output_pathspec, index=index)
                tree = _checked(repository, "write-tree", index=index)
                parent_tree = _checked(repository, "rev-parse", f"{parent}^{{tree}}")
                if tree == parent_tree:
                    return {"committed": False, "pushed": False, "remote_current": True, "published_commit": parent}
                commit = _checked(repository, "commit-tree", tree, "-p", parent, input_text=message + "\n")
                push = _run_git(repository, "push", "origin", f"{commit}:{target_ref}", timeout=600)
                if push.returncode == 0:
                    return {"committed": True, "pushed": True, "remote_current": True, "published_commit": commit}
                detail = (push.stderr or push.stdout or "unknown Git error").strip()
                # A concurrent publisher can move the remote between fetch and
                # push. Rebuild against that new tip, never force-push it away.
                if "[rejected]" not in detail or not any(
                    reason in detail for reason in ("fetch first", "non-fast-forward")
                ):
                    raise RuntimeError(f"git push failed ({push.returncode}): {detail}")
            raise RuntimeError(f"GitHub kept changing during {attempts} publish attempts. Retry publishing. {detail}")
    finally:
        _run_git(repository, "update-ref", "-d", remote_ref)
