"""Fixtures for project-generation tests."""

from __future__ import annotations

import textwrap

import pytest

from kivy_ios.config import load_config_from_text


def _cfg(extra: str = "") -> str:
    return textwrap.dedent(
        f"""
        [project]
        name = "touchtracer"
        version = "1.2.3"
        dependencies = ["kivy"]

        [tool.kivy]
        display_name = "Touch Tracer"
        app_dir = "src"
        entry_point = "main"
        orientation = ["portrait", "landscape-left"]

        [tool.kivy.ios]
        schema_version = 1
        bundle_id = "org.kivy.touchtracer"
        build = 7
        deployment_target = "13.0"

        [tool.kivy.ios.python]
        version = "3.15.0"

        [tool.kivy.ios.signing]
        team_id = "ABCDE12345"
        auto_signing = true
        {extra}
        """
    ).strip()


@pytest.fixture
def config():
    return load_config_from_text(_cfg())


@pytest.fixture
def make_config():
    return lambda extra="": load_config_from_text(_cfg(extra))


@pytest.fixture
def project_root(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n")
    return tmp_path
