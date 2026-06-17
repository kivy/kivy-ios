# Resolver spike findings (Phase 0)

**Question:** Can the current `pip` perform the iOS cross-resolution that
`toolchain lock` / `toolchain build` need, or must we adopt `uv` for
development? (Reproduce with `python scripts/resolver_spike.py`.)

## Environment

- `pip 26.1.2`, Python 3.14.5 (dev venv).
- Supplemental index probed: `https://pypi-index.psychowaspx.workers.dev/simple/`.
- Target Python for resolution: 3.13 (matches the iOS wheels currently published).

## Result: pip is sufficient as the default backend

Using `pip download --no-deps --only-binary=:all: --python-version <X.Y>
--implementation cp --abi cp<XY> --platform <ios tag> --index-url <index>`,
pip resolved and fetched **all three iOS slices** for compiled packages that
publish them:

| Package | device arm64 | sim arm64 | sim x86_64 |
|---------|:---:|:---:|:---:|
| numpy 2.4.6 | PASS | PASS | PASS |
| kiwisolver 1.5.0 | PASS | PASS | PASS |
| pillow | n/a | n/a | n/a |

`pillow` is not currently served by this particular index (its project page
returns no distributions), so it is a content gap on the index, **not** a pip
capability gap. Packages that publish iOS wheels to PyPI proper resolve from
PyPI directly; the supplemental index is only consulted via `extra_index_urls`.

## Conclusions / decisions

1. **Default resolver backend = pip.** It supports the exact platform-tagged,
   binary-only, host-independent resolution the lock needs (`--platform`,
   `--abi`, `--python-version`, `--implementation`, `--only-binary`). This is
   the `PipResolver` backend (Phase 3).
2. **uv stays a documented fallback**, not a hard dependency. The resolver is
   abstracted behind an interface so a `UvResolver` can be slotted in if a
   future pip regression or a perf need arises. We do **not** depend on pip's
   experimental `-r pylock.toml` reader (it ignores platform-selection flags);
   `toolchain build` installs the pinned wheels itself, exactly as specced.
3. **Do not over-constrain `--abi`.** Some packages ship `abi3`/limited-API or
   a different `cp` tag than the host. The lock resolver should pass the abi
   set pip accepts for the target (e.g. `cp313`, `abi3`, `none`) rather than a
   single hardcoded value, so abi3 wheels are not missed.
4. **Per-package, per-slice availability varies.** `toolchain lock` must fail
   fast and name the specific package+slice that could not be resolved
   (host-independent error), rather than failing later at build time on one
   runner — consistent with the spec 02 "pin all three slices" rule.

## How this feeds the implementation

- Phase 3 implements `kivy_ios/lock/resolver.py` with a `Resolver` protocol and
  a `PipResolver` default; the worker index is used in integration tests as an
  `extra_index_urls` source.
