"""Native xcframework resolver (spec 01/03 — the ``native.xcframeworks`` channel).

``toolchain lock`` reads each declared ``[tool.kivy.ios.native.xcframeworks]``
entry's ``source`` (a ``.zip`` or ``.tar.gz`` archive of the ``.xcframework``,
referenced by URL or repo-relative path), computes its SHA-256, and enumerates
the slices (the ``LibraryIdentifier`` values from the framework's ``Info.plist``).
Those pins land in ``pylock.ios.toml`` so ``toolchain build`` can re-fetch the
artifact by ``url``+``sha256`` (or ``path``) and extract it into ``Frameworks/``
reproducibly.

The download backend is injectable (``Downloader``) so unit tests stay hermetic
(no network). Resolution and collection share ``frameworks.extract_xcframework_archive``
so the slice the lock describes is exactly the one the build will install.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from ..artifacts.frameworks import (
    FrameworkConflict,
    extract_xcframework_archive,
    read_xcframework_slices,
)
from ..artifacts.verify import sha256_file
from ..config.model import XcframeworkDep
from .find_links import FindLinksError, wheel_path_from_project_root
from .model import LockedXcframework

if TYPE_CHECKING:
    from ..artifacts.download import Downloader


class XcframeworkResolverError(Exception):
    """A native xcframework resolution failure surfaced with an actionable message."""


def resolve_xcframeworks(
    declared: tuple[XcframeworkDep, ...],
    *,
    project_root: Path,
    downloader: Downloader | None = None,
    offline: bool = False,
) -> list[LockedXcframework]:
    """Resolve declared native xcframeworks into slice-enumerated lock entries.

    Returns entries sorted by ``(name, version)``. The downloader is only invoked
    for remote (URL) sources, so a project with only vendored archives (or no
    xcframeworks) never needs network access.
    """
    if not declared:
        return []
    out = [
        _resolve_one(
            dep, project_root=project_root, downloader=downloader, offline=offline
        )
        for dep in declared
    ]
    out.sort(key=lambda x: (x.name.lower(), x.version))
    return out


def _resolve_one(
    dep: XcframeworkDep,
    *,
    project_root: Path,
    downloader: Downloader | None,
    offline: bool,
) -> LockedXcframework:
    archive_format = _archive_format_for(dep.source, name=dep.name)
    is_url = dep.source.startswith(("http://", "https://"))

    with tempfile.TemporaryDirectory(prefix="kivy-xc-lock-") as tmp:
        if is_url:
            url: str | None = dep.source
            path_rel: str | None = None
            archive = _download(dep, Path(tmp), downloader=downloader, offline=offline)
        else:
            url = None
            archive, path_rel = _resolve_local(dep, project_root=project_root)

        sha256 = sha256_file(archive)
        slices = _enumerate_slices(dep, archive, archive_format=archive_format)

    return LockedXcframework(
        name=dep.name,
        version=dep.version,
        sha256=sha256,
        slices=slices,
        url=url,
        path=path_rel,
        archive_format=archive_format,
        link=dep.link,
        embed=dep.embed,
        source=dep.source,
    )


def _archive_format_for(source: str, *, name: str) -> str:
    low = source.lower()
    if low.endswith(".zip"):
        return "zip"
    if low.endswith((".tar.gz", ".tgz")):
        return "tar.gz"
    raise XcframeworkResolverError(
        f"xcframework {name!r}: unsupported source {source!r}; source must be a "
        f".zip or .tar.gz archive of the .xcframework.\n"
        f"  Zip the built framework (e.g. `ditto -c -k --keepParent "
        f"My.xcframework My.xcframework.zip`) and point `source` at the archive."
    )


def _download(
    dep: XcframeworkDep,
    tmpdir: Path,
    *,
    downloader: Downloader | None,
    offline: bool,
) -> Path:
    # Imported lazily: artifacts.download imports lock.find_links, so a top-level
    # import here would close an import cycle (lock <-> artifacts).
    from ..artifacts.download import DownloadError, UrllibDownloader

    if offline:
        raise XcframeworkResolverError(
            f"xcframework {dep.name!r}: cannot download {dep.source} while offline.\n"
            f"  Re-run `toolchain lock` with network access, or vendor the archive "
            f"and point `source` at a repo-relative path."
        )
    dl = downloader or UrllibDownloader()
    filename = dep.source.rsplit("/", 1)[-1] or f"{dep.name}.zip"
    dest = tmpdir / filename
    try:
        dl.fetch_to(dep.source, dest)
    except DownloadError as exc:
        raise XcframeworkResolverError(f"xcframework {dep.name!r}: {exc}") from exc
    return dest


def _resolve_local(dep: XcframeworkDep, *, project_root: Path) -> tuple[Path, str]:
    root = project_root.resolve()
    resolved = (root / dep.source).resolve()
    try:
        rel = wheel_path_from_project_root(root, resolved)
    except FindLinksError as exc:
        raise XcframeworkResolverError(
            f"xcframework {dep.name!r}: source {dep.source!r} resolves to "
            f"{resolved}, which is outside the project directory and its parent.\n"
            f"  Vendored xcframework archives must live under the project "
            f"directory or a shared sibling directory (e.g. examples/frameworks/)."
        ) from exc
    if not resolved.is_file():
        extra = ""
        if resolved.is_dir():
            extra = (
                "\n  An unpacked .xcframework directory is not a supported source; "
                "zip it (`ditto -c -k --keepParent ...`) and reference the archive."
            )
        raise XcframeworkResolverError(
            f"xcframework {dep.name!r}: vendored archive not found at "
            f"{dep.source!r}.{extra}"
        )
    return resolved, rel


def _enumerate_slices(
    dep: XcframeworkDep, archive: Path, *, archive_format: str
) -> tuple[str, ...]:
    with tempfile.TemporaryDirectory(prefix="kivy-xc-slices-") as tmp:
        try:
            xc_dir = extract_xcframework_archive(
                archive,
                Path(tmp),
                name=dep.name,
                archive_format=archive_format,
            )
            slices = read_xcframework_slices(xc_dir)
        except (FrameworkConflict, FileNotFoundError, ValueError) as exc:
            raise XcframeworkResolverError(f"xcframework {dep.name!r}: {exc}") from exc
    if not slices:
        raise XcframeworkResolverError(
            f"xcframework {dep.name!r}: no slices found in the archive's "
            f"Info.plist (expected an AvailableLibraries list)."
        )
    return slices
