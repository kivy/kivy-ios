#!/usr/bin/env bash
# Build Kivy cp315 iOS wheels locally (Path A for Kivy examples).
#
# Mirrors kivy/kivy .github/workflows/ios_wheels.yml on the current machine.
# Wheels land in OUTPUT_DIR (default: examples/wheels).
#
# Usage:
#   scripts/build_ios_wheels.sh [OUTPUT_DIR]
#
# Environment:
#   IOS_DEPLOYMENT_TARGET  Minimum iOS version for wheel platform tags and
#                          linked xcframeworks (default: 16.0). Passed to
#                          cibuildwheel as CIBW_ENVIRONMENT_IOS so wheel tags
#                          become ios_16_0_* (not the cibuildwheel default 13.0).
#                          Must match [tool.kivy.ios].deployment_target in the
#                          example pyproject.toml.
#
# Prerequisites: macOS, Xcode, network. Host Python 3.x with pip.
# Python 3.15 iOS wheels require cibuildwheel's cpython-prerelease enablement.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="${1:-$ROOT/examples/wheels}"
BUILD_ROOT="${BUILD_ROOT:-$ROOT/.build/ios-wheels}"
KIVY_SRC="${KIVY_SRC:-$BUILD_ROOT/kivy}"
KIVY_REF="${KIVY_REF:-master}"
IOS_DEPLOYMENT_TARGET="${IOS_DEPLOYMENT_TARGET:-16.0}"

mkdir -p "$OUTPUT_DIR" "$BUILD_ROOT"

CPYTHON_PKG_ID="org.python.Python.PythonFramework-3.15"
CPYTHON_FRAMEWORK="/Library/Frameworks/Python.framework/Versions/3.15"
CPYTHON_PKG_URL="https://www.python.org/ftp/python/3.15.0/python-3.15.0b2-macos11.pkg"
CPYTHON_PKG_CACHE="${BUILD_ROOT}/python-3.15.0b2-macos11.pkg"

if ! pkgutil --pkgs 2>/dev/null | grep -qx "$CPYTHON_PKG_ID"; then
  if [[ ! -d "$CPYTHON_FRAMEWORK" ]]; then
    echo "CPython 3.15 macOS framework is required to cross-build iOS wheels."
    echo "cibuildwheel refuses to sudo-install outside CI."
    if [[ ! -f "$CPYTHON_PKG_CACHE" ]]; then
      echo "Downloading installer to $CPYTHON_PKG_CACHE ..."
      curl -fsSL -o "$CPYTHON_PKG_CACHE" "$CPYTHON_PKG_URL"
    fi
    echo ""
    echo "Install once, then re-run this script:"
    echo "  sudo installer -pkg \"$CPYTHON_PKG_CACHE\" -target /"
    echo ""
    exit 1
  fi
fi

if ! xcrun -find metal >/dev/null 2>&1; then
  echo "Metal toolchain missing; downloading via xcodebuild ..."
  xcodebuild -downloadComponent MetalToolchain
fi

if [[ ! -d "$KIVY_SRC/.git" ]]; then
  echo "Cloning kivy/kivy (${KIVY_REF}) into $KIVY_SRC ..."
  git clone --depth 1 --branch "$KIVY_REF" https://github.com/kivy/kivy.git "$KIVY_SRC"
else
  echo "Using existing Kivy checkout at $KIVY_SRC"
fi

echo "Installing cibuildwheel build deps ..."
python3 -m pip install -q -r "$KIVY_SRC/.ci/cicd-requirements.txt"
# Kivy's pin (~=3.4) predates cp315 iOS; 4.0rc+ is required for Python 3.15 wheels.
python3 -m pip install -q 'cibuildwheel>=4.0.0rc2'
python3 -m pip install -q meson ninja

pushd "$KIVY_SRC" >/dev/null

DEPS_MARKER="ios-kivy-dependencies/dist/Frameworks/SDL3.xcframework/Info.plist"
if [[ ! -f "$DEPS_MARKER" ]]; then
  echo "Building iOS native dependencies (SDL3, ANGLE, ThorVG) — this takes a while ..."
  rm -rf ios-kivy-dependencies
  ./tools/build_ios_dependencies.sh
else
  echo "Reusing cached ios-kivy-dependencies in $KIVY_SRC"
fi

export KIVY_DEPS_ROOT="$(pwd)/ios-kivy-dependencies"
export KIVY_SPLIT_EXAMPLES=1
export CIBW_PLATFORM=ios
export CIBW_ARCHS="arm64_iphoneos arm64_iphonesimulator x86_64_iphonesimulator"
export CIBW_ENABLE=cpython-prerelease
export CIBW_BUILD="cp315-*"
# Kivy's SDL3/ANGLE/ThorVG xcframeworks target iOS 16+. cibuildwheel uses
# IPHONEOS_DEPLOYMENT_TARGET for linker flags and ios_<major>_<minor>_* wheel
# tags. Exporting it in the shell is not enough: iOS builds run in an isolated
# cross-venv and cibuildwheel defaults to 13.0 unless injected via CIBW_*.
export CIBW_ENVIRONMENT_IOS="IPHONEOS_DEPLOYMENT_TARGET=$IOS_DEPLOYMENT_TARGET"

WHEELHOUSE="$(mktemp -d "$BUILD_ROOT/kivy-wheelhouse.XXXXXX")"
echo "Running cibuildwheel (IPHONEOS_DEPLOYMENT_TARGET=$IOS_DEPLOYMENT_TARGET via CIBW_ENVIRONMENT_IOS, output -> $WHEELHOUSE) ..."
python3 -m cibuildwheel --output-dir "$WHEELHOUSE"

echo "Patching wheels with bundled iOS frameworks ..."
python3 ./tools/add-ios-frameworks.py "$WHEELHOUSE"

popd >/dev/null

echo "Copying wheels to $OUTPUT_DIR ..."
cp -v "$WHEELHOUSE"/*.whl "$OUTPUT_DIR/"
rm -rf "$WHEELHOUSE"

echo "Done. Built wheels:"
ls -1 "$OUTPUT_DIR"/*.whl
