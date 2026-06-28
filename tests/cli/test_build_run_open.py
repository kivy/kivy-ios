"""Phase 6 — build step 7, run, open CLI orchestration (subprocess mocked)."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from kivy_ios.cli import build as build_cli
from kivy_ios.cli import open_cmd as open_mod
from kivy_ios.cli import run as run_mod
from kivy_ios.cli.build import build
from kivy_ios.cli.open_cmd import open_
from kivy_ios.cli.run import run as run_cmd
from kivy_ios.lock import (
    Lockfile,
    PythonXcframework,
    compute_pyproject_sha256,
    dumps,
)
from kivy_ios.xcode import runner as runner_mod

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

        [tool.kivy.ios.signing]
        team_id = "ABCDE12345"
        """
    ).strip()
    + "\n"
)


def _write_project(fs: str) -> Path:
    root = Path(fs)
    (root / "pyproject.toml").write_text(PYPROJECT)
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('hi')\n")
    lock = Lockfile(
        requires_python=">=3.15",
        packages=(),
        python_xcframework=PythonXcframework(
            version="3.15.0", url="https://example/py.tar.gz", sha256="c" * 64
        ),
        toolchain_version="3.0.0.dev0",
        generated_at="2026-01-01T00:00:00Z",
        pyproject_sha256=compute_pyproject_sha256(PYPROJECT),
        tool_kivy_ios_schema_version=1,
    )
    (root / "pylock.ios.toml").write_text(dumps(lock))
    return root


class _Proc:
    returncode = 0
    stdout = ""
    stderr = ""


_SIMCTL_JSON = json.dumps(
    {
        "devices": {
            "com.apple.CoreSimulator.SimRuntime.iOS-26-5": [
                {
                    "udid": "TEST-UDID",
                    "name": "iPhone 17",
                    "state": "Shutdown",
                    "isAvailable": True,
                }
            ]
        }
    }
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def stub_collect(monkeypatch):
    """Skip artifact collection in build/run orchestration tests."""
    monkeypatch.setattr(build_cli, "collect_artifacts", lambda *a, **k: None)


@pytest.fixture
def record_xcodebuild(monkeypatch):
    """Record every run_command argv across build/run/open."""
    calls = []

    def fake(argv, *, runner=None, check=True):
        calls.append(argv)
        proc = _Proc()
        if (
            len(argv) >= 6
            and argv[:4] == ["xcrun", "simctl", "list", "devices"]
            and "-j" in argv
        ):
            proc.stdout = _SIMCTL_JSON
        return proc

    monkeypatch.setattr(build_cli, "run_command", fake)
    monkeypatch.setattr(run_mod, "run_command", fake)
    monkeypatch.setattr(runner_mod, "run_command", fake)
    monkeypatch.setattr(open_mod, "run_command", fake)
    return calls


class TestBuildStep7:
    def test_simulator_invokes_xcodebuild(self, runner, tmp_path, record_xcodebuild):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            result = runner.invoke(build, ["--simulator"])
            assert result.exit_code == 0, result.output
            assert any("xcodebuild" in c[0] for c in record_xcodebuild)
            argv = record_xcodebuild[-1]
            assert "iphonesimulator" in argv
            assert argv[-1] == "build"

    def test_release_archive_export(self, runner, tmp_path, record_xcodebuild):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            result = runner.invoke(build, ["--release"])
            assert result.exit_code == 0, result.output
            verbs = [c[1] for c in record_xcodebuild if c[0] == "xcodebuild"]
            assert "archive" in verbs
            assert "-exportArchive" in verbs
            # ExportOptions.plist was written.
            assert (Path(fs) / "myapp-ios" / "build" / "ExportOptions.plist").is_file()

    def test_device_missing_team_id_fails_fast(self, runner, tmp_path, monkeypatch):
        # remove team_id from pyproject and clear env
        monkeypatch.delenv("KIVY_IOS_TEAM_ID", raising=False)
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            root = _write_project(fs)
            text = (
                root.joinpath("pyproject.toml")
                .read_text()
                .replace('\n[tool.kivy.ios.signing]\nteam_id = "ABCDE12345"\n', "\n")
            )
            root.joinpath("pyproject.toml").write_text(text)
            # re-lock hash to keep drift check happy
            lock = Lockfile(
                requires_python=">=3.15",
                packages=(),
                python_xcframework=PythonXcframework(
                    version="3.15.0", url="https://e/p.tar.gz", sha256="c" * 64
                ),
                toolchain_version="3.0.0.dev0",
                generated_at="t",
                pyproject_sha256=compute_pyproject_sha256(text),
                tool_kivy_ios_schema_version=1,
            )
            root.joinpath("pylock.ios.toml").write_text(dumps(lock))
            result = runner.invoke(build, ["--device"])
            assert result.exit_code != 0
            assert "code signing required" in result.output


class TestRun:
    def test_run_simulator_install_launch(self, runner, tmp_path, record_xcodebuild):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            # pre-create the built .app so the locate step passes
            app = (
                Path(fs)
                / "myapp-ios"
                / "build"
                / "DerivedData"
                / "Build"
                / "Products"
                / "Debug-iphonesimulator"
                / "myapp.app"
            )
            app.mkdir(parents=True)
            result = runner.invoke(run_cmd, ["--simulator"])
            assert result.exit_code == 0, result.output
            joined = [" ".join(c) for c in record_xcodebuild]
            assert any("simctl install" in j for j in joined)
            assert any("simctl launch" in j for j in joined)

    def test_run_no_build_missing_app_errors(self, runner, tmp_path, record_xcodebuild):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            result = runner.invoke(run_cmd, ["--no-build"])
            assert result.exit_code != 0
            assert "built app not found" in result.output

    def test_list_devices(self, runner, tmp_path, record_xcodebuild):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            result = runner.invoke(run_cmd, ["--list-devices"])
            assert result.exit_code == 0
            joined = [" ".join(c) for c in record_xcodebuild]
            assert any("simctl list" in j for j in joined)
            assert any("devicectl list" in j for j in joined)


class TestOpen:
    def test_open_missing_project_errors(self, runner, tmp_path, record_xcodebuild):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            result = runner.invoke(open_, [])
            assert result.exit_code != 0
            assert "does not exist" in result.output

    def test_open_invokes_open(self, runner, tmp_path, record_xcodebuild):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write_project(fs)
            (Path(fs) / "myapp-ios" / "myapp.xcodeproj").mkdir(parents=True)
            result = runner.invoke(open_, [])
            assert result.exit_code == 0, result.output
            assert record_xcodebuild[-1][0] == "open"
