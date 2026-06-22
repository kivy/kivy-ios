"""Materialize the Xcode project from config (build step 6, spec 06).

Given a project root with a validated config, generate the full ``<app>-ios/``
project: staging tree + ``app/`` symlink, ``main.m`` / ``main_config.h``,
``<app>-Info.plist``, ``<app>.entitlements`` (if any), ``PrivacyInfo.xcprivacy``,
``Resources/Assets.xcassets`` (if icons/splash image), ``LaunchScreen.storyboard``
(if splash), and the ``.xcodeproj``.

This is the hermetic, no-network portion of ``toolchain build`` — artifact
collection (steps 2-5) populates ``Python.xcframework/``, ``Frameworks/``, and
``pip-deps/`` separately before/around this step.
"""

from __future__ import annotations

from pathlib import Path

from ..config.model import Config
from ..lock.model import LockedSwiftPackage
from .assets import generate_asset_catalog, write_launch_screen
from .entitlements import write_entitlements
from .generator import XcodeProjectGenerator
from .plist import write_info_plist
from .privacy import write_privacy_manifest
from .sources import write_sources
from .staging import StagingLayout, create_staging


def materialize_project(
    config: Config,
    project_root: str | Path,
    *,
    layout: StagingLayout | None = None,
    python_version: str | None = None,
    last_upgrade_check: str | None = None,
    swift_packages: tuple[LockedSwiftPackage, ...] = (),
) -> StagingLayout:
    project_root = Path(project_root)
    layout = layout or create_staging(config, project_root)

    write_sources(config, layout.root, python_version=python_version)
    write_info_plist(config, layout.root / f"{config.app_slug}-Info.plist")
    write_entitlements(config, layout.root / f"{config.app_slug}.entitlements")
    write_privacy_manifest(
        config, layout.root / "PrivacyInfo.xcprivacy", project_root=project_root
    )
    generate_asset_catalog(config, layout.resources, project_root=project_root)
    write_launch_screen(config, layout.root, project_root=project_root)

    XcodeProjectGenerator(
        config,
        layout,
        last_upgrade_check=last_upgrade_check,
        swift_packages=swift_packages,
    ).generate()
    return layout
