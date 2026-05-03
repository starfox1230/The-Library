#!/bin/sh

set -eu

ADDON_FOLDER_NAME="${1:-speed_streak_v1_21}"
SOURCE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ANKI_ADDONS_ROOT="$HOME/Library/Application Support/Anki2/addons21"
TARGET_DIR="$ANKI_ADDONS_ROOT/$ADDON_FOLDER_NAME"
GENERATOR="$SOURCE_DIR/generate_web_assets.py"
REQUIRED_PATHS="
reviewer_overlay.py
web_assets.py
web/overlay.css
web/overlay.js
web/card_timer.css
web/card_timer.js
"

if [ ! -d "$ANKI_ADDONS_ROOT" ]; then
  echo "Could not find Anki add-ons folder at $ANKI_ADDONS_ROOT. Open Anki once and verify it is installed." >&2
  exit 1
fi

if [ ! -f "$GENERATOR" ]; then
  echo "Cannot install because the asset generator is missing: $GENERATOR" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Cannot install because Python was not found to generate web_assets.py." >&2
  exit 1
fi

"$PYTHON_BIN" "$GENERATOR"

for required in $REQUIRED_PATHS; do
  if [ ! -e "$SOURCE_DIR/$required" ]; then
    echo "Cannot install because required add-on files are missing: $required" >&2
    exit 1
  fi
done

mkdir -p "$TARGET_DIR"

for item in "$SOURCE_DIR"/* "$SOURCE_DIR"/.[!.]* "$SOURCE_DIR"/..?*; do
  name="$(basename "$item")"
  [ "$name" = "." ] && continue
  [ "$name" = ".." ] && continue
  [ "$name" = "install_to_anki.sh" ] && continue
  [ "$name" = "generate_web_assets.py" ] && continue
  [ "$name" = ".DS_Store" ] && continue
  case "$name" in
    *.ankiaddon|*.zip)
      continue
      ;;
  esac

  destination="$TARGET_DIR/$name"

  if [ -d "$item" ] && [ "$name" = "user_files" ]; then
    if [ ! -e "$destination" ]; then
      cp -R "$item" "$destination"
    fi
    continue
  fi

  rm -rf "$destination"
  cp -R "$item" "$destination"
done

"$PYTHON_BIN" - "$TARGET_DIR" <<'PY'
import json
import sys
import time
from pathlib import Path

target = Path(sys.argv[1])
meta_path = target / "meta.json"
if not meta_path.exists():
    def read_json(path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    manifest = read_json(target / "manifest.json")
    config = read_json(target / "config.json")
    payload = {
        "name": str(manifest.get("name") or target.name),
        "mod": int(time.time()),
        "branch_index": int(manifest.get("branch_index", 1) or 1),
        "disabled": bool(manifest.get("disabled", False)),
    }
    conflicts = manifest.get("conflicts")
    if isinstance(conflicts, list):
        payload["conflicts"] = conflicts
    if isinstance(config, dict) and config:
        payload["config"] = config
    meta_path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
PY

echo "Installed add-on to: $TARGET_DIR"
echo "Preserved add-on data folders: user_files"
echo "Restart Anki to load the add-on."
