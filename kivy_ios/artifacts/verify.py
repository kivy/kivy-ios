"""SHA-256 verification for downloaded/vendored artifacts (spec 03)."""

from __future__ import annotations

import hashlib
from pathlib import Path

_CHUNK = 1 << 20  # 1 MiB


class HashMismatch(Exception):
    """Raised when an artifact's SHA-256 does not match the lockfile pin."""

    def __init__(self, *, name: str, source: str, expected: str, actual: str) -> None:
        self.name = name
        self.source = source
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"SHA-256 mismatch for {name}\n"
            f"  source:   {source}\n"
            f"  expected: {expected}\n"
            f"  actual:   {actual}\n"
            f"  The artifact may have been tampered with, or the source registry "
            f"replaced it. Re-run `toolchain lock`, and report the source if this "
            f"persists."
        )


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_file(path: str | Path, expected: str, *, name: str, source: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise HashMismatch(name=name, source=source, expected=expected, actual=actual)
