# Hello World — minimal kivy-ios end-to-end smoke test

Pure Python (no Kivy). Imports `src/main.py`, which prints `Hello World` to the
Xcode debug console when you run the app on a simulator.

Uses the official **python.org** iOS `Python.xcframework` preview
(**3.15.0b2**). The lockfile pins the archive URL and SHA-256.

## Prerequisites

- macOS with Xcode installed (`xcode-select --install` if needed)
- Xcode license accepted: `sudo xcodebuild -license`
- kivy-ios 3.0 from this repo:

```bash
cd /path/to/kivy-ios
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Generate the Xcode project

From this directory:

```bash
cd examples/hello-world
toolchain clean    # optional: drop a stale hello-world-ios/ tree
toolchain build
```

If you already generated the project before a kivy-ios update, run `toolchain build`
again so the `.xcodeproj` picks up `app/` and `pip-deps/` in Copy Bundle Resources.

This downloads `Python.xcframework` (~83 MB, cached under
`~/Library/Caches/kivy-ios/artifacts/`), creates `hello-world-ios/`, and writes
`hello-world.xcodeproj`. No pip wheels are installed (`dependencies = []`).

To refresh the lock after editing `pyproject.toml`:

```bash
toolchain lock
```

## Run in Xcode (see console output)

```bash
toolchain open
```

In Xcode:

1. Select an **iOS Simulator** as the run destination (e.g. iPhone 16).
2. **Product → Run** (⌘R).
3. Open the **debug console** (View → Debug Area → Activate Console).
4. Look for: `Hello World`

Alternatively, build and launch from the CLI (after the Xcode license is accepted):

```bash
toolchain build --simulator
toolchain run --simulator
```

## Files

| Path | Purpose |
|------|---------|
| `pyproject.toml` | App identity + `[tool.kivy.ios]` config |
| `pylock.ios.toml` | Pinned python.org Python 3.15.0b2 runtime (no PyPI wheels) |
| `src/main.py` | Prints `Hello World` at import time |
| `hello-world-ios/` | Generated Xcode tree (gitignored; recreated by `toolchain build`) |
