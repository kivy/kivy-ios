# Release simulator startup smoke

Run from the repository root on an **Apple Silicon Mac** with active Xcode
and an available iPhone simulator. Build the recipes from your checkout first:

```bash
toolchain build python3 kivy
python3 .ci/test_simulator_startup.py --result-timeout 60 --artifacts build/ci-startup
```

The runner generates an app from production templates and builds Release/arm64
for a generic simulator destination. It chooses the first available iPhone on
the newest iOS runtime meeting the built app's minimum OS, without downloading
runtimes or retrying failed launches.

It launches two fresh processes: one without trailing arguments and one with
`-NSDocumentRevisionsDebugMode YES`. The app checks argv before disabling Kivy's
separate argument parser, exercises JSON, zlib, SQLite and SSL, and checks an
SDL2 window from a scheduled Clock callback. Only a fresh matching JSON result
from the event loop passes; a launch PID or bootstrap result is not enough.

## When it fails

Look in `build/ci-startup/diagnostics/` for:

- `build.log`, Xcode/SDK logs, device inventories and `selected.json`.
- `ordinary/` and `native-option/`: launch logs, stdout/stderr, requests and results.
- `error.txt` and `cleanup.json`: the main failure and any cleanup errors.
- `simulator-failure/`: process state, the last ten minutes of CoreSimulator
  service logs and a fresh device inventory, captured before cleanup on failure.
  `collection.json` records errors collecting these best-effort diagnostics.

Native startup can fail before writing JSON; check the case's stderr and launch
log. Release Kivy logs may be suppressed, so result files determine success.
Xcode diagnostics are also kept in `build/ci-startup/build.xcresult/`.

Each result wait defaults to 60 seconds. Commands have fixed limits: 30 seconds
normally (including cleanup), 600 for build, 180 for boot readiness and app
installation, and 60 for pre-launch termination. Failure diagnostic commands
have a 15-second limit each so an unresponsive simulator cannot block collection.
Cleanup removes the app and shuts down only a simulator booted by this run.
Before rerunning, move/remove your generated `startupsmoke-ios` project and use
a fresh artifacts directory. CI runs this in one non-venv Apple Silicon lane
with a 20-minute limit and uploads diagnostics on success and failure.
