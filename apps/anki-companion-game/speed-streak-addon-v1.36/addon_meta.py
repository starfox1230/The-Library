from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def default_meta_payload(addon_root: Path) -> Dict[str, Any]:
    manifest = _read_json(addon_root / "manifest.json")
    config = _read_json(addon_root / "config.json")
    payload: Dict[str, Any] = {
        "name": str(manifest.get("name") or addon_root.name),
        "mod": int(time.time()),
        "branch_index": int(manifest.get("branch_index", 1) or 1),
        "disabled": bool(manifest.get("disabled", False)),
    }
    conflicts = manifest.get("conflicts")
    if isinstance(conflicts, list):
        payload["conflicts"] = conflicts
    if config:
        payload["config"] = config
    return payload


def ensure_meta_json(addon_root: Path) -> Path:
    meta_path = addon_root / "meta.json"
    if meta_path.exists():
        return meta_path
    meta_path.write_text(json.dumps(default_meta_payload(addon_root), ensure_ascii=True), encoding="utf-8")
    return meta_path
