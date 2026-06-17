"""Phase 0 — CWD-only pyproject discovery."""

from __future__ import annotations

import pytest

from kivy_ios.cli._common import ToolchainError, find_pyproject, lockfile_path


def test_find_pyproject_in_cwd(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    assert find_pyproject(tmp_path) == tmp_path / "pyproject.toml"


def test_find_pyproject_missing_raises(tmp_path):
    with pytest.raises(ToolchainError) as exc:
        find_pyproject(tmp_path)
    assert "no pyproject.toml" in str(exc.value)


def test_find_pyproject_no_parent_traversal(tmp_path):
    # A pyproject in the parent must NOT be discovered from a child dir.
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    child = tmp_path / "child"
    child.mkdir()
    with pytest.raises(ToolchainError):
        find_pyproject(child)


def test_lockfile_path(tmp_path):
    assert lockfile_path(tmp_path) == tmp_path / "pylock.ios.toml"
