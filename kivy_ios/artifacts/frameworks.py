"""Populate ``<app>-ios/Frameworks/`` from wheels and xcframework archives (spec 03/06).

Two sources land in ``Frameworks/``:

1. **Wheel-embedded xcframeworks** — a wheel may ship a ``<pkg>.frameworks/``
   directory containing one or more ``<name>.xcframework`` trees (for the
   canonical Kivy app, ANGLE + the SDL3 family ride inside the kivy wheel).
   ``toolchain build`` walks installed wheels and copies each one out.
2. **Standalone native xcframework archives** — ``[[tool.kivy_ios.xcframeworks]]``
   entries, extracted from a zip/tar.gz (honoring ``archive_member`` when the
   archive holds more than one xcframework).

A duplicate-framework policy guards against two sources providing the same
``<name>.xcframework``.
"""

from __future__ import annotations

import shutil
import tarfile
import zipfile
from pathlib import Path


class FrameworkConflict(Exception):
    """Two artifacts provide the same ``<name>.xcframework``."""


def copy_wheel_frameworks(pip_deps: Path, frameworks_dir: Path) -> list[str]:
    """Copy every ``*.xcframework`` found under any ``*.frameworks/`` dir.

    Returns the list of framework names copied. Raises ``FrameworkConflict`` if
    two wheels ship the same framework name with differing content.

    After copying, wheel staging dirs (``kivy.frameworks``, ``.frameworks``, …)
    are removed from ``pip-deps/`` so Copy Bundle Resources does not ship
    duplicate xcframework trees inside the app bundle.
    """
    frameworks_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, Path] = {}
    embedded_dirs: list[Path] = []
    for frameworks_subdir in sorted(pip_deps.glob("*.frameworks")):
        if not frameworks_subdir.is_dir():
            continue
        embedded_dirs.append(frameworks_subdir)
        for xc in sorted(frameworks_subdir.glob("*.xcframework")):
            _place(xc, frameworks_dir, copied, origin=str(frameworks_subdir.name))
    for subdir in embedded_dirs:
        shutil.rmtree(subdir)
    return sorted(copied)


def extract_xcframework_archive(
    archive: Path,
    frameworks_dir: Path,
    *,
    name: str,
    archive_format: str = "zip",
    archive_member: str | None = None,
    existing: dict[str, Path] | None = None,
) -> Path:
    """Extract a native ``.xcframework`` from an archive into ``Frameworks/``.

    ``archive_member`` names the exact ``.xcframework`` directory inside the
    archive when auto-detection (single top-level ``.xcframework``) is
    insufficient. Returns the destination path.
    """
    frameworks_dir.mkdir(parents=True, exist_ok=True)
    copied = existing if existing is not None else {}
    import tempfile

    with tempfile.TemporaryDirectory(prefix="kivy-xc-") as tmp:
        tmp_dir = Path(tmp)
        _unpack(archive, tmp_dir, archive_format)
        xc_dir = _locate_xcframework(tmp_dir, archive_member, name=name)
        return _place(xc_dir, frameworks_dir, copied, origin=archive.name)


def _unpack(archive: Path, dest: Path, archive_format: str) -> None:
    if archive_format == "zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dest)
    elif archive_format in ("tar.gz", "tgz", "targz"):
        with tarfile.open(archive, "r:gz") as tf:
            _safe_extract_tar(tf, dest)
    else:
        raise ValueError(f"unsupported archive_format {archive_format!r} (zip|tar.gz)")


def _safe_extract_tar(tf: tarfile.TarFile, dest: Path) -> None:
    # filter="data" rejects path traversal, absolute paths, and unsafe
    # special files (Python 3.12+ / PEP 706).
    tf.extractall(dest, filter="data")


def _locate_xcframework(root: Path, archive_member: str | None, *, name: str) -> Path:
    if archive_member:
        candidate = root / archive_member
        if not candidate.is_dir():
            raise FileNotFoundError(
                f"{name}: archive_member {archive_member!r} not found in archive."
            )
        return candidate
    matches = [p for p in root.rglob("*.xcframework") if p.is_dir()]
    if not matches:
        raise FileNotFoundError(f"{name}: no .xcframework found in archive.")
    # Auto-detect only considers the shallowest depth (the "top level").
    min_depth = min(len(p.relative_to(root).parts) for p in matches)
    top = [p for p in matches if len(p.relative_to(root).parts) == min_depth]
    if len(top) == 1:
        return top[0]
    raise FrameworkConflict(
        f"{name}: archive contains multiple .xcframework directories "
        f"({', '.join(sorted(p.name for p in top))}); set archive_member to pick one."
    )


def _place(
    src: Path, frameworks_dir: Path, copied: dict[str, Path], *, origin: str
) -> Path:
    dest = frameworks_dir / src.name
    if src.name in copied:
        raise FrameworkConflict(
            f"{src.name} is provided by more than one source "
            f"(latest: {origin}). Remove the duplicate or rename one framework."
        )
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    _normalize_framework_plists(dest)
    copied[src.name] = dest
    return dest


def _normalize_framework_plists(xcframework: Path) -> None:
    """Ensure each embedded ``.framework`` has a root ``Info.plist``.

    Some upstream wheels (e.g. KivyThorVG) ship the plist only under
    ``Resources/``; Xcode's bundle validation requires it at the framework root.
    """
    for fw in xcframework.rglob("*.framework"):
        if not fw.is_dir():
            continue
        root_plist = fw / "Info.plist"
        if root_plist.is_file():
            continue
        resources_plist = fw / "Resources" / "Info.plist"
        if resources_plist.is_file():
            shutil.copy2(resources_plist, root_plist)
