"""Phase 5 — collect_artifacts orchestration (steps 2-5), fully hermetic.

Uses path-based lock entries (no network) with real SHA-256 pins, an injected
subprocess runner in place of pip, and a real tar.gz/zip on disk.
"""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

from kivy_ios.artifacts.cache import ArtifactCache
from kivy_ios.artifacts.collect import collect_artifacts
from kivy_ios.artifacts.verify import sha256_file
from kivy_ios.artifacts.wheels import BuildSlice
from kivy_ios.lock.model import (
    LockedPackage,
    LockedWheel,
    LockedXcframework,
    Lockfile,
    PythonXcframework,
)
from kivy_ios.project.staging import StagingLayout


def _make_python_tarball(root: Path) -> Path:
    src = root / "pysrc"
    (src / "Python.xcframework" / "ios-arm64").mkdir(parents=True)
    (src / "Python.xcframework" / "Info.plist").write_text("<plist/>")
    archive = root / "python.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(src / "Python.xcframework", arcname="Python.xcframework")
    return archive


def _make_xcframework_zip(root: Path, name: str) -> Path:
    src = root / f"{name}-src"
    (src / f"{name}.xcframework" / "ios-arm64").mkdir(parents=True)
    (src / f"{name}.xcframework" / "Info.plist").write_text("<plist/>")
    archive = root / f"{name}.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for p in (src / f"{name}.xcframework").rglob("*"):
            zf.write(p, p.relative_to(src))
    return archive


@pytest.fixture
def layout(tmp_path):
    root = tmp_path / "app-ios"
    for d in (
        root,
        root / "Frameworks",
        root / "pip-deps-device",
        root / "pip-deps-simulator",
        root / "Resources",
    ):
        d.mkdir(parents=True)
    return StagingLayout(root=root)


@pytest.fixture
def cache(tmp_path):
    return ArtifactCache(root=tmp_path / "cache")


def test_collect_installs_python_wheels_and_frameworks(tmp_path, layout, cache):
    art = tmp_path / "art"
    art.mkdir()
    py_tar = _make_python_tarball(art)
    wheel = art / "kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphoneos.whl"
    wheel.write_bytes(b"fake wheel")
    native = _make_xcframework_zip(art, "SDL3")

    lock = Lockfile(
        requires_python=">=3.15",
        packages=(
            LockedPackage(
                name="kivy",
                version="3.0.0",
                wheels=(
                    LockedWheel(
                        name=wheel.name,
                        sha256=sha256_file(wheel),
                        path=str(wheel.relative_to(tmp_path)),
                    ),
                ),
            ),
        ),
        python_xcframework=PythonXcframework(
            version="3.15.0",
            url="https://example/python.tar.gz",
            sha256=sha256_file(py_tar),
        ),
        toolchain_version="3.0.0.dev0",
        generated_at="2026-01-01T00:00:00Z",
        pyproject_sha256="d" * 64,
        tool_kivy_ios_schema_version=1,
        xcframeworks=(
            LockedXcframework(
                name="SDL3",
                version="3.0.0",
                sha256=sha256_file(native),
                slices=("ios-arm64",),
                path=str(native.relative_to(tmp_path)),
                archive_format="zip",
            ),
        ),
    )

    class FakeDownloader:
        def fetch_to(self, url, dest):
            # Python.xcframework is the only url-based artifact here.
            import shutil

            shutil.copyfile(py_tar, dest)

    pip_calls = []

    def fake_runner(cmd, capture_output=True, text=True):
        pip_calls.append(cmd)
        # Simulate pip laying down a wheel-embedded .frameworks dir inside
        # the slice-specific pip-deps (device build → pip-deps-device/).
        emb = layout.pip_deps_device / "kivy.frameworks" / "ANGLE.xcframework"
        emb.mkdir(parents=True)
        (emb / "Info.plist").write_text("<plist/>")

        class P:
            returncode = 0
            stdout = ""
            stderr = ""

        return P()

    collect_artifacts(
        lock,
        layout,
        build_slices=[BuildSlice("device", "arm64", "13.0")],
        project_root=tmp_path,
        cache=cache,
        downloader=FakeDownloader(),
        runner=fake_runner,
    )

    # Python.xcframework extracted in place.
    assert (layout.python_xcframework / "Info.plist").is_file()
    # pip install invoked once with the wheel + cross-install flags.
    assert len(pip_calls) == 1
    assert "--platform" in pip_calls[0]
    assert any(c.endswith(wheel.name) for c in pip_calls[0])
    # wheel-embedded + native frameworks both landed in Frameworks/.
    assert (layout.frameworks / "ANGLE.xcframework").is_dir()
    assert (layout.frameworks / "SDL3.xcframework").is_dir()
    assert not (layout.pip_deps_device / "kivy.frameworks").exists()


def test_collect_both_slices_installs_each_pip_deps(tmp_path, layout, cache):
    # A bare `toolchain build` collects device + simulator: Python.xcframework is
    # fetched once, but pip-deps is installed into BOTH slice directories so
    # either Xcode destination builds without re-running the toolchain.
    art = tmp_path / "art"
    art.mkdir()
    py_tar = _make_python_tarball(art)
    wheel = art / "purepkg-1.0-py3-none-any.whl"
    wheel.write_bytes(b"fake wheel")

    lock = Lockfile(
        requires_python=">=3.15",
        packages=(
            LockedPackage(
                name="purepkg",
                version="1.0",
                wheels=(
                    LockedWheel(
                        name=wheel.name,
                        sha256=sha256_file(wheel),
                        path=str(wheel.relative_to(tmp_path)),
                    ),
                ),
            ),
        ),
        python_xcframework=PythonXcframework(
            version="3.15.0",
            url="https://example/python.tar.gz",
            sha256=sha256_file(py_tar),
        ),
        toolchain_version="3.0.0.dev0",
        generated_at="2026-01-01T00:00:00Z",
        pyproject_sha256="d" * 64,
        tool_kivy_ios_schema_version=1,
    )

    class FakeDownloader:
        def fetch_to(self, url, dest):
            import shutil

            shutil.copyfile(py_tar, dest)

    target_dirs = []

    def fake_runner(cmd, capture_output=True, text=True):
        target_dirs.append(cmd[cmd.index("--target") + 1])

        class P:
            returncode = 0
            stdout = ""
            stderr = ""

        return P()

    collect_artifacts(
        lock,
        layout,
        build_slices=[
            BuildSlice("device", "arm64", "13.0"),
            BuildSlice("simulator", "arm64", "13.0"),
        ],
        project_root=tmp_path,
        cache=cache,
        downloader=FakeDownloader(),
        runner=fake_runner,
    )

    # Python.xcframework extracted exactly once (shared, slice-independent).
    assert (layout.python_xcframework / "Info.plist").is_file()
    # pip ran once per slice, each into its own slice-specific pip-deps dir.
    assert target_dirs == [
        str(layout.pip_deps_device),
        str(layout.pip_deps_simulator),
    ]


def test_collect_no_packages_skips_pip(tmp_path, layout, cache):
    art = tmp_path / "art"
    art.mkdir()
    py_tar = _make_python_tarball(art)
    lock = Lockfile(
        requires_python=">=3.15",
        packages=(),
        python_xcframework=PythonXcframework(
            version="3.15.0",
            url="https://example/python.tar.gz",
            sha256=sha256_file(py_tar),
        ),
        toolchain_version="3.0.0.dev0",
        generated_at="2026-01-01T00:00:00Z",
        pyproject_sha256="d" * 64,
        tool_kivy_ios_schema_version=1,
    )

    class FakeDownloader:
        def fetch_to(self, url, dest):
            import shutil

            shutil.copyfile(py_tar, dest)

    def boom(*a, **k):  # pip must not be called with zero wheels
        raise AssertionError("pip should not run with no packages")

    collect_artifacts(
        lock,
        layout,
        build_slices=[BuildSlice("device", "arm64", "13.0")],
        project_root=tmp_path,
        cache=cache,
        downloader=FakeDownloader(),
        runner=boom,
    )
    assert (layout.python_xcframework / "Info.plist").is_file()
