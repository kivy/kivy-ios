"""Generate the app-level ``PrivacyInfo.xcprivacy`` (spec 06).

Either copies the user's ``[tool.kivy.ios.privacy_manifest].source`` or writes a
minimal valid stub. This is the *app-level* manifest only; per-xcframework
privacy manifests are the framework author's responsibility (spec 06).
"""

from __future__ import annotations

import plistlib
import shutil
from pathlib import Path

from ..config.model import Config

# Minimal valid privacy manifest: declares no tracking and no collected data.
STUB_MANIFEST: dict = {
    "NSPrivacyTracking": False,
    "NSPrivacyTrackingDomains": [],
    "NSPrivacyCollectedDataTypes": [],
    "NSPrivacyAccessedAPITypes": [],
}


def write_privacy_manifest(
    config: Config, dest: str | Path, *, project_root: Path | None = None
) -> Path:
    dest = Path(dest)
    source = config.ios.privacy_manifest_source if config.ios else None
    if source:
        root = project_root or Path.cwd()
        src_path = (root / source).resolve()
        if not src_path.is_file():
            raise FileNotFoundError(f"privacy_manifest source not found: {source}")
        shutil.copyfile(src_path, dest)
        return dest
    with open(dest, "wb") as f:
        plistlib.dump(STUB_MANIFEST, f, sort_keys=True)
    return dest
