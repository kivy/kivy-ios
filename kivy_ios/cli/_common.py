"""Shared helpers for the ``toolchain`` CLI.

All verbs look for ``pyproject.toml`` in the **current working directory
only** — no parent-directory traversal (per spec 05).
"""

from __future__ import annotations

from pathlib import Path

import click

PYPROJECT_NAME = "pyproject.toml"
LOCKFILE_NAME = "pylock.ios.toml"
MIGRATION_URL = "https://kivy.org/docs/migration-2.x-to-3.0.html"


class ToolchainError(click.ClickException):
    """A user-facing error that prints cleanly and exits non-zero.

    Unlike a bare exception, ``click`` renders this as ``Error: <message>``
    without a traceback, which is what we want for expected failure modes
    (missing pyproject, validation errors, drift, etc.).
    """

    exit_code = 1


def find_pyproject(start: Path | None = None) -> Path:
    """Return the path to ``pyproject.toml`` in the current directory.

    Raises ``ToolchainError`` if it is not present. No parent traversal is
    performed — the tool is intentionally CWD-scoped so it never picks up an
    unrelated ``pyproject.toml`` from an ancestor directory.
    """
    base = Path.cwd() if start is None else start
    candidate = base / PYPROJECT_NAME
    if not candidate.is_file():
        raise ToolchainError(
            f"no {PYPROJECT_NAME} found in the current directory ({base}).\n"
            f"  Run toolchain commands from the directory that contains your "
            f"{PYPROJECT_NAME}, or run `toolchain init` to create one."
        )
    return candidate


def lockfile_path(start: Path | None = None) -> Path:
    """Return the path where ``pylock.ios.toml`` lives (sibling to pyproject)."""
    base = Path.cwd() if start is None else start
    return base / LOCKFILE_NAME
