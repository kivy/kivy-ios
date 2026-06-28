"""Phase 3 — toolchain lock CLI: write, in-sync no-op, --update, --check (spec 05)."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from kivy_ios.cli import lock as lock_cli
from kivy_ios.cli.lock import lock


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def patch_backends(monkeypatch, fake_resolver, fake_python_provider):
    """Make the CLI use the hermetic fakes instead of pip/python.org."""
    import kivy_ios.lock.builder as builder

    real_build = builder.build_lockfile

    def fake_build(
        config,
        text,
        *,
        project_root=None,
        resolver=None,
        python_provider=None,
        offline=False,
        now=None,
    ):
        return real_build(
            config,
            text,
            project_root=project_root,
            resolver=fake_resolver,
            python_provider=fake_python_provider,
            offline=offline,
            now=now,
        )

    monkeypatch.setattr(lock_cli, "build_lockfile", fake_build)
    return fake_resolver


class TestLockCli:
    def test_writes_lockfile(self, runner, tmp_path, minimal_pyproject):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            from pathlib import Path

            (Path(fs) / "pyproject.toml").write_text(minimal_pyproject + "\n")
            result = runner.invoke(lock, [])
            assert result.exit_code == 0, result.output
            assert (Path(fs) / "pylock.ios.toml").is_file()
            assert "packages pinned" in result.output

    def test_in_sync_noop(self, runner, tmp_path, minimal_pyproject):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            from pathlib import Path

            (Path(fs) / "pyproject.toml").write_text(minimal_pyproject + "\n")
            runner.invoke(lock, [])
            result = runner.invoke(lock, [])
            assert result.exit_code == 0
            assert "already in sync" in result.output

    def test_check_passes_when_in_sync(self, runner, tmp_path, minimal_pyproject):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            from pathlib import Path

            (Path(fs) / "pyproject.toml").write_text(minimal_pyproject + "\n")
            runner.invoke(lock, [])
            result = runner.invoke(lock, ["--check"])
            assert result.exit_code == 0, result.output
            assert "up to date" in result.output

    def test_check_fails_when_stale(self, runner, tmp_path, minimal_pyproject):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            from pathlib import Path

            pp = Path(fs) / "pyproject.toml"
            pp.write_text(minimal_pyproject + "\n")
            runner.invoke(lock, [])
            # edit pyproject so the recorded hash no longer matches
            pp.write_text(minimal_pyproject + "\n# changed\n")
            result = runner.invoke(lock, ["--check"])
            assert result.exit_code != 0
            assert "out of date" in result.output or "stale" in result.output

    def test_check_without_lock_errors(self, runner, tmp_path, minimal_pyproject):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            from pathlib import Path

            (Path(fs) / "pyproject.toml").write_text(minimal_pyproject + "\n")
            result = runner.invoke(lock, ["--check"])
            assert result.exit_code != 0
            assert "does not exist" in result.output

    def test_no_pyproject_errors(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(lock, [])
            assert result.exit_code != 0
            assert "no pyproject.toml" in result.output
