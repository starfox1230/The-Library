from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

from aqt import mw


PROFILE_DATA_DIRECTORY_NAME = "addons-data"
SPEED_STREAK_DATA_DIRECTORY_NAME = "speed_streak"
LEGACY_USER_FILES_DIRECTORY_NAME = "user_files"
MIGRATION_SENTINEL_NAME = ".speed_streak_data_migration.json"


def current_profile_folder() -> Path | None:
    profile_manager = getattr(mw, "pm", None)
    if profile_manager is None:
        return None
    for attr_name in ("profileFolder", "profile_folder"):
        candidate = getattr(profile_manager, attr_name, None)
        try:
            value = candidate() if callable(candidate) else candidate
        except Exception:
            continue
        path = _coerce_path(value)
        if path is not None:
            return path
    return None


def speed_streak_data_root(addon_root: Path) -> Path:
    legacy_root = Path(addon_root) / LEGACY_USER_FILES_DIRECTORY_NAME
    profile_root = current_profile_folder()
    if profile_root is None:
        legacy_root.mkdir(parents=True, exist_ok=True)
        return legacy_root

    data_root = profile_root / PROFILE_DATA_DIRECTORY_NAME / SPEED_STREAK_DATA_DIRECTORY_NAME
    try:
        data_root.mkdir(parents=True, exist_ok=True)
    except Exception:
        legacy_root.mkdir(parents=True, exist_ok=True)
        return legacy_root

    _migrate_legacy_user_files(legacy_root=legacy_root, data_root=data_root)
    return data_root


def _coerce_path(value: Any) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return Path(text)
    except Exception:
        return None


def _migrate_legacy_user_files(*, legacy_root: Path, data_root: Path) -> None:
    try:
        if not legacy_root.exists() or _same_path(legacy_root, data_root):
            return
    except Exception:
        return

    sentinel_path = data_root / MIGRATION_SENTINEL_NAME
    if sentinel_path.exists():
        return

    errors: list[str] = []
    for source in legacy_root.rglob("*"):
        relative_path = source.relative_to(legacy_root)
        target = data_root / relative_path
        try:
            if source.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(source, target)
        except Exception as exc:
            errors.append(f"{relative_path}: {exc}")

    if errors:
        return

    try:
        sentinel_path.write_text(
            json.dumps(
                {
                    "migratedAtEpoch": int(time.time()),
                    "source": str(legacy_root),
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except Exception:
        return str(left) == str(right)
