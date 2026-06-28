"""Native xcframework resolver: source fetch, SHA-256 pin, slice enumeration."""

from __future__ import annotations

import plistlib
import shutil
import tarfile
import zipfile
from pathlib import Path

import pytest

from kivy_ios.artifacts.verify import sha256_file
from kivy_ios.config.model import XcframeworkDep
from kivy_ios.lock.xcframework import (
    XcframeworkResolverError,
    resolve_xcframeworks,
)


def _make_xcframework(root: Path, name: str, slices: list[str]) -> Path:
    """Build a minimal but real ``.xcframework`` tree with a valid Info.plist."""
    xc = root / f"{name}.xcframework"
    libraries = []
    for ident in slices:
        (xc / ident).mkdir(parents=True)
        (xc / ident / name).write_text("binary")
        libraries.append(
            {"LibraryIdentifier": ident, "LibraryPath": f"{name}.framework"}
        )
    with open(xc / "Info.plist", "wb") as fh:
        plistlib.dump(
            {"AvailableLibraries": libraries, "CFBundlePackageType": "XFWK"}, fh
        )
    return xc


def _zip(xc: Path, archive: Path) -> Path:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w") as zf:
        for p in xc.rglob("*"):
            zf.write(p, p.relative_to(xc.parent))
    return archive


class _FakeDownloader:
    """Copies a prebuilt local archive to the requested dest (no network)."""

    def __init__(self, source_archive: Path) -> None:
        self._archive = source_archive
        self.calls: list[str] = []

    def fetch_to(self, url: str, dest: Path) -> None:
        self.calls.append(url)
        shutil.copy2(self._archive, dest)


class TestLocalArchive:
    def test_resolves_zip_path(self, tmp_path):
        build = tmp_path / "build"
        xc = _make_xcframework(
            build, "Sentry", ["ios-arm64", "ios-arm64_x86_64-simulator"]
        )
        archive = _zip(xc, tmp_path / "frameworks" / "Sentry.zip")

        dep = XcframeworkDep(
            name="Sentry",
            version="8.49.0",
            source="frameworks/Sentry.zip",
            embed=False,
        )
        (locked,) = resolve_xcframeworks((dep,), project_root=tmp_path)

        assert locked.name == "Sentry"
        assert locked.version == "8.49.0"
        assert locked.path == "frameworks/Sentry.zip"
        assert locked.url is None
        assert locked.sha256 == sha256_file(archive)
        assert locked.slices == ("ios-arm64", "ios-arm64_x86_64-simulator")
        assert locked.archive_format == "zip"
        assert locked.link is True
        assert locked.embed is False
        assert locked.source == "frameworks/Sentry.zip"

    def test_resolves_tar_gz_path(self, tmp_path):
        build = tmp_path / "build"
        xc = _make_xcframework(build, "Analytics", ["ios-arm64"])
        archive = tmp_path / "Analytics.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            tf.add(xc, arcname="Analytics.xcframework")

        dep = XcframeworkDep("Analytics", "1.0.0", "Analytics.tar.gz")
        (locked,) = resolve_xcframeworks((dep,), project_root=tmp_path)

        assert locked.archive_format == "tar.gz"
        assert locked.slices == ("ios-arm64",)
        assert locked.sha256 == sha256_file(archive)

    def test_missing_archive_raises(self, tmp_path):
        dep = XcframeworkDep("Gone", "1.0.0", "frameworks/Gone.zip")
        with pytest.raises(XcframeworkResolverError, match="not found"):
            resolve_xcframeworks((dep,), project_root=tmp_path)

    def test_unpacked_directory_source_is_actionable(self, tmp_path):
        # An unpacked .xcframework directory is not an archive; require zipping.
        dep = XcframeworkDep("Dir", "1.0.0", "Dir.xcframework")
        with pytest.raises(XcframeworkResolverError, match="zip"):
            resolve_xcframeworks((dep,), project_root=tmp_path)

    def test_escaping_path_rejected(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()
        with pytest.raises(XcframeworkResolverError, match="outside the project"):
            resolve_xcframeworks(
                (XcframeworkDep("X", "1.0.0", "../../etc/X.zip"),),
                project_root=project,
            )


class TestRemoteArchive:
    def test_resolves_via_injected_downloader(self, tmp_path):
        build = tmp_path / "build"
        xc = _make_xcframework(build, "Remote", ["ios-arm64"])
        archive = _zip(xc, tmp_path / "Remote.zip")
        downloader = _FakeDownloader(archive)

        dep = XcframeworkDep("Remote", "2.0.0", "https://example.com/Remote.zip")
        (locked,) = resolve_xcframeworks(
            (dep,), project_root=tmp_path, downloader=downloader
        )

        assert downloader.calls == ["https://example.com/Remote.zip"]
        assert locked.url == "https://example.com/Remote.zip"
        assert locked.path is None
        assert locked.sha256 == sha256_file(archive)
        assert locked.slices == ("ios-arm64",)

    def test_offline_url_raises(self, tmp_path):
        dep = XcframeworkDep("Remote", "2.0.0", "https://example.com/Remote.zip")
        with pytest.raises(XcframeworkResolverError, match="offline"):
            resolve_xcframeworks((dep,), project_root=tmp_path, offline=True)


class TestMisc:
    def test_unsupported_extension_raises(self, tmp_path):
        dep = XcframeworkDep("Weird", "1.0.0", "frameworks/Weird.rar")
        with pytest.raises(XcframeworkResolverError, match=r"\.zip or \.tar\.gz"):
            resolve_xcframeworks((dep,), project_root=tmp_path)

    def test_empty_declared_returns_empty(self, tmp_path):
        assert resolve_xcframeworks((), project_root=tmp_path) == []

    def test_sorted_by_name(self, tmp_path):
        for nm in ("Zeta", "Alpha"):
            xc = _make_xcframework(tmp_path / f"b_{nm}", nm, ["ios-arm64"])
            _zip(xc, tmp_path / f"{nm}.zip")
        deps = (
            XcframeworkDep("Zeta", "1.0.0", "Zeta.zip"),
            XcframeworkDep("Alpha", "1.0.0", "Alpha.zip"),
        )
        locked = resolve_xcframeworks(deps, project_root=tmp_path)
        assert [x.name for x in locked] == ["Alpha", "Zeta"]
