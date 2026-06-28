"""Phase 2 — SPM resolver pure helpers + backend selection (spec 07)."""

from __future__ import annotations

from pathlib import Path

import pytest

from kivy_ios.config.model import SwiftPackageDep
from kivy_ios.lock.spm import (
    SpmResolverError,
    XcodeSpmResolver,
    _match_pin,
    _normalize_git_url,
    _Pin,
    get_spm_resolver,
    package_clause,
    parse_package_resolved,
    render_manifest,
)


def _pkg(requirement, url="https://github.com/x/foo.git"):
    return SwiftPackageDep(
        name="Foo", products=("Foo",), url=url, requirement=requirement
    )


class TestPackageClause:
    @pytest.mark.parametrize(
        "requirement,expected",
        [
            ({"exact": "1.2.3"}, 'exact: "1.2.3"'),
            ({"from": "1.2.3"}, 'from: "1.2.3"'),
            ({"up_to_next_minor": "1.2.3"}, '.upToNextMinor(from: "1.2.3")'),
            ({"range": ["1.0.0", "2.0.0"]}, '"1.0.0"..<"2.0.0"'),
            ({"branch": "main"}, 'branch: "main"'),
            ({"revision": "abc123"}, 'revision: "abc123"'),
        ],
    )
    def test_each_rule_kind(self, requirement, expected):
        clause = package_clause(_pkg(requirement))
        assert clause.startswith('.package(url: "https://github.com/x/foo.git"')
        assert expected in clause

    def test_escapes_quotes_in_url(self):
        clause = package_clause(_pkg({"from": "1.0.0"}, url='https://x/a"b.git'))
        assert '\\"' in clause

    def test_local_package_is_not_renderable(self):
        local = SwiftPackageDep(name="L", products=("L",), path="vendor/L")
        with pytest.raises(SpmResolverError):
            package_clause(local)


class TestRenderManifest:
    def test_lists_every_remote_dependency(self):
        manifest = render_manifest(
            [
                _pkg({"from": "1.0.0"}, url="https://x/a.git"),
                SwiftPackageDep(
                    name="B",
                    products=("B",),
                    url="https://x/b.git",
                    requirement={"exact": "2.0.0"},
                ),
            ]
        )
        assert "swift-tools-version:5.9" in manifest
        assert "https://x/a.git" in manifest
        assert "https://x/b.git" in manifest
        assert manifest.count(".package(url:") == 2


class TestParsePackageResolved:
    def test_v2_top_level_pins(self):
        text = """
        {
          "pins": [
            {
              "identity": "sentry-cocoa",
              "location": "https://github.com/getsentry/sentry-cocoa",
              "state": { "revision": "deadbeef", "version": "8.49.0" }
            }
          ],
          "version": 2
        }
        """
        pins = parse_package_resolved(text)
        assert len(pins) == 1
        assert pins[0].revision == "deadbeef"
        assert pins[0].version == "8.49.0"

    def test_v1_nested_pins_repository_url(self):
        text = """
        {
          "object": {
            "pins": [
              {
                "package": "Sentry",
                "repositoryURL": "https://github.com/getsentry/sentry-cocoa.git",
                "state": { "revision": "cafe", "version": "8.0.0" }
              }
            ]
          },
          "version": 1
        }
        """
        pins = parse_package_resolved(text)
        assert pins[0].url.endswith("sentry-cocoa.git")
        assert pins[0].revision == "cafe"

    def test_branch_pin_without_version(self):
        text = """
        {"pins": [{"location": "https://x/a", "state": {"revision": "ff"}}], "version": 2}
        """
        pins = parse_package_resolved(text)
        assert pins[0].version is None
        assert pins[0].revision == "ff"

    def test_pins_without_revision_are_dropped(self):
        text = '{"pins": [{"location": "https://x/a", "state": {}}], "version": 2}'
        assert parse_package_resolved(text) == []


class TestUrlMatching:
    @pytest.mark.parametrize(
        "a,b",
        [
            ("https://github.com/x/Foo.git", "https://github.com/x/foo"),
            ("https://github.com/x/foo/", "https://github.com/x/foo"),
            ("https://github.com/x/foo.git/", "https://github.com/x/foo"),
        ],
    )
    def test_normalize_equates_variants(self, a, b):
        assert _normalize_git_url(a) == _normalize_git_url(b)

    def test_match_pin_ignores_dot_git_and_case(self):
        pins = [
            _Pin(url="https://github.com/X/Foo.git", revision="rr", version="1.0.0")
        ]
        match = _match_pin(pins, "https://github.com/x/foo")
        assert match is not None and match.revision == "rr"

    def test_match_pin_returns_none_when_absent(self):
        pins = [_Pin(url="https://x/a", revision="r", version=None)]
        assert _match_pin(pins, "https://x/b") is None


class TestBackendSelection:
    def test_default_backend(self):
        assert isinstance(get_spm_resolver(), XcodeSpmResolver)

    def test_unknown_backend(self):
        with pytest.raises(SpmResolverError, match="unknown SPM resolver backend"):
            get_spm_resolver("nope")


class TestMissingToolchain:
    def test_missing_swift_executable_raises(self, tmp_path: Path):
        resolver = XcodeSpmResolver(swift_executable="definitely-not-a-real-binary-xyz")
        pkg = _pkg({"from": "1.0.0"})
        with pytest.raises(SpmResolverError, match="Swift toolchain is required"):
            resolver.resolve([pkg], project_root=tmp_path)

    def test_no_remote_packages_returns_empty(self, tmp_path: Path):
        resolver = XcodeSpmResolver(swift_executable="definitely-not-a-real-binary-xyz")
        local = SwiftPackageDep(name="L", products=("L",), path="vendor/L")
        # No remote packages → resolver short-circuits, never invokes swift.
        assert resolver.resolve([local], project_root=tmp_path) == []
