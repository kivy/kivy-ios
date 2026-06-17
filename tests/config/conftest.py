"""Shared fixtures for config tests."""

from __future__ import annotations

import textwrap

import pytest

VALID = textwrap.dedent(
    """
    [project]
    name = "touchtracer"
    version = "1.0.0"
    description = "Touchtracer demo"
    requires-python = ">=3.13"
    dependencies = ["kivy>=3.0,<4"]
    authors = [{ name = "Kivy Team", email = "team@kivy.org" }]

    [tool.kivy]
    display_name = "Touchtracer"
    app_dir = "src"
    entry_point = "main"
    orientation = ["portrait", "landscape-left"]

    [tool.kivy.ios]
    schema_version = 1
    bundle_id = "org.kivy.touchtracer"
    build = 1
    deployment_target = "13.0"
    extra_index_urls = ["https://wheels.example.com/simple"]

    [tool.kivy.ios.python]
    version = "3.15.0"

    [tool.kivy.ios.icons]
    source = "assets/icon.png"

    [tool.kivy.ios.splash]
    source = "assets/splash.png"
    background = "#000000"

    [tool.kivy.ios.signing]
    team_id = "ABCDE12345"
    auto_signing = true
    """
).strip()


@pytest.fixture
def valid_toml() -> str:
    return VALID
