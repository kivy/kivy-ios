"""``toolchain open`` — open the generated Xcode project (spec 05)."""

from __future__ import annotations

from pathlib import Path

import click

from ..config import ConfigError, load_config
from ..xcode import CommandError, open_command, run_command
from ._common import ToolchainError, find_pyproject


@click.command(name="open")
def open_() -> None:
    """Open <app>-ios/<app>.xcodeproj in Xcode."""
    pyproject = find_pyproject()
    try:
        config = load_config(pyproject)
    except ConfigError as exc:
        raise ToolchainError(exc.format()) from exc

    slug = config.app_slug
    xcodeproj = Path.cwd() / f"{slug}-ios" / f"{slug}.xcodeproj"
    if not xcodeproj.exists():
        raise ToolchainError(
            f"{xcodeproj.name} does not exist yet.\n"
            "  Run `toolchain build` first to generate the Xcode project."
        )
    try:
        run_command(open_command(xcodeproj))
    except CommandError as exc:
        raise ToolchainError(str(exc)) from exc
