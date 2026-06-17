"""In-memory model of ``pylock.ios.toml`` (spec 02).

PEP 751-shaped ``[[packages]]`` plus the ``[tool.kivy_ios]`` extension. These
dataclasses are produced by the builder/resolver and serialized by ``writer``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

LOCK_VERSION = "1.0"
CREATED_BY = "kivy-ios"
TOOL_SCHEMA_VERSION = 1
DEFAULT_REQUIRES_PYTHON = ">=3.15"


@dataclass(frozen=True)
class LockedWheel:
    """One ``[[packages.wheels]]`` entry (a single platform slice)."""

    name: str  # wheel filename; platform tag is parsed back out of this
    sha256: str
    url: str | None = None
    path: str | None = None
    upload_time: str | None = None
    size: int | None = None

    def __post_init__(self) -> None:
        if bool(self.url) == bool(self.path):
            raise ValueError(f"wheel {self.name!r} must have exactly one of url/path")

    @property
    def platform_tag(self) -> str:
        """The platform tag parsed from the wheel filename (last tag segment)."""
        stem = self.name[:-4] if self.name.endswith(".whl") else self.name
        return stem.rsplit("-", 1)[-1]

    @property
    def is_pure_python(self) -> bool:
        return "none-any" in self.name


@dataclass(frozen=True)
class PackageDep:
    name: str
    marker: str | None = None


@dataclass(frozen=True)
class LockedPackage:
    """One ``[[packages]]`` entry."""

    name: str
    version: str
    wheels: tuple[LockedWheel, ...]
    requires_python: str | None = None
    dependencies: tuple[PackageDep, ...] = ()
    marker: str | None = None
    direct_requirement: bool = False
    source_index: str | None = None

    @property
    def sort_key(self) -> tuple[str, str]:
        return (canonical_name(self.name), self.version)


@dataclass(frozen=True)
class PythonXcframework:
    version: str
    url: str
    sha256: str


@dataclass(frozen=True)
class LockedXcframework:
    """One ``[[tool.kivy_ios.xcframeworks]]`` entry."""

    name: str
    version: str
    sha256: str
    slices: tuple[str, ...]
    url: str | None = None
    path: str | None = None
    archive_format: str = "zip"
    archive_member: str | None = None
    privacy_manifest_path: str | None = None
    link: bool = True
    embed: bool = True
    source: str | None = None

    def __post_init__(self) -> None:
        if bool(self.url) == bool(self.path):
            raise ValueError(
                f"xcframework {self.name!r} must have exactly one of url/path"
            )


@dataclass(frozen=True)
class Lockfile:
    requires_python: str
    packages: tuple[LockedPackage, ...]
    python_xcframework: PythonXcframework
    toolchain_version: str
    generated_at: str
    pyproject_sha256: str
    tool_kivy_ios_schema_version: int
    xcframeworks: tuple[LockedXcframework, ...] = ()
    schema_version: int = TOOL_SCHEMA_VERSION
    lock_version: str = LOCK_VERSION
    created_by: str = CREATED_BY
    extras: tuple[str, ...] = ()
    dependency_groups: tuple[str, ...] = ()
    default_groups: tuple[str, ...] = ()


def canonical_name(name: str) -> str:
    """PEP 503 normalization for package-name comparison."""
    return re.sub(r"[-_.]+", "-", name).lower()
