"""Phase 3 — Swift package wiring into the generated .xcodeproj (spec 07)."""

from __future__ import annotations

import json

import pytest
from pbxproj import XcodeProject

from kivy_ios.lock.model import LockedSwiftPackage
from kivy_ios.project.materialize import materialize_project
from kivy_ios.project.swift_packages import (
    package_resolved_json,
    xcode_requirement,
)

REMOTE = LockedSwiftPackage(
    name="Sentry",
    products=("Sentry",),
    url="https://github.com/getsentry/sentry-cocoa",
    requirement={"from": "8.49.0"},
    revision="a" * 40,
    version="8.49.0",
)
LOCAL = LockedSwiftPackage(
    name="MyKit",
    products=("MyKit",),
    path="vendor/MyKit",
)


def _materialize(config, project_root, packages):
    layout = materialize_project(config, project_root, swift_packages=tuple(packages))
    project = XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))
    return layout, project


def _section(project, name):
    return list(project.objects.get_objects_in_section(name))


def _dep_id(project, product_name):
    for dep in _section(project, "XCSwiftPackageProductDependency"):
        if dep["productName"] == product_name:
            return dep.get_id()
    return None


def _build_files_for(project, section, dep_id):
    out = []
    for phase in _section(project, section):
        for bf_id in phase["files"]:
            bf = project.objects[bf_id]
            if "productRef" in bf and bf["productRef"] == dep_id:
                out.append(bf)
    return out


def _resolved_path(layout):
    return (
        layout.xcodeproj
        / "project.xcworkspace"
        / "xcshareddata"
        / "swiftpm"
        / "Package.resolved"
    )


class TestRemotePackage:
    def test_creates_reference_and_product_dependency(self, config, project_root):
        _, project = _materialize(config, project_root, [REMOTE])
        refs = _section(project, "XCRemoteSwiftPackageReference")
        assert len(refs) == 1
        assert refs[0]["repositoryURL"] == "https://github.com/getsentry/sentry-cocoa"
        assert refs[0]["requirement"]["kind"] == "upToNextMajorVersion"
        assert refs[0]["requirement"]["minimumVersion"] == "8.49.0"
        assert _dep_id(project, "Sentry") is not None

    def test_links_and_embeds_product(self, config, project_root):
        _, project = _materialize(config, project_root, [REMOTE])
        dep_id = _dep_id(project, "Sentry")
        link = _build_files_for(project, "PBXFrameworksBuildPhase", dep_id)
        embed = _build_files_for(project, "PBXCopyFilesBuildPhase", dep_id)
        assert len(link) == 1
        assert len(embed) == 1
        assert "CodeSignOnCopy" in embed[0]["settings"]["ATTRIBUTES"]

    def test_writes_package_resolved(self, config, project_root):
        layout, _ = _materialize(config, project_root, [REMOTE])
        data = json.loads(_resolved_path(layout).read_text())
        assert data["version"] == 2
        (pin,) = data["pins"]
        assert pin["identity"] == "sentry-cocoa"
        assert pin["location"] == "https://github.com/getsentry/sentry-cocoa"
        assert pin["state"]["revision"] == "a" * 40
        assert pin["state"]["version"] == "8.49.0"

    def test_target_lists_product_dependency(self, config, project_root):
        _, project = _materialize(config, project_root, [REMOTE])
        target = project.get_target_by_name("touchtracer")
        dep_id = _dep_id(project, "Sentry")
        assert dep_id in target["packageProductDependencies"]


class TestLocalPackage:
    def test_creates_local_reference(self, config, project_root):
        _, project = _materialize(config, project_root, [LOCAL])
        refs = _section(project, "XCLocalSwiftPackageReference")
        assert len(refs) == 1
        assert refs[0]["relativePath"] == "vendor/MyKit"
        assert _dep_id(project, "MyKit") is not None

    def test_no_package_resolved_for_local_only(self, config, project_root):
        layout, _ = _materialize(config, project_root, [LOCAL])
        assert not _resolved_path(layout).exists()


class TestEmbedAndLinkFlags:
    def test_embed_false_skips_embed_phase(self, config, project_root):
        pkg = LockedSwiftPackage(
            name="MyKit", products=("MyKit",), path="vendor/MyKit", embed=False
        )
        _, project = _materialize(config, project_root, [pkg])
        dep_id = _dep_id(project, "MyKit")
        assert _build_files_for(project, "PBXFrameworksBuildPhase", dep_id)
        assert not _build_files_for(project, "PBXCopyFilesBuildPhase", dep_id)

    def test_link_false_skips_frameworks_phase(self, config, project_root):
        pkg = LockedSwiftPackage(
            name="MyKit",
            products=("MyKit",),
            path="vendor/MyKit",
            link=False,
            embed=True,
        )
        _, project = _materialize(config, project_root, [pkg])
        dep_id = _dep_id(project, "MyKit")
        assert not _build_files_for(project, "PBXFrameworksBuildPhase", dep_id)
        assert _build_files_for(project, "PBXCopyFilesBuildPhase", dep_id)


class TestIdempotency:
    def test_second_run_no_duplicates(self, config, project_root):
        _materialize(config, project_root, [REMOTE, LOCAL])
        _, project = _materialize(config, project_root, [REMOTE, LOCAL])
        assert len(_section(project, "XCRemoteSwiftPackageReference")) == 1
        assert len(_section(project, "XCLocalSwiftPackageReference")) == 1
        assert len(_section(project, "XCSwiftPackageProductDependency")) == 2
        dep_id = _dep_id(project, "Sentry")
        assert len(_build_files_for(project, "PBXFrameworksBuildPhase", dep_id)) == 1
        assert len(_build_files_for(project, "PBXCopyFilesBuildPhase", dep_id)) == 1


class TestPruning:
    def test_removed_package_is_pruned(self, config, project_root):
        _materialize(config, project_root, [REMOTE, LOCAL])
        _, project = _materialize(config, project_root, [REMOTE])
        assert len(_section(project, "XCRemoteSwiftPackageReference")) == 1
        assert _section(project, "XCLocalSwiftPackageReference") == []
        assert _dep_id(project, "MyKit") is None
        assert _dep_id(project, "Sentry") is not None

    def test_package_resolved_removed_when_no_remote(self, config, project_root):
        layout, _ = _materialize(config, project_root, [REMOTE])
        assert _resolved_path(layout).exists()
        layout, _ = _materialize(config, project_root, [LOCAL])
        assert not _resolved_path(layout).exists()

    def test_requirement_updates_on_relock(self, config, project_root):
        _materialize(config, project_root, [REMOTE])
        changed = LockedSwiftPackage(
            name="Sentry",
            products=("Sentry",),
            url="https://github.com/getsentry/sentry-cocoa",
            requirement={"exact": "8.50.0"},
            revision="b" * 40,
            version="8.50.0",
        )
        _, project = _materialize(config, project_root, [changed])
        (ref,) = _section(project, "XCRemoteSwiftPackageReference")
        assert ref["requirement"]["kind"] == "exactVersion"
        assert ref["requirement"]["version"] == "8.50.0"


class TestXcodeRequirement:
    @pytest.mark.parametrize(
        "rule,expected",
        [
            ({"exact": "1.2.3"}, {"kind": "exactVersion", "version": "1.2.3"}),
            (
                {"from": "1.2.3"},
                {"kind": "upToNextMajorVersion", "minimumVersion": "1.2.3"},
            ),
            (
                {"up_to_next_minor": "1.2.3"},
                {"kind": "upToNextMinorVersion", "minimumVersion": "1.2.3"},
            ),
            (
                {"range": ["1.0.0", "2.0.0"]},
                {
                    "kind": "versionRange",
                    "minimumVersion": "1.0.0",
                    "maximumVersion": "2.0.0",
                },
            ),
            ({"branch": "main"}, {"kind": "branch", "branch": "main"}),
            ({"revision": "deadbeef"}, {"kind": "revision", "revision": "deadbeef"}),
        ],
    )
    def test_maps_each_rule(self, rule, expected):
        assert xcode_requirement(rule) == expected

    def test_empty_rule_raises(self):
        with pytest.raises(ValueError, match="missing a requirement"):
            xcode_requirement({})


class TestPackageResolvedJson:
    def test_sorted_by_identity_and_optional_version(self):
        pkgs = (
            LockedSwiftPackage(
                name="Z",
                products=("Z",),
                url="https://x/zeta.git",
                requirement={"branch": "main"},
                revision="f" * 40,
            ),
            LockedSwiftPackage(
                name="A",
                products=("A",),
                url="https://x/alpha",
                requirement={"from": "1.0.0"},
                revision="0" * 40,
                version="1.0.0",
            ),
        )
        data = json.loads(package_resolved_json(pkgs))
        assert [p["identity"] for p in data["pins"]] == ["alpha", "zeta"]
        # branch pin has no resolved semantic version
        assert "version" not in data["pins"][1]["state"]
        assert data["pins"][0]["state"]["version"] == "1.0.0"

    def test_local_packages_excluded(self):
        data = json.loads(package_resolved_json((LOCAL,)))
        assert data["pins"] == []
