"""``toolchain lock`` — resolve dependencies into pylock.ios.toml (spec 02)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import click

from ..config import ConfigError, load_config
from ..lock import (
    BuildError,
    build_lockfile,
    diff_summary,
    dumps,
    load,
    semantic_equal,
)
from ..lock.reader import LockError, is_in_sync
from ._common import ToolchainError, find_pyproject, lockfile_path


@click.command()
@click.option("--update", is_flag=True, help="Re-resolve even if the lock is in sync.")
@click.option("--offline", is_flag=True, help="Use cached resolution results only.")
@click.option(
    "--check",
    is_flag=True,
    help="CI pre-flight: exit non-zero if the lock is stale; write nothing.",
)
def lock(update: bool, offline: bool, check: bool) -> None:
    """Generate pylock.ios.toml from pyproject.toml."""
    pyproject = find_pyproject()
    pyproject_text = pyproject.read_text(encoding="utf-8")
    out_path = lockfile_path()

    try:
        config = load_config(pyproject)
    except ConfigError as exc:
        raise ToolchainError(exc.format()) from exc

    if check:
        _run_check(
            config,
            pyproject_text,
            out_path,
            project_root=pyproject.parent,
            offline=offline,
        )
        return

    if out_path.is_file() and not update:
        try:
            existing = load(out_path)
        except LockError:
            existing = None
        if existing is not None and is_in_sync(existing, pyproject_text):
            click.echo("pylock.ios.toml is already in sync with pyproject.toml.")
            click.echo("  (use --update to force re-resolution)")
            return

    new_lock = _build(
        config, pyproject_text, project_root=pyproject.parent, offline=offline
    )
    _atomic_write(out_path, dumps(new_lock))
    click.echo(f"Wrote {out_path.name} ({len(new_lock.packages)} packages pinned).")


def _run_check(
    config, pyproject_text, out_path: Path, *, project_root: Path, offline: bool
) -> None:
    if not out_path.is_file():
        raise ToolchainError(
            f"{out_path.name} does not exist. Run `toolchain lock` first."
        )
    try:
        existing = load(out_path)
    except LockError as exc:
        raise ToolchainError(str(exc)) from exc

    candidate = _build(
        config, pyproject_text, project_root=project_root, offline=offline
    )
    if semantic_equal(existing, candidate):
        click.echo(f"{out_path.name} is up to date.")
        return
    click.echo(f"{out_path.name} is out of date:", err=True)
    for line in diff_summary(existing, candidate):
        click.echo(line, err=True)
    raise ToolchainError("lock is stale; run `toolchain lock`.")


def _build(config, pyproject_text, *, project_root: Path, offline: bool):
    try:
        return build_lockfile(
            config,
            pyproject_text,
            project_root=project_root,
            offline=offline,
        )
    except BuildError as exc:
        raise ToolchainError(str(exc)) from exc


def _atomic_write(path: Path, text: str) -> None:
    """Write to a tempfile, fsync, then rename (spec 02 step 5)."""
    directory = path.parent
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".pylock.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
