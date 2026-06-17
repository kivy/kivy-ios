"""Select and install pinned iOS wheels into ``pip-deps/`` (spec 03 / spec 05 step 4).

``toolchain build`` already has the exact per-slice wheels pinned in the lock,
so installation uses ``--no-deps`` (pip does not re-resolve) with the iOS
cross-install flags. Slice selection is driven by the build target + ``--arch``.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from ..lock.model import LockedPackage, LockedWheel

# Build target -> the simulator/device platform-tag suffix.
TARGET_SUFFIX = {
    ("device", "arm64"): "arm64_iphoneos",
    ("simulator", "arm64"): "arm64_iphonesimulator",
    ("simulator", "x86_64"): "x86_64_iphonesimulator",
}


@dataclass(frozen=True)
class BuildSlice:
    target: str  # "device" | "simulator"
    arch: str  # "arm64" | "x86_64"
    deployment_target: str

    @property
    def platform_tag(self) -> str:
        suffix = TARGET_SUFFIX.get((self.target, self.arch))
        if suffix is None:
            raise ValueError(f"unsupported target/arch: {self.target}/{self.arch}")
        dt = self.deployment_target.replace(".", "_")
        return f"ios_{dt}_{suffix}"


def select_wheel(package: LockedPackage, slice_: BuildSlice) -> LockedWheel:
    """Pick the wheel matching the build slice (pure-Python wheels match any).

    For native wheels, the arch/sdk suffix must match exactly, but the iOS
    version component uses compatibility matching: a wheel tagged ios_13_0_*
    is valid for a project targeting ios_16_0 because the wheel can run on
    any iOS >= 13.0.  The best (highest compatible) version is preferred.

    Background: wheel tags are determined by the Python binary's compile-time
    sysconfig.get_platform(), which reflects the Python.xcframework minimum OS
    (e.g. python.org cp315 targets 13.0 regardless of IPHONEOS_DEPLOYMENT_TARGET
    used when compiling the extension code itself).
    """
    pure = [w for w in package.wheels if w.is_pure_python]
    if pure:
        return pure[0]

    arch_sdk = TARGET_SUFFIX.get((slice_.target, slice_.arch))
    if arch_sdk is None:
        raise ValueError(f"unsupported target/arch: {slice_.target}/{slice_.arch}")

    dt_parts = tuple(int(x) for x in slice_.deployment_target.split("."))

    candidates: list[tuple[tuple[int, ...], LockedWheel]] = []
    for wheel in package.wheels:
        tag = wheel.platform_tag  # e.g. "ios_13_0_arm64_iphonesimulator"
        if not tag.endswith(f"_{arch_sdk}"):
            continue
        # Extract the ios_<major>_<minor> prefix.
        prefix = tag[: -(len(arch_sdk) + 1)]  # "ios_13_0"
        parts = prefix.split("_")  # ["ios", "13", "0"]
        if parts[0] != "ios" or len(parts) < 3:
            continue
        try:
            wheel_ver = tuple(int(x) for x in parts[1:])
        except ValueError:
            continue
        if wheel_ver <= dt_parts:
            candidates.append((wheel_ver, wheel))

    if candidates:
        # Prefer the highest compatible version.
        candidates.sort(key=lambda t: t[0], reverse=True)
        return candidates[0][1]

    available = ", ".join(sorted(w.platform_tag for w in package.wheels))
    raise WheelSelectionError(
        f"{package.name} has no compatible wheel for slice "
        f"{slice_.platform_tag} (have: {available})."
    )


class WheelSelectionError(Exception):
    pass


def pip_install_command(
    wheel_files: list[str],
    *,
    target_dir: str,
    platform_tag: str,
    python_version: str,
    abi: str,
    python_executable: str | None = None,
) -> list[str]:
    """Build the pip cross-install command (spec 05 step 4); no re-resolution."""
    py = python_executable or sys.executable
    cmd = [
        py,
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--only-binary=:all:",
        "--platform",
        platform_tag,
        "--python-version",
        python_version,
        "--abi",
        abi,
        "--implementation",
        "cp",
        "--target",
        target_dir,
    ]
    cmd += wheel_files
    return cmd
