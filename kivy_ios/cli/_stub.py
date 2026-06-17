"""Helper for verbs not yet implemented in the current build phase.

Lets the full CLI surface exist (so ``--help`` lists every verb and dispatch
works) while individual verbs are filled in phase by phase.
"""

from __future__ import annotations

from ._common import ToolchainError


def not_implemented(verb: str) -> None:
    raise ToolchainError(f"`toolchain {verb}` is not implemented yet.")
