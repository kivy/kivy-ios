# Swift-linking spike findings (Phase 0, spec 07)

**Question:** When kivy-ios wires a Swift Swift Package Manager (SPM) product into
its generated **pure-Objective-C** app target (`main.m` + `kivy_ios_bootstrap.m`,
no Swift sources), what is the *minimal, authoritative* set of project changes
that lets the app link, embed, and **launch** the Swift dependency at the iOS 13
deployment floor? In particular: is the widely-repeated "add an empty `.swift`
file to the target" trick actually required, or even correct? (Reproduce with
`bash scripts/swift_spm_spike.sh`.)

The goal was to replace folklore (Stack Overflow / Apple QA1881-era advice) with
evidence from Xcode's own build output for our exact code path.

## Environment

- Xcode 26.5 (build 17F42), Apple Swift 6.3.2.
- Simulator: iPhone 15 on **iOS 17.2** (ABI-stable; Swift runtime shipped in the
  OS). App built at `IPHONEOS_DEPLOYMENT_TARGET = 13.0`, `-sdk iphonesimulator`,
  `arm64`.
- Device: **iPhone 13 Pro Max on iOS 26.5**, signed development build
  (`minimal` and `noembed` confirmed on hardware).
- `pbxproj` 4.3.3 (the pinned dependency), driven exactly as Phase 3 will drive
  it.

## Method

A pure-ObjC app target (only `main.m`, built with the repo's real
`kivy_ios.project.skeleton.skeleton_pbxproj`) links a **local dynamic Swift
package** `SwiftKit`, wired via `pbxproj`'s `add_package_dependency` +
`XCLocalSwiftPackageReference`. The Swift code is exported with `@_cdecl` and
called from `main.m`, so the linker cannot dead-strip it and any runtime wiring
problem surfaces at launch (before `main` returns). Variants differ only in the
Swift "folklore" knobs:

| Variant | What it adds over the baseline | `xcodebuild` build | Framework embedded? | Simulator launch |
|---------|--------------------------------|:---:|:---:|:---:|
| `noembed` | link only, **no** Embed phase | OK | no | OK\* (false positive) |
| `minimal` | link + Embed Frameworks + `@executable_path/Frameworks` rpath | OK | yes | **OK** |
| `stub` | `minimal` + empty `swift_shim.swift` on the target | **FAIL** | n/a | n/a |
| `stub-swiftver` | `stub` + `SWIFT_VERSION = 5.0` | OK | yes | OK |
| `swift-settings` | `minimal` + `SWIFT_VERSION` + `/usr/lib/swift` rpath | OK | yes | OK |
| `embed-std` | `minimal` + `ALWAYS_EMBED_SWIFT_STANDARD_LIBRARIES = YES` | OK | yes | OK |

\* `noembed` launched on the *simulator* only because the app binary's `LC_RPATH`
still contained the absolute dev build path
`.../Debug-iphonesimulator/PackageFrameworks`, which the simulator can read off
the host filesystem. The bundle has **no** `Frameworks/` directory. **Confirmed
on device:** the same `noembed` build crashes at launch on an iPhone with
`dyld: Library not loaded: @rpath/SwiftKit.framework/SwiftKit` (it probes
`SpikeApp.app/Frameworks/SwiftKit.framework` and the host `PackageFrameworks`
path, neither of which exists on the phone). `minimal` launches cleanly on the
same device. Embedding is genuinely required.

## Binary evidence (`otool`, `minimal` variant)

The Swift dynamic framework references the Swift runtime by **absolute install
name**, not `@rpath`:

```
SwiftKit.framework/SwiftKit:
    /usr/lib/swift/libswiftCore.dylib            (not @rpath/libswiftCore.dylib)
    /usr/lib/swift/libswiftFoundation.dylib
    ... (libswiftDarwin/Dispatch/ObjectiveC/... weak)
```

The pure-ObjC app binary has **no** Swift dependency at all; it only links the
product:

```
SpikeApp:
    @rpath/SwiftKit.framework/SwiftKit
    /System/Library/Frameworks/Foundation.framework/Foundation
    /usr/lib/libobjc.A.dylib ...
app LC_RPATH: @executable_path/Frameworks
```

Grepping every binary for `@rpath/libswift*` returns **nothing** — the classic
`dyld: Library not loaded: @rpath/libswiftCore.dylib` dependency does not exist
at this deployment floor. This matches Apple's Swift 5 ABI-stability model: the
runtime ships in the OS and is linked by absolute path for deployment targets
>= iOS 12.2.

## Conclusions / decisions

1. **No Swift-specific build settings are required, and no `.swift` stub.** The
   `minimal` variant — link the product, embed the framework, and have
   `@executable_path/Frameworks` on the app's runpath — builds and launches a
   Swift dependency from a pure-ObjC target. `SWIFT_VERSION`,
   `/usr/lib/swift` in the runpath, and `ALWAYS_EMBED_SWIFT_STANDARD_LIBRARIES`
   are all unnecessary at the iOS 13 floor (`swift-settings` / `embed-std` pass
   but add nothing).
2. **The empty-`.swift`-file trick is wrong for our case.** Adding it with no
   other change *breaks the build*: `error: SWIFT_VERSION '' is unsupported`.
   Adding a Swift source forces the *app target* into Swift compilation, which
   then demands `SWIFT_VERSION` and gains nothing over `minimal`
   (`stub-swiftver` only matches what `minimal` already does). kivy-ios will
   **not** emit a stub `.swift`.
3. **Embedding is a real Phase 3 requirement that `pbxproj` does not handle.**
   `add_package_dependency` only adds the product to *Link Binary With
   Libraries*; it does **not** add an *Embed Frameworks* phase. Without an
   explicit Copy-Files/Embed phase (with `CodeSignOnCopy`), the dynamic
   framework is missing from `.app/Frameworks` and the app would fail on device.
   The generator must add this embed step itself for dynamic SPM products.
4. **The only app-target setting needed is the embedding runpath**
   (`LD_RUNPATH_SEARCH_PATHS` containing `@executable_path/Frameworks`), and that
   is required for *any* embedded framework (Swift or not), not a Swift concern.

## Caveats / residual items

- **Confirmed on a real device.** The simulator masked the embedding requirement
  (`noembed` false positive via a host-absolute rpath); on an iPhone 13 Pro Max
  (iOS 26.5) `minimal` launches and `noembed` crashes at launch with the dyld
  `@rpath/SwiftKit.framework` error, so embedding is confirmed mandatory on
  device.
- **Static SPM products.** This spike used a dynamic product (the common case,
  and what forces an embed step). A product that resolves to a *static* library
  links the Swift objects straight into the app binary; at the 12.2+ floor those
  also reference `/usr/lib/swift/...` by absolute path, so the same conclusion is
  expected, but it was not exercised here.
- This is the authoritative reference we have: reproducible Xcode build output
  for our own `pbxproj` path, corroborated by Apple's
  [ABI Stability and More](https://swift.org/blog/abi-stability-and-apple/)
  (runtime in-OS for iOS 12.2+). No Apple document addresses the modern
  "ObjC app consumes a Swift SPM package" case head-on.

## How this feeds the implementation (Phase 3)

- The generator wires SPM products with `add_package_dependency` **plus an
  explicit Embed Frameworks phase** (`PBXCopyFilesBuildPhase`, `dstSubfolderSpec
  = 10`, `CodeSignOnCopy`) for products with `embed = true`.
- It ensures `@executable_path/Frameworks` is on `LD_RUNPATH_SEARCH_PATHS`
  (already needed for `Python.xcframework` / wheel-embedded frameworks).
- It does **not** add a stub `.swift`, `SWIFT_VERSION`,
  `ALWAYS_EMBED_SWIFT_STANDARD_LIBRARIES`, or a `/usr/lib/swift` runpath for the
  SPM case at the supported deployment floor.
