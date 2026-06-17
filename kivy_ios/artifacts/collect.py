"""Collect lockfile artifacts into the staging tree (build steps 2-5, spec 06).

Downloads/verifies the Python.xcframework, installs pinned wheels into
``pip-deps/``, copies wheel-embedded ``.frameworks/`` into ``Frameworks/``, and
extracts user-declared native xcframeworks. The subprocess runner is injectable
so the orchestration can be unit-tested without invoking pip.
"""

from __future__ import annotations

import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

from ..lock.model import LockedWheel, Lockfile
from .cache import ArtifactCache
from .download import Downloader, fetch_artifact
from .frameworks import copy_wheel_frameworks, extract_xcframework_archive
from .wheels import BuildSlice, pip_install_command, select_wheel


class CollectError(Exception):
    pass


def collect_artifacts(
    lock: Lockfile,
    layout,
    *,
    build_slices: list[BuildSlice],
    project_root: Path,
    cache: ArtifactCache | None = None,
    downloader: Downloader | None = None,
    no_cache: bool = False,
    runner=subprocess.run,
    python_executable: str | None = None,
) -> None:
    cache = cache or ArtifactCache()

    # Python.xcframework is multi-slice and slice-independent, so it is fetched
    # once regardless of how many pip-deps slices we populate. pip-deps itself is
    # installed per slice (device/simulator never share .so files): a bare
    # `toolchain build` passes both slices so either Xcode destination builds
    # without a re-run, while a targeted build passes only its slice.
    _install_python_xcframework(
        lock, layout, cache=cache, downloader=downloader, no_cache=no_cache
    )
    # Wheel-embedded frameworks are multi-slice xcframeworks; union them across
    # slices (dedup by name) so user-declared natives below don't clobber them.
    copied: dict[str, Path] = {}
    for build_slice in build_slices:
        slice_pip_deps = layout.pip_deps_for_slice(build_slice.target)
        _install_wheels(
            lock,
            layout,
            slice_pip_deps=slice_pip_deps,
            build_slice=build_slice,
            project_root=project_root,
            cache=cache,
            downloader=downloader,
            no_cache=no_cache,
            runner=runner,
            python_executable=python_executable,
        )
        for name in copy_wheel_frameworks(slice_pip_deps, layout.frameworks):
            copied[name] = layout.frameworks / name
    _install_native_xcframeworks(
        lock,
        layout,
        copied=copied,
        project_root=project_root,
        cache=cache,
        downloader=downloader,
        no_cache=no_cache,
    )


def _install_python_xcframework(lock, layout, *, cache, downloader, no_cache) -> None:
    px = lock.python_xcframework
    filename = px.url.rsplit("/", 1)[-1]
    archive = fetch_artifact(
        name=f"Python.xcframework {px.version}",
        sha256=px.sha256,
        filename=filename,
        url=px.url,
        cache=cache,
        downloader=downloader,
        no_cache=no_cache,
    )
    dest = layout.python_xcframework
    if dest.exists():
        shutil.rmtree(dest)
    with tempfile.TemporaryDirectory(prefix="kivy-pyxc-") as tmp:
        tmp_dir = Path(tmp)
        with tarfile.open(archive, "r:gz") as tf:
            _safe_extract(tf, tmp_dir)
        found = next(
            (p for p in tmp_dir.rglob("Python.xcframework") if p.is_dir()), None
        )
        if found is None:
            raise CollectError(
                "Python.xcframework not found inside downloaded archive."
            )
        shutil.copytree(found, dest)


def _install_wheels(
    lock,
    layout,
    *,
    slice_pip_deps,
    build_slice,
    project_root,
    cache,
    downloader,
    no_cache,
    runner,
    python_executable,
) -> None:
    with tempfile.TemporaryDirectory(prefix="kivy-wheels-") as tmp:
        stage = Path(tmp)
        wheel_files: list[str] = []
        selected_wheels: list[LockedWheel] = []
        for pkg in lock.packages:
            wheel = select_wheel(pkg, build_slice)
            selected_wheels.append(wheel)
            local = fetch_artifact(
                name=f"{pkg.name} {pkg.version}",
                sha256=wheel.sha256,
                filename=wheel.name,
                url=wheel.url,
                path=wheel.path,
                project_root=project_root,
                cache=cache,
                downloader=downloader,
                no_cache=no_cache,
            )
            # Cache entries are content-addressed ({sha256}-{name}); pip rejects
            # that filename, so stage each wheel under its canonical PEP 427 name.
            staged = stage / wheel.name
            if local.resolve() != staged.resolve():
                shutil.copy2(local, staged)
            wheel_files.append(str(staged))
        if not wheel_files:
            return
        # Each collect always starts from a clean slate so no stale .so
        # files from a previous slice accumulate in the slice-specific dir.
        if slice_pip_deps.is_dir():
            shutil.rmtree(slice_pip_deps)
        slice_pip_deps.mkdir(parents=True, exist_ok=True)
        abi = "cp" + "".join(lock.python_xcframework.version.split(".")[:2])
        # Use the selected wheels' actual platform tag for pip's --platform.
        # The wheel tag reflects the Python binary's compile-time minimum OS
        # (e.g. ios_13_0 from python.org's cp315 binary), which may be lower
        # than the project's deployment_target.  pip requires --platform to
        # match the wheel being installed, so use the selected native wheel's
        # tag rather than the computed build_slice tag.
        pip_platform = _native_platform_tag(selected_wheels, build_slice)
        cmd = pip_install_command(
            wheel_files,
            target_dir=str(slice_pip_deps),
            platform_tag=pip_platform,
            python_version=".".join(lock.python_xcframework.version.split(".")[:2]),
            abi=abi,
            python_executable=python_executable,
        )
        proc = runner(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise CollectError(
                f"pip install of pinned wheels failed:\n{proc.stderr or proc.stdout}"
            )
        # pip --target creates a bin/ of host-platform console scripts.
        # Strip it immediately — these macOS executables cannot run on iOS
        # and should not appear in the Xcode project tree or app bundle.
        bin_dir = slice_pip_deps / "bin"
        if bin_dir.is_dir():
            shutil.rmtree(bin_dir)


def _install_native_xcframeworks(
    lock, layout, *, copied, project_root, cache, downloader, no_cache
) -> None:
    for xc in lock.xcframeworks:
        filename = (xc.url or xc.path or xc.name).rsplit("/", 1)[-1]
        archive = fetch_artifact(
            name=xc.name,
            sha256=xc.sha256,
            filename=filename,
            url=xc.url,
            path=xc.path,
            project_root=project_root,
            cache=cache,
            downloader=downloader,
            no_cache=no_cache,
        )
        extract_xcframework_archive(
            archive,
            layout.frameworks,
            name=xc.name,
            archive_format=xc.archive_format,
            archive_member=xc.archive_member,
            existing=copied,
        )


def _native_platform_tag(selected: list[LockedWheel], slice_: BuildSlice) -> str:
    """Return the pip --platform tag to use for the selected wheels.

    All native wheels in a single build are produced by the same Python binary
    and therefore share the same platform tag (e.g. ios_13_0_arm64_iphoneos).
    Using the wheel's actual tag (rather than the project deployment_target tag)
    ensures pip accepts the wheel even when the wheel's min-OS is lower than the
    project's deployment_target.
    """
    for wheel in selected:
        if not wheel.is_pure_python:
            return wheel.platform_tag
    return slice_.platform_tag


def _safe_extract(tf: tarfile.TarFile, dest: Path) -> None:
    dest = dest.resolve()
    for member in tf.getmembers():
        target = (dest / member.name).resolve()
        if not str(target).startswith(str(dest)):
            raise CollectError(f"unsafe path in archive: {member.name}")
    tf.extractall(dest)
