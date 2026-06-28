"""Migration pointers for kivy-ios 2.x verbs that no longer exist in 3.0.

Spec 05 "Disposition of legacy verbs": a removed verb that the user calls
explicitly emits a one-line deprecation pointer instead of an opaque
"no such command" error.
"""

from __future__ import annotations

import click

from ._common import MIGRATION_URL

# verb -> remediation line (the message body after the "is not a verb" header).
LEGACY_VERBS: dict[str, str] = {
    "recipes": "No recipes in 3.0. `toolchain doctor` shows what's pinned in the lock.",
    "create": "Replaced by `init`. Migration: cd <project> && toolchain init",
    "update": "Replaced by `upgrade`. Run `toolchain upgrade`.",
    "pip": "Removed. Edit [project].dependencies in pyproject.toml and run `toolchain lock`.",
    "pip3": "Removed. Edit [project].dependencies in pyproject.toml and run `toolchain lock`.",
    "distclean": "Removed. `toolchain clean --cache` covers it.",
    "launchimage": "Removed. Configure [tool.kivy.ios.splash] in pyproject.toml.",
    "icon": "Removed. Configure [tool.kivy.ios.icons] in pyproject.toml.",
}


def legacy_verb_message(verb: str) -> str:
    """Build the full multi-line migration message for a removed verb."""
    remediation = LEGACY_VERBS[verb]
    return (
        f"'{verb}' is not a verb in kivy-ios 3.0.\n"
        f"  {remediation}\n"
        f"  See: {MIGRATION_URL}"
    )


def make_legacy_command(verb: str) -> click.Command:
    """Create a hidden click command that prints the migration pointer."""

    @click.command(
        name=verb,
        hidden=True,
        context_settings={"ignore_unknown_options": True},
        add_help_option=False,
    )
    @click.argument("args", nargs=-1, type=click.UNPROCESSED)
    def _cmd(args: tuple[str, ...]) -> None:
        raise click.ClickException(legacy_verb_message(verb))

    return _cmd
