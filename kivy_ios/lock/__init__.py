"""kivy-ios lock layer: resolver backends + ``pylock.ios.toml`` (spec 02)."""

from __future__ import annotations

from .builder import BuildError, build_lockfile, diff_summary, semantic_equal
from .model import (
    LockedPackage,
    LockedSwiftPackage,
    LockedWheel,
    LockedXcframework,
    Lockfile,
    PythonXcframework,
)
from .reader import LockError, compute_pyproject_sha256, is_in_sync, load, loads
from .resolver import (
    PipResolver,
    ResolvedPackage,
    ResolvedWheel,
    Resolver,
    ResolverError,
    get_resolver,
    slice_tags,
)
from .spm import (
    ResolvedSwiftPackage,
    SpmResolver,
    SpmResolverError,
    XcodeSpmResolver,
    get_spm_resolver,
)
from .writer import dumps
from .xcframework import XcframeworkResolverError, resolve_xcframeworks

__all__ = [
    "BuildError",
    "build_lockfile",
    "diff_summary",
    "semantic_equal",
    "Lockfile",
    "LockedPackage",
    "LockedSwiftPackage",
    "LockedWheel",
    "LockedXcframework",
    "PythonXcframework",
    "LockError",
    "compute_pyproject_sha256",
    "is_in_sync",
    "load",
    "loads",
    "dumps",
    "PipResolver",
    "Resolver",
    "ResolvedPackage",
    "ResolvedWheel",
    "ResolverError",
    "get_resolver",
    "slice_tags",
    "ResolvedSwiftPackage",
    "SpmResolver",
    "SpmResolverError",
    "XcodeSpmResolver",
    "get_spm_resolver",
    "XcframeworkResolverError",
    "resolve_xcframeworks",
]
