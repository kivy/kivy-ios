#!/usr/bin/env bash
# Build pyobjus cp315 iOS wheels locally and drop them in examples/wheels.
#
# pyobjus is an optional Objective-C bridge for app code that calls iOS system
# frameworks (the kivy-ios platform shim itself uses ctypes and does not depend
# on it). It is a Cython extension that links libffi + the ObjC runtime.
#
# This mirrors scripts/build_ios_wheels.sh (the Kivy wheel builder): cibuildwheel
# cross-builds the three iOS slices, against a libffi that pyobjus's own
# .ci/build_ios_dependencies.sh produces in ios-deps-install/. Unlike Kivy there
# is no bundled-framework step — pyobjus ships no xcframeworks.
#
# Usage:
#   scripts/build_pyobjus_ios_wheels.sh [OUTPUT_DIR]
#
# Environment:
#   PYOBJUS_REF            git ref to build (default: master). PR #105 (Obj-C
#                          *protocol* loading rework) is marked "DO NOT MERGE
#                          YET" upstream, so master is the default.
#   IOS_DEPLOYMENT_TARGET  Minimum iOS version (default: 16.0; matches the
#                          examples' [tool.kivy.ios].deployment_target). The
#                          python.org cp315 binary targets iOS 13.0, so wheels
#                          may still tag as ios_13_0_* — that is fine, a lower
#                          min-OS is compatible with a 16.0 project.
#   PYOBJUS_SRC            Checkout dir (default: .build/ios-wheels/pyobjus).
#
# Prerequisites (identical to build_ios_wheels.sh): macOS + Xcode + network, a
# host Python 3.x with pip, and the CPython 3.15 macOS framework installed —
# cibuildwheel drives the iOS cross-build with it.
#
# NOTE: pyobjus has no iOS CI yet, so this exact cibuildwheel-iOS path is not
# upstream-validated. setup.py gates the iOS branch on sys.platform == "ios" and
# picks the libffi slice by platform.ios_ver().is_simulator + ARCH; if a build
# fails, those are the first two things to check.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="${1:-$ROOT/examples/wheels}"
BUILD_ROOT="${BUILD_ROOT:-$ROOT/.build/ios-wheels}"
PYOBJUS_SRC="${PYOBJUS_SRC:-$BUILD_ROOT/pyobjus}"
PYOBJUS_REF="${PYOBJUS_REF:-master}"
IOS_DEPLOYMENT_TARGET="${IOS_DEPLOYMENT_TARGET:-16.0}"

mkdir -p "$OUTPUT_DIR" "$BUILD_ROOT"

# --- CPython 3.15 macOS framework (cibuildwheel cross-builds iOS with it) -----
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

# --- pyobjus checkout --------------------------------------------------------
if [[ ! -d "$PYOBJUS_SRC/.git" ]]; then
  echo "Cloning kivy/pyobjus (${PYOBJUS_REF}) into $PYOBJUS_SRC ..."
  git clone --depth 1 --branch "$PYOBJUS_REF" \
    https://github.com/kivy/pyobjus.git "$PYOBJUS_SRC"
else
  echo "Using existing pyobjus checkout at $PYOBJUS_SRC (ref: $PYOBJUS_REF)"
fi

echo "Installing cibuildwheel ..."
# 4.0rc+ is required for Python 3.15 iOS wheels (cpython-prerelease enablement).
python3 -m pip install -q 'cibuildwheel>=4.0.0rc2'

pushd "$PYOBJUS_SRC" >/dev/null

# pyobjus's only native dependency is libffi; its .ci script cross-builds the
# three slices (with the armv7 xcodeproj patch) into ios-deps-install/, which
# setup.py links per slice.
DEPS_MARKER="ios-deps-install/iphoneos/arm64/lib/libffi.a"
if [[ ! -f "$DEPS_MARKER" ]]; then
  echo "Building libffi for iOS (pyobjus .ci/build_ios_dependencies.sh) ..."
  bash .ci/build_ios_dependencies.sh
else
  echo "Reusing cached ios-deps-install in $PYOBJUS_SRC"
fi

export CIBW_PLATFORM=ios
export CIBW_ARCHS="arm64_iphoneos arm64_iphonesimulator x86_64_iphonesimulator"
export CIBW_ENABLE=cpython-prerelease
export CIBW_BUILD="cp315-*"
# iOS builds run in an isolated cross-venv; cibuildwheel defaults the wheel tag
# to 13.0 unless IPHONEOS_DEPLOYMENT_TARGET is injected via CIBW_ENVIRONMENT_IOS.
export CIBW_ENVIRONMENT_IOS="IPHONEOS_DEPLOYMENT_TARGET=$IOS_DEPLOYMENT_TARGET"

WHEELHOUSE="$(mktemp -d "$BUILD_ROOT/pyobjus-wheelhouse.XXXXXX")"
echo "Running cibuildwheel (IPHONEOS_DEPLOYMENT_TARGET=$IOS_DEPLOYMENT_TARGET, output -> $WHEELHOUSE) ..."
python3 -m cibuildwheel --output-dir "$WHEELHOUSE"

popd >/dev/null

echo "Copying wheels to $OUTPUT_DIR ..."
cp -v "$WHEELHOUSE"/*.whl "$OUTPUT_DIR/"
rm -rf "$WHEELHOUSE"

echo "Done. Built wheels:"
ls -1 "$OUTPUT_DIR"/pyobjus-*.whl
