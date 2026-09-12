#!/bin/sh

set -eu

SOURCE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
EXECUTABLE="$SOURCE_DIR/SpeedStreakHaptics.app/Contents/MacOS/SpeedStreakHaptics"
REPORT="$SOURCE_DIR/SpeedStreakHaptics-diagnostic.json"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required to run the diagnostic harness." >&2
  exit 1
fi

sh "$SOURCE_DIR/build_poc.sh"
python3 "$SOURCE_DIR/controller_free_self_test.py" "$EXECUTABLE" "$REPORT"

echo "The helper is now staged in the add-on source folder."
echo "With Anki closed, run: sh ../install_to_anki.sh"
echo "After restarting Anki, open Speed Streak > macOS Haptics Diagnostics."
