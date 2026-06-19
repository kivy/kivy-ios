"""kivy-ios artifact layer: fetch/cache/verify, wheels, frameworks, runtimes (spec 03)."""

from __future__ import annotations

from .cache import ArtifactCache
from .download import Downloader, DownloadError, UrllibDownloader, fetch_artifact
from .frameworks import (
    FrameworkConflict,
    copy_wheel_frameworks,
    extract_xcframework_archive,
)
from .runtime import (
    PythonOrgRuntime,
    PythonRuntime,
    RuntimeArtifact,
    get_runtime,
)
from .verify import HashMismatch, sha256_bytes, sha256_file, verify_file
from .wheels import BuildSlice, WheelSelectionError, select_wheel

__all__ = [
    "ArtifactCache",
    "DownloadError",
    "Downloader",
    "UrllibDownloader",
    "fetch_artifact",
    "FrameworkConflict",
    "copy_wheel_frameworks",
    "extract_xcframework_archive",
    "PythonOrgRuntime",
    "PythonRuntime",
    "RuntimeArtifact",
    "get_runtime",
    "HashMismatch",
    "sha256_bytes",
    "sha256_file",
    "verify_file",
    "BuildSlice",
    "WheelSelectionError",
    "select_wheel",
]
