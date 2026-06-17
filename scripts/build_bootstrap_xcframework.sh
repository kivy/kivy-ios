#!/usr/bin/env bash
# Build KivyiOSBootstrap.xcframework from the kivy_ios_bootstrap.{h,m} sources.
#
# This script is provided for reference and future automation. The xcframework
# is NOT currently required — toolchain build compiles kivy_ios_bootstrap.m
# directly as part of the generated Xcode project. The xcframework step
# would be the natural next move once the source-based approach is validated.
#
# Prerequisites:
#   - macOS with Xcode and command-line tools installed
#   - SDL3.xcframework available (built by build_ios_wheels.sh or manually)
#   - Python.xcframework available (downloaded by toolchain)
#
# Usage:
#   scripts/build_bootstrap_xcframework.sh [SDL3_XCFW_DIR] [PYTHON_XCFW_DIR]
#
#   Defaults:
#     SDL3_XCFW_DIR   .build/ios-wheels/kivy/ios-kivy-dependencies/dist/Frameworks/SDL3.xcframework
#     PYTHON_XCFW_DIR ~/Library/Caches/kivy-ios/artifacts/Python.xcframework
#
# Output: kivy_ios/project/frameworks/KivyiOSBootstrap.xcframework

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/kivy_ios/project/templates"
OUT="$ROOT/kivy_ios/project/frameworks/KivyiOSBootstrap.xcframework"

SDL3_XCFW="${1:-$ROOT/.build/ios-wheels/kivy/ios-kivy-dependencies/dist/Frameworks/SDL3.xcframework}"
PYTHON_XCFW="${2:-$HOME/Library/Caches/kivy-ios/artifacts/Python.xcframework}"

if [[ ! -d "$SDL3_XCFW" ]]; then
    echo "SDL3.xcframework not found at: $SDL3_XCFW"
    echo "Run scripts/build_ios_wheels.sh first, or pass SDL3 xcframework path as \$1."
    exit 1
fi

if [[ ! -d "$PYTHON_XCFW" ]]; then
    echo "Python.xcframework not found at: $PYTHON_XCFW"
    echo "Run 'toolchain build' once to download it, or pass path as \$2."
    exit 1
fi

BUILD="$(mktemp -d /tmp/kivy-ios-bootstrap.XXXXXX)"
trap 'rm -rf "$BUILD"' EXIT

# SDL3 header paths per slice
SDL3_IOS_HEADERS="$SDL3_XCFW/ios-arm64/SDL3.framework/Headers"
SDL3_SIM_HEADERS="$SDL3_XCFW/ios-arm64_x86_64-simulator/SDL3.framework/Headers"

# Python.h per slice (python.org xcframework layout)
PY_IOS_HEADERS="$PYTHON_XCFW/ios-arm64/Headers"
PY_SIM_HEADERS="$PYTHON_XCFW/ios-arm64_x86_64-simulator/Headers"

compile_slice() {
    local target="$1"
    local sdk="$2"
    local sdl_headers="$3"
    local py_headers="$4"
    local out="$5"

    echo "  Compiling for $target ..."
    xcrun clang \
        -target "$target" \
        -isysroot "$(xcrun --sdk "$sdk" --show-sdk-path)" \
        -I"$sdl_headers" \
        -I"$py_headers" \
        -I"$SRC" \
        -fmodules -fobjc-arc \
        -c "$SRC/kivy_ios_bootstrap.m" \
        -o "$out"
}

echo "Building KivyiOSBootstrap slices ..."

compile_slice "arm64-apple-ios16.0" "iphoneos" \
    "$SDL3_IOS_HEADERS" "$PY_IOS_HEADERS" \
    "$BUILD/arm64_iphoneos.o"
xcrun ar rcs "$BUILD/arm64_iphoneos.a" "$BUILD/arm64_iphoneos.o"

compile_slice "arm64-apple-ios16.0-simulator" "iphonesimulator" \
    "$SDL3_SIM_HEADERS" "$PY_SIM_HEADERS" \
    "$BUILD/arm64_iphonesimulator.o"
xcrun ar rcs "$BUILD/arm64_iphonesimulator.a" "$BUILD/arm64_iphonesimulator.o"

compile_slice "x86_64-apple-ios16.0-simulator" "iphonesimulator" \
    "$SDL3_SIM_HEADERS" "$PY_SIM_HEADERS" \
    "$BUILD/x86_64_iphonesimulator.o"
xcrun ar rcs "$BUILD/x86_64_iphonesimulator.a" "$BUILD/x86_64_iphonesimulator.o"

# Combine simulator slices into a fat archive
echo "  Lipo arm64 + x86_64 simulator slices ..."
xcrun lipo -create \
    "$BUILD/arm64_iphonesimulator.a" \
    "$BUILD/x86_64_iphonesimulator.a" \
    -output "$BUILD/simulator.a"

mkdir -p "$BUILD/headers"
cp "$SRC/kivy_ios_bootstrap.h" "$BUILD/headers/"

echo "Assembling xcframework ..."
rm -rf "$OUT"
mkdir -p "$(dirname "$OUT")"
xcodebuild -create-xcframework \
    -library "$BUILD/arm64_iphoneos.a"  -headers "$BUILD/headers" \
    -library "$BUILD/simulator.a"       -headers "$BUILD/headers" \
    -output "$OUT"

echo "Done: $OUT"
