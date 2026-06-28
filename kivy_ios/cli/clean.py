"""``toolchain clean`` — remove generated artifacts (spec 05)."""

from __future__ import annotations

import shutil
from pathlib import Path

import click

from ..artifacts.cache import ArtifactCache
from ..config import ConfigError, load_config
from ._common import PYPROJECT_NAME, ToolchainError


@click.command()
@click.option(
    "--cache",
    "flush_cache",
    is_flag=True,
    help="Also flush the artifact download cache.",
)
@click.option(
    "--project-only",
    is_flag=True,
    default=False,
    help="Only the generated <app>-ios/ folder (default).",
)
def clean(flush_cache: bool, project_only: bool) -> None:
    """Remove generated artifacts in the project folder."""
    cwd = Path.cwd()
    pyproject = cwd / PYPROJECT_NAME

    if pyproject.is_file():
        try:
            config = load_config(pyproject)
        except ConfigError as exc:
            raise ToolchainError(exc.format()) from exc
        staging = cwd / f"{config.app_slug}-ios"
        if staging.is_dir():
            shutil.rmtree(staging)
            click.echo(f"Removed {staging.name}/")
        else:
            click.echo(f"Nothing to clean ({staging.name}/ does not exist).")
    elif not flush_cache:
        raise ToolchainError(
            f"no {PYPROJECT_NAME} found in the current directory.\n"
            "  Run clean from your project directory, or pass --cache to flush "
            "only the global artifact cache."
        )

    if flush_cache:
        cache = ArtifactCache()
        cache.clear()
        click.echo("Flushed the artifact download cache.")
