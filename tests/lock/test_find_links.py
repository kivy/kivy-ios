"""find_links validation before pip resolution."""

from __future__ import annotations

import pytest

from kivy_ios.config import load_config_from_text
from kivy_ios.lock import BuildError, build_lockfile
from kivy_ios.lock.find_links import FindLinksError, validate_find_links

from .conftest import FakePythonProvider, FakeResolver


def _toml_with_find_links(find_links: str) -> str:
    return (
        "[project]\nname='a'\nversion='1'\ndependencies=['kivy']\n"
        "[tool.kivy]\napp_dir='src'\n[tool.kivy.ios]\nschema_version=1\n"
        f"bundle_id='o.x.a'\nfind_links={find_links}\n"
        "[tool.kivy.ios.python]\nversion='3.15.0'"
    )


class TestValidateFindLinks:
    def test_missing_directory(self, tmp_path):
        with pytest.raises(FindLinksError, match="does not exist"):
            validate_find_links(tmp_path, ("wheels",))

    def test_empty_directory(self, tmp_path):
        (tmp_path / "wheels").mkdir()
        with pytest.raises(FindLinksError, match="no .whl files"):
            validate_find_links(tmp_path, ("wheels",))

    def test_directory_with_wheels_passes(self, tmp_path):
        wheels = tmp_path / "wheels"
        wheels.mkdir()
        (wheels / "kivy-1.whl").write_bytes(b"whl")
        validate_find_links(tmp_path, ("wheels",))

    def test_sibling_directory_allowed(self, tmp_path):
        app = tmp_path / "hello-kivy"
        shared = tmp_path / "wheels"
        app.mkdir()
        shared.mkdir()
        (shared / "kivy-1.whl").write_bytes(b"whl")
        validate_find_links(app, ("../wheels",))


class TestBuildUsesFindLinksValidation:
    def test_lock_fails_before_resolver_when_find_links_missing(self, tmp_path):
        resolver = FakeResolver()
        toml = _toml_with_find_links('["wheels"]')
        cfg = load_config_from_text(toml)
        with pytest.raises(BuildError, match="does not exist"):
            build_lockfile(
                cfg,
                toml,
                project_root=tmp_path,
                resolver=resolver,
                python_provider=FakePythonProvider(),
            )
        assert resolver.calls == []

    def test_normalize_sibling_wheel_path(self, tmp_path):
        from kivy_ios.lock.builder import _normalize_wheel_source

        app = tmp_path / "app"
        shared = tmp_path / "wheels"
        app.mkdir()
        shared.mkdir()
        wheel = shared / "kivy-1.whl"
        wheel.write_bytes(b"whl")
        _, path = _normalize_wheel_source(wheel.as_uri(), project_root=app)
        assert path == "../wheels/kivy-1.whl"
