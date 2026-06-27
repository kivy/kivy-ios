"""Validate ``[tool.kivy.ios.icons].source`` (spec 01).

Apple's single-size ``AppIcon`` catalog entry must be exactly 1024x1024 PNG.
kivy-ios does not resize - the source file must already match.
"""

from __future__ import annotations

import struct
from pathlib import Path

APP_ICON_SIZE = 1024
_PNG_SIG = b"\x89PNG\r\n\x1a\n"


class IconSourceError(Exception):
    """``[tool.kivy.ios.icons].source`` failed validation."""


def png_dimensions(path: Path) -> tuple[int, int]:
    """Read width and height from a PNG IHDR chunk."""
    with path.open("rb") as fh:
        header = fh.read(24)
    if len(header) < 24 or header[:8] != _PNG_SIG:
        raise IconSourceError(f"{path}: not a PNG file (expected 1024x1024 PNG)")
    return struct.unpack(">II", header[16:24])


def validate_icon_source(path: Path) -> None:
    """Fail fast when the icon path is missing, not PNG, or not 1024x1024."""
    if not path.is_file():
        raise IconSourceError(
            f"app icon not found: {path}\n"
            "  [tool.kivy.ios.icons].source must point to an existing "
            f"{APP_ICON_SIZE}x{APP_ICON_SIZE} PNG."
        )
    try:
        width, height = png_dimensions(path)
    except IconSourceError:
        raise
    except OSError as exc:
        raise IconSourceError(f"cannot read app icon {path}: {exc}") from exc
    if (width, height) != (APP_ICON_SIZE, APP_ICON_SIZE):
        raise IconSourceError(
            f"app icon {path} is {width}x{height}; "
            f"expected {APP_ICON_SIZE}x{APP_ICON_SIZE} PNG.\n"
            f"  Resize the source image to {APP_ICON_SIZE}x{APP_ICON_SIZE} "
            "before building."
        )


def icon_source_problem(path: Path) -> str | None:
    """Return an error message, or None when the icon source is valid."""
    try:
        validate_icon_source(path)
    except IconSourceError as exc:
        return str(exc)
    return None
