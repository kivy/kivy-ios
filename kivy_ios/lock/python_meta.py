"""Resolve ``Python.xcframework`` metadata for the lock (spec 02 §python_xcframework).

``toolchain lock`` records the pinned Python.xcframework's URL + SHA-256 and
uses its declared iOS floor to validate ``deployment_target`` (spec 01 rule
11). The provider is an injection point so unit tests stay offline.
"""

from __future__ import annotations

import hashlib
import time
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from ..artifacts.cache import ArtifactCache
from ..artifacts.verify import sha256_file

# python.org publishes the official iOS xcframework from 3.15.0b1 onward.
PYTHON_ORG_URL = "https://www.python.org/ftp/python/{version}/python-{version}-iOS-XCframework.tar.gz"

_DOWNLOAD_ATTEMPTS = 4
_RETRY_BACKOFF_SEC = (1.0, 2.0, 4.0)


def python_org_ios_url(version: str) -> str:
    """Return the python.org FTP URL for an iOS ``Python.xcframework`` archive.

    Pre-releases (``3.15.0b2``, ``3.15.0rc1``, …) live under the base
    ``/ftp/python/3.Y.0/`` directory; final releases use ``/ftp/python/X.Y.Z/``.
    """
    if _is_prerelease(version):
        base = ".".join(version.split(".")[:2]) + ".0"
        return (
            f"https://www.python.org/ftp/python/{base}/"
            f"python-{version}-iOS-XCframework.tar.gz"
        )
    return PYTHON_ORG_URL.format(version=version)


def archive_filename(version: str) -> str:
    return f"python-{version}-iOS-XCframework.tar.gz"


def _is_prerelease(version: str) -> bool:
    tail = version.split(".")[-1]
    return any(tag in tail for tag in ("a", "b", "rc"))


# Known minimum iOS deployment target per Python minor (the xcframework floor).
_IOS_FLOORS = {
    "3.15": "13.0",
    "3.14": "13.0",
    "3.13": "12.0",
}


@dataclass(frozen=True)
class PythonXcframeworkInfo:
    version: str
    url: str
    sha256: str
    ios_floor: str


class PythonXcframeworkProvider(Protocol):
    def get(self, version: str, *, offline: bool = False) -> PythonXcframeworkInfo: ...


class PythonOrgProvider:
    """Default provider: build the python.org URL and hash the artifact."""

    def __init__(
        self,
        *,
        url_template: str = PYTHON_ORG_URL,
        cache: ArtifactCache | None = None,
    ) -> None:
        self._url_template = url_template
        self._cache = cache or ArtifactCache()

    def get(self, version: str, *, offline: bool = False) -> PythonXcframeworkInfo:
        url = (
            python_org_ios_url(version)
            if self._url_template == PYTHON_ORG_URL
            else self._url_template.format(version=version)
        )
        sha256 = self._resolve_sha256(url, version, offline=offline)
        return PythonXcframeworkInfo(
            version=version,
            url=url,
            sha256=sha256,
            ios_floor=ios_floor(version),
        )

    def _resolve_sha256(self, url: str, version: str, *, offline: bool) -> str:
        filename = archive_filename(version)
        cached = self._cache.find_by_filename(filename)
        if cached is not None:
            return sha256_file(cached)

        if offline:
            raise PythonXcframeworkError(
                f"Python.xcframework {version} is not in the artifact cache "
                f"({filename}).\n"
                f"  Run `toolchain lock` online once, or `toolchain build` to "
                f"populate the cache, then retry with --offline."
            )

        return self._download_sha256(url, version)

    @staticmethod
    def _download_sha256(url: str, version: str) -> str:
        last_exc: OSError | None = None
        for attempt in range(_DOWNLOAD_ATTEMPTS):
            try:
                digest = hashlib.sha256()
                with urllib.request.urlopen(url) as resp:  # noqa: S310
                    for chunk in iter(lambda: resp.read(1 << 20), b""):
                        digest.update(chunk)
                return digest.hexdigest()
            except OSError as exc:
                last_exc = exc
                if attempt < _DOWNLOAD_ATTEMPTS - 1:
                    time.sleep(
                        _RETRY_BACKOFF_SEC[min(attempt, len(_RETRY_BACKOFF_SEC) - 1)]
                    )
        assert last_exc is not None
        raise PythonXcframeworkError(
            f"could not fetch Python.xcframework {version} from {url}: {last_exc}\n"
            f"  Check the version exists on python.org (3.15.0b1+) and that "
            f"you are online. Transient network/SSL errors are retried "
            f"{_DOWNLOAD_ATTEMPTS} times."
        ) from last_exc


class PythonXcframeworkError(Exception):
    pass


def ios_floor(version: str) -> str:
    minor = ".".join(version.split(".")[:2])
    return _IOS_FLOORS.get(minor, "13.0")
