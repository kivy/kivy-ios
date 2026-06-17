"""Phase 3 — lock builder: slice pinning, drift, floor check, fail-fast (spec 02)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kivy_ios.config import load_config_from_text
from kivy_ios.lock import BuildError, build_lockfile, dumps, loads, semantic_equal
from kivy_ios.lock.reader import compute_pyproject_sha256, is_in_sync


def _build(toml, resolver, provider, **kw):
    cfg = load_config_from_text(toml)
    return build_lockfile(cfg, toml, resolver=resolver, python_provider=provider, **kw)


class TestBuild:
    def test_pins_all_three_slices_for_compiled(
        self, minimal_pyproject, fake_resolver, fake_python_provider
    ):
        lock = _build(minimal_pyproject, fake_resolver, fake_python_provider)
        kivy = next(p for p in lock.packages if p.name == "kivy")
        tags = {w.platform_tag for w in kivy.wheels}
        assert tags == {
            "ios_13_0_arm64_iphoneos",
            "ios_13_0_arm64_iphonesimulator",
            "ios_13_0_x86_64_iphonesimulator",
        }

    def test_pure_python_single_wheel(
        self, minimal_pyproject, fake_resolver, fake_python_provider
    ):
        lock = _build(minimal_pyproject, fake_resolver, fake_python_provider)
        mi = next(p for p in lock.packages if p.name == "more-itertools")
        assert len(mi.wheels) == 1
        assert mi.wheels[0].is_pure_python

    def test_direct_requirement_marking(
        self, minimal_pyproject, fake_resolver, fake_python_provider
    ):
        lock = _build(minimal_pyproject, fake_resolver, fake_python_provider)
        assert all(p.direct_requirement for p in lock.packages)

    def test_python_xcframework_pinned(
        self, minimal_pyproject, fake_resolver, fake_python_provider
    ):
        lock = _build(minimal_pyproject, fake_resolver, fake_python_provider)
        assert lock.python_xcframework.version == "3.15.0"
        assert lock.python_xcframework.sha256 == "c" * 64

    def test_resolver_receives_extra_index_urls(
        self, fake_resolver, fake_python_provider
    ):
        toml = (
            "[project]\nname='a'\nversion='1'\ndependencies=['kivy']\n"
            "[tool.kivy]\napp_dir='src'\n[tool.kivy.ios]\nschema_version=1\n"
            "bundle_id='o.x.a'\nextra_index_urls=['https://wheels.example.com/simple']\n"
            "[tool.kivy.ios.python]\nversion='3.15.0'"
        )
        _build(toml, fake_resolver, fake_python_provider)
        assert fake_resolver.calls[0]["extra_index_urls"] == [
            "https://wheels.example.com/simple"
        ]

    def test_pyproject_sha_recorded(
        self, minimal_pyproject, fake_resolver, fake_python_provider
    ):
        lock = _build(minimal_pyproject, fake_resolver, fake_python_provider)
        assert lock.pyproject_sha256 == compute_pyproject_sha256(minimal_pyproject)


class TestFailFast:
    def test_missing_slice_fails(self, minimal_pyproject, fake_python_provider):
        from tests.lock.conftest import FakeResolver

        resolver = FakeResolver(drop_slice="ios_13_0_x86_64_iphonesimulator")
        with pytest.raises(BuildError, match="missing iOS wheel slice"):
            _build(minimal_pyproject, resolver, fake_python_provider)

    def test_deployment_target_below_floor(self, fake_resolver):
        from tests.lock.conftest import FakePythonProvider

        toml = (
            "[project]\nname='a'\nversion='1'\ndependencies=[]\n"
            "[tool.kivy]\napp_dir='src'\n[tool.kivy.ios]\nschema_version=1\n"
            "bundle_id='o.x.a'\ndeployment_target='12.0'\n"
            "[tool.kivy.ios.python]\nversion='3.15.0'"
        )
        with pytest.raises(BuildError, match="below the minimum iOS"):
            _build(toml, fake_resolver, FakePythonProvider(floor="13.0"))


class TestDriftAndCheck:
    def test_in_sync_detection(
        self, minimal_pyproject, fake_resolver, fake_python_provider
    ):
        lock = _build(minimal_pyproject, fake_resolver, fake_python_provider)
        assert is_in_sync(lock, minimal_pyproject)
        assert not is_in_sync(lock, minimal_pyproject + "\n# edited\n")

    def test_semantic_equal_ignores_timestamp(
        self, minimal_pyproject, fake_resolver, fake_python_provider
    ):
        a = _build(
            minimal_pyproject,
            fake_resolver,
            fake_python_provider,
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        b = _build(
            minimal_pyproject,
            fake_resolver,
            fake_python_provider,
            now=datetime(2026, 6, 1, tzinfo=UTC),
        )
        assert a.generated_at != b.generated_at
        assert semantic_equal(a, b)


class TestRoundTrip:
    def test_dumps_then_loads(
        self, minimal_pyproject, fake_resolver, fake_python_provider
    ):
        lock = _build(minimal_pyproject, fake_resolver, fake_python_provider)
        text = dumps(lock)
        reloaded = loads(text)
        assert semantic_equal(lock, reloaded)
        # second serialization is byte-identical (deterministic)
        assert dumps(reloaded) == text

    def test_deterministic_ordering(
        self, minimal_pyproject, fake_resolver, fake_python_provider
    ):
        lock = _build(minimal_pyproject, fake_resolver, fake_python_provider)
        text = dumps(lock)
        # kivy sorts before more-itertools; within kivy, iphoneos slice sorts
        # before the simulator slices by filename.
        assert text.index('name = "kivy"') < text.index('name = "more-itertools"')
