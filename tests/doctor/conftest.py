"""Fakes for doctor checks: a configurable Probe and a project config."""

from __future__ import annotations

import textwrap

import pytest

from kivy_ios.config import load_config_from_text


class FakeProbe:
    """A Probe whose every answer is set per test."""

    def __init__(self, **overrides):
        self._xcode = overrides.get("xcode", "16.0")
        self._select = overrides.get("select", "/Applications/Xcode.app")
        self._clang = overrides.get("clang", True)
        self._swift = overrides.get("swift", True)
        self._runtimes = overrides.get("runtimes", ["18.0"])
        self._latest = overrides.get("latest", None)
        self._identities = overrides.get("identities", [])
        self._reachable = overrides.get("reachable", True)
        self._platforms = overrides.get("platforms", {})
        self._pip = overrides.get("pip", "24.3.1")

    def xcode_version(self):
        return self._xcode

    def pip_version(self):
        return self._pip

    def xcode_select_path(self):
        return self._select

    def has_xcrun_clang(self):
        return self._clang

    def has_swift_toolchain(self):
        return self._swift

    def simulator_runtimes(self):
        return list(self._runtimes)

    def latest_toolchain_version(self):
        return self._latest

    def keychain_identities(self):
        return list(self._identities)

    def tcp_reachable(self, host, port):
        if isinstance(self._reachable, dict):
            return self._reachable.get(host, True)
        return self._reachable

    def binary_platforms(self, path):
        return set(self._platforms.get(path.name, set()))


@pytest.fixture
def fake_probe():
    return FakeProbe()


@pytest.fixture
def config():
    return load_config_from_text(
        textwrap.dedent(
            """
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
            """
        ).strip()
    )
