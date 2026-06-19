"""kivy-ios lock layer: resolver backends + ``pylock.ios.toml`` (spec 02)."""

from __future__ import annotations

from .builder import BuildError, build_lockfile, diff_summary, semantic_equal
from .model import (
    LockedPackage,
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
from .writer import dumps

__all__ = [
    "BuildError",
    "build_lockfile",
    "diff_summary",
    "semantic_equal",
    "Lockfile",
    "LockedPackage",
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
]
