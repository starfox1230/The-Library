#!/bin/sh

set -eu

SOURCE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
APP_DIR="$SOURCE_DIR/SpeedStreakHaptics.app"
EXECUTABLE="$APP_DIR/Contents/MacOS/SpeedStreakHaptics"
VALIDATION_FILE="$SOURCE_DIR/POC_VALIDATED.json"

if [ ! -x "$EXECUTABLE" ]; then
  sh "$SOURCE_DIR/build_poc.sh"
fi

python3 "$SOURCE_DIR/poc_client.py" "$EXECUTABLE"

printf "Did a physical controller rumble with all three test patterns? [y/N] "
read -r confirmed
case "$confirmed" in
  y|Y|yes|YES)
    validated_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf '{"validated":true,"backend":"native-macos-gamecontroller","protocolVersion":1,"validatedAtUtc":"%s","confirmation":"physical-rumble-observed"}\n' "$validated_at" > "$VALIDATION_FILE"
    echo "Hardware validation recorded at: $VALIDATION_FILE"
    echo "The marker records physical confirmation for diagnostics; automatic routing remains capability-based."
    ;;
  *)
    rm -f "$VALIDATION_FILE"
    echo "No physical-validation marker was created. Controller-free diagnostics and safe automatic detection remain available."
    exit 2
    ;;
esac
