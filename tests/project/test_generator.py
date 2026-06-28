"""Phase 5 — pbxproj generation + materialization, structural + idempotent."""

from __future__ import annotations

import pytest
from pbxproj import XcodeProject

from kivy_ios.project.generator import XcodeProjectGenerator
from kivy_ios.project.materialize import materialize_project
from kivy_ios.project.staging import StagingError, create_staging


def _objects(project):
    """pbxproj's dynamic object store is untyped; reach it via an Any-typed param."""
    return project.objects


def _settings_for(project, target_name, configuration):
    target = project.get_target_by_name(target_name)
    clist = project.get_object(target.buildConfigurationList)
    for cid in clist.buildConfigurations:
        cfg = project.get_object(cid)
        if cfg.name == configuration:
            return {k: cfg.buildSettings[k] for k in cfg.buildSettings.get_keys()}
    return {}


class TestStaging:
    def test_creates_layout_and_symlink(self, config, project_root):
        layout = create_staging(config, project_root)
        assert layout.root.name == "touchtracer-ios"
        assert layout.frameworks.is_dir()
        assert layout.pip_deps_simulator.is_dir()
        assert layout.pip_deps_device.is_dir()
        assert layout.resources.is_dir()
        assert layout.app.is_symlink()
        # symlink points at ../src
        import os

        assert os.readlink(layout.app) == "../src"

    def test_symlink_idempotent(self, config, project_root):
        create_staging(config, project_root)
        layout = create_staging(config, project_root)  # second call
        assert layout.app.is_symlink()

    def test_missing_app_dir_hard_fails(self, config, project_root):
        # app_dir is "src"; remove it so staging has nothing to symlink.
        import shutil

        shutil.rmtree(project_root / "src")
        with pytest.raises(StagingError, match="app_dir"):
            create_staging(config, project_root)

    def test_generator_hard_fails_on_dangling_app(self, config, project_root):
        # A successful materialize, then the source disappears: regeneration must
        # fail loudly rather than ship a bundle with no Python source.
        import shutil

        layout = materialize_project(config, project_root)
        shutil.rmtree(project_root / "src")  # app symlink now dangles
        with pytest.raises(StagingError, match="app source directory is missing"):
            XcodeProjectGenerator(config, layout).generate()


class TestPbxprojGeneration:
    def test_generates_parseable_project(self, config, project_root):
        layout = materialize_project(config, project_root)
        pbx = layout.xcodeproj / "project.pbxproj"
        assert pbx.is_file()
        project = XcodeProject.load(str(pbx))
        assert project.get_target_by_name("touchtracer") is not None

    def test_build_python_run_script_present(self, config, project_root):
        layout = materialize_project(config, project_root)
        text = (layout.xcodeproj / "project.pbxproj").read_text()
        assert "install_python Python.xcframework app pip-deps" in text
        assert "build_utils.sh" in text
        # Platform-aware rsync selects the correct slice at Xcode build time.
        assert "pip-deps-simulator" in text
        assert "pip-deps-device" in text
        assert "rsync" in text

    def test_run_script_guards_uncollected_slice(self, config, project_root):
        # The run script must refuse to build a target whose pip-deps slice was
        # never collected, rather than silently shipping an app with no deps.
        # The signal is the `.collected` marker, not directory emptiness, so a
        # dependency-free app (empty slice + marker) still builds.
        layout = materialize_project(config, project_root)
        text = (layout.xcodeproj / "project.pbxproj").read_text()
        assert ".collected" in text
        assert "was never collected for this" in text
        assert "COLLECT_HINT" in text
        assert "exit 1" in text

    def test_build_python_run_script_is_valid_shell(self):
        # Guards against quoting regressions in the embedded run script.
        import subprocess

        from kivy_ios.project.buildsettings import BUILD_PYTHON_SCRIPT

        result = subprocess.run(
            ["bash", "-n"], input=BUILD_PYTHON_SCRIPT, text=True, capture_output=True
        )
        assert result.returncode == 0, result.stderr

    def test_app_in_resources_pip_deps_excluded(self, config, project_root):
        # app/ is a Copy Bundle Resources folder reference. pip-deps/ is NOT: it
        # is platform-sliced and staged by the Build Python run script's rsync,
        # so a folder reference would copy a fixed (wrong-for-device) slice.
        layout = materialize_project(config, project_root)
        text = (layout.xcodeproj / "project.pbxproj").read_text()
        assert "app in Resources" in text
        assert "lastKnownFileType = folder" in text
        assert "pip-deps in Resources" not in text

    def test_pip_deps_browse_reference(self, config, project_root):
        # pip-deps ships via the run script, not Copy Bundle Resources, so it
        # gets a browse-only navigator reference to the simulator slice: visible
        # in Xcode, but referenced by no build file (zero build impact).
        from pbxproj.pbxextensions.ProjectFiles import TreeType

        layout = materialize_project(config, project_root)
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        refs = project.get_files_by_path(
            "pip-deps-simulator", tree=TreeType.SOURCE_ROOT
        )
        assert len(refs) == 1
        assert refs[0]["name"] == "pip-deps"
        ref_id = refs[0].get_id()
        build_files = [
            bf
            for bf in _objects(project).get_objects_in_section("PBXBuildFile")
            if getattr(bf, "fileRef", None) == ref_id
        ]
        assert build_files == []  # browse-only: in no build phase

    def test_run_script_always_out_of_date(self, config, project_root):
        layout = materialize_project(config, project_root)
        text = (layout.xcodeproj / "project.pbxproj").read_text()
        assert "alwaysOutOfDate = 1" in text

    def test_always_search_user_paths_no(self, config, project_root):
        layout = materialize_project(config, project_root)
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        debug = _settings_for(project, "touchtracer", "Debug")
        assert debug["ALWAYS_SEARCH_USER_PATHS"] == "NO"

    def test_run_script_ordered_before_frameworks(self, config, project_root):
        layout = materialize_project(config, project_root)
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        target = project.get_target_by_name("touchtracer")
        assert target is not None
        isas = [project.get_object(p).isa for p in target.buildPhases]
        assert "PBXShellScriptBuildPhase" in isas
        assert isas.index("PBXShellScriptBuildPhase") < isas.index(
            "PBXFrameworksBuildPhase"
        )

    def test_managed_settings_per_config(self, config, project_root):
        layout = materialize_project(config, project_root)
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        debug = _settings_for(project, "touchtracer", "Debug")
        release = _settings_for(project, "touchtracer", "Release")
        assert debug["ENABLE_TESTABILITY"] == "YES"
        assert release["ENABLE_TESTABILITY"] == "NO"
        assert debug["DEBUG_INFORMATION_FORMAT"] == "dwarf"
        assert release["DEBUG_INFORMATION_FORMAT"] == "dwarf-with-dsym"
        assert debug["ENABLE_USER_SCRIPT_SANDBOXING"] == "NO"
        assert debug["IPHONEOS_DEPLOYMENT_TARGET"] == "13.0"
        assert debug["TARGETED_DEVICE_FAMILY"] == "1,2"
        # Pre-signed embedded frameworks must not be stripped on copy.
        assert debug["COPY_PHASE_STRIP"] == "NO"
        assert release["COPY_PHASE_STRIP"] == "NO"
        # Embedded dynamic frameworks load via @rpath; the runpath must include
        # @executable_path/Frameworks regardless of pbxproj embedding side effects.
        for cfg in (debug, release):
            assert "@executable_path/Frameworks" in cfg["LD_RUNPATH_SEARCH_PATHS"]
            assert "$(inherited)" in cfg["LD_RUNPATH_SEARCH_PATHS"]

    def test_signing_settings(self, config, project_root):
        layout = materialize_project(config, project_root)
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        debug = _settings_for(project, "touchtracer", "Debug")
        assert debug["CODE_SIGN_STYLE"] == "Automatic"
        assert debug["DEVELOPMENT_TEAM"] == "ABCDE12345"

    def test_last_upgrade_check_current(self, config, project_root):
        # Xcode prompts "Update to recommended settings" when LastUpgradeCheck
        # is stale; the generator keeps it current on every build.
        from kivy_ios.project.generator import RECOMMENDED_LAST_UPGRADE_CHECK

        layout = materialize_project(config, project_root)
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        proj = next(iter(_objects(project).get_objects_in_section("PBXProject")))
        assert proj["attributes"]["LastUpgradeCheck"] == RECOMMENDED_LAST_UPGRADE_CHECK

    def test_last_upgrade_check_uses_provided_value(self, config, project_root):
        # `toolchain build` passes the installed Xcode's encoded version so the
        # "Update to recommended settings" banner never appears; an explicit
        # value overrides the fallback constant.
        layout = materialize_project(config, project_root, last_upgrade_check="2699")
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        proj = next(iter(_objects(project).get_objects_in_section("PBXProject")))
        assert proj["attributes"]["LastUpgradeCheck"] == "2699"

    def test_idempotent_regeneration(self, config, project_root):
        layout = materialize_project(config, project_root)
        # Re-generate; run-script phase must not duplicate.
        XcodeProjectGenerator(config, layout).generate()
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        target = project.get_target_by_name("touchtracer")
        assert target is not None
        script_phases = [
            p
            for p in target.buildPhases
            if project.get_object(p).isa == "PBXShellScriptBuildPhase"
        ]
        assert len(script_phases) == 1
        # source files must be referenced exactly once after re-generation.
        assert len(project.get_files_by_name("main.m")) == 1
        assert len(project.get_files_by_name("kivy_ios_bootstrap.m")) == 1
        assert len(project.get_files_by_name("PrivacyInfo.xcprivacy")) == 1
        assert len(project.get_files_by_name("pip-deps")) == 1

    def test_main_files_written(self, config, project_root):
        layout = materialize_project(config, project_root)
        assert (layout.root / "main.m").is_file()
        assert (layout.root / "main_config.h").is_file()
        assert (layout.root / "kivy_ios_bootstrap.h").is_file()
        assert (layout.root / "kivy_ios_bootstrap.m").is_file()
        assert (layout.root / "touchtracer-Info.plist").is_file()
        assert (layout.root / "PrivacyInfo.xcprivacy").is_file()

    def test_no_platform_shim_written(self, config, project_root):
        # Mobile geometry now ships in Kivy core as kivy.mobile (kivy/kivy#9331);
        # kivy-ios no longer vendors a platform/ shim into the bundle.
        layout = materialize_project(config, project_root)
        assert not (layout.root / "platform").exists()

    def test_main_m_is_trivial_wrapper(self, config, project_root):
        layout = materialize_project(config, project_root)
        main_m = (layout.root / "main.m").read_text(encoding="utf-8")
        assert "kivy_ios_main" in main_m
        assert "ENTRY_POINT" in main_m
        # No SDL or Python includes — those live in kivy_ios_bootstrap.m
        assert "#include <SDL3/" not in main_m
        assert "#include <Python.h>" not in main_m

    def test_bootstrap_excludes_platform_from_pythonpath(self, config, project_root):
        # The vendored platform/ shim is gone (kivy.mobile ships in Kivy core),
        # so it is no longer placed on PYTHONPATH.
        layout = materialize_project(config, project_root)
        bootstrap = (layout.root / "kivy_ios_bootstrap.m").read_text(encoding="utf-8")
        assert "platformPath" not in bootstrap

    def test_bootstrap_in_sources_phase(self, config, project_root):
        layout = materialize_project(config, project_root)
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        assert project.get_files_by_name("kivy_ios_bootstrap.m")

    def test_platform_folder_not_in_resources(self, config, project_root):
        # No vendored platform/ shim, so it is not a Copy Bundle Resources ref.
        layout = materialize_project(config, project_root)
        text = (layout.xcodeproj / "project.pbxproj").read_text()
        assert "platform in Resources" not in text

    def test_privacy_manifest_in_resources(self, config, project_root):
        # PrivacyInfo.xcprivacy is generated on disk; it must also be wired into
        # Copy Bundle Resources or it never ships in the .app bundle.
        layout = materialize_project(config, project_root)
        text = (layout.xcodeproj / "project.pbxproj").read_text()
        assert "PrivacyInfo.xcprivacy in Resources" in text
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        assert project.get_files_by_name("PrivacyInfo.xcprivacy")

    def test_embedded_frameworks_grouped(self, config, project_root):
        layout = materialize_project(config, project_root)
        xc = layout.frameworks / "SDL3.xcframework"
        (xc / "ios-arm64").mkdir(parents=True)
        (xc / "Info.plist").write_text("<plist/>")
        XcodeProjectGenerator(config, layout).generate()
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        groups = project.get_groups_by_name("Frameworks")
        assert len(groups) == 1
        fw_group = groups[0]
        assert fw_group.get_path() == "Frameworks"
        child_names = [
            project.get_object(cid).get_name()
            for cid in fw_group.children
            if project.get_object(cid) is not None
        ]
        assert "SDL3.xcframework" in child_names
        main = _objects(project)[_objects(project)[project["rootObject"]].mainGroup]
        main_child_names = [
            project.get_object(cid).get_name()
            for cid in main.children
            if project.get_object(cid) is not None
            and hasattr(project.get_object(cid), "get_name")
        ]
        assert "SDL3.xcframework" not in main_child_names
        assert "Frameworks" in main_child_names


class TestAssetCatalog:
    def test_catalog_generated_from_icon(self, make_config, project_root):
        from tests.project.test_icon import _write_minimal_png

        (project_root / "assets").mkdir()
        _write_minimal_png(project_root / "assets" / "icon.png", 1024, 1024)
        cfg = make_config('\n[tool.kivy.ios.icons]\nsource = "assets/icon.png"')
        layout = materialize_project(cfg, project_root)
        catalog = layout.resources / "Assets.xcassets"
        assert (catalog / "AppIcon.appiconset" / "Contents.json").is_file()
        assert (catalog / "AppIcon.appiconset" / "AppIcon.png").is_file()

    def test_appicon_name_set_when_icon_configured(self, make_config, project_root):
        # Without ASSETCATALOG_COMPILER_APPICON_NAME the catalog compiles but
        # Xcode assigns no app icon, so the generated AppIcon set is ignored.
        from tests.project.test_icon import _write_minimal_png

        (project_root / "assets").mkdir()
        _write_minimal_png(project_root / "assets" / "icon.png", 1024, 1024)
        cfg = make_config('\n[tool.kivy.ios.icons]\nsource = "assets/icon.png"')
        layout = materialize_project(cfg, project_root)
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        for configuration in ("Debug", "Release"):
            settings = _settings_for(project, "touchtracer", configuration)
            assert settings["ASSETCATALOG_COMPILER_APPICON_NAME"] == "AppIcon"

    def test_appicon_name_absent_without_icon(self, config, project_root):
        # No icon configured -> setting must not be emitted, or Xcode warns
        # about a missing AppIcon set.
        layout = materialize_project(config, project_root)
        project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
        debug = _settings_for(project, "touchtracer", "Debug")
        assert "ASSETCATALOG_COMPILER_APPICON_NAME" not in debug

    def test_splash_writes_launch_screen_and_plist(self, make_config, project_root):
        from PIL import Image

        (project_root / "assets").mkdir()
        Image.new("RGBA", (100, 100), (0, 0, 255, 255)).save(
            project_root / "assets" / "splash.png"
        )
        cfg = make_config(
            '\n[tool.kivy.ios.splash]\nsource = "assets/splash.png"\n'
            'background = "#000000"'
        )
        layout = materialize_project(cfg, project_root)
        assert (layout.root / "LaunchScreen.storyboard").is_file()
        assert (layout.resources / "Assets.xcassets" / "Splash.imageset").is_dir()

        import plistlib

        with open(layout.root / "touchtracer-Info.plist", "rb") as f:
            plist = plistlib.load(f)
        assert plist["UILaunchStoryboardName"] == "LaunchScreen"

    def test_no_catalog_without_assets(self, config, project_root):
        layout = materialize_project(config, project_root)
        assert not (layout.resources / "Assets.xcassets").exists()
        assert not (layout.root / "LaunchScreen.storyboard").exists()
