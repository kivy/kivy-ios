"""Content-addressed artifact cache (spec 03).

Artifacts (wheels, xcframework archives, Python.xcframework) are cached by
SHA-256 under ``~/Library/Caches/kivy-ios/artifacts/`` so repeated builds and
``--no-cache`` opt-outs are cheap and deterministic. The cache key is the
content hash, so a tampered/replaced upstream artifact can never silently
satisfy a cache hit for a different hash.
"""

from __future__ import annotations

import shutil
from pathlib import Path

APP_NAME = "kivy-ios"
DEFAULT_CACHE_ROOT = Path.home() / "Library" / "Caches" / APP_NAME / "artifacts"


class ArtifactCache:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = DEFAULT_CACHE_ROOT if root is None else Path(root)

    def path_for(self, sha256: str, filename: str) -> Path:
        # Shard by the first two hex chars to keep directories small.
        return self.root / sha256[:2] / f"{sha256}-{filename}"

    def get(self, sha256: str, filename: str) -> Path | None:
        candidate = self.path_for(sha256, filename)
        return candidate if candidate.is_file() else None

    def find_by_filename(self, filename: str) -> Path | None:
        """Return a cached artifact path matching ``{sha256}-{filename}``, if any."""
        if not self.root.is_dir():
            return None
        suffix = f"-{filename}"
        for shard in self.root.iterdir():
            if not shard.is_dir():
                continue
            for path in shard.iterdir():
                if path.is_file() and path.name.endswith(suffix):
                    return path
        return None

    def put_file(self, src: str | Path, sha256: str, filename: str) -> Path:
        dest = self.path_for(sha256, filename)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.is_file():
            shutil.copyfile(src, dest)
        return dest

    def put_bytes(self, data: bytes, sha256: str, filename: str) -> Path:
        dest = self.path_for(sha256, filename)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest

    def clear(self) -> None:
        if self.root.is_dir():
            shutil.rmtree(self.root)
