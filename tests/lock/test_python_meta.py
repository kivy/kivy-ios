"""python.org iOS xcframework URL resolution (pre-releases vs finals)."""

from __future__ import annotations

from kivy_ios.artifacts.cache import ArtifactCache
from kivy_ios.lock.python_meta import (
    PythonOrgProvider,
    PythonXcframeworkError,
    archive_filename,
    python_org_ios_url,
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


def test_lock_offline_requires_cached_python_xcframework(tmp_path):
    cache = ArtifactCache(root=tmp_path)
    provider = PythonOrgProvider(cache=cache)

    try:
        provider.get("3.15.0b2", offline=True)
    except PythonXcframeworkError as exc:
        assert "not in the artifact cache" in str(exc)
    else:
        raise AssertionError("expected PythonXcframeworkError")
