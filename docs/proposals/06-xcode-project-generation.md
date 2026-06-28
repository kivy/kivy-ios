# 06 — Xcode Project Generation

**Status:** rfc-v1 (draft)
**Depends on:** [00-overview](00-overview.md), [01-pyproject-kivy-spec](01-pyproject-kivy-spec.md), [02-pylock-ios-spec](02-pylock-ios-spec.md), [03-artifact-distribution](03-artifact-distribution.md)

This spec defines how `toolchain build` materializes a `pyproject.toml` (with `[tool.kivy]` + `[tool.kivy.ios]` tables) + `pylock.ios.toml` (PEP 751) into a working Xcode project. It adopts the maintainer's project-layout spec verbatim, replaces cookiecutter with programmatic `pbxproj` generation, and pins the integration with python.org's `install_python` helper.

## Build process overview

Building an iOS app with kivy-ios is a four-phase pipeline across two tools:

1. **Collect** (`toolchain build`) — downloads Python.xcframework, native xcframeworks, and Python wheels from python.org, PyPI, and GitHub using `pylock.ios.toml` as the pinned manifest. Artifacts are cached locally to avoid redundant downloads.
2. **Stage** (`toolchain build`) — lays out the downloaded artifacts and the user's app code into an `<app>-ios/` staging directory, and generates the Xcode project file (`<app>.xcodeproj`) via the `pbxproj` library.
3. **Transform** (Xcode "Build Python" Run Script) — calls python.org's `install_python` helper, which converts `.so` C extensions into per-module `.frameworks` (required by the App Store) and lays out the Python stdlib inside the app bundle.
4. **Compile & link** (Xcode) — compiles `main.m` (the Objective-C bootstrap), links against the embedded frameworks, and produces the runnable `<app>.app` bundle.


## Project layout

`toolchain build` produces a `<app>-ios/` folder (sibling to `pyproject.toml`):

```
<app>-ios/
├── <app>.xcodeproj/
├── Python.xcframework/            ← downloaded per pylock.ios.toml
├── Frameworks/                    ← .xcframework archives staged for Link + Embed
│   └── <see "Populating Frameworks/" below — empty by default>

├── app/                           ← user code (per [tool.kivy].app_dir)
│   ├── main.py
│   └── <whatever else>
├── pip-deps/                      ← installed by pip per pylock.ios.toml
│   ├── kivy/
│   ├── PIL/
│   └── ...
├── Resources/
│   ├── icon.png                   ← from [tool.kivy.ios.icons].source
│   ├── splash.png                 ← from [tool.kivy.ios.splash].source
│   └── Assets.xcassets/           ← generated asset catalog
├── main.m                         ← ObjC bootstrap: init Python, launch app
├── <app>-Info.plist
├── PrivacyInfo.xcprivacy          ← generated stub, or copy of [tool.kivy.ios.privacy_manifest].source
└── <app>.entitlements             ← if [tool.kivy.ios.entitlements] table present
```

### Why these folders, not others

- **`Python.xcframework/`** at the project root, per python.org's iOS docs. The Xcode build phase resolves `$(PROJECT_DIR)/Python.xcframework` relative to this location.
- **`Frameworks/`** holds pure-native xcframeworks. Kept separate from `Python.xcframework/` because the latter is special: it's the Python runtime, not just another framework. See "Populating `Frameworks/`" below — empty by default for a vanilla Kivy app.
- **`pip-deps/`** holds installed iOS wheels (Kivy ecosystem wheels + user-declared deps). The "Build Python" Run Script phase processes this folder.
- **`app/`** is a **symlink to the user's `app_dir`** (e.g. `../src` when `app_dir = "src"`). `app_dir` must be a subdirectory — the project root (`"."`) is rejected (see [spec 01](01-pyproject-kivy-spec.md#app_dir--entry_point-interaction)), so the symlink always points at a folder that excludes `<app>-ios/` and the project's non-app files. The user's actual `.py` files are never copied into `<app>-ios/`; the symlink ensures Xcode's folder-reference machinery walks the real source folder on every build. See "Developer iteration workflow" below.
- **`Resources/`** holds non-source assets that need to be in the Xcode "Copy Bundle Resources" phase but aren't Python code.

### Populating `Frameworks/`

Two sources feed `<app>-ios/Frameworks/` at build time:

1. **Wheel-embedded xcframeworks.** Some iOS wheels — notably the kivy iOS wheel — ship their native xcframeworks inside the wheel under a top-level `.frameworks/` directory (see `kivy/kivy` `tools/add-ios-frameworks.py`). After pip installs wheels into `pip-deps/`, `toolchain build` walks every installed wheel for a `.frameworks/` directory and copies each `<name>.xcframework` it finds into `<app>-ios/Frameworks/`. For the canonical Kivy app this is where ANGLE, the SDL3 family, and any other kivy-bundled framework arrive.
2. **User-declared third-party xcframeworks.** Entries in `[tool.kivy.ios.native.xcframeworks]` (pinned in `pylock.ios.toml` as `[[tool.kivy_ios.xcframeworks]]`) are downloaded, SHA-verified, and extracted into `<app>-ios/Frameworks/`. Empty by default.

Both sources flow into the same Xcode Link Binary With Libraries + Embed Frameworks phases. Source (1) covers the entire Kivy dependency set; source (2) is for app-specific extras the Python wheel can't deliver.

> **Privacy manifests in xcframeworks.** Apple requires that any xcframework using [required-reason APIs](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files/describing-use-of-required-reason-api) include its own `PrivacyInfo.xcprivacy` **inside the xcframework bundle** (at `<Name>.xcframework/ios-arm64/PrivacyInfo.xcprivacy` or equivalent per-slice path). This is the responsibility of the framework or wheel author — kivy-ios does not generate or patch privacy manifests for xcframeworks. `toolchain doctor` warns if any `.xcframework` in `Frameworks/` is missing a `PrivacyInfo.xcprivacy` file in all of its slices. The app-level `PrivacyInfo.xcprivacy` (generated or user-supplied, see spec 01) is separate and does not substitute for per-xcframework manifests.

#### Duplicate framework policy

Because two sources feed `Frameworks/` (and a single source can carry the same dependency twice — e.g. two wheels each bundling `Foo.xcframework`), `toolchain build` needs a deterministic rule when two providers contribute an xcframework with the **same framework basename** (`<name>.xcframework`):

1. **Identical → deduplicate silently.** If the two artifacts have the same SHA-256 (or, for wheel-embedded frameworks lacking a pinned hash, the same computed content hash *and* the same version metadata), they are the same artifact. Keep one copy; emit nothing.
2. **Conflicting → fail by default.** If the basename collides but the content hash or version metadata differs, `toolchain build` aborts with a diagnostic that names **both providers** (e.g. the two wheels, or a wheel and a `[tool.kivy.ios.native.xcframeworks]` entry), each artifact's version and SHA-256, and the colliding framework name.
3. **No silent "warn and proceed."** v3.0 never picks a winner on its own. A version mismatch between two copies of the same framework can link successfully and then fail at runtime — a clear build-time failure is strictly better than a latent runtime crash.

A future schema revision may add an explicit per-framework override letting the app author pin which provider wins, but v3.0 deliberately does not guess. The check runs after both sources have been staged and before the pbxproj Link/Embed phases are wired, so a conflict is caught before any Xcode work begins.

## Developer iteration workflow

This section makes explicit how a user's Python edits flow through to a running app, because the choice of symlink-vs-copy for `app/` materially affects the iteration UX.

### The default model

- The user keeps `.py` files in their source subfolder — typically `src/` (with `app_dir = "src"`). `app_dir` must be a subdirectory; the project root (`"."`) is not allowed.
- `toolchain build` creates `<app>-ios/app/` as a **symlink** to `app_dir` (resolved as a relative path from `<app>-ios/`). The symlink is created once on first build and refreshed only if `[tool.kivy].app_dir` changes.
- The Xcode project's pbxproj registers `<app>-ios/app/` as a **folder reference** (blue folder, dynamic). Folder references are walked at *every* Xcode build, so any file added, modified, or deleted in the underlying source folder is picked up automatically. Group references (yellow folders, static) are explicitly not used for source code — that would force the user to manually add new files to the project.

### What the user runs after each kind of change

| Change | Command to run |
|--------|----------------|
| Edit `main.py` or any other `.py` file under `app_dir` | Cmd-R in Xcode, or `toolchain run` |
| Add a `.py` file, subfolder, or asset (PNG, JSON, data file) under `app_dir` | Cmd-R in Xcode (folder reference picks it up) |
| **Any edit to `pyproject.toml`** — dependencies, native xcframeworks, Python version, deployment target, names, bundle id, orientation, icons, splash, signing, entitlements | `toolchain lock && toolchain build` |

The mental model: **`pyproject.toml` describes the *shape* of your app; your Python files are the *content*.** Any edit to `pyproject.toml` goes through `toolchain lock && toolchain build` — the lock's whole-file drift check guarantees the build always matches your committed config, so there's a single rule to remember rather than a per-field one. (A re-lock after a cosmetic change is cheap: dependency resolution is a cache hit and `lock` just rewrites the hash and metadata.) Content changes under `app_dir` flow through normal Xcode rebuilds.

### Why symlink, not copy

Three alternatives, and why we chose the symlink:

| Approach | Iteration UX | Verdict |
|----------|--------------|---------|
| **Symlink (chosen)** | Edit → Cmd-R → see change. No `toolchain build` for source edits. | Best UX. Requires Xcode to follow folder-reference symlinks (it does). |
| Copy each build | Edit → `toolchain build` → Cmd-R → see change. Two-step every time. | Painful inner loop; rejected. |
| Xcode folder reference directly to `app_dir` (no `<app>-ios/app` indirection) | Same iteration UX as symlink. | Adds awkward `../` paths inside the `.xcodeproj`; complicates `install_python`'s folder-walk argument; rejected for the readability/portability cost. |

The symlink approach also has a nice property for source control: the user commits `pyproject.toml`, `pylock.ios.toml`, and their `.py` files. `<app>-ios/` is `.gitignore`-able in its entirety because it's regenerable.

### Practical notes

1. **`app_dir` must be a subdirectory; the project root (`"."`) is rejected.** Because the bundle copy of `app/` mirrors the symlinked source folder verbatim, pointing it at the project root would sweep *everything* into `MyApp.app/app/` (`pyproject.toml`, `.git/`, `.venv/`, `tests/`, `__pycache__/`) **and** recurse the `<app>-ios/` build output into itself. The toolchain therefore refuses `"."` (and empty/absolute/escaping paths) at validation time and directs the user to a subdirectory such as `src/`. A single-file app lives at `src/main.py`. This is why kivy-ios v3.0 needs no per-*file* exclusion mechanism for bundle contents — keeping app code in its own subfolder keeps the bundle clean by construction. (The separate `[tool.kivy.ios].exclude` key prunes unused *packages* from the resolved dependency graph; see [spec 01 §"Excluding unused transitive dependencies"](01-pyproject-kivy-spec.md).)
2. **Adding a new `.py` file**: Xcode folder references usually pick it up on the next build. If Xcode caches stale folder contents (occasional), in the Xcode IDE select Product → Clean Build Folder.
3. **`.gitignore`**: `<app>-ios/` (all of it) is safe to ignore. `pylock.ios.toml` should be committed.
4. **Tests in `tests/`**: if `tests/` lives inside `app_dir`, it will be bundled into the `.app`. To keep tests out of the shipped app, put `tests/` outside `app_dir` (e.g. `tests/` at project root with `app_dir = "src"`).
5. **Editing `<app>-ios/app/<file>.py` directly from Xcode's project navigator** edits the user's real source file (since the navigator's `app/` follows the symlink). There is no "bundle copy" the user might accidentally edit and lose work on — there's the source and there's the build product, full stop.


## Xcode build phases

In order:

1. **Sources** — compiles `main.m`.
2. **Copy Bundle Resources** — copies `Resources/*` and `app/` into the build product. Neither `pip-deps/` nor `Python.xcframework/` is in this phase. `pip-deps/` is platform-sliced (`pip-deps-simulator` / `pip-deps-device`); the **Build Python** Run Script `rsync`s the correct slice into the bundle every build, so a fixed folder reference here would stage the wrong slice for half of all builds (notably simulator `.so` on a device build) ahead of that `rsync`. `Python.xcframework/` is wired with **Embed & Sign** (Link Binary With Libraries + Embed Frameworks, see "pbxproj wiring" below), so Xcode extracts the correct slice as `Python.framework/` into the bundle's `Frameworks/` rather than copying the multi-slice source tree as a resource. The `install_python` Run Script reads the runtime from `$PROJECT_DIR/Python.xcframework` (the project-root source tree), not from the bundle. See "`Python.xcframework/` absent" under "Final app bundle layout".
3. **Build Python** (Run Script) — converts every `.so` in `pip-deps/` and `app/` into a per-module `.framework` in the built app's `Frameworks/` folder. See "The Build Python Run Script" below.
4. **Link Binary With Libraries** — links against each `Frameworks/*.xcframework`.
5. **Embed Frameworks** — copies each `Frameworks/*.xcframework` (selecting the right slice for the target) into the built app's `Frameworks/`, code-signs them.


## The "Build Python" Run Script

The phase's script body wraps the python.org [Python 3.15 iOS docs](https://docs.python.org/3.15/using/ios.html#adding-python-to-an-ios-project) §7.2.2 step 7 call with the slice-selection and slice-copy logic kivy-ios needs (because `pip-deps` is platform-sliced — see "Project layout" and the Copy Bundle Resources note). The generated script (`kivy_ios/project/buildsettings.py` `BUILD_PYTHON_SCRIPT`):

```bash
set -e
# build_utils.sh was renamed to utils.sh in some Python.xcframework builds; try both.
UTILS="$PROJECT_DIR/Python.xcframework/build/build_utils.sh"
if [ ! -f "$UTILS" ]; then UTILS="$PROJECT_DIR/Python.xcframework/build/utils.sh"; fi
source "$UTILS"

# Copy the platform-appropriate pip-deps slice into the app bundle so that
# device and simulator builds never share compiled extension modules.
if [ "$EFFECTIVE_PLATFORM_NAME" = "-iphonesimulator" ]; then
    PIP_DEPS_SRC="$PROJECT_DIR/pip-deps-simulator"
    COLLECT_HINT="toolchain build --simulator"
else
    PIP_DEPS_SRC="$PROJECT_DIR/pip-deps-device"
    COLLECT_HINT="toolchain build --device"
fi

# Fail loudly if this platform's slice was never collected. Xcode picks the
# slice from its own destination, so switching to an uncollected target would
# otherwise ship an app with no dependencies (crash at launch).
if [ ! -d "$PIP_DEPS_SRC" ] || [ -z "$(ls -A "$PIP_DEPS_SRC" 2>/dev/null)" ]; then
    echo "error: $PIP_DEPS_SRC has no collected pip-deps for this platform. Run '$COLLECT_HINT' (or 'toolchain run') first, then rebuild."
    exit 1
fi
mkdir -p "$CODESIGNING_FOLDER_PATH/pip-deps"
rsync -a --delete "$PIP_DEPS_SRC/" "$CODESIGNING_FOLDER_PATH/pip-deps/"

install_python Python.xcframework app pip-deps
```

The final line is **one** call to `install_python`, with **multiple trailing folder arguments**. The python.org docs are explicit: "If you're using a separate folder for third-party packages, ensure that folder is **added to the end of the call** to `install_python` in step 7" (emphasis ours). A single call processes both folders in one pass and ensures the stdlib layout step (see below) runs exactly once. Everything above that line is kivy-ios's slice plumbing: it resolves the active destination's slice, fails fast if it was never collected, and `rsync`s it into the bundle at `pip-deps/` before `install_python` walks it.

What `install_python` does, per the python.org iOS docs (§7.1.4 "Binary extension modules" and §7.2.2 step 7):

1. **Lays out the Python runtime + stdlib** inside the app bundle. Creates a `python/` subfolder with `python/lib/python3.X/` (pure-Python stdlib) and `python/lib/python3.X/lib-dynload/` (stdlib C extensions). The runtime's compiled binaries are extracted from the right slice of `Python.xcframework` for the build configuration.
2. **Walks each trailing folder argument** (`app`, then `pip-deps`) for `.so` files.
3. **For each `.so`**, creates a per-module `.framework` bundle in the **built app's** `Frameworks/` folder, with an `Info.plist` identifying it as a framework. The framework name encodes the full import path — for example, `kivy/_window.abi3.so` becomes `Frameworks/kivy._window.framework/kivy._window`.
4. **Replaces the original `.so`** on `sys.path` with a `.fwork` text marker file containing the framework binary's bundle-relative path.
5. **Writes a `.origin` file** inside the framework pointing back at the `.fwork` marker. Python's `AppleFrameworkLoader` uses both to resolve the import at runtime, and `__file__` ends up reporting as the `.fwork` location.
6. **Copies `<modulename>.xcprivacy`** (per §7.3.2) into the framework as `PrivacyInfo.xcprivacy` if it exists next to the original `.so`.

After this phase, the **build product** has `.fwork` text markers in `pip-deps/` and `app/`, real binaries in `Frameworks/`, and a populated `python/` subfolder. App Store rules are satisfied (no executable binaries outside `Frameworks/`) and `sys.path` resolution works.

Either trailing folder can be empty; `install_python` is a safe no-op for the folder-walk steps in that case. The stdlib layout step still runs.

> **`pip-deps` requires two registrations — both are mandatory.** Passing `pip-deps` to `install_python` handles the *build-time* side: every `.so` C extension inside it is wrapped in a per-module `.framework` and replaced with a `.fwork` marker. That step is necessary but not sufficient for importability. `main.m` must *also* register `pip-deps` as a **site directory** via `site.addsitedir()` (not merely append it to `PYTHONPATH`) — because pip-installed wheels routinely include `.pth` files (namespace packages, editable installs, path-manipulation plugins). Without `addsitedir()`, any package whose presence on `sys.path` depends on a `.pth` hook will be invisibly absent at runtime even though its files exist in the bundle. Neither half can be omitted: skipping the `install_python` argument leaves `.so` binaries outside `Frameworks/` (App Store rejection); skipping `addsitedir()` leaves `.pth`-dependent packages silently unimportable. See "`main.m` step 5" below.

> **`app/` is pure-Python only.** `install_python` wraps any `.so` it finds in `app/`, but it does **not** cross-compile — a `.so` compiled on macOS targets the macOS architecture and will fail to load on an iOS device. Native or Cython extensions must be cross-compiled for iOS and delivered as iOS wheels (installed into `pip-deps/`); they cannot be dropped loose into `app/`. See [spec 03 §"App-specific native extensions"](03-artifact-distribution.md). `toolchain doctor` flags any non-iOS `.so` found under `app/`.


## `main.m` — Python embedding bootstrap

The generated `main.m` is parameterized on `[tool.kivy].app_dir` + `[tool.kivy].entry_point` via generated compile-time defines. `toolchain build` writes:

```c
#define APP_DIR          "@APP_DIR@"
#define ENTRY_POINT      "@ENTRY_POINT@"
```

…into a header included by `main.m`. The actual `main.m` template is fixed; only the header changes per project. Changing `app_dir` or `entry_point` in `[tool.kivy]` triggers a rebuild (header regenerated) without re-templating the whole project.

The `main.m` template, aligned with the [Python 3.15 iOS docs](https://docs.python.org/3.15/using/ios.html#adding-python-to-an-ios-project) §7.2.2 step 8:

1. Sets `PYTHONHOME` to `[[NSBundle mainBundle] resourcePath] + "/python"` — i.e. the `python/` subfolder that `install_python` laid out, **not** the `Python.xcframework/` source-tree path.
2. Sets `PYTHONPATH` to a colon-joined list, in this order:
   - `python/lib/python3.X` (stdlib pure-Python)
   - `python/lib/python3.X/lib-dynload` (stdlib C extensions, now converted to frameworks)
   - `app` (or whatever `APP_DIR` resolved to)
3. Calls `PyPreConfig` with:
   - `utf8_mode = 1` (per python.org docs)
   - `buffered_stdio = 0` (per python.org docs)
   - `write_bytecode = 0` (per python.org docs)
   - `install_signal_handlers = 1`
   - `use_system_logger = 1` (default in 3.13+)
4. Initializes Python via `Py_InitializeFromConfig`.
5. **Registers `pip-deps/` as a site directory** via `site.addsitedir(<resource_path>/pip-deps)` *after* Python init. Per python.org's docs: "If any of the folders that contain third-party packages will contain `.pth` files, you should add that folder as a *site directory* (using `site.addsitedir()`), rather than adding to PYTHONPATH or sys.path directly." Pip-installed wheels frequently include `.pth` files (namespace packages, editable installs), so `pip-deps/` goes through `addsitedir` rather than `PYTHONPATH`. The user-code `app/` folder typically has no `.pth` files and goes on `PYTHONPATH` directly. This pairs with passing `pip-deps` to `install_python` above — both registrations are required for packages in `pip-deps/` to be importable (see the "two registrations" note in the Build Python section).
6. Imports the entry module via `PyImport_ImportModule(ENTRY_POINT)`.
7. Drops into the iOS run loop (UIApplicationMain) — Kivy's iOS hooks take over.

### Why `app/` is on PYTHONPATH but `pip-deps/` is a site directory

This is a python.org-prescribed asymmetry, not a Kivy choice. PYTHONPATH is sufficient for plain folders of `.py` files; site directories additionally process `.pth` files (which add more paths, install custom encodings, run import-time hooks, etc.). User code rarely uses `.pth` files; pip-installed packages routinely do. Following the docs avoids the rare-but-painful "this dep imports fine on macOS but fails on iOS" class of bug.

## pbxproj wiring

The Xcode project file is generated programmatically using the `pbxproj` Python library. The generator at `[kivy_ios/project/](../../kivy_ios/project/)` performs:

### One-time per project (when `<app>.xcodeproj/` doesn't exist)

- Create the project (PBXProject, PBXNativeTarget for the app, configuration list, default build configurations).
- Add the static files (`main.m`, `<app>-Info.plist`, `<app>.entitlements` if present) to the Sources or relevant phases.
- Add `Resources/` to Copy Bundle Resources.
- Add Build Python Run Script phase (with the script body above) between Copy Bundle Resources and the Frameworks phase. Disable "Based on dependency analysis" so it runs every build (or use input/output file lists if we determine which files are inputs).
- Add the **bootstrap baseline** — the frameworks the generated `main.m` shell link-references regardless of dependencies (Foundation, UIKit) — to Link Binary With Libraries. This is the *only* static framework list the toolchain wires. Frameworks needed by *libraries* (Metal, AVFoundation, CoreGraphics, … for Kivy) are **never** declared here: every dependency ships as a **dynamic** framework that records its own SDK dependencies as `LC_LOAD_DYLIB` load commands, and `dyld` resolves them transitively at launch (app → `kivy…framework` → `Metal`/`AVFoundation`/…). See [spec 01 §"System frameworks are not declared"](01-pyproject-kivy-spec.md#system-frameworks-are-not-declared--they-link-transitively).

### Every build (idempotent)

- Sync `Python.xcframework` reference — added with **"Embed & Sign"** selected (per python.org docs §7.2.2 step 5). Listed in Link Binary With Libraries *and* Embed Frameworks for the app target.
- Sync `Frameworks/*.xcframework` references — for each `.xcframework` in `<app>-ios/Frameworks/`, ensure it's in Link Binary With Libraries (if `link = true` in lock) and Embed Frameworks (if `embed = true` in lock). Remove stale entries that no longer exist. No Apple SDK system frameworks are added here — they link transitively through these dynamic frameworks' own load commands (see the bootstrap-baseline note above).
- Sync the `app/` folder reference in Copy Bundle Resources (as a folder reference, not a group reference — preserves the directory structure in the bundle). `pip-deps/` is deliberately **not** a Copy Bundle Resources reference: it is platform-sliced and the Build Python Run Script `rsync`s the correct slice into the bundle (see "The Build Python Run Script"). So the installed packages still show in Xcode's navigator, the `pip-deps-simulator` slice is added as a **browse-only** folder reference (displayed as `pip-deps`, with `create_build_files=False` so it belongs to no build phase and has zero build impact). The package set is identical across slices, so the simulator slice is a fine stand-in for browsing.
- Apply the **toolchain-managed build settings** from the python.org docs §7.2.2 step 6 (see table below).
- Apply `[tool.kivy.ios.xcode.build_settings]` entries to the app target's build configurations. Reject any reserved keys (managed by toolchain) with a diagnostic.
- Apply `[tool.kivy.ios.info_plist]` keys into `<app>-Info.plist` (merged with kivy-ios-managed keys; user-supplied keys that conflict with managed keys are rejected with a diagnostic).
- Apply `[tool.kivy.ios.entitlements]` to `<app>.entitlements` (regenerate the plist).
- Apply `[tool.kivy.ios.signing]` to the build settings (`CODE_SIGN_STYLE`, `DEVELOPMENT_TEAM`, `PROVISIONING_PROFILE_SPECIFIER`).
- Regenerate `PrivacyInfo.xcprivacy`: copy `[tool.kivy.ios.privacy_manifest].source` if set, otherwise write the minimal stub. Ensure the file is in the Copy Bundle Resources phase (added on first build, verified on subsequent builds).

### Toolchain-managed build settings (python.org §7.2.2 step 6)

The pbxproj generator sets the following on every app target build configuration. Users cannot override these via `[tool.kivy.ios.xcode.build_settings]` (they're on the reserved list — see [spec 01 §`[tool.kivy.ios.xcode.build_settings]`](01-pyproject-kivy-spec.md) for the full reserved set):

| Setting | Value | Why |
|---------|-------|-----|
| `ENABLE_USER_SCRIPT_SANDBOXING` | `NO` | Xcode 15+ sandboxes Run Script phases by default; the Build Python phase needs to write into the build product, which requires the sandbox off. |
| `ENABLE_TESTABILITY` | Debug: `YES`, Release: `NO` | Testability emits extra symbol visibility (for `@testable import`) and disables some cross-module optimization — useful for Debug/test hosts, but pointless overhead in a shipping app. Scoped per-configuration so Release archives stay lean. Unrelated to crash-report dSYMs (see `DEBUG_INFORMATION_FORMAT`). |
| `DEBUG_INFORMATION_FORMAT` | Debug: `dwarf`, Release: `dwarf-with-dsym` | Guarantees a `.dSYM` bundle is produced for Release archives so crashes can be symbolicated. This is what crash-reporting services (Sentry, Crashlytics, App Store Connect) consume — it is independent of `[tool.kivy.ios.signing].upload_symbols`, which only controls upload to App Store Connect. Managed (not left to Xcode defaults) so a stray `[tool.kivy.ios.xcode.build_settings]` override can't silently disable dSYM generation. |
| `FRAMEWORK_SEARCH_PATHS` | `$(PROJECT_DIR)` | So the linker finds `Python.xcframework` and `Frameworks/*.xcframework`. |
| `HEADER_SEARCH_PATHS` | `"$(BUILT_PRODUCTS_DIR)/Python.framework/Headers"` | For any C code that links against the Python C API. |
| `LD_RUNPATH_SEARCH_PATHS` | `$(inherited) @executable_path/Frameworks` | Every embedded dynamic framework (`Python.xcframework`, the SDL3/ANGLE family, wheel-embedded and SPM frameworks) is loaded via `@rpath` at runtime. Managed explicitly so the runpath is correct regardless of which provider triggers embedding, rather than relying on pbxproj's embedding side effects. `$(inherited)` preserves any project- or xcconfig-level runpaths. |
| `GCC_WARN_QUOTED_INCLUDE_IN_FRAMEWORK_HEADER` | `NO` | Suppresses warnings from Python.framework headers. |
| `COPY_PHASE_STRIP` | `NO` | The SDL3 family and `Python.xcframework` ship ad-hoc code-signed; Xcode's built-in default (`YES`) tries to strip them while embedding and warns "not stripping binary because it is signed". `NO` matches Xcode's own template default and silences the warning. The app binary is still stripped via `STRIP_INSTALLED_PRODUCT` on Release archives — this only governs the copy/embed phase. |
| `ASSETCATALOG_COMPILER_APPICON_NAME` | `AppIcon` *(only when `[tool.kivy.ios.icons].source` is set)* | Designates the generated `AppIcon` set in `Assets.xcassets` as the app icon. Without it the catalog still compiles, but Xcode assigns no icon and the `AppIcon.appiconset` is silently ignored. Emitted only when an icon is configured, so projects without one don't trigger Xcode's "missing AppIcon set" warning. |

Beyond the build settings above, the generator sets the project's `LastUpgradeCheck` attribute to the **installed Xcode's version** — detected via `xcodebuild -version` and encoded as Xcode's integer version code (e.g. Xcode 26.5 → `2650`), with a built-in constant as fallback when Xcode can't be queried. Xcode shows the "Update to recommended settings" banner whenever `LastUpgradeCheck` is below the running Xcode; pinning it to the detected version suppresses that prompt without applying Xcode's recommendations — several of which (notably `ENABLE_USER_SCRIPT_SANDBOXING = YES`) would break the Build Python phase. It is refreshed on every build, so it tracks Xcode upgrades automatically rather than going stale at a hardcoded version. Detection happens in `toolchain build` (the CLI layer); the project generator itself stays hermetic and simply receives the value.

### Idempotency

Re-running `toolchain build` on an existing project produces the same `.xcodeproj` content (modulo the UUIDs `pbxproj` generates). We sort entries deterministically inside each phase to minimize diff churn.

## Information flow

```
pyproject.toml
([project] + [tool.kivy.*])
     │
     ▼
toolchain lock ──────────────────────────────────► PyPI / python.org  (resolve only)
     │
     ▼
pylock.ios.toml
(PEP 751 + [tool.kivy_ios])
     │
     ▼                          download / cache
toolchain build ───────────►   ┌──────────────────┐◄── python.org   (Python.xcframework)
                               │                  │◄── PyPI         (wheels)
                               │                  │◄── GitHub       (xcframeworks)
                               └────────┬─────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
          Python.xcframework/     Frameworks/           pip-deps/
          app/ (symlink)          <app>.xcodeproj
                                        │
                                        ▼
                                   xcodebuild
                                        │
                                        ▼
                               <app>.app  (per-module .frameworks
                                          built by install_python)
```


## Generated file inventory (per project)

| File | Source | Regenerated by toolchain build? |
|------|--------|----------------------------------|
| `<app>.xcodeproj/project.pbxproj` | pbxproj generator | Yes (idempotent merge) |
| `<app>.xcodeproj/xcshareddata/...` | static template | One-time |
| `main.m` | static template | One-time |
| `main_config.h` | per-build (APP_DIR + ENTRY_POINT defines) | Yes |
| `<app>-Info.plist` | template + `[project]` + `[tool.kivy.ios]` + `[tool.kivy.ios.info_plist]` | Yes (regenerated) |
| `<app>.entitlements` | template + `[tool.kivy.ios.entitlements]` | Yes (regenerated) |
| `PrivacyInfo.xcprivacy` | generated minimal stub, or copy of `[tool.kivy.ios.privacy_manifest].source` | Yes (regenerated) |
| `Resources/Assets.xcassets/` | generated from `[tool.kivy.ios.icons]` + `[tool.kivy.ios.splash]` (omit either to skip that asset) | Yes |
| `Python.xcframework/` | download | Yes (cache-hit-able) |
| `Frameworks/*.xcframework` | downloads | Yes (cache-hit-able) |
| `pip-deps/` | `pip install --target` | Yes (cache-hit-able) |
| `app/` | symlink/copy from user code | Yes |

## Final app bundle layout

`toolchain build` produces the `<app>-ios/` source tree (step 1). Xcode then compiles and runs the "Build Python" Run Script phase, which calls `install_python` to transform that tree into the shipped `.app` bundle (step 2). The final bundle on-device looks like:

```
<app>.app/
├── <app>                          ← compiled Mach-O binary (from main.m)
├── Info.plist
├── PrivacyInfo.xcprivacy          ← app-level privacy manifest (generated stub or user-supplied)
├── Frameworks/
│   ├── Python.framework/          ← sliced from Python.xcframework by Xcode
│   ├── <lib>.<ext>.framework/     ← per-module frameworks created by install_python
│   │   ...                           (one per .so found in pip-deps/ and app/)
│   ├── ANGLE.xcframework/         ← native xcframeworks from Frameworks/ (embedded)
│   └── ...
├── python/                        ← Python runtime + stdlib, laid out by install_python
│   └── lib/
│       └── python3.X/
│           ├── *.py               ← pure-Python stdlib
│           └── lib-dynload/
│               └── *.fwork        ← text markers → Frameworks/<module>.framework
├── app/                           ← user Python code (copied from symlink)
│   ├── main.py
│   ├── *.fwork                    ← any .so in app/ replaced with .fwork markers
│   └── ...
├── pip-deps/                      ← installed wheels; .so replaced with .fwork markers
│   ├── kivy/
│   │   ├── __init__.py
│   │   └── _window.fwork
│   └── ...
└── Resources/
    ├── icon.png
    ├── splash.png
    └── Assets.xcassets/
```

Key transformations `install_python` makes between the source tree and the bundle:

- **`.so` → `.fwork` + `.framework`**: every C extension in `pip-deps/` and `app/` is wrapped in a `.framework` bundle under `Frameworks/` and replaced in-place with a `.fwork` text marker. App Store rules prohibit executable binaries outside `Frameworks/`; this satisfies them.
- **`python/` created**: the Python stdlib and runtime are extracted from the correct `Python.xcframework` slice and laid out under `python/lib/python3.X/`. Stdlib C extensions in `lib-dynload/` are similarly converted to `.fwork` markers.
- **`Python.xcframework/` absent**: Xcode's Embed Frameworks phase extracts the right slice as `Python.framework/` into `Frameworks/`; the source-tree `Python.xcframework/` directory is not copied into the bundle.

