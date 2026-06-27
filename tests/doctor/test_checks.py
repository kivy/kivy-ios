"""Phase 7 — doctor check logic (hermetic, fake probe)."""

from __future__ import annotations

import struct

import pytest

from kivy_ios.config import load_config_from_text
from kivy_ios.doctor import checks as C
from kivy_ios.doctor.result import Status, worst_status
from kivy_ios.doctor.runner import run_checks
from kivy_ios.lock import LockedSwiftPackage, Lockfile, PythonXcframework

from .conftest import FakeProbe


def _config_with_swift_package():
    return load_config_from_text(
        "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
        "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
        "[tool.kivy.ios.python]\nversion='3.15.0'\n"
        "[tool.kivy.ios.native.swift_packages]\n"
        'Sentry = { url = "https://github.com/getsentry/sentry-cocoa", '
        'requirement = { from = "8.49.0" }, products = ["Sentry"] }'
    )


class TestEnvironmentChecks:
    def test_xcode_missing(self):
        r = C.check_xcode_version(FakeProbe(xcode=None))
        assert r.status is Status.FAIL

    def test_xcode_too_old(self):
        r = C.check_xcode_version(FakeProbe(xcode="14.2"))
        assert r.status is Status.FAIL

    def test_xcode_ok(self):
        r = C.check_xcode_version(FakeProbe(xcode="16.1"))
        assert r.status is Status.PASS

    def test_clt_missing_path(self):
        r = C.check_command_line_tools(FakeProbe(select=None))
        assert r.status is Status.FAIL

    def test_clt_no_clang(self):
        r = C.check_command_line_tools(FakeProbe(clang=False))
        assert r.status is Status.FAIL

    def test_no_runtimes_warns(self, config):
        r = C.check_simulator_runtimes(FakeProbe(runtimes=[]), config)
        assert r.status is Status.WARN

    def test_runtime_below_floor_warns(self, config):
        r = C.check_simulator_runtimes(FakeProbe(runtimes=["12.0"]), config)
        assert r.status is Status.WARN

    def test_runtime_meets_floor(self, config):
        r = C.check_simulator_runtimes(FakeProbe(runtimes=["13.0", "18.0"]), config)
        assert r.status is Status.PASS

    def test_toolchain_offline_pass(self):
        r = C.check_toolchain_version(FakeProbe(), "3.0.0", offline=True)
        assert r.status is Status.PASS

    def test_toolchain_newer_warns(self):
        r = C.check_toolchain_version(FakeProbe(latest="9.0.0"), "3.0.0", offline=False)
        assert r.status is Status.WARN


class TestProjectChecks:
    def test_app_dir_missing_fails(self, config, tmp_path):
        # tmp_path has no src/ directory
        assert C.check_app_dir(config, tmp_path).status is Status.FAIL

    def test_app_dir_present_passes(self, config, tmp_path):
        (tmp_path / "src").mkdir()
        assert C.check_app_dir(config, tmp_path).status is Status.PASS

    def test_signing_auto_pass(self, config, fake_probe):
        assert C.check_signing_identity(fake_probe, config).status is Status.PASS

    def test_signing_manual_missing_fail(self):
        from kivy_ios.config import load_config_from_text

        cfg = load_config_from_text(
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
            "[tool.kivy.ios.python]\nversion='3.15.0'\n"
            "[tool.kivy.ios.signing]\nauto_signing=false\nidentity='Acme Inc'"
        )
        probe = FakeProbe(identities=['1) ABC "Apple Development: x"'])
        assert C.check_signing_identity(probe, cfg).status is Status.FAIL

    def test_provisioning_unset_pass(self, config, tmp_path):
        assert C.check_provisioning_profile(config, tmp_path).status is Status.PASS

    def test_app_icon_skip_when_unconfigured(self, config, tmp_path):
        assert C.check_app_icon(config, tmp_path).status is Status.SKIP

    def test_app_icon_fail_wrong_size(self, tmp_path):
        from kivy_ios.config import load_config_from_text
        from tests.project.test_icon import _write_minimal_png

        (tmp_path / "assets").mkdir()
        _write_minimal_png(tmp_path / "assets" / "icon.png", 100, 100)
        cfg = load_config_from_text(
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
            "[tool.kivy.ios.python]\nversion='3.15.0'\n"
            '[tool.kivy.ios.icons]\nsource = "assets/icon.png"'
        )
        result = C.check_app_icon(cfg, tmp_path)
        assert result.status is Status.FAIL
        assert "100x100" in (result.hint or "")

    def test_app_icon_pass(self, tmp_path):
        from kivy_ios.config import load_config_from_text
        from tests.project.test_icon import _write_minimal_png

        (tmp_path / "assets").mkdir()
        _write_minimal_png(tmp_path / "assets" / "icon.png", 1024, 1024)
        cfg = load_config_from_text(
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
            "[tool.kivy.ios.python]\nversion='3.15.0'\n"
            '[tool.kivy.ios.icons]\nsource = "assets/icon.png"'
        )
        assert C.check_app_icon(cfg, tmp_path).status is Status.PASS

    def test_hosts_reachable_pass(self, fake_probe):
        lock = _lock_with_python_url("https://www.python.org/x.tar.gz")
        assert C.check_hosts_reachable(fake_probe, lock).status is Status.PASS

    def test_hosts_unreachable_fail(self):
        lock = _lock_with_python_url("https://www.python.org/x.tar.gz")
        probe = FakeProbe(reachable={"www.python.org": False})
        r = C.check_hosts_reachable(probe, lock)
        assert r.status is Status.FAIL
        assert "www.python.org" in r.detail

    def test_swift_toolchain_skipped_without_packages(self, config, fake_probe):
        r = C.check_swift_toolchain(fake_probe, config)
        assert r.status is Status.SKIP

    def test_swift_toolchain_fail_when_missing(self):
        cfg = _config_with_swift_package()
        probe = FakeProbe(swift=False)
        r = C.check_swift_toolchain(probe, cfg)
        assert r.status is Status.FAIL
        assert "swift not found" in r.detail

    def test_swift_toolchain_pass(self):
        cfg = _config_with_swift_package()
        r = C.check_swift_toolchain(FakeProbe(swift=True), cfg)
        assert r.status is Status.PASS
        assert "1 swift package" in r.detail

    def test_hosts_include_swift_package_git_host(self, fake_probe):
        lock = _lock_with_swift_url("https://github.com/getsentry/sentry-cocoa")
        r = C.check_hosts_reachable(fake_probe, lock)
        assert r.status is Status.PASS
        assert "github.com" in r.detail

    def test_hosts_swift_scp_url_host(self, fake_probe):
        lock = _lock_with_swift_url("git@github.com:getsentry/sentry-cocoa.git")
        r = C.check_hosts_reachable(fake_probe, lock)
        assert "github.com" in r.detail

    def test_native_binary_macos_fails(self, config, tmp_path, fake_probe_factory):
        (tmp_path / "src").mkdir()
        so = tmp_path / "src" / "ext.so"
        so.write_bytes(b"\x00")
        probe = fake_probe_factory(platforms={"ext.so": {"macos"}})
        r = C.check_app_native_binaries(probe, config, tmp_path)
        assert r.status is Status.FAIL

    def test_native_binary_ios_passes(self, config, tmp_path, fake_probe_factory):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "ext.so").write_bytes(b"\x00")
        probe = fake_probe_factory(platforms={"ext.so": {"ios"}})
        assert (
            C.check_app_native_binaries(probe, config, tmp_path).status is Status.PASS
        )

    def test_privacy_manifest_absent_warns(self, config, tmp_path):
        assert C.check_app_privacy_manifest(config, tmp_path).status is Status.WARN

    def test_privacy_manifest_present_pass(self, config, tmp_path):
        staging = tmp_path / "myapp-ios"
        staging.mkdir()
        (staging / "PrivacyInfo.xcprivacy").write_text("<plist/>")
        assert C.check_app_privacy_manifest(config, tmp_path).status is Status.PASS

    def test_xcframework_privacy_missing_warns(self, config, tmp_path):
        fw = tmp_path / "myapp-ios" / "Frameworks" / "SDL3.xcframework" / "ios-arm64"
        fw.mkdir(parents=True)
        r = C.check_xcframework_privacy_manifests(config, tmp_path)
        assert r.status is Status.WARN
        assert "SDL3" in r.detail


class TestRunModes:
    def test_environment_mode_skips_project(self, fake_probe):
        results = run_checks(fake_probe, toolchain_version="3.0.0", config=None)
        skipped = [r for r in results if r.status is Status.SKIP]
        assert len(skipped) == 10

    def test_project_mode_runs_all(self, fake_probe, config, tmp_path):
        results = run_checks(
            fake_probe,
            toolchain_version="3.0.0",
            config=config,
            project_root=tmp_path,
        )
        names = {r.name for r in results}
        assert "App source directory" in names
        assert "Signing identity" in names
        assert "find_links directories" in names
        assert "App icon" in names
        assert "App-level privacy manifest" in names

    def test_find_links_missing_fail(self, tmp_path):
        from kivy_ios.config import load_config_from_text

        cfg = load_config_from_text(
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
            'find_links = ["wheels"]\n'
            "[tool.kivy.ios.python]\nversion='3.15.0'"
        )
        result = C.check_find_links(cfg, tmp_path)
        assert result.status is Status.FAIL
        assert "missing" in result.detail

    def test_find_links_empty_warns(self, tmp_path):
        from kivy_ios.config import load_config_from_text

        (tmp_path / "wheels").mkdir()
        cfg = load_config_from_text(
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
            'find_links = ["wheels"]\n'
            "[tool.kivy.ios.python]\nversion='3.15.0'"
        )
        result = C.check_find_links(cfg, tmp_path)
        assert result.status is Status.WARN
        assert "no .whl files" in result.detail

    def test_find_links_with_wheels_passes(self, tmp_path):
        from kivy_ios.config import load_config_from_text

        wheels = tmp_path / "wheels"
        wheels.mkdir()
        (wheels / "kivy-1.whl").write_bytes(b"whl")
        cfg = load_config_from_text(
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
            'find_links = ["wheels"]\n'
            "[tool.kivy.ios.python]\nversion='3.15.0'"
        )
        assert C.check_find_links(cfg, tmp_path).status is Status.PASS

    def test_worst_status(self):
        from kivy_ios.doctor.result import CheckResult

        results = [
            CheckResult("a", Status.PASS),
            CheckResult("b", Status.WARN),
            CheckResult("c", Status.FAIL),
        ]
        assert worst_status(results) is Status.FAIL


class TestMachOParser:
    def test_parses_ios_platform(self):
        from kivy_ios.doctor.probe import _macho_platforms

        assert "ios" in _macho_platforms(_thin_macho(platform=2))

    def test_parses_macos_platform(self):
        from kivy_ios.doctor.probe import _macho_platforms

        assert "macos" in _macho_platforms(_thin_macho(platform=1))

    def test_non_macho_returns_empty(self):
        from kivy_ios.doctor.probe import _macho_platforms

        assert _macho_platforms(b"not a macho") == set()


@pytest.fixture
def fake_probe_factory():
    return lambda **kw: FakeProbe(**kw)


def _lock_with_python_url(url: str) -> Lockfile:
    return Lockfile(
        requires_python=">=3.15",
        packages=(),
        python_xcframework=PythonXcframework(
            version="3.15.0", url=url, sha256="c" * 64
        ),
        toolchain_version="3.0.0",
        generated_at="t",
        pyproject_sha256="d" * 64,
        tool_kivy_ios_schema_version=1,
    )


def _lock_with_swift_url(url: str) -> Lockfile:
    return Lockfile(
        requires_python=">=3.15",
        packages=(),
        python_xcframework=PythonXcframework(version="3.15.0", url="", sha256="c" * 64),
        toolchain_version="3.0.0",
        generated_at="t",
        pyproject_sha256="d" * 64,
        tool_kivy_ios_schema_version=1,
        swift_packages=(
            LockedSwiftPackage(
                name="Sentry",
                products=("Sentry",),
                url=url,
                requirement={"from": "8.49.0"},
                revision="a" * 40,
                version="8.49.0",
            ),
        ),
    )


def _thin_macho(*, platform: int) -> bytes:
    # 64-bit Mach-O, big-endian, one LC_BUILD_VERSION command.
    # mach_header_64: magic, cputype, cpusubtype, filetype, ncmds,
    #                 sizeofcmds, flags, reserved  (8 x uint32 = 32 bytes)
    header = struct.pack(">IiiIIIII", 0xFEEDFACF, 0x0100000C, 0, 2, 1, 24, 0, 0)
    # LC_BUILD_VERSION: cmd, cmdsize, platform, minos, sdk, ntools
    lc = struct.pack(">IIIIII", 0x32, 24, platform, 0, 0, 0)
    return header + lc
