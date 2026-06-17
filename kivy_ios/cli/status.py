"""``toolchain status`` — read-only project state snapshot (spec 05)."""

from __future__ import annotations

import time
from pathlib import Path

import click

from ..config import ConfigError, load_config
from ..lock import LockError, is_in_sync, load
from ..xcode.commands import product_app_path
from ._common import LOCKFILE_NAME, ToolchainError, find_pyproject


@click.command()
def status() -> None:
    """Show app identity, Python version, lock sync, and build state."""
    pyproject = find_pyproject()
    project_root = pyproject.parent
    try:
        config = load_config(pyproject)
    except ConfigError as exc:
        raise ToolchainError(exc.format()) from exc

    ios = config.ios_required
    click.echo(f"App:        {config.display_name}  ({ios.bundle_id})")
    click.echo(f"Python:     {ios.python_version or '(unset)'}")
    click.echo(f"Lock:       {_lock_state(project_root, pyproject)}")

    click.echo("Build:")
    build_dir = project_root / f"{config.app_slug}-ios" / "build" / "DerivedData"
    for label, target in (("simulator (arm64)", "simulator"), ("device", "device")):
        app = product_app_path(build_dir, config.app_slug, target)
        click.echo(f"  {label:<20}{_build_state(app)}")


def _lock_state(project_root: Path, pyproject: Path) -> str:
    lockfile = project_root / LOCKFILE_NAME
    if not lockfile.is_file():
        return "missing (run `toolchain lock`)"
    try:
        lock = load(lockfile)
    except LockError:
        return "unreadable (run `toolchain lock`)"
    if is_in_sync(lock, pyproject.read_text("utf-8")):
        return "in sync"
    return "out of date (run `toolchain lock`)"


def _build_state(app: Path) -> str:
    if not app.exists():
        return "not built"
    age = time.time() - app.stat().st_mtime
    return f"last built {_humanize(age)}"


def _humanize(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        m = seconds // 60
        return f"{m} minute{'s' if m != 1 else ''} ago"
    if seconds < 86400:
        h = seconds // 3600
        return f"{h} hour{'s' if h != 1 else ''} ago"
    d = seconds // 86400
    return f"{d} day{'s' if d != 1 else ''} ago"
