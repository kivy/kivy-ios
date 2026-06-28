#!/bin/bash
#
# Swift-linking spike (spec 07, Phase 0). See docs/dev/swift-spm-findings.md.
#
# Builds a pure-Objective-C iOS app (only main.m, via the repo's real pbxproj
# skeleton) that links a local *dynamic* Swift package through SPM, then builds
# and launches several variants in the simulator to determine what a pure-ObjC
# target actually needs to consume a Swift dependency -- and whether the
# "empty .swift file" folklore is required (it is not).
#
# Requires: macOS + Xcode + an available iPhone simulator. Runs xcodebuild and
# xcrun simctl. Reproduces the findings doc; nothing is written to the repo.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d -t kivy-spm-spike)"
DD="$WORK/dd"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$DD"
echo "workdir: $WORK"

UDID="$(xcrun simctl list devices available | grep -m1 'iPhone' \
        | grep -oE '[0-9A-Fa-f-]{36}')"
[ -n "$UDID" ] || { echo "no iPhone simulator available" >&2; exit 1; }
echo "simulator: $UDID"

# --- local dynamic Swift package -----------------------------------------
mkdir -p "$WORK/src/SwiftKit/Sources/SwiftKit"
cat >"$WORK/src/SwiftKit/Package.swift" <<'EOF'
// swift-tools-version:5.9
import PackageDescription
let package = Package(
    name: "SwiftKit",
    products: [.library(name: "SwiftKit", type: .dynamic, targets: ["SwiftKit"])],
    targets: [.target(name: "SwiftKit")]
)
EOF
cat >"$WORK/src/SwiftKit/Sources/SwiftKit/SwiftKit.swift" <<'EOF'
import Foundation
@_cdecl("swiftkit_ping")
public func swiftkit_ping() {
    NSLog("SPIKE_OK swiftkit_ping ran from Swift dynamic framework")
}
EOF

# --- app sources ----------------------------------------------------------
cat >"$WORK/src/main.m" <<'EOF'
#import <Foundation/Foundation.h>
extern void swiftkit_ping(void);
int main(int argc, char *argv[]) {
    @autoreleasepool { swiftkit_ping(); NSLog(@"SPIKE_MAIN_DONE"); }
    return 0;
}
EOF
cat >"$WORK/src/SpikeApp-Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleExecutable</key><string>$(EXECUTABLE_NAME)</string>
  <key>CFBundleIdentifier</key><string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
  <key>CFBundleName</key><string>$(PRODUCT_NAME)</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>LSRequiresIPhoneOS</key><true/>
</dict></plist>
EOF
printf '// empty\n' >"$WORK/src/swift_shim.swift"

# --- project generator (uses the repo's real skeleton + pbxproj) ----------
cat >"$WORK/gen.py" <<'EOF'
import shutil, sys
from pathlib import Path
from pbxproj import PBXGenericObject, PBXList, XcodeProject
from pbxproj.pbxextensions.ProjectFiles import FileOptions
from pbxproj.pbxsections.XCLocalSwiftPackageReference import XCLocalSwiftPackageReference
sys.path.insert(0, sys.argv[3])  # repo root
from kivy_ios.project.skeleton import skeleton_pbxproj

APP, BUNDLE, DT = "SpikeApp", "com.kivyios.spike", "13.0"
TARGET_ID = "1A0000000000000000000030"
variant, out, src = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[4])

if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
shutil.copy(src / "main.m", out / "main.m")
shutil.copy(src / "SpikeApp-Info.plist", out / "SpikeApp-Info.plist")
shutil.copytree(src / "SwiftKit", out / "SwiftKit")
if variant in ("stub", "stub-swiftver"):
    shutil.copy(src / "swift_shim.swift", out / "swift_shim.swift")

xcp = out / f"{APP}.xcodeproj"
xcp.mkdir()
(xcp / "project.pbxproj").write_text(skeleton_pbxproj(APP, BUNDLE), "utf-8")
p = XcodeProject.load(str(xcp / "project.pbxproj"))

grp = p.get_or_create_group("Sources")
p.add_file("main.m", parent=grp, target_name=APP, tree="SOURCE_ROOT",
           file_options=FileOptions(embed_framework=False))
if variant in ("stub", "stub-swiftver"):
    p.add_file("swift_shim.swift", parent=grp, target_name=APP, tree="SOURCE_ROOT",
               file_options=FileOptions(embed_framework=False))

ref = XCLocalSwiftPackageReference.create("SwiftKit")
p.objects[ref.get_id()] = ref
for proj in p.objects.get_objects_in_section("PBXProject"):
    if "packageReferences" not in proj:
        proj["packageReferences"] = PBXList()
    proj.packageReferences.append(ref.get_id())
dep = p.add_package_dependency(APP, (ref, "SwiftKit"))

if variant != "noembed":
    bf = PBXGenericObject().parse({"_id": PBXGenericObject._generate_id(),
        "isa": "PBXBuildFile", "productRef": dep.get_id(),
        "settings": {"ATTRIBUTES": ["CodeSignOnCopy"]}})
    p.objects[bf.get_id()] = bf
    ph = PBXGenericObject().parse({"_id": PBXGenericObject._generate_id(),
        "isa": "PBXCopyFilesBuildPhase", "buildActionMask": 2147483647,
        "dstPath": "", "dstSubfolderSpec": 10, "files": [bf.get_id()],
        "name": "Embed Frameworks", "runOnlyForDeploymentPostprocessing": 0})
    p.objects[ph.get_id()] = ph
    p.get_target_by_name(APP).buildPhases.append(ph.get_id())

base = {"PRODUCT_BUNDLE_IDENTIFIER": BUNDLE, "PRODUCT_NAME": "$(TARGET_NAME)",
        "INFOPLIST_FILE": "SpikeApp-Info.plist", "IPHONEOS_DEPLOYMENT_TARGET": DT,
        "SDKROOT": "iphoneos", "TARGETED_DEVICE_FAMILY": "1,2",
        "GENERATE_INFOPLIST_FILE": "NO",
        "LD_RUNPATH_SEARCH_PATHS": "$(inherited) @executable_path/Frameworks"}
if variant in ("swift-settings", "stub-swiftver"):
    base["SWIFT_VERSION"] = "5.0"
if variant == "swift-settings":
    base["LD_RUNPATH_SEARCH_PATHS"] = "$(inherited) @executable_path/Frameworks /usr/lib/swift"
if variant == "embed-std":
    base["ALWAYS_EMBED_SWIFT_STANDARD_LIBRARIES"] = "YES"
for cfg in ("Debug", "Release"):
    for k, v in base.items():
        p.set_flags(k, v, target_name=APP, configuration_name=cfg)
p.save()

sch = xcp / "xcshareddata" / "xcschemes"
sch.mkdir(parents=True)
(sch / f"{APP}.xcscheme").write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="2650" version="1.7"><BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES"><BuildActionEntries><BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{TARGET_ID}" BuildableName="{APP}.app" BlueprintName="{APP}" ReferencedContainer="container:{APP}.xcodeproj"></BuildableReference></BuildActionEntry></BuildActionEntries></BuildAction><LaunchAction buildConfiguration="Debug"><BuildableProductRunnable runnableDebuggingMode="0"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{TARGET_ID}" BuildableName="{APP}.app" BlueprintName="{APP}" ReferencedContainer="container:{APP}.xcodeproj"></BuildableReference></BuildableProductRunnable></LaunchAction></Scheme>
''', "utf-8")
print("ok")
EOF

# --- variant matrix -------------------------------------------------------
xcrun simctl boot "$UDID" 2>/dev/null || true
sleep 2
printf '\n%-15s %-7s %-5s %-13s %-11s\n' VARIANT BUILD STUB EMBED LAUNCH
for V in noembed minimal stub stub-swiftver swift-settings embed-std; do
  set +e
  if ! python3 "$WORK/gen.py" "$V" "$WORK/proj/$V" "$REPO" "$WORK/src" >"$DD-gen-$V.log" 2>&1; then
    echo "gen failed for $V:"; cat "$DD-gen-$V.log"; exit 1
  fi
  ( cd "$WORK/proj/$V" && xcodebuild -project SpikeApp.xcodeproj -scheme SpikeApp \
      -configuration Debug -sdk iphonesimulator -arch arm64 \
      -derivedDataPath "$DD/$V" CODE_SIGNING_ALLOWED=NO build >"$DD/$V.log" 2>&1 )
  BR=$?
  set -e
  APP="$DD/$V/Build/Products/Debug-iphonesimulator/SpikeApp.app"
  [ -d "$APP/Frameworks/SwiftKit.framework" ] && EMB=embedded || EMB=NOT-embedded
  STUB=no; [ -f "$WORK/proj/$V/swift_shim.swift" ] && STUB=yes
  RES=skip
  if [ "$BR" -eq 0 ]; then
    xcrun simctl uninstall "$UDID" com.kivyios.spike >/dev/null 2>&1 || true
    xcrun simctl install "$UDID" "$APP" >/dev/null 2>&1 || true
    OUT="$(xcrun simctl launch --console-pty "$UDID" com.kivyios.spike 2>&1 || true)"
    echo "$OUT" | grep -q SPIKE_OK && RES=LAUNCH-OK || RES=LAUNCH-FAIL
  fi
  printf '%-15s %-7s %-5s %-13s %-11s\n' "$V" "$BR" "$STUB" "$EMB" "$RES"
done

echo; echo "=== otool evidence (minimal) ==="
APP="$DD/minimal/Build/Products/Debug-iphonesimulator/SpikeApp.app"
otool -L "$APP/Frameworks/SwiftKit.framework/SwiftKit" | grep -i swift || true
