"""Phase 7 — status / clean / upgrade / doctor CLI verbs."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from kivy_ios.cli import doctor as doctor_mod
from kivy_ios.cli import upgrade as upgrade_mod
from kivy_ios.cli.clean import clean
from kivy_ios.cli.doctor import doctor
from kivy_ios.cli.status import _humanize, status
from kivy_ios.cli.upgrade import upgrade
from kivy_ios.lock import (
    LockedXcframework,
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
        display_name = "My App"

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


def _lock(text: str, *, xcframeworks=()) -> Lockfile:
    return Lockfile(
        requires_python=">=3.15",
        packages=(),
        python_xcframework=PythonXcframework(
            version="3.15.0", url="https://example/py.tar.gz", sha256="c" * 64
        ),
        toolchain_version="3.0.0.dev0",
        generated_at="t",
        pyproject_sha256=compute_pyproject_sha256(text),
        tool_kivy_ios_schema_version=1,
        xcframeworks=tuple(xcframeworks),
    )


def _write(fs: str, *, lock: bool = True, **lock_kw) -> Path:
    root = Path(fs)
    (root / "pyproject.toml").write_text(PYPROJECT)
    (root / "src").mkdir()
    if lock:
        (root / "pylock.ios.toml").write_text(dumps(_lock(PYPROJECT, **lock_kw)))
    return root


@pytest.fixture
def runner():
    return CliRunner()


class TestHumanize:
    def test_just_now(self):
        assert _humanize(0) == "just now"
        assert _humanize(59) == "just now"

    def test_minutes(self):
        assert _humanize(60) == "1 minute ago"
        assert _humanize(120) == "2 minutes ago"
        assert _humanize(3599) == "59 minutes ago"

    def test_hours(self):
        assert _humanize(3600) == "1 hour ago"
        assert _humanize(7200) == "2 hours ago"
        assert _humanize(86399) == "23 hours ago"

    def test_days(self):
        assert _humanize(86400) == "1 day ago"
        assert _humanize(172800) == "2 days ago"


class TestStatus:
    def test_snapshot(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs)
            result = runner.invoke(status, [])
            assert result.exit_code == 0, result.output
            assert "My App  (org.example.myapp)" in result.output
            assert "Python:     3.15.0" in result.output
            assert "Lock:       in sync" in result.output
            assert "not built" in result.output

    def test_lock_missing(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs, lock=False)
            result = runner.invoke(status, [])
            assert result.exit_code == 0
            assert "missing" in result.output

    def test_lock_unreadable(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs, lock=False)
            # Valid TOML but missing [tool.kivy_ios] → LockError from reader
            (Path(fs) / "pylock.ios.toml").write_text("lock-version = '1.0'\n")
            result = runner.invoke(status, [])
            assert result.exit_code == 0
            assert "unreadable" in result.output

    def test_config_error_exits_nonzero(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            # Write a pyproject.toml missing required ios fields
            (Path(fs) / "pyproject.toml").write_text(
                "[project]\nname='x'\nversion='1'\n"
            )
            (Path(fs) / "src").mkdir()
            result = runner.invoke(status, [])
            assert result.exit_code != 0

    def test_no_pyproject_exits_nonzero(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(status, [])
            assert result.exit_code != 0

    def test_built_app_shows_age(self, runner, tmp_path, monkeypatch):
        import time

        fixed_time = 1_000_000.0
        monkeypatch.setattr(time, "time", lambda: fixed_time)
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs)
            # Create a fake built app directory
            app_path = (
                Path(fs)
                / "myapp-ios"
                / "build"
                / "DerivedData"
                / "Build"
                / "Products"
                / "Debug-iphonesimulator"
                / "myapp.app"
            )
            app_path.mkdir(parents=True)
            import os

            os.utime(app_path, (fixed_time - 120, fixed_time - 120))
            result = runner.invoke(status, [])
            assert result.exit_code == 0, result.output
            assert "minute" in result.output


class TestClean:
    def test_removes_staging(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs)
            (Path(fs) / "myapp-ios").mkdir()
            (Path(fs) / "myapp-ios" / "x.txt").write_text("x")
            result = runner.invoke(clean, [])
            assert result.exit_code == 0, result.output
            assert not (Path(fs) / "myapp-ios").exists()
            assert "Removed myapp-ios/" in result.output

    def test_nothing_to_clean(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs)
            result = runner.invoke(clean, [])
            assert result.exit_code == 0
            assert "Nothing to clean" in result.output

    def test_cache_flush(self, runner, tmp_path, monkeypatch):
        cleared = []

        class FakeCache:
            def clear(self):
                cleared.append(True)

        monkeypatch.setattr(
            "kivy_ios.cli.clean.ArtifactCache", lambda *a, **k: FakeCache()
        )
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs)
            result = runner.invoke(clean, ["--cache"])
            assert result.exit_code == 0
            assert cleared == [True]

    def test_cache_only_without_pyproject(self, runner, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "kivy_ios.cli.clean.ArtifactCache",
            lambda *a, **k: type("C", (), {"clear": lambda self: None})(),
        )
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(clean, ["--cache"])
            assert result.exit_code == 0


class TestUpgrade:
    def test_refreshes_python_and_xcframeworks(self, runner, tmp_path, monkeypatch):
        fetched = []

        def fake_fetch(*, name, sha256, filename, url=None, **kw):
            fetched.append(name)
            return Path("/cache") / filename

        monkeypatch.setattr(upgrade_mod, "fetch_artifact", fake_fetch)
        xc = LockedXcframework(
            name="SDL3",
            version="3.0.0",
            sha256="a" * 64,
            slices=("ios-arm64",),
            url="https://example/SDL3.zip",
        )
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs, xcframeworks=[xc])
            result = runner.invoke(upgrade, [])
            assert result.exit_code == 0, result.output
            assert "Python.xcframework" in fetched
            assert "SDL3" in fetched
            assert "Refreshed 2 artifact(s)" in result.output

    def test_python_only(self, runner, tmp_path, monkeypatch):
        fetched = []
        monkeypatch.setattr(
            upgrade_mod,
            "fetch_artifact",
            lambda *, name, **kw: fetched.append(name) or Path("/x"),
        )
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs)
            result = runner.invoke(upgrade, ["--python"])
            assert result.exit_code == 0
            assert fetched == ["Python.xcframework"]

    def test_skips_vendored_xcframework(self, runner, tmp_path, monkeypatch):
        fetched = []
        monkeypatch.setattr(
            upgrade_mod,
            "fetch_artifact",
            lambda *, name, **kw: fetched.append(name) or Path("/x"),
        )
        xc = LockedXcframework(
            name="Local",
            version="1",
            sha256="a" * 64,
            slices=("ios-arm64",),
            path="vendor/Local.zip",
        )
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs, xcframeworks=[xc])
            result = runner.invoke(upgrade, ["--xcframeworks"])
            assert result.exit_code == 0
            assert "Local" not in fetched
            assert "Skipped 1 vendored" in result.output

    def test_missing_lock_errors(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs, lock=False)
            result = runner.invoke(upgrade, [])
            assert result.exit_code != 0
            assert "toolchain lock" in result.output


class TestDoctor:
    def test_environment_mode_no_pyproject(self, runner, tmp_path, monkeypatch):
        from tests.doctor.conftest import FakeProbe

        monkeypatch.setattr(doctor_mod, "RealProbe", lambda: FakeProbe())
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(doctor, ["--offline"])
            assert "environment mode" in result.output
            assert "SKIP" in result.output

    def test_project_mode_fail_exits_nonzero(self, runner, tmp_path, monkeypatch):
        from tests.doctor.conftest import FakeProbe

        monkeypatch.setattr(doctor_mod, "RealProbe", lambda: FakeProbe(xcode=None))
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            _write(fs)
            result = runner.invoke(doctor, ["--offline"])
            assert "project mode" in result.output
            assert result.exit_code != 0
