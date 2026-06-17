"""``toolchain upgrade`` — re-download pinned artifacts per the lock (spec 05)."""

from __future__ import annotations

from pathlib import Path

import click

from ..artifacts.download import DownloadError, fetch_artifact
from ..artifacts.verify import HashMismatch
from ..lock import LockError, load
from ._common import LOCKFILE_NAME, ToolchainError, find_pyproject, lockfile_path


@click.command()
@click.option(
    "--python", "python_only", is_flag=True, help="Only refresh Python.xcframework."
)
@click.option(
    "--xcframeworks",
    "xcframeworks_only",
    is_flag=True,
    help="Only refresh xcframework artifacts.",
)
@click.option("--name", default=None, help="Only refresh a specific artifact by name.")
def upgrade(python_only: bool, xcframeworks_only: bool, name: str | None) -> None:
    """Re-fetch pinned Python.xcframework / xcframework artifacts."""
    pyproject = find_pyproject()
    project_root = pyproject.parent
    lock = _load_lock(project_root)

    # No selector flag => refresh everything.
    do_python = python_only or not (python_only or xcframeworks_only or name)
    do_xc = xcframeworks_only or not (python_only or xcframeworks_only or name)
    if name:
        do_python = name == "Python.xcframework"
        do_xc = True

    refreshed = 0
    skipped_vendored = 0
    try:
        if do_python and (not name or name == "Python.xcframework"):
            px = lock.python_xcframework
            click.echo(f"Refreshing Python.xcframework {px.version} ...")
            fetch_artifact(
                name="Python.xcframework",
                sha256=px.sha256,
                filename=px.url.rsplit("/", 1)[-1],
                url=px.url,
                no_cache=True,
            )
            refreshed += 1

        if do_xc:
            for xc in lock.xcframeworks:
                if name and xc.name != name:
                    continue
                if xc.path:
                    skipped_vendored += 1
                    continue
                url = xc.url
                if url is None:
                    continue
                click.echo(f"Refreshing {xc.name} {xc.version} ...")
                fetch_artifact(
                    name=xc.name,
                    sha256=xc.sha256,
                    filename=url.rsplit("/", 1)[-1],
                    url=url,
                    project_root=project_root,
                    no_cache=True,
                )
                refreshed += 1
    except HashMismatch as exc:
        raise ToolchainError(str(exc)) from exc
    except DownloadError as exc:
        raise ToolchainError(str(exc)) from exc

    if name and refreshed == 0 and skipped_vendored == 0:
        raise ToolchainError(f"no artifact named {name!r} found in {LOCKFILE_NAME}.")
    msg = f"Refreshed {refreshed} artifact(s)."
    if skipped_vendored:
        msg += f" Skipped {skipped_vendored} vendored (path-based) entry/entries."
    click.echo(msg)


def _load_lock(project_root: Path):
    path = lockfile_path(project_root)
    if not path.is_file():
        raise ToolchainError(f"no {LOCKFILE_NAME} found. Run `toolchain lock` first.")
    try:
        return load(path)
    except LockError as exc:
        raise ToolchainError(str(exc)) from exc
