#!/bin/sh

set -eu

ADDON_FOLDER_NAME="${1:-speed_streak}"
SOURCE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ANKI_ADDONS_ROOT="$HOME/Library/Application Support/Anki2/addons21"
TARGET_DIR="$ANKI_ADDONS_ROOT/$ADDON_FOLDER_NAME"

if [ ! -d "$ANKI_ADDONS_ROOT" ]; then
  echo "Could not find Anki add-ons folder at $ANKI_ADDONS_ROOT. Open Anki once and verify it is installed." >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"

for item in "$SOURCE_DIR"/* "$SOURCE_DIR"/.[!.]* "$SOURCE_DIR"/..?*; do
  name="$(basename "$item")"
  [ "$name" = "." ] && continue
  [ "$name" = ".." ] && continue
  [ "$name" = "install_to_anki.sh" ] && continue

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

echo "Installed add-on to: $TARGET_DIR"
echo "Preserved add-on data folders: user_files"
echo "Restart Anki to load the add-on."
