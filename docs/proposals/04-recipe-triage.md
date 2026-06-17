# 04 — Recipe Triage

**Status:** rfc-v1 (draft)
**Depends on:** [00-overview](00-overview.md), [03-artifact-distribution](03-artifact-distribution.md)

This spec assigns every recipe in `kivy_ios/recipes/` to one of five outcomes. The recipe system is removed entirely in kivy-ios 3.0; each recipe either disappears, is replaced by an upstream artifact, or becomes a published wheel or xcframework.

---

## Deleted recipes

These recipes are removed when kivy-ios 3.0 ships. No replacement within kivy-ios — see the "Replacement" column for where users go instead.

| Recipe | Replacement |
|--------|-------------|
| `hostpython3`, `hostpython.py` | `Python.xcframework` from python.org |
| `python3`, `python.py` | `Python.xcframework` from python.org |
| `hostopenssl`, `openssl` | Python.xcframework bundles its own TLS; OpenSSL 1.1.1 is end-of-life |
| `libffi` | Bundled in Python.xcframework |
| `sdl2`, `sdl2_image`, `sdl2_ttf`, `sdl2_mixer` | Kivy 3.x drops SDL2; these stay on kivy-ios 2.x |
| `ffmpeg` | AVFoundation-based video player in Kivy 3.0 |
| `freetype` / `libpng` / `libjpeg` | No longer needed separately: kivy iOS wheel bundles its native deps; modern Pillow/matplotlib iOS wheels vendor their own |
| `libcurl` | stdlib `urllib`/`http.client`; or `pyobjus` + `NSURLSession` for native paths |
| `libzbar` | Apple `Vision` framework (`VNDetectBarcodesRequest`) via `pyobjus` — ships since iOS 11 |
| `zbarlight` | Same as libzbar above |
| `ffpyplayer` | AVFoundation-based video player in Kivy 3.0 |
| `click`, `flask`, `itsdangerous`, `jinja2`, `werkzeug`, `pykka`, `plyer`, `py3dns` | Pure-Python; `pip install <name>` |
| `markupsafe` | Has C extension but pure-Python fallback works; upstream iOS wheel expected eventually |
| `pyyaml` | 3.11 (2014 — over 10 years out of date). Has optional C extension (`libyaml`) but pure-Python fallback works. Recipe comment: "pure-python package, this can be removed when we'll support any Python package." `pip install pyyaml` installs pure-Python automatically when no compiled wheel is available. |
| `pycrypto` | Abandoned since 2014; use `pycryptodome` via `[project].dependencies` |
| `curly` | Kivy `AsyncImage` + stdlib `urllib` / `pyobjus` `NSURLSession` |
| `cymunk` | Last commit 2017; never on PyPI. Use `pymunk` (actively maintained, compatible API) |
| `kivent_core` | Never on PyPI; p4a already removed support. Port to a maintained ECS library |
| `audiostream` | Still 0.2-alpha; build errors reported. Use AVFoundation via `pyobjus` (`AVAudioEngine`/`AVAudioSession`) |
| `photolibrary` | Last pushed 2015; wraps the deprecated `UIImagePickerController`. Use `PHPickerViewController` via `pyobjus` |
| `ios` recipe — Kivy platform bridge (`ios.pyx`, `ios_mail.m`, `ios_browser.m`, `ios_filechooser.m`, `ios_utils.m`) | This Obj-C bridge predates mature `pyobjus`. Every function it wraps can be called from Python via the optional `pyobjus` bridge: `UIApplication.shared.openURL(_:)` (browser), `MFMailComposeViewController` (mail). The filechooser wraps the deprecated `UIImagePickerController` (deprecated iOS 14) and is dropped entirely. The remainder (screen scale, DPI, keyboard height, safe-area insets) is provided by the **`ios` platform module**: kivy-ios writes a pure-Python `ios.py` (direct ObjC-runtime calls via `ctypes` — no extra dependencies) into every generated Xcode project at `<app>-ios/platform/ios.py`. Kivy calls `ios.get_scale()`, `ios.get_dpi()`, and `ios.get_kheight()` internally; app code calls `ios.get_safe_area()` directly for notch / Dynamic Island padding. The implementation lives in kivy-ios for active development but is intended to move to the kivy repository once the interface stabilises. See [spec 05 §"The vendored `ios` platform module"](05-cli-shape.md#the-vendored-ios-platform-module). |

---

## Consumed from upstream

The lockfile points directly at an upstream-published URL; no Kivy CI involvement.

| Artifact | Source |
|----------|--------|
| `Python.xcframework` | [python.org releases](https://www.python.org/downloads/) — available from 3.15.0b1 (May 2026). URL pattern: `https://www.python.org/ftp/python/<X.Y.Z>/python-<version>-iOS-XCframework.tar.gz`. Pinned in the lockfile's `[tool.kivy_ios.python_xcframework]` block; mandatory and singular, not a `[[tool.kivy_ios.xcframeworks]]` row. |

---

## Resolved via PyPI or a configured supplemental index

PyPI is the primary resolution source. The Python ecosystem is mid-transition to iOS-tagged wheels, so `toolchain` supports configuring one or more supplemental `pip --extra-index-url` indexes. The list is plural-by-design, channel-agnostic, and **empty by default**; specific channel choices are a per-user or per-Kivy-deployment decision.

`toolchain lock` records the resolved wheel URL and source index in `[[packages.wheels]]`; `toolchain build` passes `--platform ios_13_0_arm64_iphoneos --only-binary :all:` so pip fetches iOS slices rather than macOS ones.

**Packages from former recipes now resolved this way:**

| Recipe | Disposition |
|--------|-------------|
| `materialyoucolor` | iOS wheels expected via PyPI or a configured supplemental index; upstream is active (v3.0.2, Feb 2026) |
| `kiwisolver` | Same |
| `matplotlib` | Same |
| `pillow` | Same (modern Pillow already ships iOS wheels via some channels) |
| `numpy` | Same (primary transition candidate) |
| `netifaces` | Same |



---

## Kivy-published iOS wheels

These packages have C extensions that Kivy builds and publishes as iOS-tagged wheels to PyPI. Both must be rebuilt against Python 3.15 and published around the sametime kivy-ios 3.0 ships.

| Recipe | Notes |
|--------|-------|
| `kivy` | The kivy iOS wheel bundles every native xcframework it links against (ANGLE, SDL3 family, Skia); kivy-ios consumes it like any other Python wheel. |
| `pyobjus` | Already on PyPI (v1.2.4, Dec 2025); Kivy adds `cp315-cp315-ios_*` wheels to the existing publish pipeline. |

