#!/usr/bin/env python3
"""Resolver spike: can the current pip resolve/fetch iOS-tagged wheels?

kivy-ios 3.0's `toolchain lock` needs to resolve dependencies to iOS wheels
on a macOS *host* (cross-resolution), and `toolchain build` needs to install
those pinned wheels. This probes whether stock pip can do platform-tagged,
binary-only resolution against a supplemental index, so we can decide the
default resolver backend (pip) and whether a uv fallback is warranted.

Usage:
    python scripts/resolver_spike.py [--index URL] [--python-version X.Y]

It runs read-only experiments (`pip download --no-deps` into a temp dir,
plus `pip index versions`) and prints a PASS/FAIL summary per experiment.
Nothing is installed into the active environment.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_INDEX = "https://pypi-index.psychowaspx.workers.dev/simple/"

# (package, platform tag, abi) triples to probe. These map onto spec 03's
# three iOS slices for a compiled package.
IOS_SLICES = [
    ("ios_13_0_arm64_iphoneos", "iphoneos / arm64 (device)"),
    ("ios_13_0_arm64_iphonesimulator", "iphonesimulator / arm64"),
    ("ios_13_0_x86_64_iphonesimulator", "iphonesimulator / x86_64"),
]


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr)


def pip_base() -> list[str]:
    return [sys.executable, "-m", "pip"]


def experiment_pip_version() -> None:
    code, out = run([*pip_base(), "--version"])
    print(f"[info] {out.strip()}")


def experiment_download(index: str, pyver: str, package: str) -> bool:
    """Try `pip download` for each iOS slice; PASS if at least one resolves."""
    abi = "cp" + pyver.replace(".", "")
    any_ok = False
    for tag, label in IOS_SLICES:
        tmp = Path(tempfile.mkdtemp(prefix="spike-"))
        try:
            cmd = [
                *pip_base(),
                "download",
                package,
                "--no-deps",
                "--only-binary=:all:",
                "--python-version",
                pyver,
                "--implementation",
                "cp",
                "--abi",
                abi,
                "--platform",
                tag,
                "--index-url",
                index,
                "--dest",
                str(tmp),
            ]
            code, out = run(cmd)
            wheels = list(tmp.glob("*.whl"))
            ok = code == 0 and bool(wheels)
            any_ok = any_ok or ok
            status = "PASS" if ok else "fail"
            detail = wheels[0].name if wheels else out.strip().splitlines()[-1:] or ""
            print(f"  [{status}] {package} {label}: {detail}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return any_ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default=DEFAULT_INDEX)
    parser.add_argument("--python-version", default="3.13")
    parser.add_argument(
        "--packages", nargs="*", default=["numpy", "pillow", "kiwisolver"]
    )
    args = parser.parse_args()

    print("=== Resolver spike: pip iOS cross-resolution ===")
    experiment_pip_version()
    print(f"[info] index: {args.index}")
    print(f"[info] target python: {args.python_version}\n")

    results: dict[str, bool] = {}
    for pkg in args.packages:
        print(f"- {pkg}:")
        results[pkg] = experiment_download(args.index, args.python_version, pkg)

    print("\n=== Summary ===")
    for pkg, ok in results.items():
        print(f"  {pkg}: {'PASS' if ok else 'FAIL'}")
    overall = any(results.values())
    print(
        f"\noverall: {'pip can fetch at least one iOS slice' if overall else 'pip fetched nothing'}"
    )
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
