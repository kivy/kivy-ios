"""``toolchain doctor`` — environment + project health check (spec 05)."""

from __future__ import annotations

from pathlib import Path

import click

from .. import __version__
from ..config import ConfigError, load_config
from ..doctor import RealProbe, Status, run_checks, worst_status
from ..lock import LockError, load
from ._common import LOCKFILE_NAME, PYPROJECT_NAME


@click.command()
@click.option("--offline", is_flag=True, help="Skip network-dependent checks.")
def doctor(offline: bool) -> None:
    """Run environment and project health checks."""
    cwd = Path.cwd()
    pyproject = cwd / PYPROJECT_NAME
    config = None
    lock = None
    if pyproject.is_file():
        try:
            config = load_config(pyproject)
        except ConfigError as exc:
            click.echo(f"[FAIL] pyproject.toml: {exc.format()}")
        lockfile = cwd / LOCKFILE_NAME
        if lockfile.is_file():
            try:
                lock = load(lockfile)
            except LockError:
                lock = None

    mode = "project" if config is not None else "environment"
    click.echo(f"toolchain doctor ({mode} mode)\n")

    results = run_checks(
        RealProbe(),
        toolchain_version=__version__,
        config=config,
        project_root=cwd,
        lock=lock,
        offline=offline,
    )
    for result in results:
        click.echo(result.render())

    if worst_status(results) is Status.FAIL:
        raise SystemExit(1)
