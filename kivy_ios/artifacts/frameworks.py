"""Populate ``<app>-ios/Frameworks/`` from wheels and xcframework archives (spec 03/06).

Two sources land in ``Frameworks/``:

1. **Wheel-embedded xcframeworks** — a wheel may ship a ``<pkg>.frameworks/``
   directory containing one or more ``<name>.xcframework`` trees (for the
   canonical Kivy app, ANGLE + the SDL3 family ride inside the kivy wheel).
   ``toolchain build`` walks installed wheels and copies each one out.
2. **Standalone native xcframework archives** — ``[[tool.kivy_ios.xcframeworks]]``
   entries, extracted from a zip/tar.gz (honoring ``archive_member`` when the
   archive holds more than one xcframework).

A duplicate-framework policy (spec 06) guards against two sources providing the
same ``<name>.xcframework``: identical content (same tree hash) is deduplicated
silently, while a basename collision with differing content fails the build,
naming both providers and their hashes.
"""

from __future__ import annotations

import hashlib
import plistlib
import shutil
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


class FrameworkConflict(Exception):
    """Two artifacts provide the same ``<name>.xcframework`` with differing content."""


@dataclass(frozen=True)
class PlacedFramework:
    """A framework staged into ``Frameworks/``, with provenance for conflict checks."""

    path: Path
    origin: str
    tree_hash: str


def copy_wheel_frameworks(
    pip_deps: Path,
    frameworks_dir: Path,
    *,
    existing: dict[str, PlacedFramework] | None = None,
) -> list[str]:
    """Copy every ``*.xcframework`` found under any ``*.frameworks/`` dir.

    Returns the names placed during this call. Two artifacts that share a
    framework basename are deduplicated when their content trees hash equal, and
    raise ``FrameworkConflict`` (naming both providers) when they differ.

    ``existing`` is a shared registry threaded across the multiple pip-deps
    slices (and into native xcframework extraction) so cross-source duplicates
    are reconciled against everything already staged.

    After copying, wheel staging dirs (``kivy.frameworks``, ``.frameworks``, …)
    are removed from ``pip-deps/`` so Copy Bundle Resources does not ship
    duplicate xcframework trees inside the app bundle.
    """
    frameworks_dir.mkdir(parents=True, exist_ok=True)
    registry = existing if existing is not None else {}
    placed: set[str] = set()
    embedded_dirs: list[Path] = []
    for frameworks_subdir in sorted(pip_deps.glob("*.frameworks")):
        if not frameworks_subdir.is_dir():
            continue
        embedded_dirs.append(frameworks_subdir)
        for xc in sorted(frameworks_subdir.glob("*.xcframework")):
            _place(xc, frameworks_dir, registry, origin=str(frameworks_subdir.name))
            placed.add(xc.name)
    for subdir in embedded_dirs:
        shutil.rmtree(subdir)
    return sorted(placed)


def extract_xcframework_archive(
    archive: Path,
    frameworks_dir: Path,
    *,
    name: str,
    archive_format: str = "zip",
    archive_member: str | None = None,
    existing: dict[str, PlacedFramework] | None = None,
) -> Path:
    """Extract a native ``.xcframework`` from an archive into ``Frameworks/``.

    ``archive_member`` names the exact ``.xcframework`` directory inside the
    archive when auto-detection (single top-level ``.xcframework``) is
    insufficient. Returns the destination path. ``existing`` is the shared
    registry used to dedupe identical duplicates and reject conflicting ones.
    """
    frameworks_dir.mkdir(parents=True, exist_ok=True)
    registry = existing if existing is not None else {}
    import tempfile

    with tempfile.TemporaryDirectory(prefix="kivy-xc-") as tmp:
        tmp_dir = Path(tmp)
        _unpack(archive, tmp_dir, archive_format)
        xc_dir = _locate_xcframework(tmp_dir, archive_member, name=name)
        return _place(xc_dir, frameworks_dir, registry, origin=archive.name)


def read_xcframework_slices(xcframework: Path) -> tuple[str, ...]:
    """Return the slice identifiers declared in an ``.xcframework`` root plist.

    These are the ``LibraryIdentifier`` values from ``Info.plist``'s
    ``AvailableLibraries`` (e.g. ``ios-arm64``, ``ios-arm64_x86_64-simulator``),
    returned sorted for a deterministic lockfile. ``toolchain lock`` records them
    so the lock advertises which device/simulator slices an artifact ships.
    """
    info = xcframework / "Info.plist"
    try:
        with open(info, "rb") as fh:
            data = plistlib.load(fh)
    except OSError as exc:
        raise FileNotFoundError(
            f"{xcframework.name}: missing or unreadable Info.plist ({exc})."
        ) from exc
    libraries = data.get("AvailableLibraries", [])
    identifiers = [
        lib["LibraryIdentifier"]
        for lib in libraries
        if isinstance(lib, dict) and lib.get("LibraryIdentifier")
    ]
    return tuple(sorted(identifiers))


def _unpack(archive: Path, dest: Path, archive_format: str) -> None:
    if archive_format == "zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dest)
    elif archive_format in ("tar.gz", "tgz", "targz"):
        with tarfile.open(archive, "r:gz") as tf:
            # filter="data" rejects path traversal, absolute paths, and
            # unsafe special files (Python 3.12+ / PEP 706).
            tf.extractall(dest, filter="data")
    else:
        raise ValueError(f"unsupported archive_format {archive_format!r} (zip|tar.gz)")


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
    src: Path,
    frameworks_dir: Path,
    registry: dict[str, PlacedFramework],
    *,
    origin: str,
) -> Path:
    """Stage ``src`` into ``Frameworks/`` applying the duplicate policy (spec 06).

    Identical content (matching tree hash) already staged under the same
    basename is deduplicated silently; differing content raises
    ``FrameworkConflict`` naming both providers and their hashes.
    """
    dest = frameworks_dir / src.name
    new_hash = _tree_hash(src)
    prior = registry.get(src.name)
    if prior is not None:
        if prior.tree_hash == new_hash:
            # Same artifact from two sources (or the same wheel across slices):
            # keep the copy already staged, emit nothing.
            return prior.path
        raise FrameworkConflict(
            f"{src.name} is provided by two sources with different contents:\n"
            f"  - {prior.origin} (sha256 {prior.tree_hash})\n"
            f"  - {origin} (sha256 {new_hash})\n"
            "  Pin a single provider, or remove the duplicate. kivy-ios does not "
            "pick a winner: a version mismatch can link yet crash at runtime."
        )
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    _normalize_framework_plists(dest)
    registry[src.name] = PlacedFramework(path=dest, origin=origin, tree_hash=new_hash)
    return dest


def _tree_hash(root: Path) -> str:
    """Deterministic SHA-256 over a directory tree's structure and file contents.

    Walks entries in sorted relative-path order, framing each with a type tag
    (file/dir/symlink), its relative path, and — for files — a length-prefixed
    stream of contents, so two trees hash equal iff their layout and bytes match.
    """
    h = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        if path.is_symlink():
            target = path.readlink().as_posix().encode("utf-8")
            h.update(b"L\0" + rel + b"\0" + target + b"\0")
        elif path.is_dir():
            h.update(b"D\0" + rel + b"\0")
        elif path.is_file():
            size = path.stat().st_size
            h.update(b"F\0" + rel + b"\0" + str(size).encode("ascii") + b"\0")
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    h.update(chunk)
    return h.hexdigest()


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
