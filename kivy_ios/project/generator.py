"""Programmatic ``<app>.xcodeproj`` generation via ``pbxproj`` (spec 06).

Bootstraps from the internal skeleton on first run, then performs the spec's
idempotent "every build" sync: managed build settings (per-config), the Build
Python run script (ordered between Copy Bundle Resources and Frameworks),
``main.m`` in Sources, Python.xcframework + Frameworks/* embed & sign, the app/
folder reference, and signing/user settings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from pbxproj import XcodeProject
from pbxproj.pbxextensions.ProjectFiles import FileOptions, ProjectFiles, TreeType

from ..config.model import Config
from ..lock.model import LockedSwiftPackage, LockedXcframework
from .buildsettings import (
    BUILD_PYTHON_SCRIPT,
    managed_settings,
    signing_settings,
    user_build_settings,
)
from .skeleton import skeleton_pbxproj
from .staging import StagingError, StagingLayout
from .swift_packages import sync_swift_packages, write_package_resolved
from .xcframeworks import sync_native_frameworks

CONFIGURATIONS = ("Debug", "Release")

# Xcode shows "Update to recommended settings" when the project's
# LastUpgradeCheck is below the running Xcode's version. `toolchain build`
# detects the installed Xcode and passes its encoded version down (see
# kivy_ios/cli/build.py); this constant is only the fallback used when Xcode
# can't be queried. Keep it at/above the minimum supported Xcode.
RECOMMENDED_LAST_UPGRADE_CHECK = "2650"

# pbxproj does not ship .storyboard; register for LaunchScreen.storyboard sync.
ProjectFiles._FILE_TYPES.setdefault(
    ".storyboard", ("file.storyboard", "PBXResourcesBuildPhase")
)


class XcodeProjectGenerator:
    def __init__(
        self,
        config: Config,
        layout: StagingLayout,
        *,
        last_upgrade_check: str | None = None,
        swift_packages: tuple[LockedSwiftPackage, ...] = (),
        xcframeworks: tuple[LockedXcframework, ...] = (),
    ) -> None:
        self.config = config
        self.layout = layout
        self.app_name = config.app_slug
        self.last_upgrade_check = last_upgrade_check or RECOMMENDED_LAST_UPGRADE_CHECK
        self.swift_packages = swift_packages
        self.xcframeworks = xcframeworks

    @property
    def pbxproj_path(self) -> Path:
        return self.layout.xcodeproj / "project.pbxproj"

    def generate(self) -> Path:
        project = self._load_or_bootstrap()
        self._sync_project_attributes(project)
        self._apply_build_settings(project)
        self._sync_run_script(project)
        self._sync_sources(project)
        self._sync_bundle_folders(project)
        self._sync_pip_deps_browse_reference(project)
        self._sync_resources(project)
        self._sync_embedded_frameworks(project)
        self._sync_swift_packages(project)
        project.save()
        self._write_package_resolved()
        return self.pbxproj_path

    # -- swift packages (spec 07) ------------------------------------------ #
    def _sync_swift_packages(self, project: XcodeProject) -> None:
        sync_swift_packages(
            project,
            self.app_name,
            self.swift_packages,
            staging_root=self.layout.root,
        )

    def _write_package_resolved(self) -> None:
        resolved = (
            self.layout.xcodeproj
            / "project.xcworkspace"
            / "xcshareddata"
            / "swiftpm"
            / "Package.resolved"
        )
        write_package_resolved(resolved, self.swift_packages)

    # -- bootstrap ---------------------------------------------------------- #
    def _load_or_bootstrap(self) -> XcodeProject:
        if self.pbxproj_path.is_file():
            return XcodeProject.load(str(self.pbxproj_path))
        self.layout.xcodeproj.mkdir(parents=True, exist_ok=True)
        assert self.config.ios is not None
        self.pbxproj_path.write_text(
            skeleton_pbxproj(self.app_name, self.config.ios.bundle_id),
            encoding="utf-8",
        )
        return XcodeProject.load(str(self.pbxproj_path))

    # -- project attributes ------------------------------------------------- #
    def _sync_project_attributes(self, project: XcodeProject) -> None:
        """Keep LastUpgradeCheck current so Xcode doesn't prompt to "Update to
        recommended settings" (self-heals projects bootstrapped by older runs).
        """
        for proj in cast(Any, project).objects.get_objects_in_section("PBXProject"):
            attributes = proj["attributes"]
            attributes["LastUpgradeCheck"] = self.last_upgrade_check

    # -- build settings ----------------------------------------------------- #
    def _apply_build_settings(self, project: XcodeProject) -> None:
        signing = signing_settings(self.config)
        user = user_build_settings(self.config)
        for configuration in CONFIGURATIONS:
            project.set_flags(
                "ALWAYS_SEARCH_USER_PATHS",
                "NO",
                configuration_name=configuration,
            )
            settings = managed_settings(
                self.config, configuration=configuration, layout=self.layout
            )
            # user settings layered under managed (reserved keys already rejected)
            merged = {**user, **settings, **signing}
            for key, value in merged.items():
                project.set_flags(
                    key,
                    value,
                    target_name=self.app_name,
                    configuration_name=configuration,
                )

    # -- run script --------------------------------------------------------- #
    def _sync_run_script(self, project: XcodeProject) -> None:
        # Idempotent: drop any prior copy, re-add, then order it between Copy
        # Bundle Resources and the Frameworks (Link) phase.
        project.remove_run_script(BUILD_PYTHON_SCRIPT)
        project.add_run_script(BUILD_PYTHON_SCRIPT, target_name=self.app_name)
        self._configure_run_script(project)
        self._order_run_script(project)

    def _configure_run_script(self, project: XcodeProject) -> None:
        # Spec 06: run every build (install_python walks app/ + pip-deps/).
        target = project.get_target_by_name(self.app_name)
        if target is None:
            raise RuntimeError(f"target {self.app_name!r} not found in Xcode project")
        for phase_id in target.buildPhases:
            phase = project.get_object(phase_id)
            if (
                getattr(phase, "isa", None) == "PBXShellScriptBuildPhase"
                and getattr(phase, "shellScript", None) == BUILD_PYTHON_SCRIPT
            ):
                phase["alwaysOutOfDate"] = 1
                break

    def _order_run_script(self, project: XcodeProject) -> None:
        target = project.get_target_by_name(self.app_name)
        if target is None:
            raise RuntimeError(f"target {self.app_name!r} not found in Xcode project")
        phases = list(target.buildPhases)
        kinds = {pid: project.get_object(pid).isa for pid in phases}
        script = next(
            (p for p in phases if kinds[p] == "PBXShellScriptBuildPhase"), None
        )
        frameworks = next(
            (p for p in phases if kinds[p] == "PBXFrameworksBuildPhase"), None
        )
        if script is None or frameworks is None:
            return
        phases.remove(script)
        idx = phases.index(frameworks)
        phases.insert(idx, script)
        target.buildPhases = phases

    # -- sources ------------------------------------------------------------ #
    def _sync_sources(self, project: XcodeProject) -> None:
        sources_group = project.get_or_create_group("Sources")
        for source_file in ("main.m", "kivy_ios_bootstrap.m"):
            fpath = self.layout.root / source_file
            if fpath.is_file() and not project.get_files_by_name(source_file):
                project.add_file(
                    source_file,
                    parent=sources_group,
                    target_name=self.app_name,
                    tree="SOURCE_ROOT",
                    file_options=FileOptions(embed_framework=False),
                )

    # -- bundle resources --------------------------------------------------- #
    def _sync_bundle_folders(self, project: XcodeProject) -> None:
        """Add ``app/`` as a folder reference (spec 06).

        ``app/`` is mandatory — it is the symlink to the user's ``app_dir`` and
        carries the app's Python source into the bundle. If it does not resolve
        to an existing directory, fail loudly rather than silently shipping an
        app with no code.

        ``pip-deps/`` is intentionally *not* a Copy Bundle Resources folder
        reference. It is platform-sliced (``pip-deps-simulator`` /
        ``pip-deps-device``) and the Build Python run script rsyncs the correct
        slice into the bundle on every build; a folder reference here would
        stage one fixed slice — the wrong one for half of all builds — ahead of
        that rsync.
        """
        if not self.layout.app.exists():
            raise StagingError(
                f"app source directory is missing: {self.layout.app} does not "
                f"resolve to an existing directory (app_dir = "
                f"{self.config.kivy.app_dir!r}). Fix [tool.kivy].app_dir in "
                f"pyproject.toml."
            )
        if not project.get_files_by_name("app"):
            project.add_file(
                "app",
                target_name=self.app_name,
                tree="SOURCE_ROOT",
                file_options=FileOptions(embed_framework=False),
            )
            # pbxproj type detection uses CWD; force folder refs for bundle copy.
            for ref in project.get_files_by_name("app"):
                ref.set_last_known_file_type("folder")

    def _sync_pip_deps_browse_reference(self, project: XcodeProject) -> None:
        """Show the pip-deps packages in the navigator without building them.

        pip-deps is staged into the bundle by the Build Python run script, not
        Copy Bundle Resources, so it would otherwise be invisible in Xcode's
        project navigator. Add the simulator slice as a folder reference for
        browsing only: ``create_build_files=False`` keeps it out of every build
        phase, so it has no effect on the build (the package set is identical
        across slices). Its on-disk path is ``pip-deps-simulator``; only its
        display name is ``pip-deps``.
        """
        if not self.layout.pip_deps_simulator.is_dir():
            return
        if project.get_files_by_path("pip-deps-simulator", tree=TreeType.SOURCE_ROOT):
            return  # already present (idempotent)
        project.add_file(
            "pip-deps-simulator",
            tree=TreeType.SOURCE_ROOT,
            force=True,
            file_options=FileOptions(create_build_files=False, embed_framework=False),
        )
        for ref in project.get_files_by_path(
            "pip-deps-simulator", tree=TreeType.SOURCE_ROOT
        ):
            ref.set_last_known_file_type("folder")
            ref["name"] = "pip-deps"

    def _sync_resources(self, project: XcodeProject) -> None:
        opts = FileOptions(embed_framework=False)
        # PrivacyInfo.xcprivacy must ship in the bundle (Apple required-reason
        # APIs); pbxproj already maps .xcprivacy -> Copy Bundle Resources.
        privacy = self.layout.root / "PrivacyInfo.xcprivacy"
        if privacy.is_file() and not project.get_files_by_name("PrivacyInfo.xcprivacy"):
            project.add_file(
                "PrivacyInfo.xcprivacy",
                target_name=self.app_name,
                tree="SOURCE_ROOT",
                file_options=opts,
            )
        catalog = self.layout.resources / "Assets.xcassets"
        if catalog.is_dir() and not project.get_files_by_name("Assets.xcassets"):
            project.add_file(
                "Resources/Assets.xcassets",
                target_name=self.app_name,
                tree="SOURCE_ROOT",
                file_options=opts,
            )
        launch = self.layout.root / "LaunchScreen.storyboard"
        if launch.is_file() and not project.get_files_by_name(
            "LaunchScreen.storyboard"
        ):
            project.add_file(
                "LaunchScreen.storyboard",
                target_name=self.app_name,
                tree="SOURCE_ROOT",
                file_options=opts,
            )

    # -- frameworks (embed & sign) ----------------------------------------- #
    def _sync_embedded_frameworks(self, project: XcodeProject) -> None:
        embed = FileOptions(embed_framework=True, code_sign_on_copy=True)
        frameworks_group = project.get_or_create_group("Frameworks", "Frameworks")
        # Python.xcframework: Embed & Sign (Link + Embed) per python.org docs.
        if self.layout.python_xcframework.exists() and not project.get_files_by_name(
            "Python.xcframework"
        ):
            project.add_file(
                "Python.xcframework",
                target_name=self.app_name,
                tree="SOURCE_ROOT",
                file_options=embed,
            )
        # Frameworks/*.xcframework — link/embed per the locked native entries
        # (wheel-embedded SDL3/ANGLE default to Embed & Sign); stale refs for
        # frameworks no longer on disk are pruned.
        link_embed = {xc.name: (xc.link, xc.embed) for xc in self.xcframeworks}
        sync_native_frameworks(
            project,
            self.app_name,
            frameworks_dir=self.layout.frameworks,
            frameworks_group=frameworks_group,
            link_embed=link_embed,
        )
