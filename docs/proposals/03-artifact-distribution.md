# 03 — Artifact Distribution

**Status:** rfc-v1 (draft)
**Depends on:** [00-overview](00-overview.md), [01-pyproject-kivy-spec](01-pyproject-kivy-spec.md), [02-pylock-ios-spec](02-pylock-ios-spec.md)
**Consumed by:** [06-xcode-project-generation](06-xcode-project-generation.md)

This spec defines **where artifacts live**, **how they're signed and verified**, **how kivy-ios consumes them**, and **how lockfile entries map to project folders**.

## Three distribution channels, deliberately

kivy-ios 3.0 sources native dependencies through three deliberate channels, each matched to the shape the artifact naturally takes:

1. **iOS wheels** — for Python packages with C extensions (Kivy itself, pyobjus, the iOS support package, pillow, numpy, etc.), distributed via pip-compatible indexes. The natural shape for things Python imports.
2. **`.xcframework` archives** — for pure-native libraries that aren't bundled inside any Python wheel, distributed as zip or tarball archives. The natural shape for things Xcode links and embeds. In the canonical Kivy app this channel goes unused: the kivy iOS wheel bundles every xcframework it links against (ANGLE, SDL3 family) inside the wheel under `.frameworks/`. The channel exists for apps that need *additional* third-party native libraries.
3. **Swift Package Manager packages** — for third-party iOS libraries that ship *only* as SPM packages (binary, source, or hybrid), with no standalone `.xcframework` release asset. Declared by Git URL (or local path) and resolved by Xcode. The natural shape for the growing set of SDKs distributed solely through SPM. Full design in [spec 07](07-swift-packages.md).

The first two channels share one consumption model: **kivy-ios downloads the artifact, verifies its SHA-256, and stages it into `<app>-ios/`.** The third is deliberately different — **Xcode owns the full SPM lifecycle** (resolve, fetch, compile, embed); kivy-ios only emits the package references and pins the resolved Git revision (plus a generated `Package.resolved`) in the lock. That is a documented deviation from the content-hash rule, scoped to SPM, and it does not reopen the recipe wound: the invariant that matters is *kivy-ios runs no from-source build pipeline of its own*, and Xcode's first-class package manager is categorically different from a bespoke kivy-ios recipe system (see [spec 07 §"How this reconciles with the 'no on-mac compilation' principle"](07-swift-packages.md)).

## App-specific native extensions (Cython / C)

A natural question: what if the *app author* writes their own native code — a Cython module, a hand-written C extension, or any package with a compiled component — that isn't published anywhere? It's neither a third-party dependency nor a Kivy artifact, so which channel does it use?

The answer follows directly from the architecture's core rule: **kivy-ios runs no from-source build pipeline of its own — it does not cross-compile Python C extensions; it consumes pre-built wheels.** A user-authored extension is just an artifact that doesn't exist yet, so it must be **built into an iOS wheel out-of-band and then consumed exactly like any other dependency** (channel 1 above). kivy-ios has no recipe/compile step for Python extensions in `toolchain build`, by design. (The one exception to "kivy-ios compiles nothing" is SPM source packages, which **Xcode** — not kivy-ios — compiles via its own first-class package manager; see channel 3 above and [spec 07](07-swift-packages.md). That does not apply to Python C extensions, which always arrive as wheels.)

Concretely, an author with a custom extension:

1. Packages it as a normal distribution (its own `pyproject.toml` / `setup.py`).
2. Cross-builds iOS wheels for it using the standard Python iOS build tooling — `cibuildwheel` with iOS support, or the python.org / Briefcase iOS build flow. This is the same out-of-band CI path Kivy uses to publish its own iOS wheels (`[spec 04](04-recipe-triage.md)` §"Kivy-published iOS wheels"); kivy-ios does not reimplement it.
3. Consumes the wheel one of two ways, both of which flow through `pip-deps/` and the `install_python` framework conversion like every other binary wheel:
   - **Hosted** — publish it (PyPI under a name the author owns, or a private/supplemental index) and reference it by name in `[project].dependencies`. Best when the wheel is shared across projects.
   - **Vendored** — commit the built wheel into the repo (e.g. `wheels/`) and let the lockfile pin it by `path`. `toolchain lock` records a repo-relative `path` + SHA-256 in `[[packages.wheels]]` (see [spec 02 §"Locally built wheels"](02-pylock-ios-spec.md)). Best when the wheel is app-specific and the author wants it versioned alongside the app.

   Either way, the artifact is **never compiled by kivy-ios** — it must already be a cross-built iOS wheel. Use a repo-relative path, not an absolute one; absolute paths aren't portable across clones or CI and are rejected by `toolchain build`.

**Corollary — `app/` is pure-Python only.** The user's `app_dir` (symlinked as `app/`, see `[spec 06](06-xcode-project-generation.md)`) is for `.py` source. The `install_python` step *will* wrap any `.so` it finds in `app/` into a per-module framework, but it does **not** cross-compile — so a `.so` that the author compiled locally on macOS is a macOS-architecture binary and will fail to load on an iOS device. Native code belongs in a wheel, never loose in `app/`. `toolchain doctor` flags a non-iOS `.so` found under `app/`.

The common case — *using* `pyobjus` to reach Objective-C / system frameworks (`NSURLSession`, `Vision`, etc.) — does **not** hit any of this. `pyobjus` bridges to Objective-C dynamically at runtime, so the app author writes pure Python; `pyobjus` itself arrives as a pre-built Kivy iOS wheel (`[spec 04](04-recipe-triage.md)`). No author-side compilation is involved.

## Distribution channel 1: iOS wheels

### Source registry: PyPI direct, plus configurable supplemental indexes

Every iOS wheel that Kivy itself publishes goes to PyPI proper under canonical names. For packages whose upstream maintainers haven't yet published iOS-tagged wheels to PyPI, `toolchain` resolves through one or more configurable supplemental indexes; each resolved wheel's URL is then pinned directly in `[[packages.wheels]]` in the lockfile.

PEP 621 `[project].dependencies` entries in the user's `pyproject.toml` are resolved against PyPI. For packages not yet publishing iOS wheels on PyPI, users can declare one or more `extra_index_urls` in `[tool.kivy.ios]`; `toolchain lock` passes these to pip as `--extra-index-url` when resolving. Each resolved wheel's source URL is pinned in `[[packages.wheels]]` in the lockfile regardless of which index supplied it, keeping builds reproducible.

Two categories of wheel ship through this channel:

1. **Upstream-published iOS wheels** — Pillow, numpy, matplotlib, cryptography, pyyaml (as upstream publishes), pycryptodome, kiwisolver, etc. Consumed directly from PyPI under canonical names.
2. **Kivy-owned PyPI names with iOS wheels uploaded by Kivy** — `kivy` and `pyobjus`. iOS-tagged wheels (`ios_13_0_arm64_iphoneos`, `ios_13_0_arm64_iphonesimulator`, `ios_13_0_x86_64_iphonesimulator`) are published alongside any existing desktop wheels under the same package name. Because the build host is macOS, `toolchain` passes `--platform ios_13_0_arm64_iphoneos` (and equivalent slices) to pip so that the iOS wheels are selected rather than the macOS ones.

Wheel sourcing is implicit: every PEP 508 string in `[project].dependencies` resolves to a PyPI URL (or to a supplemental-index URL when PyPI doesn't carry the needed iOS slice — see the `extra_index_urls` discussion above). The user does not annotate `source = ...` per wheel; `toolchain lock` resolves each dependency and pins the resolved wheel URL in `pylock.ios.toml`:

```toml
[project]
dependencies = [
    "kivy>=3.0",       # PyPI; canonical kivy
    "requests",        # PyPI; pure-Python from upstream
]
```


Binary wheels follow [PEP 730](https://peps.python.org/pep-0730/) platform tags (`ios_13_0_arm64_iphoneos`, `ios_13_0_arm64_iphonesimulator`, `ios_13_0_x86_64_iphonesimulator`); pure-Python wheels use `py3-none-any`.

### Wheel content rules

To ensure the python.org `install_python` framework conversion works correctly, iOS wheels in the Kivy ecosystem must:

- Contain `.so` files only at importable paths (not in arbitrary subdirectories that aren't on `sys.path`).
- Place a `<modulename>.xcprivacy` file next to each `.so` if the module uses APIs covered by Apple's privacy manifest rules. `install_python` copies these into the generated per-module framework as `PrivacyInfo.xcprivacy`.
- Not contain executables (Apple's App Store rule: only the main app binary is allowed). 

Pure-Python wheels have no such constraints.

### Apple SDK frameworks need no declaration (all-dynamic linking)

Apple SDK frameworks (`Metal`, `AVFoundation`, `CoreGraphics`, …) and SDK libraries (`sqlite3`, …) are shipped by iOS, so they are never bundled. They also do **not** need to be enumerated by the app or by any wheel manifest, because every native artifact in the 3.0 model is a **dynamic** framework:

- The kivy wheel's bundled xcframeworks (ANGLE, SDL3 family), the per-module `.framework`s `install_python` builds from each `.so`, and `Python.framework` are all dynamic. Each records the SDK frameworks it needs as `LC_LOAD_DYLIB` load commands in its own Mach-O, fixed when that framework was built.
- At launch `dyld` resolves those dependencies transitively (app → `kivy…framework` → `Metal`/`AVFoundation`/…). The app target only link-references the Foundation/UIKit symbols its `main.m` bootstrap uses; everything else flows through the dynamic frameworks' own load commands.

The 2.x recipe model needed an explicit per-framework list (`recipe.pbx_frameworks`) only because it linked **static** libraries into the app binary, forcing the app target to resolve every transitive system symbol. The all-dynamic 3.0 model removes that need entirely — there is no `ios-system-frameworks.toml` manifest, no `system_frameworks` key, and no scan step. See [spec 01 §"System frameworks are not declared"](01-pyproject-kivy-spec.md) and [spec 06](06-xcode-project-generation.md).

### Signing and verification

- All wheels published to PyPI are subject to PyPI's own integrity model (HTTPS + the [PEP 740](https://peps.python.org/pep-0740/) attestations once stable).
- The lockfile pins each wheel's SHA-256. `toolchain build` verifies before extraction.


## Distribution channel 2: `.xcframework` archives

### Source registries

`[tool.kivy.ios.native.xcframeworks]` entries in the user's `pyproject.toml` are resolved against one of:

1. **Upstream library publishers** for libraries that ship their own iOS xcframeworks. For v3.0:
   - **`Python.xcframework`** — the foundational artifact. python.org publishes the iOS XCFramework directly as a release artifact alongside the existing macOS pkg, starting with [Python 3.15.0b1 (May 7, 2026)](https://www.python.org/downloads/release/python-3150b1/). URL pattern: `https://www.python.org/ftp/python/<X.Y.Z>/python-<version>-iOS-XCframework.tar.gz`.
2. **Third-party xcframework publishers** for app-specific native dependencies that aren't bundled inside any Python wheel. Users declare these in `[tool.kivy.ios.native.xcframeworks]`. Empty in the canonical Kivy case.
   - **Locally built / vendored frameworks** are a sub-case: an author who builds their own `.xcframework` can commit it into the repo and point `source` at a repo-relative path instead of a URL (see [spec 01 §`[tool.kivy.ios.native.xcframeworks]`](01-pyproject-kivy-spec.md)). `toolchain lock` reads the local artifact, computes its SHA-256, and pins the relative `path` in `pylock.ios.toml` — the same reproducibility model as a vendored wheel.

The `source` value in `[tool.kivy.ios.native.xcframeworks]` is always **explicit** — a direct download URL (registries 1–3) or a repo-relative path (the vendored sub-case under 2). There are no magic indirection strings; the user states exactly where the artifact comes from, and `toolchain lock` reads it to pin the SHA-256 and slice list.

### Archive formats

The runtime supports two archive formats for `.xcframework` artifacts:

| Format | When used | Extraction |
|--------|-----------|------------|
| `.xcframework.zip` | Default for Kivy-built artifacts | Standard zip extraction |
| `.tar.gz` | Alternate for Kivy-built artifacts | tarfile extraction |

**Locating the xcframework inside the archive.** When the archive contains exactly one top-level `.xcframework` directory (the common case), the runtime auto-detects it — no extra configuration. When an archive instead bundles **multiple** xcframeworks or sibling files alongside the one you want, the lockfile's `[[tool.kivy_ios.xcframeworks]].archive_member` (see [spec 02 §`[[tool.kivy_ios.xcframeworks]]`](02-pylock-ios-spec.md)) names the exact directory to extract, and `toolchain build` honors it rather than guessing. `archive_member` is omitted whenever auto-detection suffices. See spec 02 for the full lockfile schema.

## Distribution channel 3: Swift Package Manager packages

Unlike channels 1 and 2, this channel is **not** an artifact kivy-ios downloads, verifies, and stages. The user declares an SPM package in `[tool.kivy.ios.native.swift_packages]` (Git URL or local path + version requirement + products); `toolchain lock` resolves it to a concrete Git **revision** and records the pin in `pylock.ios.toml`; `toolchain build` emits the package references into the generated `.xcodeproj` and writes a `Package.resolved`. From there **Xcode** resolves, fetches, compiles (for source/hybrid packages), and embeds — kivy-ios writes no build logic and computes no output hash.

Consequently this channel's registry, archive-format, and SHA-256 verification concerns (channels 1–2 above) do not apply: integrity comes from the pinned revision (and, for binary targets, SPM's own `.binaryTarget` checksum that Xcode verifies on fetch). The complete schema, resolution semantics, pbxproj wiring, and reproducibility rationale live in [spec 07](07-swift-packages.md); this section exists only to give SPM a home alongside the channel 1 and channel 2 sections.

## Lockfile-entry to project-folder mapping

`toolchain build` materializes the lockfile into the generated `<app>-ios/` per these rules:

| Lockfile entry (in `pylock.ios.toml`) | Target folder | Why |
|---------------------------------------|---------------|-----|
| `[[packages.wheels]]` with `name` ending `-py3-none-any.whl` | `pip-deps/` | Pure-Python; just unpacked. |
| `[[packages.wheels]]` with `name` containing `ios_..._iphoneos` | `pip-deps/` (when building for device) | The Xcode "Build Python" phase converts `.so` → `.framework`. |
| `[[packages.wheels]]` with `name` containing `ios_..._iphonesimulator` | `pip-deps/` (when building for simulator) | Same. |
| `[[tool.kivy_ios.xcframeworks]]` | `Frameworks/` | Xcode handles linking and embedding. |
| `[tool.kivy_ios.python_xcframework]` | `Python.xcframework/` at the project root | Foundational; `install_python` reads from here. |
| `[[tool.kivy_ios.swift_packages]]` | *(no folder)* — pbxproj package references + `Package.resolved` | Xcode resolves, fetches, compiles, and embeds; kivy-ios stages nothing (see channel 3 and [spec 07](07-swift-packages.md)). |

`toolchain build` does not commingle wheels and xcframeworks; the two folders have disjoint contents and disjoint Xcode phase semantics:

- `pip-deps/` (and `app/`) are processed by the **Build Python** Run Script phase via a single `install_python Python.xcframework app pip-deps` call (per [Python 3.15 iOS docs §7.2.2 step 7](https://docs.python.org/3.15/using/ios.html#adding-python-to-an-ios-project)). `install_python` walks both folders, converts each `.so` to a per-module `.framework` under the built app's `Frameworks/`, and replaces each `.so` with a `.fwork` text marker (see [spec 06](06-xcode-project-generation.md)). The `.so` files briefly visible in the staged bundle between Copy Bundle Resources and the Run Script phase are an intermediate state, not a violation — by Embed Frameworks time and archive time, every binary lives under `Frameworks/`.
- `Frameworks/*.xcframework` are registered in the pbxproj's **Link Binary With Libraries** and **Embed Frameworks** phases. `install_python` does not touch them; they're already in the canonical framework shape.

