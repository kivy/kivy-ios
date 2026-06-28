"""Phase 6 — xcodebuild/export command + signing builders (hermetic, pure)."""

from __future__ import annotations

import textwrap

import pytest

from kivy_ios.config import load_config_from_text
from kivy_ios.xcode.commands import (
    SigningError,
    XcodeBuild,
    archive_command,
    build_command,
    default_simulator_arch,
    export_command,
    export_options_plist,
    preflight_signing,
    product_app_path,
    resolve_team_id,
    sdk_for,
)


def _config(signing: str = "") -> str:
    return textwrap.dedent(
        f"""
        [project]
        name = "myapp"
        version = "1.0.0"

        [tool.kivy]
        app_dir = "src"

        [tool.kivy.ios]
        schema_version = 1
        bundle_id = "org.example.myapp"
        deployment_target = "13.0"

        [tool.kivy.ios.python]
        version = "3.15.0"
        {signing}
        """
    ).strip()


@pytest.fixture
def config():
    return load_config_from_text(_config())


@pytest.fixture
def xb(config, tmp_path):
    return XcodeBuild.from_config(config, tmp_path)


class TestPaths:
    def test_locations(self, xb, tmp_path):
        assert xb.project_path == tmp_path / "myapp-ios" / "myapp.xcodeproj"
        assert xb.archive_path == tmp_path / "myapp-ios" / "build" / "myapp.xcarchive"
        assert xb.ipa_path == tmp_path / "myapp-ios" / "build" / "myapp.ipa"

    def test_sdk_mapping(self):
        assert sdk_for("simulator") == "iphonesimulator"
        assert sdk_for("device") == "iphoneos"
        assert sdk_for("release") == "iphoneos"


class TestBuildCommand:
    def test_simulator_debug(self, xb):
        cmd = build_command(xb, "simulator")
        assert "-sdk" in cmd and "iphonesimulator" in cmd
        assert "Debug" in cmd
        # Default simulator arch follows the host (arm64 / x86_64), so assert
        # against the helper rather than a hard-coded arch.
        assert f"ARCHS={default_simulator_arch()}" in cmd
        assert "ONLY_ACTIVE_ARCH=NO" in cmd
        assert cmd[-1] == "build"

    def test_simulator_default_arch_matches_host(self, monkeypatch):
        import kivy_ios.xcode.commands as commands

        monkeypatch.setattr(commands.platform, "machine", lambda: "x86_64")
        assert commands.default_simulator_arch() == "x86_64"
        monkeypatch.setattr(commands.platform, "machine", lambda: "arm64")
        assert commands.default_simulator_arch() == "arm64"

    def test_device_debug(self, xb):
        cmd = build_command(xb, "device")
        assert "iphoneos" in cmd
        assert "Debug" in cmd

    def test_arch_override(self, xb):
        cmd = build_command(xb, "simulator", arch="x86_64")
        assert "ARCHS=x86_64" in cmd
        assert "ONLY_ACTIVE_ARCH=NO" in cmd

    def test_derived_data_path(self, xb, tmp_path):
        cmd = build_command(xb, "simulator", derived_data_path=tmp_path / "dd")
        assert "-derivedDataPath" in cmd
        assert str(tmp_path / "dd") in cmd

    def test_product_path(self, tmp_path):
        p = product_app_path(tmp_path / "dd", "myapp", "simulator")
        assert p == (
            tmp_path
            / "dd"
            / "Build"
            / "Products"
            / "Debug-iphonesimulator"
            / "myapp.app"
        )


class TestArchiveExport:
    def test_archive(self, xb):
        cmd = archive_command(xb)
        assert cmd[1] == "archive"
        assert "Release" in cmd
        assert "-archivePath" in cmd

    def test_export(self, xb, tmp_path):
        cmd = export_command(xb, tmp_path / "ExportOptions.plist")
        assert "-exportArchive" in cmd
        assert "-exportOptionsPlist" in cmd
        assert str(tmp_path / "ExportOptions.plist") in cmd

    def test_export_options_plist(self):
        plist = export_options_plist(method="ad-hoc", team_id="ABCDE12345")
        assert plist == {
            "method": "ad-hoc",
            "teamID": "ABCDE12345",
            "uploadSymbols": True,
        }

    def test_export_options_upload_symbols_false(self):
        plist = export_options_plist(
            method="app-store", team_id="T", upload_symbols=False
        )
        assert plist["uploadSymbols"] is False

    def test_export_options_unknown_method(self):
        with pytest.raises(ValueError, match="unknown export method"):
            export_options_plist(method="enterprise", team_id="T")


class TestSigning:
    def test_simulator_skips(self, config):
        assert preflight_signing(config, "simulator") is None

    def test_device_requires_team_id(self, config):
        with pytest.raises(SigningError, match="code signing required"):
            preflight_signing(config, "device", env={})

    def test_flag_precedence(self, config):
        assert (
            preflight_signing(config, "device", team_id_flag="FLAG", env={}) == "FLAG"
        )

    def test_env_precedence(self, config):
        tid = resolve_team_id(config, env={"KIVY_IOS_TEAM_ID": "ENVID"})
        assert tid == "ENVID"

    def test_pyproject_team_id(self):
        cfg = load_config_from_text(
            _config('\n[tool.kivy.ios.signing]\nteam_id = "PROJID"')
        )
        assert resolve_team_id(cfg, env={}) == "PROJID"

    def test_flag_beats_env_and_project(self):
        cfg = load_config_from_text(
            _config('\n[tool.kivy.ios.signing]\nteam_id = "PROJID"')
        )
        tid = resolve_team_id(
            cfg, team_id_flag="FLAG", env={"KIVY_IOS_TEAM_ID": "ENVID"}
        )
        assert tid == "FLAG"
