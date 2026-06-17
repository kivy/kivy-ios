# 01 — `pyproject.toml` `[tool.kivy]` / `[tool.kivy.ios]` Schema

**Status:** rfc-v2 (draft — harmonization rewrite)
**Depends on:** [00-overview](00-overview.md)
**Consumed by:** [02-pylock-ios-spec](02-pylock-ios-spec.md), [05-cli-shape](05-cli-shape.md), [06-xcode-project-generation](06-xcode-project-generation.md)

`pyproject.toml` is the **sole user-facing surface** for declaring how a Kivy mobile app is built. The configuration lives in tables inside the project's existing `pyproject.toml`:

- **`[project]`** — PEP 621. App name, version, description, dependencies, entry points. *Shared* across all platforms.
- **`[tool.kivy]`** — cross-platform Kivy metadata (display name, orientation, app source layout).
- **`[tool.kivy.ios]`** — iOS-specific (bundle_id, deployment_target, signing, Python.xcframework version, native xcframeworks).
- **`[tool.kivy.android]`** — Android-specific (out of scope for kivy-ios 3.0 but reserved in the schema so `p4a` / `Buildozer` can adopt the same shape).

The file is hand-edited (after being seeded by `toolchain init`) and committed to version control. `pylock.ios.toml` is generated from it by `toolchain lock`; `toolchain build` consumes the lock.

This spec defines the schema and the evolution policy.

## Design principles

- **Single source of truth.** One `pyproject.toml` per app. iOS and Android tooling read the same `[project]` and the same `[tool.kivy]` tables; only the platform-specific subtables differ.
- **PEP-aligned.** PEP 621 (`[project]`), PEP 518 (`[tool.*]` namespace). No invented file formats.
- **Declarative.** Every field describes intent, not action. No imperative statements, no shell hooks.
- **Schema-versioned per platform.** Each platform overlay carries its own `schema_version` integer — `[tool.kivy.ios].schema_version` for iOS, `[tool.kivy.android].schema_version` for Android. kivy-ios and p4a/Buildozer evolve on independent cadences; locking them to a shared number would force coupled releases and that's the wrong trade. The shared `[tool.kivy]` table itself is **unversioned**: each platform's spec documents which `[tool.kivy]` keys it consumes, and validates them as part of its own platform `schema_version`. Adding a new key under `[tool.kivy]` is always backward-compatible at the parser level (extra TOML keys are ignored); semantic consumption is opt-in per platform via a normal `schema_version` bump on the side that adopts it.
- **TOML-native.** Stable, parseable by `tomllib` (stdlib since Python 3.11), readable to humans.
- **Platform tables are additive overlays.** `[tool.kivy.ios]` only contains keys whose value must differ from the cross-platform default in `[tool.kivy]`, or keys that are meaningless on Android (e.g. `bundle_id`, `signing.team_id`).

## Top-level structure

```toml
# Standard PEP 621 metadata — shared by every platform.
[project]
name = "myapp"
version = "0.1.0"
description = "A Kivy app"
requires-python = ">=3.15"
# One dependency list for all platforms; PEP 508 markers select platform-specific entries.
dependencies = [
    "kivy>=3.0,<4",
    "pillow>=11",
    "ios-only-helper>=1.0; sys_platform == 'ios'",
    "android-only-helper>=1.0; sys_platform == 'android'",
]

# Optional standard PEP 621 author info, license, etc. — passed through to
# platform metadata where the platform supports it (CFBundleHumanReadableCopyright
# on iOS, etc.).
authors = [{ name = "Your Name", email = "you@example.com" }]

# Cross-platform Kivy configuration. Unversioned: each platform overlay
# declares its own schema_version and validates its consumption of these keys.
[tool.kivy]
display_name = "My App"
app_dir = "src"
entry_point = "main"
orientation = ["portrait"]

# iOS-specific overlay. Required for `toolchain build` to produce an iOS app.
[tool.kivy.ios]
schema_version = 1
bundle_id = "org.example.myapp"
build = 1
deployment_target = "13.0"
# Optional supplemental wheel indexes, consulted in addition to PyPI. Empty by
# default. Use only for packages whose iOS wheels aren't on PyPI proper yet.
# extra_index_urls = ["https://wheels.example.com/simple"]
# Optional repo-relative directories of pre-built wheels for `toolchain lock`.
# Passed to pip as `--find-links` (flat `.whl` folders, not simple indexes).
# find_links = ["wheels"]

[tool.kivy.ios.python]
version = "3.15.0"

# iOS-specific icons and splash.
[tool.kivy.ios.icons]
source = "assets/icon-ios.png"     # 1024×1024 PNG; Xcode generates all sizes

[tool.kivy.ios.splash]
source = "assets/splash-ios.png"
background = "#ffffff"

[tool.kivy.ios.native.xcframeworks]
# Pure-native deps shipped as .xcframework archives.

[tool.kivy.ios.entitlements]
# iOS entitlements key/value table (raw plist semantics).

[tool.kivy.ios.signing]
# Signing configuration.

[tool.kivy.ios.privacy_manifest]
# source = "privacy/PrivacyInfo.xcprivacy"
# Omit to use the generated minimal stub (no tracking, no required-reason APIs).

[tool.kivy.ios.info_plist]
# Additional Info.plist keys merged into <app>-Info.plist. Use this for keys
# that kivy-ios doesn't expose through a dedicated field (e.g. usage-description
# strings, capability flags). Keys that kivy-ios already writes from the schema
# (CFBundleIdentifier, CFBundleVersion, UISupportedInterfaceOrientations, etc.)
# are rejected here — set those via the dedicated fields above instead.
# NSCameraUsageDescription = "Used for QR code scanning."
# UIFileSharingEnabled = true

[tool.kivy.ios.xcode.build_settings]
# Free-form pass-through to .xcodeproj build settings.

# Android overlay — reserved; not consumed by kivy-ios. Documented here for
# cross-tool harmonization with p4a/Buildozer. Has its own schema_version
# independent of [tool.kivy.ios].
[tool.kivy.android]
# schema_version = 1
# package = "org.example.myapp"
# target_api = 34
# permissions = ["android.permission.INTERNET"]
```

The two tables `[project]` and `[tool.kivy]` are **the cross-platform contract**. Everything inside `[tool.kivy.ios]` is consumed only by kivy-ios; everything inside `[tool.kivy.android]` is consumed only by p4a/Buildozer.

## `[project]` (PEP 621)

kivy-ios consumes the following PEP 621 keys directly; the rest are passed through where iOS exposes a slot for them.


| PEP 621 key              | iOS use                                                                                                                                                                                                                                   | Required by kivy-ios       |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| `name`                   | Standard PEP 621 distribution name (may contain hyphens, dots, or underscores per PEP 503). Used as the Xcode target name and file slug — kivy-ios normalizes it for the slug as needed — and, when `[tool.kivy].display_name` is absent, as the home-screen name. Not required to be a valid Python identifier; that constraint applies only to `entry_point`.                              | yes                        |
| `version`                | `CFBundleShortVersionString`. Marketing version.                                                                                                                                                                                          | yes                        |
| `description`            | `CFBundleDisplayName` fallback when `[tool.kivy].display_name` is unset; also used for App Store metadata if present.                                                                                                                     | no                         |
| `requires-python`        | Cross-checked against `[tool.kivy.ios.python].version` to fail fast on impossible combinations (e.g. `requires-python = ">=3.16"` with `[tool.kivy.ios.python].version = "3.15.0"`).                                                      | no, but warned on mismatch |
| `dependencies`           | The full Python dependency set (PEP 508 strings, including environment markers for platform-specific entries). `toolchain lock` evaluates markers against the iOS target and resolves the matching subset to wheels in `pylock.ios.toml`. | yes (may be empty)         |
| `optional-dependencies`  | Treated as ignored by kivy-ios v3.0 unless the user opts in per-extra via a future `[tool.kivy.ios].extras` allowlist.                                                                                                                    | no                         |
| `authors`, `maintainers` | First `authors` entry's `name` populates the bundle copyright string when no override is given.                                                                                                                                           | no                         |


Anything PEP 621 specifies is honored by every PEP 621-compliant tool — so ruff, mypy, uv, pdm, pip all stay happy with the same file.

## `[tool.kivy]`

```toml
[tool.kivy]
display_name = "My App"
app_dir = "src"      # folder holding your app code; the project root (".") is not allowed
entry_point = "main"
orientation = ["portrait", "portrait-upside-down"]
```

`[tool.kivy]` carries fields that are meaningful to every Kivy mobile platform. It has **no `schema_version` of its own** — see "Schema-versioned per platform" in the design principles. Each platform overlay validates its consumption of these keys as part of its own `schema_version`.


| Field          | Type           | Required | Default                 | Description                                                                                                                                                                                                                                                                                                                                                                                                           |
| -------------- | -------------- | -------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `display_name` | string         | no       | `[project].name` titled | App display name on home screen. Both iOS (CFBundleDisplayName) and Android (`android:label`) consume it.                                                                                                                                                                                                                                                                                                             |
| `app_dir`      | string         | yes      | —                       | Folder containing your `.py` source files, relative to `pyproject.toml`. **Must be a subdirectory** (e.g. `"src"`); the project root (`"."`), an empty value, an absolute path, or a path escaping the project are all rejected — see the note under "`app_dir` + `entry_point` interaction" for why. `toolchain build` creates `<app>-ios/app/` as a symlink to this folder (not a copy), and Xcode walks it as a folder reference on every build — so source edits flow to the next Xcode build without re-running `toolchain build`. See [spec 06 "Developer iteration workflow"](06-xcode-project-generation.md#developer-iteration-workflow). |
| `entry_point`  | string         | no       | `"main"`                | Python module reference (dotted name). The generated `main.m` does the equivalent of `PyImport_ImportModule(entry_point)` after putting `app_dir` on `sys.path`.                                                                                                                                                                                                                                                      |
| `orientation`  | list of string | no       | `["portrait"]`          | Allowed orientations. Valid: `portrait`, `portrait-upside-down`, `landscape-left`, `landscape-right`. iOS writes the list to **both** `UISupportedInterfaceOrientations` (iPhone) and `UISupportedInterfaceOrientations~ipad` (iPad) with identical values — necessary because `TARGETED_DEVICE_FAMILY` is `1,2`, and without the `~ipad` key iPad would silently fall back to all four orientations. Android tooling consumes the same list.                                                                                                                                                                                                      |


### `app_dir` + `entry_point` interaction

These two fields together specify *what* code runs and *where it lives*. `entry_point` defaults to `"main"`; `app_dir` has **no default and is required** — `toolchain init` seeds it to `"src"` (the recommended layout), and a project that keeps its code elsewhere adjusts it by hand (the same way it fills in `bundle_id` and `signing.team_id`).

> **`app_dir` must be a subdirectory — the project root (`"."`) is rejected.** Two problems make `"."` unsafe, so the toolchain refuses it outright rather than working around it:
> - **Bundle bloat / dev-file leakage.** `app/` is a symlink that Xcode copies wholesale into the `.app`. Pointed at the project root, it sweeps in `.git/`, `.venv/`, `tests/`, `__pycache__/`, `pyproject.toml`, and everything else at the root.
> - **Symlink recursion.** The `<app>-ios/` build output lives at the project root, so `app_dir = "."` would point the copy at a folder that *contains its own build product* — recursively copying `Python.xcframework/`, `pip-deps/`, etc. into the bundle.
>
> Putting your code under a subdirectory like `src/` (with `app_dir = "src"`) avoids both: the symlink points only at your source, and the build output stays outside it. This also means kivy-ios v3.0 needs no per-file `exclude` mechanism. A single-file app simply lives at `src/main.py`.

Example layouts:


| Layout                                                   | `app_dir` | `entry_point`   |
| -------------------------------------------------------- | --------- | --------------- |
| `./src/main.py`                                          | `"src"`   | `"main"`        |
| `./src/app.py`                                           | `"src"`   | `"app"`         |
| `./src/start.py` (no `src/__init__.py`)                  | `"src"`   | `"start"`       |
| `./src/myapp/start.py` (only `src/myapp/__init__.py`)    | `"src"`   | `"myapp.start"` |

> **`entry_point` is *imported*, not run as `__main__`.** The bootstrap does the equivalent of `PyImport_ImportModule(entry_point)`, so `entry_point` must name a module whose top-level code starts the app *on import*. Pointing it at a package (e.g. `"myapp"`) runs that package's `__init__.py`, **not** its `__main__.py` — `__main__.py` only executes under `python -m myapp` (runpy), which the iOS bootstrap does not use. If your launch code lives in `myapp/__main__.py`, either move it to an explicitly-named module (e.g. `myapp/start.py` with `entry_point = "myapp.start"`) or have `__init__.py` import and run it.


## Icons and splash screens

Icons and splash screens are inherently platform-specific: iOS requires a 1024×1024 flat PNG (Xcode generates all sizes into an asset catalog); Android adaptive icons require separate foreground and background layers; splash screen aspect ratios and conventions differ further. A single shared asset set cannot satisfy all platforms correctly, so **each platform declares its own icon and splash in its own subtable**. If `[tool.kivy.ios.icons]` or `[tool.kivy.ios.splash]` is absent, no icon or splash is generated and Xcode uses its defaults.

### `[tool.kivy.ios.icons]`

```toml
[tool.kivy.ios.icons]
source = "assets/icon-ios.png"   # 1024×1024 PNG
```


| Field    | Type   | Required | Description                                                                                                                                                        |
| -------- | ------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `source` | string | no       | Path to a 1024×1024 source PNG relative to `pyproject.toml`. `toolchain build` generates the full iOS icon set (all `AppIcon` sizes) into the Xcode asset catalog. |


### `[tool.kivy.ios.splash]`

```toml
[tool.kivy.ios.splash]
source = "assets/splash-ios.png"
background = "#ffffff"
```


| Field        | Type   | Required | Description                                                                                           |
| ------------ | ------ | -------- | ----------------------------------------------------------------------------------------------------- |
| `source`     | string | no       | Path to a launch-screen image. Used as the centered image in the generated `LaunchScreen.storyboard`. |
| `background` | string | no       | Hex color (`#rrggbb`) for the launch screen background.                                               |


## `[tool.kivy.ios]`

iOS-specific overlay. Every field below applies to iOS only.

```toml
[tool.kivy.ios]
schema_version = 1
bundle_id = "org.example.myapp"
build = 1
deployment_target = "13.0"
```


| Field               | Type    | Required | Default  | Description                                                                                                                                                                                                                                          |
| ------------------- | ------- | -------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `schema_version`    | integer | yes      | —        | Declares the major version of the iOS schema this `[tool.kivy.ios]` table targets. `toolchain` refuses to operate on a value higher than it understands, with a clear "upgrade kivy-ios" error. Independent of `[tool.kivy.android].schema_version`. |
| `bundle_id`         | string  | yes      | —        | iOS bundle identifier. Init suggests `org.example.<slug>` with a comment to change it.                                                                                                                                                               |
| `build`             | integer | no       | `1`      | Build number (`CFBundleVersion`). Increment per submission. Android's version-code lives under `[tool.kivy.android]`.                                                                                                                                |
| `deployment_target` | string  | no       | `"13.0"` | Minimum iOS version. Must be >= the floor of the selected `Python.xcframework`.                                                                                                                                                                      |
| `extra_index_urls`  | list of string | no | `[]`     | Supplemental pip index URLs consulted *in addition to* PyPI when resolving iOS wheels. `toolchain lock` passes each as `--extra-index-url` to pip. Plural-by-design, channel-agnostic, and **empty by default**; PyPI is always the primary source. Each resolved wheel's source URL is pinned in `pylock.ios.toml`'s `[[packages.wheels]]` (and its index recorded under `[packages.tool.kivy_ios].source_index`) regardless of which index supplied it, keeping builds reproducible. As packages publish iOS wheels to PyPI proper, configured entries go quiet on their own. See [spec 03 §"Source registry: PyPI direct"](03-artifact-distribution.md) and [spec 00](00-overview.md). |
| `find_links`        | list of string | no | `[]`     | Repo-relative directories of pre-built wheels consulted during `toolchain lock` only. Each entry is passed to pip as `--find-links` (pip's name for flat wheel directories or direct wheel URLs). Use when a dependency's iOS wheels are vendored in the repo but not published to PyPI or a supplemental index yet — e.g. locally cross-built `kivy` cp315 wheels under `wheels/`. Entries must be repo-relative (not absolute, must not escape the project directory). **Not** used at `toolchain build` time; the lockfile's per-wheel `path` or `url` pins are authoritative after lock. See "Local wheel directories (`find_links`)" below and [spec 02 §"Locally built wheels"](02-pylock-ios-spec.md). |


### Local wheel directories (`find_links`)

`[project].dependencies` stays PEP 508 only (`kivy>=3.0`, not a file path per package). When an iOS wheel is vendored locally, two layers are involved:

1. **Lock-time discovery (pyproject)** — `find_links` tells pip where to *search* while `toolchain lock` resolves the graph. The name matches pip's `--find-links` flag deliberately: it is for directories of `.whl` files, not PEP 503 simple indexes.
2. **Build-time pin (lockfile)** — each resolved slice is recorded in `pylock.ios.toml` as `url` (remote) or `path` (repo-relative), per PEP 751. `toolchain build` installs from those pins; it does not re-read `find_links`.

This is **not** the same as:

- **`extra_index_urls`** — supplemental *indexes* (`--extra-index-url`), which serve HTML/JSON simple API pages. A flat `wheels/` folder is not an index; use `find_links` instead.
- **`[tool.kivy.ios.native.xcframeworks].source`** — per-entry explicit URL or path for a *native* `.xcframework` archive, not a Python wheel. Kivy's ANGLE/SDL payloads ride inside the kivy *wheel*; they do not belong in `native.xcframeworks` for a vanilla app.

Example (local Kivy wheels until PyPI carries cp315 iOS slices):

```toml
[project]
dependencies = ["kivy>=3.0.0.dev0,<4"]

[tool.kivy.ios]
find_links = ["wheels"]
```

After `toolchain lock`, `pylock.ios.toml` holds entries such as:

```toml
[[packages.wheels]]
name = "kivy-3.0.0.dev0-cp315-cp315-ios_13_0_arm64_iphonesimulator.whl"
path = "wheels/kivy-3.0.0.dev0-cp315-cp315-ios_13_0_arm64_iphonesimulator.whl"
hashes = { sha256 = "..." }
```

`deployment_target` in `[tool.kivy.ios]` must match the platform tags on the vendored wheels (e.g. `ios_13_0_*` vs `ios_16_0_*`); see [spec 02](02-pylock-ios-spec.md).

### `schema_version` evolution policy (iOS)

- Additive changes (new optional fields, new optional subtables) **do not** bump `[tool.kivy.ios].schema_version`.
- Backward-incompatible changes (rename, remove, semantics change, required-field added) **must** bump it.
- The toolchain supports reading the latest N major iOS schema versions (initially N=1). A separate `toolchain migrate` verb in a future minor release converts older `[tool.kivy.ios]` blocks to the latest schema.
- When schema bumps occur, `pylock.ios.toml` records the source iOS schema version in its `[tool.kivy_ios]` block as `tool_kivy_ios_schema_version`.
- If kivy-ios extends a field that lives under the shared `[tool.kivy]` table (e.g. it starts consuming a newly-added `[tool.kivy].background_color`), that adoption is an iOS-side change and bumps `[tool.kivy.ios].schema_version`. Android can decide independently when (or whether) to adopt the same key.
- `[tool.kivy.android].schema_version` evolves on the p4a/Buildozer cadence; kivy-ios neither reads nor enforces it.

### `[tool.kivy.ios.python]`

```toml
[tool.kivy.ios.python]
version = "3.15.0"
```


| Field     | Type   | Required | Default | Description                                                                                                                                                                                                                      |
| --------- | ------ | -------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `version` | string | yes      | —       | Python.xcframework version. Init pins to the latest known release. The full download URL is derived (the canonical python.org distribution path is recorded in `pylock.ios.toml`'s `[tool.kivy_ios]` block for reproducibility). |


Future fields (xcframework URL override, explicit SHA) are described in spec 02 since they belong in the lock when present.

### `[tool.kivy.ios.native.xcframeworks]`

```toml
[tool.kivy.ios.native.xcframeworks]
# Empty by default for a vanilla Kivy app — the kivy iOS wheel bundles every
# native xcframework it links against (ANGLE, SDL3 family, etc.) inside the
# wheel itself. This table is for apps that need *additional* third-party
# xcframeworks not delivered via a Python wheel. `source` is always explicit —
# a direct download URL or a repo-relative path. Examples:
# Sentry        = { version = "8.49.0", source = "https://github.com/getsentry/sentry-cocoa/releases/download/8.49.0/Sentry.xcframework.zip" }
# MyNativeLib   = { version = "0.3.0",  source = "frameworks/MyNativeLib.xcframework.zip" }
```

- **Type**: table of name → inline table.
- **Semantics**: each entry declares a pure-native `.xcframework` dependency that ships to the user's `.app/Frameworks/` and is wired into Xcode's Link Binary With Libraries + Embed Frameworks phases.
- **Default**: empty. A vanilla Kivy app needs no entries here because the kivy iOS wheel bundles its native dependencies internally (see `kivy/kivy` `tools/add-ios-frameworks.py`).

Per-entry fields:


| Field     | Type   | Required                                                 | Description                                                                                                                                                                                                                                 |
| --------- | ------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `version` | string | yes                 | Exact version or semver spec. |
| `source`  | string | yes                 | Where to fetch the xcframework artifact (zip, tar.gz, or an unpacked `.xcframework` directory). Always **explicit**: either a **direct download URL** or a **repo-relative path** to a locally built/vendored artifact. There are no indirection keywords — the value states exactly where the artifact comes from. `toolchain lock` reads the artifact to resolve its SHA-256 and slice list and pins them in `pylock.ios.toml`. See [spec 03 §"Distribution channel 2"](03-artifact-distribution.md). |
| `link`    | bool   | no (default `true`) | Add to Link Binary With Libraries phase. |
| `embed`   | bool   | no (default `true`) | Add to Embed Frameworks phase (copies into `.app/Frameworks/`, code-signs). |


Init never auto-populates this table: the canonical Kivy dependency set needs no entries because the kivy iOS wheel bundles its own native xcframeworks. An app that needs an *additional* third-party xcframework adds an entry here by hand, providing the name, version, and an explicit `source`.

**`source` as a URL vs. a path.** A URL is right for published SDKs and frameworks shared across projects. A repo-relative path is right for a framework the author built and versions alongside the app — because both the artifact and the path live in the repo, it resolves identically on every clone and in CI. `toolchain build` rejects an absolute path (or one escaping the project directory) with a diagnostic. This mirrors the local-wheel mechanism in [spec 02](02-pylock-ios-spec.md) and follows PEP 751's path conventions, so users learn one rule for both wheels and xcframeworks.

### System frameworks are not declared — they link transitively

There is **no `system_frameworks` key**, and the app does not enumerate Apple SDK frameworks (`Metal`, `AVFoundation`, `CoreBluetooth`, …) anywhere. This is a direct consequence of the all-dynamic distribution model:

- Every native dependency arrives as a **dynamic** framework — the kivy wheel's bundled xcframeworks (ANGLE, SDL3 family), the per-module `.framework`s `install_python` builds from each `.so`, and `Python.framework` itself. A dynamic framework records the Apple SDK frameworks it needs as `LC_LOAD_DYLIB` load commands **inside its own Mach-O**, set when *that* framework was built. At app launch `dyld` walks the dependency graph transitively (app → `kivy…framework` → `Metal`/`AVFoundation`/…), so the app target never has to re-declare them.
- The app target compiles only the `main.m` bootstrap, which references just Foundation/UIKit/the Python C API. Those Foundation/UIKit references are the **bootstrap baseline** the toolchain links automatically (see [spec 06](06-xcode-project-generation.md)); nothing in the dependency graph needs app-level declaration.
- Calling a system API from Python via `pyobjus` is **dynamic loading** at runtime (`pyobjus.dylib_manager.load_framework(...)` / the Objective-C runtime), which involves no link-time symbol references and therefore no Xcode link entry either.

The only case that historically required an explicit per-app framework list was **static** linking (the kivy-ios 2.x recipe model linked static `.a` libraries into the app binary, so the app target had to resolve every transitive system symbol). kivy-ios 3.0 is all-dynamic, so that requirement is gone. If a future need arises (e.g. weak-linking an SDK framework for availability that the *app's own compiled code* references), it can be added as an additive, `schema_version`-bumping change — but v3.0 ships without it.

### `[tool.kivy.ios.entitlements]`

```toml
[tool.kivy.ios.entitlements]
"com.apple.security.network.client" = true
"com.apple.developer.healthkit" = false
```

- **Type**: table of plist key → plist value (bool, string, or list).
- **Semantics**: written verbatim into the generated `<app>.entitlements` file. Pass-through; no Kivy-specific validation.
- iOS-only. Android permissions go under `[tool.kivy.android].permissions`.

### `[tool.kivy.ios.signing]`

```toml
[tool.kivy.ios.signing]
team_id = "ABCDE12345"
identity = "Apple Development"
provisioning_profile = ""
auto_signing = true
upload_symbols = true
```


| Field                  | Type   | Required | Default               | Description                                                  |
| ---------------------- | ------ | -------- | --------------------- | ------------------------------------------------------------ |
| `team_id`              | string | no       | `""`                  | Apple Developer team identifier. Required for device builds and release exports. |
| `identity`             | string | no       | `"Apple Development"` | Code signing identity. |
| `provisioning_profile` | string | no       | `""`                  | Provisioning profile name or UUID (empty for auto). |
| `auto_signing`         | bool   | no       | `true`                | Use Xcode's automatic signing (`CODE_SIGN_STYLE = Automatic`). |
| `upload_symbols`       | bool   | no       | `true`                | Sets the `uploadSymbols` key in the generated `ExportOptions.plist` used by `--release` exports (controls dSYM inclusion in the `.ipa`; `--release` only — see [spec 05 §`toolchain build`](05-cli-shape.md)). Set to `false` if you don't use a crash-reporting service and want a smaller export artifact; the `.xcarchive` still retains dSYMs for manual upload. |


iOS-only; Android keystore configuration is the analogous `[tool.kivy.android].keystore` block (out of scope for kivy-ios).

### `[tool.kivy.ios.privacy_manifest]`

```toml
[tool.kivy.ios.privacy_manifest]
source = "privacy/PrivacyInfo.xcprivacy"
```

| Field    | Type   | Required | Description                                                                                                                                                                                                                                                                                                                                                     |
| -------- | ------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `source` | string | no       | Repo-relative path to a hand-authored `PrivacyInfo.xcprivacy` plist. When set, `toolchain build` copies this file into the project's Copy Bundle Resources phase as the app-level privacy manifest. When absent, the toolchain generates a **minimal stub** (`NSPrivacyTracking = false`, empty `NSPrivacyTrackingDomains`, `NSPrivacyCollectedDataTypes`, and `NSPrivacyAccessedAPITypes` arrays). |

**App Store requirement.** Apple has required an app-level `PrivacyInfo.xcprivacy` for all new and updated submissions since May 2024. The generated stub is valid for apps that perform no tracking, collect no data, and use none of Apple's [required-reason APIs](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files/describing-use-of-required-reason-api). Any app that *does* use required-reason APIs (file timestamps, system boot time, disk space, active keyboard, user defaults) must supply a `source` declaring them — the stub will be rejected by App Store Connect validation.

**Native xcframework privacy manifests.** Each `.xcframework` in `Frameworks/` (whether wheel-embedded or user-declared via `[tool.kivy.ios.native.xcframeworks]`) must include its own `PrivacyInfo.xcprivacy` **inside the xcframework bundle** if it uses required-reason APIs. This is the responsibility of the framework or wheel author, not kivy-ios. `toolchain doctor` warns if any xcframework in `Frameworks/` is missing a `PrivacyInfo.xcprivacy` entirely (see spec 05).

### `[tool.kivy.ios.info_plist]`

```toml
[tool.kivy.ios.info_plist]
NSCameraUsageDescription = "Used for QR code scanning."
UIFileSharingEnabled = true
```

- **Type**: table of string → string, bool, integer, or list (TOML native types, mapped to plist equivalents).
- **Semantics**: each key/value is merged into the generated `<app>-Info.plist`. Useful for usage-description strings (required by iOS for privacy-sensitive APIs), capability flags, and any other plist key that kivy-ios does not expose through a dedicated schema field.
- **Conflict handling**: user-supplied keys that collide with kivy-ios-managed keys are rejected with a diagnostic listing both the offending key and the kivy-ios field that controls it.

**Kivy-ios-managed `Info.plist` keys** — these are written automatically from the schema and cannot be set via `[tool.kivy.ios.info_plist]`:

| Managed key | Source |
|-------------|--------|
| `CFBundleName` | `[project].name` |
| `CFBundleDisplayName` | `[tool.kivy].display_name` (falls back to `[project].name`) |
| `CFBundleIdentifier` | `[tool.kivy.ios].bundle_id` |
| `CFBundleShortVersionString` | `[project].version` |
| `CFBundleVersion` | `[tool.kivy.ios].build` |
| `MinimumOSVersion` | `[tool.kivy.ios].deployment_target` |
| `UISupportedInterfaceOrientations` | `[tool.kivy].orientation` |
| `UISupportedInterfaceOrientations~ipad` | `[tool.kivy].orientation` (same values; written so iPad honors the declared orientations) |
| `UIRequiresFullScreen` | toolchain (always `true` — Kivy/SDL apps are full-screen and cannot join iPad Split View; also required by Xcode validation when not all four iPad orientations are declared) |
| `LSRequiresIPhoneOS` | toolchain (always `true`) |
| `CFBundlePackageType` | toolchain (always `APPL`) |
| `CFBundleInfoDictionaryVersion` | toolchain (plist format version boilerplate) |
| `CFBundleExecutable` | set by Xcode |
| `NSHumanReadableCopyright` | first `[project].authors` entry's `name` (when present) |

Two generator-written keys are deliberately **not** managed and may be overridden via `[tool.kivy.ios.info_plist]`: `UIApplicationSupportsIndirectInputEvents` (default `true`; SDL3 uses it for indirect input / mouse events — override to opt out) and `UILaunchStoryboardName` (written automatically when `[tool.kivy.ios.splash]` is configured; a user-supplied value takes precedence, for apps that maintain their own launch storyboard).

### `[tool.kivy.ios.xcode.build_settings]`

```toml
[tool.kivy.ios.xcode.build_settings]
SWIFT_VERSION = "5.0"
ENABLE_BITCODE = "NO"
GCC_OPTIMIZATION_LEVEL = "s"
```

- **Type**: table of string → string.
- **Semantics**: each key/value is written into the generated `.xcodeproj`'s build settings (`buildSettings` dictionary) for the application target. Free-form escape hatch for users who need specific Xcode build configurations not exposed elsewhere.
- **Caveats**: `toolchain build` reserves the keys it manages. User-supplied values for any reserved key are rejected with a diagnostic that names the key and the kivy-ios field that controls it. The reserved set is:

| Reserved key | Controlled by |
|---|---|
| `INFOPLIST_FILE` | toolchain (path to generated plist) |
| `PRODUCT_BUNDLE_IDENTIFIER` | `[tool.kivy.ios].bundle_id` |
| `IPHONEOS_DEPLOYMENT_TARGET` | `[tool.kivy.ios].deployment_target` |
| `TARGETED_DEVICE_FAMILY` | toolchain (always `1,2` — iPhone + iPad) |
| `CODE_SIGN_STYLE` | `[tool.kivy.ios.signing].auto_signing` |
| `CODE_SIGN_IDENTITY` | `[tool.kivy.ios.signing].identity` |
| `DEVELOPMENT_TEAM` | `[tool.kivy.ios.signing].team_id` |
| `PROVISIONING_PROFILE_SPECIFIER` | `[tool.kivy.ios.signing].provisioning_profile` |
| `ENABLE_USER_SCRIPT_SANDBOXING` | toolchain (must be `NO` for Build Python phase) |
| `ENABLE_TESTABILITY` | toolchain |
| `FRAMEWORK_SEARCH_PATHS` | toolchain |
| `HEADER_SEARCH_PATHS` | toolchain |
| `GCC_WARN_QUOTED_INCLUDE_IN_FRAMEWORK_HEADER` | toolchain |

See also [spec 06 §"Toolchain-managed build settings"](06-xcode-project-generation.md) for the rationale behind each toolchain-managed entry.

## `[tool.kivy.android]` (reserved)

Defined here purely so p4a/Buildozer can implement the matching overlay using the same shape. Out of scope for kivy-ios 3.0 — kivy-ios ignores it entirely. The expected shape (subject to ratification by the p4a/Buildozer maintainers) mirrors the iOS overlay, including its own independent `schema_version`:

```toml
[tool.kivy.android]
schema_version = 1
package = "org.example.myapp"
target_api = 34
min_api = 26
permissions = ["android.permission.INTERNET"]

[tool.kivy.android.keystore]
# release_keystore = "release.keystore"
# release_alias = "myapp"
```

`[tool.kivy.android].schema_version` is owned and bumped by p4a/Buildozer on its own cadence; kivy-ios neither reads nor enforces it (and vice-versa).

The cross-tool agreement is that **adding a Python dependency to `[project].dependencies` resolves the same way for both platforms**; only the artifact-binding subtables (`[tool.kivy.ios.native.xcframeworks]`, `[tool.kivy.android.native.so_families]` or similar) differ.

## Reserved desktop platform namespaces

The `[tool.kivy]` namespace is intentionally scoped to accommodate future desktop packaging tools that adopt the same `pyproject.toml` shape. The following subtable names are **reserved** — no Kivy tool currently reads or writes them, but third-party tooling or future Kivy desktop packaging solutions should use these keys if they adopt a `pyproject.toml`-based config model:


| Namespace             | Platform                                                                                                                                                                                                                                                                                                                                |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[tool.kivy.windows]` | Windows (all architectures)                                                                                                                                                                                                                                                                                                             |
| `[tool.kivy.macos]`   | macOS                                                                                                                                                                                                                                                                                                                                   |
| `[tool.kivy.linux]`   | Linux, including Raspberry Pi (any architecture). Architecture-specific settings, if needed, belong as sub-keys within `[tool.kivy.linux]` (e.g. `[tool.kivy.linux.aarch64]`) rather than a separate `[tool.kivy.rpi]` namespace — this mirrors how `sys_platform` and `platform_machine` work as separate concepts in PEP 508 markers. |


These namespaces are reserved in the sense that:

- kivy-ios **ignores** any `[tool.kivy.windows]`, `[tool.kivy.macos]`, or `[tool.kivy.linux]` tables it finds (unknown keys are silently passed over by TOML parsers and are not validated).
- Future Kivy tooling that adopts these namespaces should follow the same **additive overlay + independent `schema_version`** convention that `[tool.kivy.ios]` and `[tool.kivy.android]` use.
- App developers may add these tables today without breaking kivy-ios or any current Kivy tool.

## Concrete example

A real-world `pyproject.toml` for a typical Kivy 3.x app, iOS-focused:

```toml
[project]
name = "touchtracer"
version = "1.0.0"
description = "Touchtracer demo"
requires-python = ">=3.15"
dependencies = [
    "kivy>=3.0,<4",
]
authors = [{ name = "Kivy Team", email = "team@kivy.org" }]

[tool.kivy]
display_name = "Touchtracer"
app_dir = "src"
entry_point = "main"
orientation = ["portrait", "portrait-upside-down", "landscape-left", "landscape-right"]

[tool.kivy.ios]
schema_version = 1
bundle_id = "org.kivy.touchtracer"
build = 1
deployment_target = "13.0"

[tool.kivy.ios.python]
version = "3.15.0"

[tool.kivy.ios.icons]
source = "assets/icon.png"        # 1024×1024 PNG

[tool.kivy.ios.splash]
source = "assets/splash.png"
background = "#000000"

[tool.kivy.ios.native.xcframeworks]
# Empty — the kivy wheel bundles every native xcframework it needs.

# find_links = ["wheels"]   # uncomment when vendoring local iOS wheels for lock

# Note: Apple SDK frameworks Kivy uses (Metal for rendering, AVFoundation for
# video, …) are not listed anywhere. They link transitively through the
# dynamic frameworks that reference them; see "System frameworks are not
# declared" above.

[tool.kivy.ios.signing]
team_id = ""
auto_signing = true
```

## Validation rules (toolchain side)

`toolchain lock` and `toolchain build` reject any `pyproject.toml` that:

1. Lacks a `[project]` table or omits `[project].name` / `[project].version`.
2. Lacks `[tool.kivy.ios]` when running an iOS command. (`[tool.kivy]` alone is not a buildable target.)
3. Lacks `[tool.kivy.ios].schema_version` or specifies an unsupported value.
4. Lacks `[tool.kivy.ios].bundle_id`.
5. Has `[tool.kivy].entry_point` that isn't a valid Python identifier (or dotted identifier).
6. Omits `[tool.kivy].app_dir`, or sets it to the project root (`"."`), an empty string, an absolute path, or a path that escapes the project directory. `app_dir` must name a subdirectory of the project.
7. Has `[tool.kivy].orientation` values outside the allowed set.
8. Sets reserved keys under `[tool.kivy.ios.xcode.build_settings]`.
9. Specifies a Python `version` in `[tool.kivy.ios.python]` whose `Python.xcframework` doesn't exist (verified at lock time against python.org).
10. Declares `[project].requires-python` incompatible with `[tool.kivy.ios.python].version`.
11. Sets `[tool.kivy.ios].deployment_target` lower than the minimum iOS version supported by the selected `Python.xcframework` (verified at lock time; the xcframework metadata declares its floor; e.g. Python 3.15 requires iOS 13.0+).
12. Sets `[tool.kivy.ios].find_links` entries that are absolute paths, empty, or paths that escape the project directory.

Validation errors are printed with the offending line number (TOML parsers expose this) and a remediation hint.

