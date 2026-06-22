"""Phase 3 — lock builder: slice pinning, drift, floor check, fail-fast (spec 02)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kivy_ios.config import load_config_from_text
from kivy_ios.lock import BuildError, build_lockfile, dumps, loads, semantic_equal
from kivy_ios.lock.reader import compute_pyproject_sha256, is_in_sync
from tests.lock.conftest import FakeResolver


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


class TestSimulatorArchs:
    _ARM64_ONLY = (
        "[project]\nname='a'\nversion='1'\ndependencies=['kivy']\n"
        "[tool.kivy]\napp_dir='src'\n[tool.kivy.ios]\nschema_version=1\n"
        "bundle_id='o.x.a'\nsimulator_archs=['arm64']\n"
        "[tool.kivy.ios.python]\nversion='3.15.0'"
    )

    def test_arm64_only_passes_resolver_archs(
        self, fake_resolver, fake_python_provider
    ):
        _build(self._ARM64_ONLY, fake_resolver, fake_python_provider)
        assert fake_resolver.calls[0]["simulator_archs"] == ("arm64",)

    def test_arm64_only_pins_two_slices(self, fake_resolver, fake_python_provider):
        lock = _build(self._ARM64_ONLY, fake_resolver, fake_python_provider)
        kivy = next(p for p in lock.packages if p.name == "kivy")
        tags = {w.platform_tag for w in kivy.wheels}
        assert tags == {
            "ios_13_0_arm64_iphoneos",
            "ios_13_0_arm64_iphonesimulator",
        }

    def test_arm64_only_does_not_require_x86_64(self, fake_python_provider):
        # A resolver that has no x86_64 slice at all must still satisfy an
        # arm64-only project (the dropped slice isn't a targeted one).
        from tests.lock.conftest import FakeResolver

        resolver = FakeResolver(drop_slice="ios_13_0_x86_64_iphonesimulator")
        lock = _build(self._ARM64_ONLY, resolver, fake_python_provider)
        kivy = next(p for p in lock.packages if p.name == "kivy")
        assert {w.platform_tag for w in kivy.wheels} == {
            "ios_13_0_arm64_iphoneos",
            "ios_13_0_arm64_iphonesimulator",
        }


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


_SWIFT_BASE = (
    "[project]\nname='a'\nversion='1'\ndependencies=[]\n"
    "[tool.kivy]\napp_dir='src'\n[tool.kivy.ios]\nschema_version=1\n"
    "bundle_id='o.x.a'\n[tool.kivy.ios.python]\nversion='3.15.0'\n"
)


class TestSwiftPackages:
    _REMOTE_AND_LOCAL = _SWIFT_BASE + (
        "[tool.kivy.ios.native.swift_packages]\n"
        'Sentry = { url = "https://github.com/getsentry/sentry-cocoa", '
        'requirement = { from = "8.49.0" }, products = ["Sentry"] }\n'
        'MyKit = { path = "vendor/MyKit", products = ["MyKit"], embed = false }\n'
    )

    def test_remote_pinned_and_local_passthrough(
        self, fake_spm_resolver, fake_python_provider
    ):
        lock = _build(
            self._REMOTE_AND_LOCAL,
            FakeResolver(),
            fake_python_provider,
            spm_resolver=fake_spm_resolver,
        )
        by_name = {s.name: s for s in lock.swift_packages}
        sentry = by_name["Sentry"]
        assert sentry.url == "https://github.com/getsentry/sentry-cocoa"
        assert sentry.requirement == {"from": "8.49.0"}
        assert sentry.revision and sentry.version == "9.9.9"
        assert sentry.products == ("Sentry",)

        mykit = by_name["MyKit"]
        assert mykit.path == "vendor/MyKit"
        assert mykit.requirement is None
        assert mykit.revision is None and mykit.version is None
        assert mykit.embed is False

    def test_only_remote_packages_reach_resolver(
        self, fake_spm_resolver, fake_python_provider
    ):
        _build(
            self._REMOTE_AND_LOCAL,
            FakeResolver(),
            fake_python_provider,
            spm_resolver=fake_spm_resolver,
        )
        assert fake_spm_resolver.calls[0]["names"] == ["Sentry"]

    def test_sorted_by_name(self, fake_spm_resolver, fake_python_provider):
        toml = _SWIFT_BASE + (
            "[tool.kivy.ios.native.swift_packages]\n"
            'Zeta = { path = "vendor/Zeta", products = ["Zeta"] }\n'
            'Alpha = { path = "vendor/Alpha", products = ["Alpha"] }\n'
        )
        lock = _build(
            toml, FakeResolver(), fake_python_provider, spm_resolver=fake_spm_resolver
        )
        assert [s.name for s in lock.swift_packages] == ["Alpha", "Zeta"]

    def test_local_only_never_builds_resolver(self, fake_python_provider):
        # No spm_resolver passed and no remote packages: must not need a toolchain.
        toml = _SWIFT_BASE + (
            "[tool.kivy.ios.native.swift_packages]\n"
            'MyKit = { path = "vendor/MyKit", products = ["MyKit"] }\n'
        )
        lock = _build(toml, FakeResolver(), fake_python_provider)
        assert len(lock.swift_packages) == 1
        assert lock.swift_packages[0].revision is None

    def test_resolver_error_becomes_build_error(self, fake_python_provider):
        from kivy_ios.lock.spm import SpmResolverError

        class Boom:
            def resolve(self, packages, *, project_root, offline=False):
                raise SpmResolverError("swift exploded")

        with pytest.raises(BuildError, match="swift exploded"):
            _build(
                self._REMOTE_AND_LOCAL,
                FakeResolver(),
                fake_python_provider,
                spm_resolver=Boom(),
            )

    def test_round_trip_preserves_swift_packages(
        self, fake_spm_resolver, fake_python_provider
    ):
        lock = _build(
            self._REMOTE_AND_LOCAL,
            FakeResolver(),
            fake_python_provider,
            spm_resolver=fake_spm_resolver,
        )
        text = dumps(lock)
        reloaded = loads(text)
        assert semantic_equal(lock, reloaded)
        assert dumps(reloaded) == text
        assert {s.name for s in reloaded.swift_packages} == {"Sentry", "MyKit"}

    def test_range_requirement_round_trips(
        self, fake_spm_resolver, fake_python_provider
    ):
        toml = _SWIFT_BASE + (
            "[tool.kivy.ios.native.swift_packages]\n"
            'Foo = { url = "https://example.com/foo.git", '
            'requirement = { range = ["1.0.0", "2.0.0"] }, products = ["Foo"] }\n'
        )
        lock = _build(
            toml, FakeResolver(), fake_python_provider, spm_resolver=fake_spm_resolver
        )
        reloaded = loads(dumps(lock))
        (foo,) = reloaded.swift_packages
        assert foo.requirement == {"range": ["1.0.0", "2.0.0"]}


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
