"""Fetch + verify + cache artifacts by URL or repo-relative path (spec 03).

A single ``fetch_artifact`` entry point handles the three lockfile sources:
``url`` (download), local ``path`` (vendored), and cache hits. Every byte that
enters the build is SHA-256-verified against the lockfile pin before use.

The network fetch is injectable (``Downloader``) so unit tests stay hermetic.
"""

from __future__ import annotations

import tempfile
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Protocol

from ..lock.find_links import FindLinksError, wheel_path_from_project_root
from .cache import ArtifactCache
from .verify import HashMismatch, sha256_file, verify_file


class DownloadError(Exception):
    pass


class Downloader(Protocol):
    def fetch_to(self, url: str, dest: Path) -> None: ...


class UrllibDownloader:
    def fetch_to(self, url: str, dest: Path) -> None:
        try:
            with urllib.request.urlopen(url) as resp, open(dest, "wb") as out:  # noqa: S310
                for chunk in iter(lambda: resp.read(1 << 20), b""):
                    out.write(chunk)
        except (OSError, ValueError) as exc:
            raise DownloadError(f"failed to download {url}: {exc}") from exc


def fetch_artifact(
    *,
    name: str,
    sha256: str,
    filename: str,
    url: str | None = None,
    path: str | None = None,
    project_root: Path | None = None,
    cache: ArtifactCache | None = None,
    downloader: Downloader | None = None,
    no_cache: bool = False,
) -> Path:
    """Return a verified local path for an artifact (url xor path).

    * ``url``  — cache-first download, then SHA-256 verify.
    * ``path`` — repo-relative (resolved against ``project_root``); verified in
      place. Absolute paths or paths escaping the project are rejected.
    """
    if bool(url) == bool(path):
        raise DownloadError(f"{name}: exactly one of url/path is required")

    if path is not None:
        return _resolve_local(
            name=name, path=path, sha256=sha256, project_root=project_root
        )

    if url is None:
        # xor check above guarantees one of url/path; path branch already returned.
        raise DownloadError(f"{name}: exactly one of url/path is required")

    cache = cache or ArtifactCache()
    downloader = downloader or UrllibDownloader()

    if not no_cache:
        cached = cache.get(sha256, filename)
        if cached is not None and _cache_hit_intact(cached, sha256, name=name):
            return cached

    with tempfile.TemporaryDirectory(prefix="kivy-dl-") as tmp:
        staged = Path(tmp) / filename
        downloader.fetch_to(url, staged)
        verify_file(staged, sha256, name=name, source=url)
        return cache.put_file(staged, sha256, filename)


def _cache_hit_intact(cached: Path, sha256: str, *, name: str) -> bool:
    """Re-verify a cache hit before trusting it (spec 03 "every byte verified").

    The cache key is only the *filename* (``{sha256}-{name}``); it is not proof
    that the bytes on disk still match. A non-atomic ``copyfile`` killed mid-write
    leaves a truncated file at the hash-named path, and the cache dir is
    user-writable (bit-rot/tampering). On a mismatch we drop the corrupt entry
    and return False so the caller re-downloads rather than feeding bad bytes
    into the build.
    """
    try:
        verify_file(cached, sha256, name=name, source=str(cached))
    except HashMismatch:
        cached.unlink(missing_ok=True)
        return False
    return True


def _resolve_local(
    *, name: str, path: str, sha256: str, project_root: Path | None
) -> Path:
    if PurePosixPath(path).is_absolute() or Path(path).is_absolute():
        raise DownloadError(
            f"{name}: lockfile path {path!r} is absolute; only repo-relative "
            f"paths are allowed (they resolve identically on every clone)."
        )
    root = (project_root or Path.cwd()).resolve()
    resolved = (root / path).resolve()
    try:
        wheel_path_from_project_root(root, resolved)
    except FindLinksError as exc:
        raise DownloadError(
            f"{name}: lockfile path {path!r} escapes the allowed vendored "
            f"wheel scope for this project."
        ) from exc
    if not resolved.is_file():
        raise DownloadError(f"{name}: vendored artifact not found at {path!r}.")
    actual = sha256_file(resolved)
    if actual != sha256:
        raise HashMismatch(name=name, source=path, expected=sha256, actual=actual)
    return resolved
