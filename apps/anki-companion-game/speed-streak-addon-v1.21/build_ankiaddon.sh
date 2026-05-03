#!/bin/sh

set -eu

OUTPUT_NAME="${1:-speed_streak_v1_21.ankiaddon}"
SOURCE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
STAGING_DIR="$SOURCE_DIR/.ankiaddon-build"
OUTPUT_PATH="$SOURCE_DIR/$OUTPUT_NAME"
ZIP_PATH="${OUTPUT_PATH%.ankiaddon}.zip"
GENERATOR="$SOURCE_DIR/generate_web_assets.py"
REQUIRED_PATHS="
reviewer_overlay.py
web_assets.py
web/overlay.css
web/overlay.js
web/card_timer.css
web/card_timer.js
"

if [ ! -f "$GENERATOR" ]; then
  echo "Cannot build package because the asset generator is missing: $GENERATOR" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Cannot build package because Python was not found to generate web_assets.py." >&2
  exit 1
fi

"$PYTHON_BIN" "$GENERATOR"

for required in $REQUIRED_PATHS; do
  if [ ! -e "$SOURCE_DIR/$required" ]; then
    echo "Cannot build package because required add-on files are missing: $required" >&2
    exit 1
  fi
done

rm -rf "$STAGING_DIR"
rm -f "$OUTPUT_PATH" "$ZIP_PATH"
mkdir -p "$STAGING_DIR"

for item in "$SOURCE_DIR"/* "$SOURCE_DIR"/.[!.]* "$SOURCE_DIR"/..?*; do
  name="$(basename "$item")"
  [ "$name" = "." ] && continue
  [ "$name" = ".." ] && continue
  case "$name" in
    .ankiaddon-build|__pycache__|user_files|.DS_Store|install_to_anki.ps1|build_ankiaddon.ps1|install_to_anki.sh|build_ankiaddon.sh|generate_web_assets.py|*.ankiaddon|*.zip)
      continue
      ;;
  esac
  cp -R "$item" "$STAGING_DIR/$name"
done

(cd "$STAGING_DIR" && zip -qr "$ZIP_PATH" .)
mv "$ZIP_PATH" "$OUTPUT_PATH"
rm -rf "$STAGING_DIR"

echo "Built package: $OUTPUT_PATH"
echo "Upload this .ankiaddon file at https://ankiweb.net/shared/addons/"
