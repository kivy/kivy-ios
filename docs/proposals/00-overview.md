# 00 — kivy-ios 3.0 Modernization: Overview

**Status:** rfc-v1 (draft)
**Audience:** kivy-ios maintainers, p4a/Buildozer maintainers, the Kivy core team, advanced Kivy app authors.

This RFC set proposes a major modernization of `kivy-ios` into a thin iOS bundler aligned with the official Python 3.15+ iOS support model. Python.org now ships a `Python.xcframework` plus a `build_utils.sh` / `install_python` helper that handles the App Store-compliant conversion of binary extension modules into per-module frameworks. This obviates most of what kivy-ios does today: building Python from source, building OpenSSL/libffi, managing host-vs-target Python, and the entire recipe build framework on the user's mac.

## What changes

kivy-ios 3.0 becomes a **declarative iOS bundler** with three responsibilities:

1. Read a user-authored `pyproject.toml` (`[project]` per PEP 621, plus `[tool.kivy]` / `[tool.kivy.ios]` for Kivy-specific intent) and emit a `pylock.ios.toml` (PEP 751-conformant, SHA-pinned build manifest with a `[tool.kivy_ios]` extension for the Python.xcframework and native xcframeworks).
2. Materialize the lockfile into a generated Xcode project: download Python.xcframework, install iOS-tagged wheels into `pip-deps/`, drop pinned `.xcframework` archives into `Frameworks/`, and wire pbxproj so Xcode handles signing, linking, and embedding the right way. The Xcode "Build Python" Run Script phase (a single `install_python Python.xcframework app pip-deps` invocation, per [Python 3.15 iOS docs §7.2.2 step 7](https://docs.python.org/3.15/using/ios.html#adding-python-to-an-ios-project)) converts every `.so` in `app/` and `pip-deps/` into a per-module `.framework` in the built app's `Frameworks/` folder, replacing each `.so` with a `.fwork` text marker. The final `.ipa` thus has only `.fwork` markers in `app/` and `pip-deps/` and real binaries in `Frameworks/` — satisfying the App Store rule that all executable binaries live under `Frameworks/`.
3. Run Xcode builds, simulators, and basic health diagnostics through a small CLI.

It is **no longer** responsible for:

- Building Python or OpenSSL or libffi (use Python.xcframework).
- Compiling C/C++ libraries from source through a kivy-ios build pipeline (use pre-built artifacts produced by a separate Kivy-owned central builder). The lone exception is Swift Package Manager *source* dependencies, which **Xcode's** own package manager compiles — kivy-ios writes no build logic for them; see [spec 07](07-swift-packages.md).
- Compiling Python extension modules from source on the user's mac (use iOS wheels).
- Maintaining ~50 recipes (those that survive relocate to per-library Kivy-owned sibling builder repos following the `kivy/<library>-builder` pattern; pure-Python and Python-with-C-extension wheels publish to PyPI).

## Design decisions

- **Python 3.15+ only.** Hard break with the legacy `python3`/`hostpython3`/`hostopenssl`/`openssl`/`libffi`/SDL2 recipes.
- **Single `pyproject.toml`, PEP-aligned.**  Cross-platform metadata + Python dependencies live in PEP 621 `[project]` and Kivy-cross-platform `[tool.kivy]`; iOS-specific bits live in `[tool.kivy.ios]`; an analogous `[tool.kivy.android]` overlay is reserved for p4a/Buildozer. **This is the cross-platform harmonization point with the Android tooling modernization.** See spec 01.
- **Reproducible `pylock.ios.toml` (PEP 751).** The standard `[[packages]]` section is PEP 751-shaped and is intended to remain consumable by PEP 751-aware installers; kivy-ios itself drives the iOS install from the pinned per-slice wheel URLs and hashes rather than depending on a generic installer's lockfile reader (pip's `-r pylock.toml` support is experimental as of 26.1). Kivy-specific bits (Python.xcframework, native xcframeworks, per-wheel source-index provenance) live in the PEP 751-permitted `[tool.kivy_ios]` extension table, and kivy-ios does not depend on any installer understanding that table. Android tooling gets a parallel `pylock.android.toml` with a `[tool.kivy_android]` extension. See spec 02.
- **Hybrid artifact distribution.** Python packages with C extensions ship as iOS wheels (standard PEP 751 `[[packages]]`); pure-native libraries ship as `.xcframework` archives (Kivy-extension `[[tool.kivy_ios.xcframeworks]]`). See spec 03.
- **Project layout** Generated `<app>-ios/` contains `Python.xcframework/`, `Frameworks/`, `pip-deps/`, `app/`, plus an Xcode "Build Python" Run Script phase between Copy Bundle Resources and Embed Frameworks. See spec 06.
- **Xcode project generated programmatically via `pbxproj`.** Cookiecutter dropped because Link/Embed/Run Script wiring is far easier to do programmatically. See spec 06.
- **`toolchain init` requires `pyproject.toml`.** Init reads the user's existing `pyproject.toml` and adds/updates `[tool.kivy]` + `[tool.kivy.ios]` — it never modifies `[project]` or any other non-kivy namespace. If `requirements.txt` is found but no `pyproject.toml`, init exits non-zero with a migration pointer telling the user to transfer their dependencies manually. Authoritative version pinning is deferred to `toolchain lock` / `pylock.ios.toml`. See spec 05.
- **Most recipes die; the survivors relocate.** The majority of the ~50 existing recipes are simply deleted — obsoleted by Python.xcframework, by Kivy 3.x dropping SDL2, or by the package now installing straight from PyPI. The minority that survive split two ways: xcframework builds into `kivy/kivy`'s iOS wheel; Python wheels into per-package PyPI publishing pipelines. PyPI is the convergence target; a Kivy-run fallback index stays open as an option if upstream publication lags. See spec 04.
- **Transition model: recipe-free.** kivy-ios 3.0 ships with no recipe system; see the per-recipe disposition table in spec 04.
- **Wheel distribution: PyPI direct, with one or more configurable fallback indexes.** PyPI is always the primary resolution source. The ecosystem is mid-transition to iOS-tagged wheels on PyPI proper, so `toolchain` lets users configure one or more supplemental iOS-wheel indexes to cover packages whose upstream maintainers haven't yet published iOS wheels to PyPI. The `[tool.kivy.ios].extra_index_urls` list is plural-by-design, channel-agnostic, and empty by default; whether a configured channel is third-party-operated or Kivy-operated is an organizational question outside the scope of this tool. As more packages ship iOS wheels on PyPI proper, configured fallback indexes go quiet on their own.
## Reading order

| # | Spec | Purpose |
|---|------|---------|
| 00 | This document | Modernization narrative + key decisions + reading order |
| 01 | [pyproject.toml `[tool.kivy]` / `[tool.kivy.ios]` spec](01-pyproject-kivy-spec.md) | Full schema for project intent |
| 02 | [pylock.ios.toml spec](02-pylock-ios-spec.md) | PEP 751 lockfile + Kivy extension for the resolved build manifest |
| 03 | [Artifact distribution](03-artifact-distribution.md) | Where artifacts live, how they're signed and consumed |
| 04 | [Recipe triage](04-recipe-triage.md) | Per-recipe disposition table for the ~50 existing recipes |
| 05 | [CLI shape](05-cli-shape.md) | New verbs, legacy-verb disposition |
| 06 | [Xcode project generation](06-xcode-project-generation.md) | Project layout, pbxproj wiring, Build Python phase |
| 07 | [Swift Package Manager dependencies](07-swift-packages.md) | SPM (binary + source) as a third native-dependency channel, with Xcode owning the SPM lifecycle |


## Out of scope for kivy-ios 3.0

- Android: kivy-ios is iOS-only. The `[tool.kivy.android]` overlay and `pylock.android.toml` are documented as the **harmonization shape** so p4a/Buildozer can adopt the matching layout, but kivy-ios does not produce Android builds.
- Multi-platform abstraction: kivy-ios remains iOS-only — no "build for both" verbs.
- A new artifact format or registry: we reuse PyPI for wheels and GitHub Releases for xcframeworks, and do not stand up a new package format. Whether any iOS-wheel index in the resolution chain is operated by Kivy or by a third party is an organizational question outside the scope of this tool — the supplemental-index mechanism is agnostic.
- Desktop platforms: `[tool.kivy.windows]`, `[tool.kivy.macos]`, and `[tool.kivy.linux]` are **reserved namespaces** in the `[tool.kivy]` schema (see spec 01) for future desktop packaging tools that may adopt the same `pyproject.toml` shape. kivy-ios ignores them entirely. 

