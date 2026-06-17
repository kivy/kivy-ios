"""Parse ``pylock.ios.toml`` back into a ``Lockfile`` and detect drift (spec 02)."""

from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

from .model import (
    LockedPackage,
    LockedWheel,
    LockedXcframework,
    Lockfile,
    PackageDep,
    PythonXcframework,
)


class LockError(Exception):
    """A malformed or unreadable lockfile."""


def loads(text: str) -> Lockfile:
    raw = tomllib.loads(text)
    return _from_raw(raw)


def load(path: str | Path) -> Lockfile:
    return loads(Path(path).read_text(encoding="utf-8"))


def _from_raw(raw: dict) -> Lockfile:
    lock_version = raw.get("lock-version", "1.0")
    major = lock_version.split(".", 1)[0]
    if major.isdigit() and int(major) > 1:
        raise LockError(
            f"pylock.ios.toml lock-version {lock_version} is newer than this "
            "kivy-ios understands (max 1.x). Upgrade kivy-ios."
        )

    tool = raw.get("tool", {}).get("kivy_ios", {})
    if not tool:
        raise LockError("pylock.ios.toml is missing the [tool.kivy_ios] table.")

    px = tool.get("python_xcframework", {})
    python_xcframework = PythonXcframework(
        version=px.get("version", ""),
        url=px.get("url", ""),
        sha256=px.get("sha256", ""),
    )

    packages = tuple(_parse_package(p) for p in raw.get("packages", []))
    xcframeworks = tuple(_parse_xcframework(x) for x in tool.get("xcframeworks", []))

    return Lockfile(
        requires_python=raw.get("requires-python", ">=3.15"),
        packages=packages,
        python_xcframework=python_xcframework,
        toolchain_version=tool.get("toolchain_version", ""),
        generated_at=tool.get("generated_at", ""),
        pyproject_sha256=tool.get("pyproject_sha256", ""),
        tool_kivy_ios_schema_version=tool.get("tool_kivy_ios_schema_version", 1),
        xcframeworks=xcframeworks,
        schema_version=tool.get("schema_version", 1),
        lock_version=lock_version,
        created_by=raw.get("created-by", "kivy-ios"),
        extras=tuple(raw.get("extras", [])),
        dependency_groups=tuple(raw.get("dependency-groups", [])),
        default_groups=tuple(raw.get("default-groups", [])),
    )


def _parse_package(p: dict) -> LockedPackage:
    tool = p.get("tool", {}).get("kivy_ios", {})
    deps = tuple(
        PackageDep(name=d["name"], marker=d.get("marker"))
        for d in p.get("dependencies", [])
    )
    wheels = tuple(_parse_wheel(w) for w in p.get("wheels", []))
    return LockedPackage(
        name=p["name"],
        version=p["version"],
        wheels=wheels,
        requires_python=p.get("requires-python"),
        dependencies=deps,
        marker=p.get("marker"),
        direct_requirement=bool(tool.get("direct_requirement", False)),
        source_index=tool.get("source_index"),
    )


def _parse_wheel(w: dict) -> LockedWheel:
    return LockedWheel(
        name=w["name"],
        sha256=w.get("hashes", {}).get("sha256", ""),
        url=w.get("url"),
        path=w.get("path"),
        upload_time=w.get("upload-time"),
        size=w.get("size"),
    )


def _parse_xcframework(x: dict) -> LockedXcframework:
    return LockedXcframework(
        name=x["name"],
        version=x["version"],
        sha256=x.get("sha256", ""),
        slices=tuple(x.get("slices", [])),
        url=x.get("url"),
        path=x.get("path"),
        archive_format=x.get("archive_format", "zip"),
        archive_member=x.get("archive_member"),
        privacy_manifest_path=x.get("privacy_manifest_path"),
        link=bool(x.get("link", True)),
        embed=bool(x.get("embed", True)),
        source=x.get("source"),
    )


def compute_pyproject_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_in_sync(lock: Lockfile, pyproject_text: str) -> bool:
    """True if the lock's recorded pyproject hash matches the current pyproject."""
    return lock.pyproject_sha256 == compute_pyproject_sha256(pyproject_text)
