"""Generate ``<app>.entitlements`` from ``[tool.kivy.ios.entitlements]`` (spec 06)."""

from __future__ import annotations

import plistlib
from pathlib import Path

from ..config.model import Config


def has_entitlements(config: Config) -> bool:
    return bool(config.ios and config.ios.entitlements)


def build_entitlements(config: Config) -> dict:
    if not config.ios:
        return {}
    return dict(config.ios.entitlements)


def write_entitlements(config: Config, path: str | Path) -> Path | None:
    """Write the entitlements plist; returns None when there are none.

    When no entitlements are configured, any previously generated file is
    removed so a stale ``<app>.entitlements`` (from a since-deleted config
    table) is not left referenced in the bundle.
    """
    path = Path(path)
    if not has_entitlements(config):
        path.unlink(missing_ok=True)
        return None
    with open(path, "wb") as f:
        plistlib.dump(build_entitlements(config), f, sort_keys=True)
    return path
