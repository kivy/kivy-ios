"""Parse ``pylock.ios.toml`` back into a ``Lockfile`` and detect drift (spec 02)."""

from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

from .model import (
    LOCK_VERSION,
    TOOL_SCHEMA_VERSION,
    LockedPackage,
    LockedSwiftPackage,
    LockedWheel,
    LockedXcframework,
    Lockfile,
    PackageDep,
    PythonXcframework,
)

# Highest major lock-version (PEP 751 top-level) this reader accepts.
SUPPORTED_LOCK_VERSION_MAJOR = int(LOCK_VERSION.split(".", 1)[0])
# Highest [tool.kivy_ios].schema_version (the extension's own schema) accepted.
SUPPORTED_TOOL_SCHEMA_VERSION = TOOL_SCHEMA_VERSION


class LockError(Exception):
    """A malformed or unreadable lockfile."""


def loads(text: str) -> Lockfile:
    """Parse ``pylock.ios.toml`` text into a ``Lockfile``.

    ``toolchain lock`` is the writer, so the reader's job is to fail *cleanly*
    when the file is corrupt, hand-edited, or from a future schema — never to
    leak a raw ``KeyError``/``TypeError``. Every shape failure surfaces as
    ``LockError``.
    """
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise LockError(f"pylock.ios.toml is not valid TOML: {exc}") from exc
    if not isinstance(raw, dict):
        raise LockError("pylock.ios.toml must be a TOML table.")
    try:
        return _from_raw(raw)
    except LockError:
        raise
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        # A missing/mistyped field anywhere in the tree — name the trigger but
        # don't leak the raw exception type to callers.
        raise LockError(f"pylock.ios.toml is malformed: {exc!r}") from exc


def load(path: str | Path) -> Lockfile:
    return loads(Path(path).read_text(encoding="utf-8"))


def _from_raw(raw: dict) -> Lockfile:
    lock_version = _check_lock_version(raw)

    tool_raw = raw.get("tool", {})
    if not isinstance(tool_raw, dict):
        raise LockError("pylock.ios.toml [tool] must be a table.")
    tool = tool_raw.get("kivy_ios", {})
    if not isinstance(tool, dict) or not tool:
        raise LockError("pylock.ios.toml is missing the [tool.kivy_ios] table.")

    schema_version = _check_tool_schema_version(tool)
    python_xcframework = _parse_python_xcframework(tool)

    packages = tuple(_parse_package(p) for p in _as_list(raw, "packages"))
    xcframeworks = tuple(_parse_xcframework(x) for x in _as_list(tool, "xcframeworks"))
    swift_packages = tuple(
        _parse_swift_package(s) for s in _as_list(tool, "swift_packages")
    )

    return Lockfile(
        requires_python=raw.get("requires-python", ">=3.15"),
        packages=packages,
        python_xcframework=python_xcframework,
        toolchain_version=tool.get("toolchain_version", ""),
        generated_at=tool.get("generated_at", ""),
        pyproject_sha256=tool.get("pyproject_sha256", ""),
        tool_kivy_ios_schema_version=tool.get("tool_kivy_ios_schema_version", 1),
        xcframeworks=xcframeworks,
        swift_packages=swift_packages,
        schema_version=schema_version,
        lock_version=lock_version,
        created_by=raw.get("created-by", "kivy-ios"),
        extras=tuple(raw.get("extras", [])),
        dependency_groups=tuple(raw.get("dependency-groups", [])),
        default_groups=tuple(raw.get("default-groups", [])),
    )


def _check_lock_version(raw: dict) -> str:
    lock_version = raw.get("lock-version", LOCK_VERSION)
    if not isinstance(lock_version, str):
        raise LockError("pylock.ios.toml lock-version must be a string.")
    major = lock_version.split(".", 1)[0]
    if not major.isdigit():
        raise LockError(
            f"pylock.ios.toml lock-version {lock_version!r} is not a valid version."
        )
    if int(major) > SUPPORTED_LOCK_VERSION_MAJOR:
        raise LockError(
            f"pylock.ios.toml lock-version {lock_version} is newer than this "
            f"kivy-ios understands (max {SUPPORTED_LOCK_VERSION_MAJOR}.x). "
            "Upgrade kivy-ios."
        )
    return lock_version


def _check_tool_schema_version(tool: dict) -> int:
    schema_version = tool.get("schema_version", SUPPORTED_TOOL_SCHEMA_VERSION)
    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        raise LockError("[tool.kivy_ios].schema_version must be an integer.")
    if schema_version > SUPPORTED_TOOL_SCHEMA_VERSION:
        raise LockError(
            f"[tool.kivy_ios].schema_version {schema_version} is newer than this "
            f"kivy-ios understands (max {SUPPORTED_TOOL_SCHEMA_VERSION}). "
            "Upgrade kivy-ios."
        )
    return schema_version


def _parse_python_xcframework(tool: dict) -> PythonXcframework:
    px = tool.get("python_xcframework")
    if not isinstance(px, dict) or not px:
        raise LockError(
            "pylock.ios.toml is missing [tool.kivy_ios.python_xcframework]."
        )
    for field in ("version", "url", "sha256"):
        value = px.get(field)
        if not isinstance(value, str) or not value:
            raise LockError(
                f"[tool.kivy_ios.python_xcframework].{field} is missing or empty."
            )
    return PythonXcframework(version=px["version"], url=px["url"], sha256=px["sha256"])


def _as_list(table: dict, key: str) -> list:
    value = table.get(key, [])
    if not isinstance(value, list):
        raise LockError(f"pylock.ios.toml {key!r} must be an array of tables.")
    return value


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


def _parse_swift_package(s: dict) -> LockedSwiftPackage:
    requirement = s.get("requirement")
    return LockedSwiftPackage(
        name=s["name"],
        products=tuple(s.get("products", [])),
        url=s.get("url"),
        path=s.get("path"),
        requirement=dict(requirement) if requirement else None,
        revision=s.get("revision"),
        version=s.get("version"),
        link=bool(s.get("link", True)),
        embed=bool(s.get("embed", True)),
    )


def compute_pyproject_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_in_sync(lock: Lockfile, pyproject_text: str) -> bool:
    """True if the lock's recorded pyproject hash matches the current pyproject."""
    return lock.pyproject_sha256 == compute_pyproject_sha256(pyproject_text)
