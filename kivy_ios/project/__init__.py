"""kivy-ios Xcode project generation (spec 06)."""

from __future__ import annotations

from .assets import generate_asset_catalog
from .buildsettings import (
    BUILD_PYTHON_SCRIPT,
    managed_settings,
    signing_settings,
    user_build_settings,
)
from .entitlements import write_entitlements
from .generator import XcodeProjectGenerator
from .plist import build_info_plist, write_info_plist
from .privacy import write_privacy_manifest
from .sources import render_main_config_h, write_sources
from .staging import StagingLayout, create_staging, staging_dir_name

__all__ = [
    "generate_asset_catalog",
    "BUILD_PYTHON_SCRIPT",
    "managed_settings",
    "signing_settings",
    "user_build_settings",
    "write_entitlements",
    "XcodeProjectGenerator",
    "build_info_plist",
    "write_info_plist",
    "write_privacy_manifest",
    "render_main_config_h",
    "write_sources",
    "StagingLayout",
    "create_staging",
    "staging_dir_name",
]
