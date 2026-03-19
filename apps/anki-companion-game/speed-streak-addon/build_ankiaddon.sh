#!/bin/sh

set -eu

OUTPUT_NAME="${1:-speed_streak.ankiaddon}"
SOURCE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
STAGING_DIR="$SOURCE_DIR/.ankiaddon-build"
OUTPUT_PATH="$SOURCE_DIR/$OUTPUT_NAME"
ZIP_PATH="${OUTPUT_PATH%.ankiaddon}.zip"

rm -rf "$STAGING_DIR"
rm -f "$OUTPUT_PATH" "$ZIP_PATH"
mkdir -p "$STAGING_DIR"

for item in "$SOURCE_DIR"/* "$SOURCE_DIR"/.[!.]* "$SOURCE_DIR"/..?*; do
  name="$(basename "$item")"
  [ "$name" = "." ] && continue
  [ "$name" = ".." ] && continue
  case "$name" in
    .ankiaddon-build|__pycache__|user_files|install_to_anki.ps1|build_ankiaddon.ps1|install_to_anki.sh|build_ankiaddon.sh)
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
