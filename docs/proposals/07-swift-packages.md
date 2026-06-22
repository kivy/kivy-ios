# 07 — Swift Package Manager Dependencies

**Status:** rfc-v2 (draft)
**Depends on:** [00-overview](00-overview.md), [01-pyproject-kivy-spec](01-pyproject-kivy-spec.md), [02-pylock-ios-spec](02-pylock-ios-spec.md), [03-artifact-distribution](03-artifact-distribution.md)
**Consumed by:** [06-xcode-project-generation](06-xcode-project-generation.md)

This spec adds a third way for an app to declare a native dependency: a **Swift
Package Manager (SPM) package**, declared by Git URL (or local path) and resolved
by Xcode. It fills the gap identified after specs 01–06 shipped — a growing share
of third-party iOS libraries are distributed **SPM-only**, with no standalone
`.xcframework` release artifact, so the existing
`[tool.kivy.ios.native.xcframeworks]` channel (spec 03) cannot reach them.

kivy-ios supports both SPM flavors — binary-target packages (a pre-built
`.xcframework`) and source packages (compiled by Xcode) — uniformly. The user
declares a package and the products they want; Xcode handles binary, source, and
hybrid (a source shim over a binary target) the same way, so the author never has
to classify their dependency.

## How this reconciles with the "no on-mac compilation" principle

Specs 00 and 03 state that the user's mac never compiles native code during a
`toolchain build` — it only consumes artifacts. Read literally that is already
untrue (kivy-ios compiles `main.m`, and Xcode links/embeds frameworks every
build), so the principle needs to be stated as what it actually means:

> **kivy-ios runs no from-source build pipeline of its own.** It does not
> resurrect the 2.x recipe system (building Python, OpenSSL, libffi, and ~50
> libraries through a bespoke kivy-ios build framework on the user's mac), and it
> does not cross-compile Python C extensions. Those are the genuinely painful,
> non-reproducible, toolchain-version-sensitive steps the 3.0 architecture
> exists to eliminate.

Source SPM compilation is **categorically different** from the 2.x recipe pain:

- It is driven by **Xcode's own, first-class package manager** — `xcodebuild`
  resolves, fetches, compiles, and embeds the package end-to-end. kivy-ios writes
  no build logic for it.
- The user already has the full Xcode toolchain (mandatory for any iOS build), so
  no new build prerequisite is introduced.
- It is the **native, vendor-supported** mechanism for consuming these libraries.

So letting Xcode compile an SPM dependency is not reopening the recipe wound; it
is deferring to the platform's maintained mechanism for exactly this job. The
principle that matters — *kivy-ios owns no from-source build pipeline* — is
preserved.

## Xcode owns the SPM lifecycle

**Xcode, not kivy-ios, owns the entire SPM lifecycle** — resolution, fetching,
compilation (for source/hybrid), and embedding. kivy-ios's job shrinks to:

1. At `toolchain lock`: resolve each declared package to a concrete Git
   **revision** and record the pin in `pylock.ios.toml`.
2. At `toolchain build`: emit the package references + product dependencies into
   the generated `.xcodeproj`, and write a `Package.resolved` reflecting the
   locked revisions. Xcode does the rest.

kivy-ios does **not** download, hash, extract, or dedupe SPM artifacts for this
channel — that machinery (used by `[[tool.kivy_ios.xcframeworks]]`) does not
apply. This makes the implementation *smaller*, at the cost of the reproducibility
reframing below.

## Reproducibility: pin the input revision, not the output

Spec 02's principle "every artifact pinned by URL + content hash" cannot extend
to a source package: the built binary depends on the Swift/Xcode toolchain
version, so there is no stable output hash to pin. Instead, the SPM channel pins
the **input**:

- The resolved **Git revision** (commit SHA) for every package, recorded in both
  `pylock.ios.toml` and a generated `Package.resolved`. This is exactly how every
  Xcode SPM project achieves reproducibility.
- For **binary** targets, SPM additionally records the `.binaryTarget` checksum;
  Xcode verifies it on fetch. kivy-ios carries that checksum through for audit.

This is a **deliberate, documented deviation** from the content-hash rule, scoped
to the SPM channel only. Wheels, the Python.xcframework, and direct
`.xcframework` archives remain content-hash-pinned and verified by kivy-ios as
before. The trade is intentional: it is the only way to consume source SPM
packages at all, and it matches the universally-understood Xcode SPM model.

## `pyproject.toml`: `[tool.kivy.ios.native.swift_packages]`

A new optional subtable, sibling to `[tool.kivy.ios.native.xcframeworks]`. Empty
by default — a vanilla Kivy app needs no entries.

```toml
[tool.kivy.ios.native.swift_packages]
# name = { url, requirement, products }
Sentry = { url = "https://github.com/getsentry/sentry-cocoa", requirement = { from = "8.49.0" }, products = ["Sentry"] }
```

- **Type**: table of name → inline table.
- **Semantics**: each entry declares an SPM package dependency. `toolchain lock`
  resolves it to a concrete revision; `toolchain build` wires the package
  reference and product dependencies into the `.xcodeproj`. Xcode resolves,
  builds (if source), and embeds.
- **Default**: empty.

Per-entry fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | yes (remote) | Git URL of the Swift package (`https://…` or `git@…`). Mutually exclusive with `path`. |
| `path` | string | yes (local) | Repo-relative path to a local Swift package directory (containing `Package.swift`). Mutually exclusive with `url`. Same path rules as vendored wheels/xcframeworks: relative to `pyproject.toml`, no absolute/escaping paths. |
| `requirement` | inline table | yes (remote) | Version requirement, exactly one of the SPM rule kinds — see below. Ignored for `path` packages. |
| `products` | list of string | yes | The package product names to depend on (one `XCSwiftPackageProductDependency` each). Non-empty. |
| `link` | bool | no (default `true`) | Add the product to the target's link step. |
| `embed` | bool | no (default `true`) | Embed the product's framework(s) into `.app/Frameworks/` and code-sign. For most dynamic SPM products Xcode embeds automatically; this field forces/suppresses it where relevant. |

### `requirement` rule kinds (remote packages)

`requirement` is exactly one of these inline-table shapes, mapping 1:1 to SPM's
own version rules (and to the `requirement` object pbxproj emits in the
`XCRemoteSwiftPackageReference`):

| TOML | SPM rule | Meaning |
|------|----------|---------|
| `{ exact = "X.Y.Z" }` | `exactVersion` | Exactly this version. |
| `{ from = "X.Y.Z" }` | `upToNextMajorVersion` | `>= X.Y.Z`, `< (X+1).0.0`. |
| `{ up_to_next_minor = "X.Y.Z" }` | `upToNextMinorVersion` | `>= X.Y.Z`, `< X.(Y+1).0`. |
| `{ range = ["X.Y.Z", "A.B.C"] }` | `versionRange` | Half-open `[X.Y.Z, A.B.C)`. |
| `{ branch = "main" }` | `branch` | Track a branch; resolves to its current commit at lock time. |
| `{ revision = "<sha>" }` | `revision` | Pin a specific commit directly. |

A `branch` or `revision` requirement still resolves to a concrete commit recorded
in the lock, so even a floating branch produces a reproducible build until the
next `toolchain lock`.

## `pylock.ios.toml`: `[[tool.kivy_ios.swift_packages]]`

`toolchain lock` records each resolved package as a repeatable array under the
kivy-ios extension table (invisible to other PEP 751 consumers).

```toml
[[tool.kivy_ios.swift_packages]]
name = "Sentry"
url = "https://github.com/getsentry/sentry-cocoa"
# The version rule that produced the pin, carried verbatim for re-lock/diff.
requirement = { from = "8.49.0" }
# The concrete commit SPM resolved — the reproducibility anchor.
revision = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
# Resolved semantic version, when the requirement resolved via a tag.
version = "8.49.0"
products = ["Sentry"]
link = true
embed = true
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Matches the `[tool.kivy.ios.native.swift_packages]` key. |
| `url` *or* `path` | exactly one | yes | Mirrors the pyproject declaration. |
| `requirement` | inline table | yes (remote) | The version rule, carried verbatim so `toolchain lock --check` can diff intent, not just the resolved pin. |
| `revision` | string | yes (remote) | The exact commit SPM resolved — the reproducibility anchor. |
| `version` | string | no | Resolved semantic version when the requirement resolved via a tag. |
| `products` | list of string | yes | Resolved product names. |
| `link` / `embed` | bool | no (default `true`) | Xcode-phase intent, as in pyproject. |

There is intentionally **no per-artifact `sha256`/`url` sub-array** here (unlike
`[[tool.kivy_ios.xcframeworks]]`): Xcode owns artifact fetching for this channel,
and reproducibility comes from the pinned `revision` + the generated
`Package.resolved`, not from a kivy-ios-computed output hash (see
"Reproducibility" above).

## Resolution semantics (extends spec 02 §"Resolution semantics")

`toolchain lock` adds a step after the native-xcframeworks step. For each entry in
`[tool.kivy.ios.native.swift_packages]`:

1. Resolve the package with SPM/Xcode in a scratch checkout (e.g. `xcodebuild
   -resolvePackageDependencies` against a throwaway project, or `swift package
   resolve`), producing the concrete revision (and, for binary targets, the
   `.binaryTarget` checksum SPM records).
2. Record one `[[tool.kivy_ios.swift_packages]]` entry: the declared `url`/`path`
   and `requirement`, the resolved `revision`, the `version` (if tag-resolved),
   `products`, and `link`/`embed`.

Ordering is deterministic (sorted by `name`) for clean diffs, consistent with the
rest of the lockfile.

> **Network at lock time.** SPM resolution happens during `toolchain lock` (which
> already contacts PyPI/python.org). `--offline` lock uses the SPM cache and
> errors if it is incomplete. `toolchain build` does not re-resolve floating
> requirements — it pins Xcode to the locked revisions via `Package.resolved`.

## Xcode project generation (extends spec 06 §"pbxproj wiring")

`toolchain build` (every-build, idempotent sync):

1. For each `[[tool.kivy_ios.swift_packages]]` entry, ensure a package reference
   exists on the project:
   - **Remote**: `XCRemoteSwiftPackageReference` with `repositoryURL = url` and a
     `requirement` object built from the lock's `requirement` rule (e.g.
     `{ kind = exactVersion, version = … }`). The `pbxproj` library's
     `add_package(url, requirement, product, target)` creates this plus the
     product dependency in one call.
   - **Local**: `XCLocalSwiftPackageReference` with `relativePath` pointing at the
     repo-relative package directory.
2. For each product, ensure an `XCSwiftPackageProductDependency` on the app
   target, wired into Link Binary With Libraries (and Embed Frameworks when
   `embed = true`). `pbxproj`'s `add_package_dependency` adds the link build file
   automatically; embedding of dynamic products is otherwise Xcode-automatic.
3. Write `<app>.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved`
   from the locked revisions, so Xcode resolves to the pinned commits without
   network drift. Regenerated every build (idempotent).
4. Remove stale package references/dependencies for entries no longer in the lock.

Xcode then resolves, fetches, compiles (source/hybrid), and embeds the packages
during its own build. The per-module `.so`→`.framework` conversion done by
`install_python` (spec 06) is unrelated to and unaffected by SPM products, which
are already in framework shape.

> **Verified capability.** `pbxproj` 4.3.3 (the pinned dependency, `pbxproj>=3.5`)
> ships `XCRemoteSwiftPackageReference`, `XCLocalSwiftPackageReference`, and
> `XCSwiftPackageProductDependency`, plus `add_package` /
> `add_package_dependency` / `get_or_create_package_reference` helpers. A
> round-trip against the generator's skeleton confirms it emits a valid
> `packageReferences` + `packageProductDependencies` graph. `Package.resolved` is
> a plain JSON file kivy-ios writes directly (pbxproj does not manage it).

### Interaction with the duplicate-framework policy

The duplicate-framework policy (spec 06 §"Duplicate framework policy") governs
artifacts kivy-ios stages into `<app>-ios/Frameworks/` itself (wheel-embedded and
`native.xcframeworks`). SPM products are resolved and embedded by **Xcode**, not
staged by kivy-ios, so they are outside that staging check. If an SPM product and
a kivy-staged framework collide by basename at the bundle level, the failure
surfaces as an Xcode duplicate-output error. `toolchain doctor` may warn when a
declared SPM product name matches a known wheel-embedded framework, but v3.0 does
not attempt to reconcile the two providers automatically.

## Calling a Swift package from Python

Everything above gets an SPM product **built, embedded, and loaded** — the
framework is in the app's process at launch. *Calling* it from Python is a
separate concern with a clean boundary: **kivy-ios's responsibility ends once the
framework is loadable; reaching its API from Python is the app author's.** This
section documents that boundary, because it is the first thing a user hits after
declaring a package.

### pyobjus reaches Swift only through the Objective-C runtime

The Kivy bridge for native calls is `pyobjus`, which works purely at runtime
through the Objective-C runtime (`objc_getClass`, `sel_registerName`,
`objc_msgSend`) and reads method signatures from the runtime's own type
encodings. It never parses a header. Consequently **pyobjus can call a Swift
symbol if and only if that symbol is exposed to the Objective-C runtime** — i.e.
the Swift author annotated it `@objc`. Pure-Swift API (Swift-only types,
`struct`/payload-`enum`, generics, SwiftUI surfaces) is invisible to the runtime
and unreachable by pyobjus, regardless of any project wiring kivy-ios does.

### No bridging file is generated, because none can help

"Swift bridging" names two compile-time artifacts pointing in opposite
directions; **neither is relevant to a runtime pyobjus call**:

| Artifact | Direction | Purpose |
|---|---|---|
| `<App>-Bridging-Header.h` | Objective-C → Swift | lets a target's Swift code see its Objective-C code |
| `<Module>-Swift.h` (compiler-generated) | Swift → Objective-C | lets Objective-C *source* call `@objc` Swift at compile time |

pyobjus compiles against nothing and calls at runtime, so it uses no header. What
an `@objc` annotation actually produces — and all that matters here — is
Objective-C **runtime metadata baked into the framework binary**, present whether
or not a header is generated. kivy-ios therefore emits **no** bridging file for
this channel: a generated header would be unused (pyobjus needs none) or
impossible (nothing can retroactively expose a non-`@objc` API). This matches the
spike finding ([docs/dev/swift-spm-findings.md](../dev/swift-spm-findings.md))
that the app target needs no Swift-specific build settings or `.swift` stub.

### Requirements for a Python-callable Swift symbol

For `autoclass("Foo")` followed by a method call to succeed:

1. `Foo` is declared `@objc(Foo)` and inherits `NSObject`. The explicit
   `@objc(Foo)` gives a stable runtime name; a bare `@objc` leaves Swift's
   mangled name (`_TtC…`), which pyobjus cannot look up cleanly.
2. The called method is `@objc` with Objective-C-representable parameter and
   return types (`String`↔`NSString`, `Int`↔`NSInteger`, Objective-C objects —
   *not* Swift structs, payload enums, tuples, or generics).
3. The framework is loaded — guaranteed by the link+embed wiring above; no
   `dlopen` / `load_framework` call is needed for a linked product.

Items 1–2 are properties of the **package's own source**. If a package ships no
`@objc` surface, kivy-ios cannot expose it — that is not a wiring gap but an
absence of runtime symbols.

### Reaching a non-`@objc` package: a local Swift shim

The supported pattern for a pure-Swift dependency is an app-authored **`@objc`
shim** — a small Swift package wrapping the upstream API in
Objective-C-representable signatures — declared through the **`path`** form of
`swift_packages` (specified above). kivy-ios wires the local shim like any other
SPM dependency; the shim depends on the upstream package and re-exports it behind
`@objc`:

```swift
// swift-shims/Sources/AppBridge/AppBridge.swift
import Foundation
import SomePureSwiftSDK

@objc(AppBridge)
public final class AppBridge: NSObject {
    @objc public func start(_ token: String) {
        SomePureSwiftSDK.configure(token: token)   // Swift-only API, hidden here
    }
}
```

```toml
[tool.kivy.ios.native.swift_packages]
AppBridge = { path = "swift-shims", products = ["AppBridge"] }
```

```python
from pyobjus import autoclass
AppBridge = autoclass("AppBridge")
AppBridge.alloc().init().start_(token)
```

The shim is irreducibly app-specific — it depends on which API and call surface
the app wants — so it belongs to the app, in the same category as `main.py`.
kivy-ios provides the **mechanism** (the local-package channel), not the shim.

### Alternative: `@_cdecl` + ctypes

A package or shim may instead export plain C entry points with `@_cdecl` and be
called from Python via the standard-library `ctypes` — the same mechanism the
vendored `ios` module uses for `objc_msgSend` ([spec 05](05-cli-shape.md)). This
bypasses pyobjus and the Objective-C runtime entirely, sidesteps the
`@objc`-representability constraints (the author marshals C types directly), and
adds no pyobjus dependency. It suits a narrow, performance-insensitive call
surface; a broad object-oriented API is better served by the `@objc` shim above.

### Why there is no `doctor` check for this

Whether a product exposes an `@objc` surface can only be read from the built
framework's runtime metadata, which does not exist until Xcode has compiled the
package — there is no reliable static, pre-build check. kivy-ios documents the
requirement rather than verifying it; a call into a non-exposed symbol surfaces at
runtime as a pyobjus `objc_getClass` / selector failure.

## Validation (extends spec 01 §"Validation rules")

`toolchain lock` / `toolchain build` reject a `pyproject.toml` that:

1. Declares a `swift_packages` entry with neither `url` nor `path`, or both.
2. Declares a remote entry (`url`) with no `requirement`, or a `requirement` that
   is not exactly one of the recognized rule kinds.
3. Sets a `path` that is absolute or escapes the project directory.
4. Lists an empty `products` array.

Note there is **no** "binary vs source" validation — both are supported, so no
classification or rejection step exists. A package that fails to *resolve* or
*build* surfaces its error through Xcode/SPM, with kivy-ios passing the diagnostic
through.

## `toolchain doctor` (extends spec 05 §`toolchain doctor`)

- **SPM toolchain available** (project mode, only when `swift_packages` is
  non-empty): SPM resolution at lock time and compilation at build time require
  Xcode's Swift toolchain. `doctor` checks it is present and reports an actionable
  error otherwise. (Pure-wheel projects are unaffected — the check is skipped when
  no SPM packages are declared.)
- **Required hosts reachable**: each remote package's Git host is added to the
  reachability union alongside wheel/xcframework/python hosts.
- **Privacy manifests**: SPM-embedded `.xcframework`s land in the built app's
  `Frameworks/` via Xcode; the existing xcframework-privacy guidance applies, but
  because kivy-ios does not stage them, the `doctor` `Frameworks/` scan may not
  see them pre-build. The author remains responsible for any required-reason-API
  privacy manifest in a third-party package.

## Security / supply-chain note

Because kivy-ios does not compute an output hash for SPM products, the integrity
guarantees for this channel are SPM's, not kivy-ios's: the pinned Git `revision`
fixes the source, and binary targets carry SPM's `.binaryTarget` checksum (Xcode
verifies it on fetch). This is weaker than the kivy-ios-verified `sha256` applied
to wheels and direct `.xcframework` archives, and is the documented cost of
supporting source SPM. Users who require kivy-ios-side hash verification of a
native dependency should prefer the `[tool.kivy.ios.native.xcframeworks]` channel
(build the library into an `.xcframework`, pin it by URL + SHA-256).

## Open questions (resolved)

1. **Embedding nuance — resolved (Phase 0 spike, see
   [docs/dev/swift-spm-findings.md](../dev/swift-spm-findings.md)).** For a
   dynamic SPM product, kivy-ios must add an **explicit** Embed Frameworks /
   Copy Files phase (with `CodeSignOnCopy`): `pbxproj`'s `add_package_dependency`
   only wires the *link* step, and Xcode does **not** auto-embed it for our
   generated (non-GUI) project — without the explicit phase the framework is
   absent from `.app/Frameworks` and the app fails on device. The `embed = true`
   field maps to adding this phase; `embed = false` omits it. Separately, the
   spike showed a pure-ObjC app target needs **no** Swift-specific settings and
   **no** empty `.swift` stub to consume a Swift package at the iOS 13 floor (the
   Swift runtime is referenced by absolute `/usr/lib/swift` install names); the
   only app-target requirement is `@executable_path/Frameworks` on the runpath,
   which kivy-ios already needs for its other embedded frameworks.
2. **`Package.resolved` format version — resolved.** kivy-ios writes schema
   **version 2** (`{ "pins": [ … ], "version": 2 }`, the flattened layout with
   top-level `pins` and per-pin `identity`/`kind`/`location`/`state`). v2 is
   emitted by Xcode 13–15 and is read by every currently-supported Xcode; v3
   only adds an `originHash` that Xcode recomputes on open, so writing v2 is
   forward-compatible. Implemented in
   [`kivy_ios/project/swift_packages.py`](../../kivy_ios/project/swift_packages.py)
   (`PACKAGE_RESOLVED_VERSION = 2`).
3. **Schema version — resolved.** Adding `swift_packages` is additive to
   `[tool.kivy.ios]` (new optional subtable) and to `[tool.kivy_ios]` in the
   lock, so by spec 01's evolution policy it does **not** bump
   `[tool.kivy.ios].schema_version` nor the lock's
   `[tool.kivy_ios].schema_version`. Both remain at `1`.
