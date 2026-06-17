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
    """Write the entitlements plist; returns None when there are none."""
    if not has_entitlements(config):
        return None
    path = Path(path)
    with open(path, "wb") as f:
        plistlib.dump(build_entitlements(config), f, sort_keys=True)
    return path
