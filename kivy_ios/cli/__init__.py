"""``toolchain`` — the kivy-ios 3.0 command-line interface.

A slim click-based dispatcher. Each verb lives in its own module under
``kivy_ios.cli`` and is registered onto the top-level group here. Legacy
2.x verbs are registered as hidden commands that print a migration pointer
(see ``_legacy``).
"""

from __future__ import annotations

import click

from .. import __version__
from . import build, clean, doctor, init, lock, open_cmd, run, status, upgrade
from ._legacy import LEGACY_VERBS, make_legacy_command


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    help=(
        "kivy-ios 3.0 — a declarative iOS bundler for Kivy apps.\n\n"
        "Run commands from the directory that contains your pyproject.toml."
    ),
)
@click.version_option(__version__, "-V", "--version", prog_name="toolchain")
def main() -> None:
    pass


# Real 3.0 verbs.
main.add_command(init.init)
main.add_command(lock.lock)
main.add_command(build.build)
main.add_command(run.run)
main.add_command(open_cmd.open_)
main.add_command(upgrade.upgrade)
main.add_command(clean.clean)
main.add_command(status.status)
main.add_command(doctor.doctor)

# Legacy verbs: hidden, emit a migration pointer.
for _verb in LEGACY_VERBS:
    main.add_command(make_legacy_command(_verb))


if __name__ == "__main__":
    main()
