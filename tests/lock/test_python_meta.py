"""python.org iOS xcframework URL resolution (pre-releases vs finals)."""

from __future__ import annotations

import io
import plistlib
import tarfile
from pathlib import Path

from kivy_ios.artifacts.cache import ArtifactCache
from kivy_ios.lock.python_meta import (
    PythonOrgProvider,
    PythonXcframeworkError,
    archive_filename,
    python_org_ios_url,
    read_ios_floor,
)


def test_prerelease_url_under_base_release_dir():
    assert (
        python_org_ios_url("3.15.0b2")
        == "https://www.python.org/ftp/python/3.15.0/python-3.15.0b2-iOS-XCframework.tar.gz"
    )


def test_final_release_url():
    assert (
        python_org_ios_url("3.15.0")
        == "https://www.python.org/ftp/python/3.15.0/python-3.15.0-iOS-XCframework.tar.gz"
    )


def test_lock_hashes_python_xcframework_from_artifact_cache(tmp_path):
    import hashlib

    version = "3.15.0b2"
    filename = archive_filename(version)
    data = b"fake-xcframework-archive"
    sha = hashlib.sha256(data).hexdigest()
    cache = ArtifactCache(root=tmp_path)
    cache.put_bytes(data, sha, filename)

    info = PythonOrgProvider(cache=cache).get(version)

    assert info.sha256 == sha
    assert info.url == python_org_ios_url(version)
    # Fake bytes are not a valid tarball — floor falls back to the safe default.
    assert info.ios_floor == "13.0"


def test_lock_offline_requires_cached_python_xcframework(tmp_path):
    cache = ArtifactCache(root=tmp_path)
    provider = PythonOrgProvider(cache=cache)

    try:
        provider.get("3.15.0b2", offline=True)
    except PythonXcframeworkError as exc:
        assert "not in the artifact cache" in str(exc)
    else:
        raise AssertionError("expected PythonXcframeworkError")


def _make_xcframework_archive(tmp_path, *, min_os: str) -> Path:
    """Build a minimal .tar.gz containing Python.xcframework/Info.plist."""
    plist_data = plistlib.dumps(
        {
            "AvailableLibraries": [
                {
                    "LibraryIdentifier": "ios-arm64",
                    "MinimumOSVersion": min_os,
                },
                {
                    "LibraryIdentifier": "ios-arm64-simulator",
                    "MinimumOSVersion": min_os,
                },
            ]
        }
    )
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo("Python.xcframework/Info.plist")
        info.size = len(plist_data)
        tf.addfile(info, io.BytesIO(plist_data))
    archive = tmp_path / "python-3.15.0-iOS-XCframework.tar.gz"
    archive.write_bytes(buf.getvalue())
    return archive


def test_read_ios_floor_from_xcframework_plist(tmp_path):
    archive = _make_xcframework_archive(tmp_path, min_os="14.0")
    assert read_ios_floor(archive) == "14.0"


def test_read_ios_floor_fallback_on_invalid_archive(tmp_path):
    archive = tmp_path / "bad.tar.gz"
    archive.write_bytes(b"not a tarball")
    assert read_ios_floor(archive) == "13.0"
