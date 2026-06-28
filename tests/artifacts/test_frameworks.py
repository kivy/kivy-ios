"""Phase 4 — .frameworks extraction, archive_member, duplicate policy (spec 03)."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

from kivy_ios.artifacts.frameworks import (
    FrameworkConflict,
    copy_wheel_frameworks,
    extract_xcframework_archive,
)


def _make_xcframework(root: Path, name: str, content: str = "binary") -> Path:
    xc = root / f"{name}.xcframework"
    (xc / "ios-arm64").mkdir(parents=True)
    (xc / "Info.plist").write_text("<plist/>")
    (xc / "ios-arm64" / f"{name}").write_text(content)
    return xc


class TestWheelFrameworks:
    def test_copies_embedded_frameworks(self, tmp_path):
        pip_deps = tmp_path / "pip-deps"
        embedded = pip_deps / "kivy.frameworks"
        embedded.mkdir(parents=True)
        _make_xcframework(embedded, "SDL3")
        _make_xcframework(embedded, "ANGLE")
        frameworks = tmp_path / "Frameworks"

        copied = copy_wheel_frameworks(pip_deps, frameworks)
        assert copied == ["ANGLE.xcframework", "SDL3.xcframework"]
        assert (frameworks / "SDL3.xcframework" / "Info.plist").is_file()
        assert not embedded.exists()

    def test_strips_dot_frameworks_after_copy(self, tmp_path):
        pip_deps = tmp_path / "pip-deps"
        embedded = pip_deps / ".frameworks"
        embedded.mkdir(parents=True)
        _make_xcframework(embedded, "SDL3")
        copy_wheel_frameworks(pip_deps, tmp_path / "Frameworks")
        assert not embedded.exists()

    def test_conflicting_duplicate_fails_naming_both(self, tmp_path):
        # Same basename, different content -> hard fail naming both providers.
        pip_deps = tmp_path / "pip-deps"
        a = pip_deps / "pkga.frameworks"
        b = pip_deps / "pkgb.frameworks"
        a.mkdir(parents=True)
        b.mkdir(parents=True)
        _make_xcframework(a, "SDL3", content="v1")
        _make_xcframework(b, "SDL3", content="v2")
        with pytest.raises(FrameworkConflict) as exc:
            copy_wheel_frameworks(pip_deps, tmp_path / "Frameworks")
        message = str(exc.value)
        assert "SDL3.xcframework" in message
        assert "pkga.frameworks" in message
        assert "pkgb.frameworks" in message

    def test_identical_duplicate_dedupes_silently(self, tmp_path):
        # Same basename, identical content -> keep one copy, no error.
        pip_deps = tmp_path / "pip-deps"
        a = pip_deps / "pkga.frameworks"
        b = pip_deps / "pkgb.frameworks"
        a.mkdir(parents=True)
        b.mkdir(parents=True)
        _make_xcframework(a, "SDL3")
        _make_xcframework(b, "SDL3")
        frameworks = tmp_path / "Frameworks"
        copied = copy_wheel_frameworks(pip_deps, frameworks)
        assert copied == ["SDL3.xcframework"]
        assert (frameworks / "SDL3.xcframework" / "ios-arm64" / "SDL3").is_file()

    def test_same_framework_across_slices_dedupes(self, tmp_path):
        # The same wheel-embedded framework is copied once per pip-deps slice;
        # a shared registry must treat the second slice as a no-op, not a clash.
        frameworks = tmp_path / "Frameworks"
        registry = {}
        for slice_name in ("pip-deps-simulator", "pip-deps-device"):
            pip_deps = tmp_path / slice_name
            embedded = pip_deps / "kivy.frameworks"
            embedded.mkdir(parents=True)
            _make_xcframework(embedded, "SDL3")
            copy_wheel_frameworks(pip_deps, frameworks, existing=registry)
        assert sorted(registry) == ["SDL3.xcframework"]

    def test_no_frameworks_is_empty(self, tmp_path):
        pip_deps = tmp_path / "pip-deps"
        pip_deps.mkdir()
        assert copy_wheel_frameworks(pip_deps, tmp_path / "Frameworks") == []


def _zip_archive(tmp_path: Path, build: Path, name: str) -> Path:
    archive = tmp_path / f"{name}.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for p in build.rglob("*"):
            zf.write(p, p.relative_to(build.parent))
    return archive


class TestArchiveExtraction:
    def test_zip_autodetect_single(self, tmp_path):
        staging = tmp_path / "staging"
        xc = _make_xcframework(staging, "Sentry")
        archive = _zip_archive(tmp_path, xc, "Sentry")
        frameworks = tmp_path / "Frameworks"
        dest = extract_xcframework_archive(
            archive, frameworks, name="Sentry", archive_format="zip"
        )
        assert dest == frameworks / "Sentry.xcframework"
        assert (dest / "Info.plist").is_file()

    def test_tar_gz_autodetect(self, tmp_path):
        staging = tmp_path / "staging"
        xc = _make_xcframework(staging, "Analytics")
        archive = tmp_path / "Analytics.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            tf.add(xc, arcname="Analytics.xcframework")
        frameworks = tmp_path / "Frameworks"
        dest = extract_xcframework_archive(
            archive, frameworks, name="Analytics", archive_format="tar.gz"
        )
        assert (dest / "ios-arm64" / "Analytics").is_file()

    def test_archive_member_selects_one(self, tmp_path):
        staging = tmp_path / "staging"
        staging.mkdir()
        _make_xcframework(staging, "Wanted")
        _make_xcframework(staging, "Other")
        archive = tmp_path / "multi.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            for p in staging.rglob("*"):
                zf.write(p, p.relative_to(staging))
        frameworks = tmp_path / "Frameworks"
        dest = extract_xcframework_archive(
            archive, frameworks, name="Wanted", archive_member="Wanted.xcframework"
        )
        assert dest == frameworks / "Wanted.xcframework"

    def test_cross_source_identical_dedupes(self, tmp_path):
        # A wheel and a native archive ship the same framework, byte-identical.
        frameworks = tmp_path / "Frameworks"
        pip_deps = tmp_path / "pip-deps"
        embedded = pip_deps / "kivy.frameworks"
        embedded.mkdir(parents=True)
        _make_xcframework(embedded, "Shared")
        registry = {}
        copy_wheel_frameworks(pip_deps, frameworks, existing=registry)

        staging = tmp_path / "staging"
        xc = _make_xcframework(staging, "Shared")
        archive = _zip_archive(tmp_path, xc, "Shared")
        dest = extract_xcframework_archive(
            archive, frameworks, name="Shared", existing=registry
        )
        assert dest == frameworks / "Shared.xcframework"
        assert sorted(registry) == ["Shared.xcframework"]

    def test_cross_source_conflict_names_both(self, tmp_path):
        frameworks = tmp_path / "Frameworks"
        pip_deps = tmp_path / "pip-deps"
        embedded = pip_deps / "kivy.frameworks"
        embedded.mkdir(parents=True)
        _make_xcframework(embedded, "Shared", content="from-wheel")
        registry = {}
        copy_wheel_frameworks(pip_deps, frameworks, existing=registry)

        staging = tmp_path / "staging"
        xc = _make_xcframework(staging, "Shared", content="from-archive")
        archive = _zip_archive(tmp_path, xc, "Shared")
        with pytest.raises(FrameworkConflict) as exc:
            extract_xcframework_archive(
                archive, frameworks, name="Shared", existing=registry
            )
        message = str(exc.value)
        assert "kivy.frameworks" in message
        assert "Shared.zip" in message

    def test_multiple_without_member_conflicts(self, tmp_path):
        staging = tmp_path / "staging"
        staging.mkdir()
        _make_xcframework(staging, "One")
        _make_xcframework(staging, "Two")
        archive = tmp_path / "multi.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            for p in staging.rglob("*"):
                zf.write(p, p.relative_to(staging))
        with pytest.raises(FrameworkConflict, match="multiple"):
            extract_xcframework_archive(
                archive, tmp_path / "Frameworks", name="ambiguous"
            )
