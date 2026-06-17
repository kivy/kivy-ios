# BeeWare vs python.org runtime-layout spike (Phase 4)

**Question:** Does BeeWare's `Python-Apple-support` artifact match the python.org
`install_python` contract the spec (02/03/06) is written against? Where it
diverges, the `PythonRuntime` adapter must absorb the difference so the rest of
the toolchain stays runtime-agnostic.

## Artifact sourcing (verified against live releases)

| | python.org (`PythonOrgRuntime`, canonical) | BeeWare (`BeewareRuntime`, interim) |
|---|---|---|
| Granularity | per **patch** (`3.15.0`, `3.15.1`, …) | per **minor**, build-tagged (`3.13-b13`) |
| URL | `https://www.python.org/ftp/python/<X.Y.Z>/python-<X.Y.Z>-iOS-XCframework.tar.gz` | `https://github.com/beeware/Python-Apple-support/releases/download/<X.Y>-<bN>/Python-<X.Y>-iOS-support.<bN>.tar.gz` |
| Availability | 3.15.0b1+ (May 2026) | 3.10–3.14 today (e.g. `3.13-b13`, `3.14-b9`) |
| Container | `.tar.gz` holding `Python.xcframework` | `.tar.gz` holding `Python.xcframework` + `platform-site/` + `VERSIONS` |

Both expose a `Python.xcframework` with the same slice directory names
(`ios-arm64`, `ios-arm64_x86_64-simulator`), so slice routing and the
Embed/Link wiring (Phase 5) are **identical** across runtimes.

## The key divergence: `.so` → `.framework` conversion

* **python.org** ships an `install_python` helper *inside* the xcframework. The
  generated Xcode "Build Python" Run Script phase calls
  `install_python Python.xcframework app pip-deps` (Python 3.15 iOS docs
  §7.2.2 step 7). It walks `app/` + `pip-deps/`, turns each `.so` into a
  per-module `.framework` under the bundle's `Frameworks/`, leaves a `.fwork`
  text marker in place of the `.so`, and copies `<module>.xcprivacy` →
  `PrivacyInfo.xcprivacy`. This is what specs 03/06 describe.

* **BeeWare** has **no `install_python`**. Briefcase's iOS template performs an
  equivalent conversion in its own build-phase script (historically a
  dylib-per-module + `dylib-Info-template.plist` approach). The stdlib lives in
  the framework's `lib/python3.x/`.

**Adapter consequence:** `PythonRuntime.build_python_invocation()` is the seam.
`PythonOrgRuntime` returns the `install_python …` line verbatim;
`BeewareRuntime` must emit an equivalent conversion shim (tracked TODO — it is
*not* the shipping path). Everything else — download/verify/cache (Phase 4),
slice selection, pbxproj Link/Embed (Phase 5) — is shared.

## Other notes

* iOS floor: python.org 3.15 → 13.0; BeeWare supports down to 12.0 historically.
  The adapter exposes `ios_floor()` so the lock's deployment-target check
  (spec 01 rule 11) uses the right floor per runtime.
* BeeWare bundles a `VERSIONS` file and `platform-site/`; python.org does not.
  Neither is needed by the spec's build flow, so the adapters ignore them.

## Decision

Use `PythonOrgRuntime` as the canonical/default target (specs are its source of
truth). Keep `BeewareRuntime` behind the same `PythonRuntime` protocol purely
to unblock **early real simulator/device smoke tests** (Phase 6) on a 3.13/3.14
support package while the python.org 3.15 artifact + iOS wheels mature. Confirm
the conversion shim on macOS before relying on the BeeWare path end-to-end.
