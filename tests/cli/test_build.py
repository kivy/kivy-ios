"""Phase 5 — toolchain build orchestration (steps 1 & 6; collection mocked)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from kivy_ios.cli import build as build_cli
from kivy_ios.cli.build import build
from kivy_ios.lock import (
    Lockfile,
    PythonXcframework,
    compute_pyproject_sha256,
    dumps,
)

PYPROJECT = (
    textwrap.dedent(
        """
    [project]
    name = "myapp"
    version = "1.0.0"
    requires-python = ">=3.15"
    dependencies = ["kivy"]

    [tool.kivy]
    app_dir = "src"

    [tool.kivy.ios]
    schema_version = 1
    bundle_id = "org.example.myapp"
    deployment_target = "13.0"

    [tool.kivy.ios.python]
    version = "3.15.0"
    """
    ).strip()
    + "\n"
)


def _write_project(fs: str, *, in_sync: bool = True) -> Path:
    root = Path(fs)
    (root / "pyproject.toml").write_text(PYPROJECT)
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('hi')\n")
    sha = compute_pyproject_sha256(PYPROJECT if in_sync else PYPROJECT + "# drift\n")
    lock = Lockfile(
        requires_python=">=3.15",
        packages=(),
        python_xcframework=PythonXcframework(
            version="3.15.0", url="https://example/py.tar.gz", sha256="c" * 64
        ),
        toolchain_version="3.0.0.dev0",
        generated_at="2026-01-01T00:00:00Z",
        pyproject_sha256=sha,
        tool_kivy_ios_schema_version=1,
    )
    (root / "pylock.ios.toml").write_text(dumps(lock))
    return root


@pytest.fixture
def runner():
    return CliRunner()


class _Proc:
    returncode = 0
    stdout = ""
    stderr = ""


@pytest.fixture(autouse=True)
def mock_collect(monkeypatch):
    calls = []

    def fake_collect(lock, layout, *, build_slices, project_root, no_cache=False, **kw):
        calls.append({"slices": build_slices, "layout": layout, "no_cache": no_cache})

    monkeypatch.setattr(build_cli, "collect_artifacts", fake_collect)
    # Pin the host-derived simulator arch so slice assertions are deterministic
    # regardless of whether the test runs on Apple Silicon or an Intel host.
    monkeypatch.setattr(build_cli, "default_simulator_arch", lambda: "arm64")
    # Step 7 invokes xcodebuild; stub it so these orchestration tests stay
    # hermetic (they assert on the resolved slice, not on a real build).
    monkeypatch.setattr(build_cli, "run_command", lambda *a, **k: _Proc())
    return calls


class TestBuildOrchestration:
    def test_bare_build_generates_project(self, runner, tmp_path, mock_collect):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            result = runner.invoke(build, [])
            assert result.exit_code == 0, result.output
            assert (Path(fs) / "myapp-ios" / "myapp.xcodeproj").is_dir()
            assert "Project ready" in result.output
            assert len(mock_collect) == 1
            # bare build collects BOTH slices so either Xcode destination builds
            tags = [s.platform_tag for s in mock_collect[0]["slices"]]
            assert tags == [
                "ios_13_0_arm64_iphoneos",
                "ios_13_0_arm64_iphonesimulator",
            ]

    def test_simulator_slice_passed(self, runner, tmp_path, mock_collect):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            result = runner.invoke(build, ["--simulator"])
            assert result.exit_code == 0, result.output
            tags = [s.platform_tag for s in mock_collect[0]["slices"]]
            assert tags == ["ios_13_0_arm64_iphonesimulator"]

    def test_simulator_arch_override(self, runner, tmp_path, mock_collect):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            runner.invoke(build, ["--simulator", "--arch", "x86_64"])
            tags = [s.platform_tag for s in mock_collect[0]["slices"]]
            assert tags == ["ios_13_0_x86_64_iphonesimulator"]

    def test_intel_host_collects_x86_64_simulator(
        self, runner, tmp_path, mock_collect, monkeypatch
    ):
        # On an Intel host (no --arch), the bare and targeted simulator builds
        # must collect the x86_64 slice the machine can actually run, not arm64.
        monkeypatch.setattr(build_cli, "default_simulator_arch", lambda: "x86_64")
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            runner.invoke(build, [])
            tags = [s.platform_tag for s in mock_collect[0]["slices"]]
            assert tags == [
                "ios_13_0_arm64_iphoneos",
                "ios_13_0_x86_64_iphonesimulator",
            ]

    def test_no_cache_forwarded(self, runner, tmp_path, mock_collect):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            runner.invoke(build, ["--no-cache"])
            assert mock_collect[0]["no_cache"] is True


class TestBuildGuards:
    def test_drift_blocks_build(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs, in_sync=False)
            result = runner.invoke(build, [])
            assert result.exit_code != 0
            assert "out of date" in result.output

    def test_no_verify_lock_bypasses_drift(self, runner, tmp_path, mock_collect):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs, in_sync=False)
            result = runner.invoke(build, ["--no-verify-lock"])
            assert result.exit_code == 0, result.output

    def test_missing_lock_errors(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            root = Path(fs)
            root.joinpath("pyproject.toml").write_text(PYPROJECT)
            root.joinpath("src").mkdir()
            result = runner.invoke(build, [])
            assert result.exit_code != 0
            assert "toolchain lock" in result.output

    def test_legacy_recipe_args_rejected(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            result = runner.invoke(build, ["python3", "kivy"])
            assert result.exit_code != 0
            assert "2.x" in result.output

    def test_no_pyproject_errors(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(build, [])
            assert result.exit_code != 0
            assert "no pyproject.toml" in result.output


class TestSigningIdentityWiring:
    def test_device_build_passes_signing_identity(
        self, runner, tmp_path, mock_collect, monkeypatch
    ):
        captured: list[list[str]] = []
        monkeypatch.setattr(
            build_cli,
            "run_command",
            lambda argv, *a, **k: captured.append(argv) or _Proc(),
        )
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            result = runner.invoke(
                build,
                [
                    "--device",
                    "--team-id",
                    "ABCDE12345",
                    "--signing-identity",
                    "Apple Distribution: Me",
                ],
            )
            assert result.exit_code == 0, result.output
        assert captured, "xcodebuild was not invoked"
        assert "CODE_SIGN_IDENTITY=Apple Distribution: Me" in captured[-1]

    def test_signing_identity_from_env(
        self, runner, tmp_path, mock_collect, monkeypatch
    ):
        captured: list[list[str]] = []
        monkeypatch.setattr(
            build_cli,
            "run_command",
            lambda argv, *a, **k: captured.append(argv) or _Proc(),
        )
        monkeypatch.setenv("KIVY_IOS_SIGNING_IDENTITY", "Apple Development: Env")
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            result = runner.invoke(build, ["--device", "--team-id", "ABCDE12345"])
            assert result.exit_code == 0, result.output
        assert "CODE_SIGN_IDENTITY=Apple Development: Env" in captured[-1]

    def test_release_export_options_get_signing_certificate(
        self, runner, tmp_path, mock_collect, monkeypatch
    ):
        import plistlib

        captured: list[list[str]] = []
        monkeypatch.setattr(
            build_cli,
            "run_command",
            lambda argv, *a, **k: captured.append(argv) or _Proc(),
        )
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            result = runner.invoke(
                build,
                [
                    "--release",
                    "--team-id",
                    "ABCDE12345",
                    "--signing-identity",
                    "Apple Distribution: Me",
                ],
            )
            assert result.exit_code == 0, result.output
            options = plistlib.loads(
                (Path(fs) / "myapp-ios" / "build" / "ExportOptions.plist").read_bytes()
            )
        # archive command carries the override; export options pin the cert.
        assert any("CODE_SIGN_IDENTITY=Apple Distribution: Me" in c for c in captured)
        assert options["signingCertificate"] == "Apple Distribution: Me"


class TestLastUpgradeCheck:
    def test_encodes_xcode_version(self):
        from kivy_ios.cli.build import _encode_last_upgrade_check

        assert _encode_last_upgrade_check("26.5") == "2650"
        assert _encode_last_upgrade_check("16.2") == "1620"
        assert _encode_last_upgrade_check("16.2.1") == "1621"

    def test_returns_none_when_unparseable(self):
        from kivy_ios.cli.build import _encode_last_upgrade_check

        assert _encode_last_upgrade_check("not a version") is None
