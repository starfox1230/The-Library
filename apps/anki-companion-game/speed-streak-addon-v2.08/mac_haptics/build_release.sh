#!/bin/sh

set -eu

SOURCE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BUILD_DIR="$SOURCE_DIR/.build-release"
APP_DIR="$BUILD_DIR/SpeedStreakHaptics.app"
MACOS_DIR="$APP_DIR/Contents/MacOS"
UNIVERSAL_EXECUTABLE="$MACOS_DIR/SpeedStreakHaptics"
SUBMISSION_ZIP="$BUILD_DIR/SpeedStreakHaptics-submission.zip"
OUTPUT_ZIP="$SOURCE_DIR/SpeedStreakHaptics-notarized.zip"
STAGED_APP_DIR="$SOURCE_DIR/SpeedStreakHaptics.app"
SIGNING_IDENTITY="${SPEED_STREAK_DEVELOPER_ID_APPLICATION:-}"
NOTARY_PROFILE="${SPEED_STREAK_NOTARY_PROFILE:-}"

if [ -z "$SIGNING_IDENTITY" ] || [ -z "$NOTARY_PROFILE" ]; then
  echo "Set SPEED_STREAK_DEVELOPER_ID_APPLICATION and SPEED_STREAK_NOTARY_PROFILE." >&2
  exit 1
fi

for tool in xcrun lipo codesign ditto; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Required release tool is missing: $tool" >&2
    exit 1
  fi
done

rm -rf "$BUILD_DIR"
rm -f "$OUTPUT_ZIP"
mkdir -p "$MACOS_DIR"
cp "$SOURCE_DIR/Info.plist" "$APP_DIR/Contents/Info.plist"

for arch in arm64 x86_64; do
  xcrun --sdk macosx swiftc \
    -O \
    -whole-module-optimization \
    -target "$arch-apple-macos11.0" \
    -framework AppKit \
    -framework CoreHaptics \
    -framework GameController \
    "$SOURCE_DIR/SpeedStreakHaptics.swift" \
    -o "$BUILD_DIR/SpeedStreakHaptics-$arch"
done

lipo -create \
  "$BUILD_DIR/SpeedStreakHaptics-arm64" \
  "$BUILD_DIR/SpeedStreakHaptics-x86_64" \
  -output "$UNIVERSAL_EXECUTABLE"
lipo -verify_arch arm64 x86_64 "$UNIVERSAL_EXECUTABLE"

codesign \
  --force \
  --deep \
  --options runtime \
  --timestamp \
  --sign "$SIGNING_IDENTITY" \
  "$APP_DIR"
codesign --verify --deep --strict --verbose=2 "$APP_DIR"

ditto -c -k --keepParent "$APP_DIR" "$SUBMISSION_ZIP"
xcrun notarytool submit "$SUBMISSION_ZIP" --keychain-profile "$NOTARY_PROFILE" --wait
xcrun stapler staple "$APP_DIR"
xcrun stapler validate "$APP_DIR"
spctl --assess --type execute --verbose=2 "$APP_DIR"

ditto -c -k --keepParent "$APP_DIR" "$OUTPUT_ZIP"
rm -rf "$STAGED_APP_DIR"
ditto "$APP_DIR" "$STAGED_APP_DIR"
echo "Built signed, notarized universal helper archive: $OUTPUT_ZIP"
echo "Staged the signed helper for add-on packaging: $STAGED_APP_DIR"
echo "Physical controller confirmation remains separately recorded in POC_VALIDATED.json."
