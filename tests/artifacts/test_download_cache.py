"""Phase 4 — cache hit/miss, hash verify/abort, local path resolution (spec 03)."""

from __future__ import annotations

from pathlib import Path

import pytest

from kivy_ios.artifacts.cache import DEFAULT_CACHE_ROOT, ArtifactCache
from kivy_ios.artifacts.download import DownloadError, fetch_artifact
from kivy_ios.artifacts.verify import HashMismatch, sha256_bytes, sha256_file


class FakeDownloader:
    """Writes fixed content and counts calls (to assert cache hits)."""

    def __init__(self, content: bytes) -> None:
        self.content = content
        self.calls = 0

    def fetch_to(self, url: str, dest: Path) -> None:
        self.calls += 1
        dest.write_bytes(self.content)


@pytest.fixture
def cache(tmp_path):
    return ArtifactCache(root=tmp_path / "cache")


class TestCachePaths:
    def test_default_root(self):
        assert ArtifactCache().root == DEFAULT_CACHE_ROOT
        assert DEFAULT_CACHE_ROOT == (
            Path.home() / "Library" / "Caches" / "kivy-ios" / "artifacts"
        )


class TestDownloadVerifyCache:
    def test_download_and_cache(self, cache):
        content = b"wheel-bytes"
        sha = sha256_bytes(content)
        dl = FakeDownloader(content)
        path = fetch_artifact(
            name="kivy",
            sha256=sha,
            filename="kivy.whl",
            url="https://example.com/kivy.whl",
            cache=cache,
            downloader=dl,
        )
        assert path.read_bytes() == content
        assert dl.calls == 1

    def test_cache_hit_avoids_redownload(self, cache):
        content = b"abc"
        sha = sha256_bytes(content)
        dl = FakeDownloader(content)
        for _ in range(2):
            fetch_artifact(
                name="x",
                sha256=sha,
                filename="x.whl",
                url="https://e/x.whl",
                cache=cache,
                downloader=dl,
            )
        assert dl.calls == 1  # second call was a cache hit

    def test_no_cache_forces_redownload(self, cache):
        content = b"abc"
        sha = sha256_bytes(content)
        dl = FakeDownloader(content)
        fetch_artifact(
            name="x",
            sha256=sha,
            filename="x.whl",
            url="https://e/x.whl",
            cache=cache,
            downloader=dl,
        )
        fetch_artifact(
            name="x",
            sha256=sha,
            filename="x.whl",
            url="https://e/x.whl",
            cache=cache,
            downloader=dl,
            no_cache=True,
        )
        assert dl.calls == 2

    def test_hash_mismatch_aborts(self, cache):
        dl = FakeDownloader(b"tampered")
        with pytest.raises(HashMismatch) as exc:
            fetch_artifact(
                name="evil",
                sha256="0" * 64,
                filename="e.whl",
                url="https://e/e.whl",
                cache=cache,
                downloader=dl,
            )
        assert exc.value.name == "evil"
        # nothing tampered should be cached
        assert cache.get("0" * 64, "e.whl") is None


class TestLocalPath:
    def test_vendored_path_ok(self, tmp_path):
        wheel = tmp_path / "wheels" / "myext.whl"
        wheel.parent.mkdir()
        wheel.write_bytes(b"local")
        sha = sha256_bytes(b"local")
        path = fetch_artifact(
            name="myext",
            sha256=sha,
            filename="myext.whl",
            path="wheels/myext.whl",
            project_root=tmp_path,
        )
        assert path == wheel.resolve()

    def test_absolute_path_rejected(self, tmp_path):
        with pytest.raises(DownloadError, match="absolute"):
            fetch_artifact(
                name="x",
                sha256="0" * 64,
                filename="x.whl",
                path="/etc/passwd",
                project_root=tmp_path,
            )

    def test_escaping_path_rejected(self, tmp_path):
        root = tmp_path / "proj"
        root.mkdir()
        outside = tmp_path / "outside.whl"
        outside.write_bytes(b"x")
        with pytest.raises(DownloadError, match="escapes"):
            fetch_artifact(
                name="x",
                sha256="0" * 64,
                filename="x.whl",
                path="../../outside.whl",
                project_root=root,
            )

    def test_sibling_path_accepted(self, tmp_path):
        app = tmp_path / "app"
        shared = tmp_path / "wheels"
        app.mkdir()
        shared.mkdir()
        wheel = shared / "kivy-1.whl"
        wheel.write_bytes(b"x")
        sha = sha256_file(wheel)
        path = fetch_artifact(
            name="kivy",
            sha256=sha,
            filename="kivy-1.whl",
            path="../wheels/kivy-1.whl",
            project_root=app,
        )
        assert path == wheel.resolve()

    def test_url_and_path_mutually_exclusive(self, tmp_path):
        with pytest.raises(DownloadError, match="exactly one"):
            fetch_artifact(
                name="x",
                sha256="0" * 64,
                filename="x.whl",
                url="https://e/x",
                path="x",
                project_root=tmp_path,
            )
