"""Phase 5 — Info.plist, entitlements, privacy, main.m/main_config.h."""

from __future__ import annotations

import plistlib

import pytest

from kivy_ios.config import load_config_from_text
from kivy_ios.project.entitlements import write_entitlements
from kivy_ios.project.plist import build_info_plist, write_info_plist
from kivy_ios.project.privacy import STUB_MANIFEST, write_privacy_manifest
from kivy_ios.project.sources import render_main_config_h


class TestInfoPlist:
    def test_managed_keys(self, config):
        plist = build_info_plist(config)
        assert "UILaunchStoryboardName" not in plist
        assert plist["CFBundleName"] == "touchtracer"
        assert plist["CFBundleDisplayName"] == "Touch Tracer"
        assert plist["CFBundleIdentifier"] == "org.kivy.touchtracer"
        assert plist["CFBundleShortVersionString"] == "1.2.3"
        assert plist["CFBundleVersion"] == "7"
        assert plist["MinimumOSVersion"] == "13.0"
        assert plist["UIRequiresFullScreen"] is True

    def test_sdl3_scene_manifest_always_present(self, config):
        plist = build_info_plist(config)
        manifest = plist["UIApplicationSceneManifest"]
        assert manifest["UIApplicationSupportsMultipleScenes"] is False
        configs = manifest["UISceneConfigurations"][
            "UIWindowSceneSessionRoleApplication"
        ]
        assert len(configs) == 1
        assert configs[0]["UISceneConfigurationName"] == "SDLSceneConfiguration"
        assert configs[0]["UISceneDelegateClassName"] == "SDLUIKitSceneDelegate"

    @pytest.mark.parametrize(
        "key,value",
        [
            ("UIRequiresFullScreen", "false"),
            ("LSRequiresIPhoneOS", "false"),
            ("CFBundlePackageType", '"BNDL"'),
            ("CFBundleInfoDictionaryVersion", '"7.0"'),
        ],
    )
    def test_managed_keys_rejected_in_info_plist(self, key, value):
        from kivy_ios.config.errors import ConfigError

        with pytest.raises(ConfigError, match=key):
            load_config_from_text(
                "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
                "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
                "[tool.kivy.ios.python]\nversion='3.15.0'\n"
                f"[tool.kivy.ios.info_plist]\n{key} = {value}"
            )

    def test_indirect_input_events_overridable(self, make_config):
        cfg = make_config(
            "\n[tool.kivy.ios.info_plist]\n"
            "UIApplicationSupportsIndirectInputEvents = false"
        )
        plist = build_info_plist(cfg)
        assert plist["UIApplicationSupportsIndirectInputEvents"] is False

    def test_launch_storyboard_user_override_wins(self, make_config):
        cfg = make_config(
            '\n[tool.kivy.ios.splash]\nbackground = "#ffffff"\n'
            '\n[tool.kivy.ios.info_plist]\nUILaunchStoryboardName = "Custom"'
        )
        plist = build_info_plist(cfg)
        assert plist["UILaunchStoryboardName"] == "Custom"

    def test_orientation_includes_ipad(self, config):
        plist = build_info_plist(config)
        expected = [
            "UIInterfaceOrientationPortrait",
            "UIInterfaceOrientationLandscapeLeft",
        ]
        assert plist["UISupportedInterfaceOrientations"] == expected
        assert plist["UISupportedInterfaceOrientations~ipad"] == expected

    def test_launch_storyboard_when_splash_configured(self, make_config):
        cfg = make_config('\n[tool.kivy.ios.splash]\nbackground = "#ffffff"')
        plist = build_info_plist(cfg)
        assert plist["UILaunchStoryboardName"] == "LaunchScreen"

    def test_info_plist_merge_user_keys(self, make_config):
        cfg = make_config(
            '\n[tool.kivy.ios.info_plist]\nNSCameraUsageDescription = "scan QR"'
        )
        plist = build_info_plist(cfg)
        assert plist["NSCameraUsageDescription"] == "scan QR"

    def test_write_roundtrip(self, config, tmp_path):
        path = write_info_plist(config, tmp_path / "App-Info.plist")
        with open(path, "rb") as f:
            data = plistlib.load(f)
        assert data["CFBundleIdentifier"] == "org.kivy.touchtracer"


class TestEntitlements:
    def test_none_when_absent(self, config, tmp_path):
        assert write_entitlements(config, tmp_path / "x.entitlements") is None

    def test_written_when_present(self, make_config, tmp_path):
        cfg = make_config(
            '\n[tool.kivy.ios.entitlements]\n"aps-environment" = "development"'
        )
        path = write_entitlements(cfg, tmp_path / "x.entitlements")
        assert path is not None
        with open(path, "rb") as f:
            data = plistlib.load(f)
        assert data["aps-environment"] == "development"


class TestPrivacy:
    def test_stub_written(self, config, tmp_path):
        path = write_privacy_manifest(config, tmp_path / "PrivacyInfo.xcprivacy")
        with open(path, "rb") as f:
            data = plistlib.load(f)
        assert data == STUB_MANIFEST

    def test_copies_user_source(self, make_config, tmp_path):
        src = tmp_path / "custom.xcprivacy"
        with open(src, "wb") as f:
            plistlib.dump({"NSPrivacyTracking": True}, f)
        cfg = make_config(
            '\n[tool.kivy.ios.privacy_manifest]\nsource = "custom.xcprivacy"'
        )
        path = write_privacy_manifest(
            cfg, tmp_path / "PrivacyInfo.xcprivacy", project_root=tmp_path
        )
        with open(path, "rb") as f:
            data = plistlib.load(f)
        assert data["NSPrivacyTracking"] is True


class TestMainConfigHeader:
    def test_defines(self, config):
        header = render_main_config_h(config)
        assert '#define APP_DIR            "app"' in header
        assert '#define ENTRY_POINT        "main"' in header
        assert '#define PYTHON_MAJOR_MINOR "3.15"' in header

    def test_entry_point_dotted(self):
        cfg = load_config_from_text(
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "entry_point='pkg.start'\n[tool.kivy.ios]\nschema_version=1\n"
            "bundle_id='o.x.a'\n[tool.kivy.ios.python]\nversion='3.14.1'"
        )
        header = render_main_config_h(cfg)
        assert 'ENTRY_POINT        "pkg.start"' in header
        assert 'PYTHON_MAJOR_MINOR "3.14"' in header
