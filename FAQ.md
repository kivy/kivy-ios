# FAQ for Kivy for iOS

## Introduction

Kivy for iOS (kivy-ios) is a declarative toolchain that bundles
[Kivy](https://kivy.org) (and other Python) applications into an
[Xcode](https://developer.apple.com/xcode/) project for
[iOS](https://www.apple.com/ios/). You describe your app in `pyproject.toml`;
the toolchain resolves dependencies into a lockfile, downloads the official
`Python.xcframework` plus prebuilt iOS wheels, and generates the `.xcodeproj`.

For the full workflow see the [README](README.md); for design and reference
details see the [3.0 docs](docs/proposals/00-overview.md). When something looks
wrong, `toolchain doctor` runs environment and project health checks and is a
good first stop.

## FAQ

### `toolchain: command not found`

The `toolchain` script is installed into your virtual environment. Activate it
(`. .venv/bin/activate`) and make sure kivy-ios is installed
(`pip install -e ".[dev]"` from the repo).

### Error: SDK "iphonesimulator" cannot be located

The active Xcode path is not set correctly. Point `xcode-select` at your Xcode:

    sudo xcode-select --switch /Applications/Xcode.app

If the command line tools are missing, install them with `xcode-select --install`.

### `toolchain build` says the lock is out of sync

Your `pyproject.toml` changed since `pylock.ios.toml` was generated. Re-resolve:

    toolchain lock

In CI, `toolchain lock --check` exits non-zero when the lock is stale (it writes
nothing). Use `--no-verify-lock` on `build` only if you intentionally want to
skip the drift check.

### Downloading `Python.xcframework` fails with HTTP 404

`[tool.kivy.ios.python].version` must match a build that python.org actually
publishes. iOS support is new, so during the preview period you may need a
prerelease such as `3.15.0b2` rather than a final `3.15.0`. Set the version to a
published release and re-run `toolchain lock`.

### "invalid character in Bundle Identifier"

A bundle identifier is a UTI: only letters, digits, hyphen (`-`), and period
(`.`) are allowed — no underscores. Fix `[tool.kivy.ios].bundle_id`, e.g. use
`org.example.hello-world` instead of `org.example.hello_world`.

### I edited my Python source but the app didn't change

Editing Python source does **not** require `toolchain build`: the generated
project links your source directory (`app/` is a symlink to `app_dir`), so just
relaunch — `toolchain run --simulator`, or ⌘R in Xcode. Re-run `toolchain build`
only when you change app config or need to regenerate the project, and
`toolchain clean` to reset the generated `<app>-ios/` folder for a fresh build.

### Where are downloaded artifacts stored?

`Python.xcframework` and other xcframeworks are cached under
`~/Library/Caches/kivy-ios/artifacts/` and shared across projects. Flush the
cache with `toolchain clean --cache`, or force a fresh download for one build
with `toolchain build --no-cache`.

### Can I bundle a plain Python app without Kivy?

Yes. List no Kivy in `dependencies` and the toolchain bundles a pure-Python app
(this is what `examples/hello-world` does). It runs Python directly with no UI —
ideal as a smoke test of the toolchain or for validating pure-Python code
on-device. To ship an actual app you still need a UI layer: Kivy (via SDL), or a
native bridge such as `rubicon-objc`/`pyobjus` that your Python code drives.

### Why does the Python `multiprocessing`/`subprocess` module not work?

The iOS application model does not support spawning subprocesses in a
cross-platform-compatible way. The platform focuses on minimizing processor
usage (and therefore power consumption) and promotes an
[alternative concurrency model](https://developer.apple.com/library/archive/documentation/General/Conceptual/ConcurrencyProgrammingGuide/Introduction/Introduction.html).
Use threads or async concurrency instead.
