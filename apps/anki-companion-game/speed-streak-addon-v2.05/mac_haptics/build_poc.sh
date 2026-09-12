#!/bin/sh

set -eu

SOURCE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BUILD_DIR="$SOURCE_DIR/.build-poc"
APP_DIR="$SOURCE_DIR/SpeedStreakHaptics.app"
EXECUTABLE="$APP_DIR/Contents/MacOS/SpeedStreakHaptics"
ARCH="$(uname -m)"

case "$ARCH" in
  arm64|x86_64) ;;
  *)
    echo "Unsupported Mac architecture: $ARCH" >&2
    exit 1
    ;;
esac

if ! command -v xcrun >/dev/null 2>&1; then
  echo "Xcode Command Line Tools are required for this proof of concept." >&2
  exit 1
fi

rm -rf "$BUILD_DIR" "$APP_DIR"
mkdir -p "$BUILD_DIR" "$APP_DIR/Contents/MacOS"
cp "$SOURCE_DIR/Info.plist" "$APP_DIR/Contents/Info.plist"

xcrun --sdk macosx swiftc \
  -O \
  -whole-module-optimization \
  -target "$ARCH-apple-macos11.0" \
  -framework AppKit \
  -framework CoreHaptics \
  -framework GameController \
  "$SOURCE_DIR/SpeedStreakHaptics.swift" \
  -o "$EXECUTABLE"

codesign --force --deep --sign - --options runtime "$APP_DIR"
codesign --verify --deep --strict --verbose=2 "$APP_DIR"
rm -rf "$BUILD_DIR"

echo "Built host-architecture proof of concept: $APP_DIR"
echo "Run sh ./run_controller_free_test.sh to validate launch and IPC without a controller."
echo "Run sh ./test_poc.sh later with a paired controller to record physical rumble confirmation."
