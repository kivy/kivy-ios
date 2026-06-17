"""App icon source validation (spec 01)."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

import pytest

from kivy_ios.project.icon import (
    APP_ICON_SIZE,
    IconSourceError,
    icon_source_problem,
    validate_icon_source,
)


def _write_minimal_png(path: Path, width: int, height: int) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    row = b"\x00" + b"\xff" * (width * 3)
    idat = chunk(b"IDAT", zlib.compress(row * height))
    iend = chunk(b"IEND", b"")
    path.write_bytes(sig + ihdr + idat + iend)


class TestValidateIconSource:
    def test_accepts_1024_png(self, tmp_path):
        icon = tmp_path / "icon.png"
        _write_minimal_png(icon, APP_ICON_SIZE, APP_ICON_SIZE)
        validate_icon_source(icon)
        assert icon_source_problem(icon) is None

    def test_rejects_missing_file(self, tmp_path):
        with pytest.raises(IconSourceError, match="not found"):
            validate_icon_source(tmp_path / "missing.png")

    def test_rejects_wrong_dimensions(self, tmp_path):
        icon = tmp_path / "icon.png"
        _write_minimal_png(icon, 512, 512)
        with pytest.raises(IconSourceError, match="512×512"):
            validate_icon_source(icon)

    def test_rejects_non_png(self, tmp_path):
        bad = tmp_path / "icon.png"
        bad.write_bytes(b"not a png")
        with pytest.raises(IconSourceError, match="not a PNG"):
            validate_icon_source(bad)
