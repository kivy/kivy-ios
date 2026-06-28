"""Native xcframework link/embed wiring + stale-ref pruning in project gen."""

from __future__ import annotations

import plistlib

from pbxproj import XcodeProject
from pbxproj.pbxextensions.ProjectFiles import TreeType

from kivy_ios.lock.model import LockedXcframework
from kivy_ios.project.generator import XcodeProjectGenerator
from kivy_ios.project.materialize import materialize_project

EMBED_DST = "10"  # PBXCopyFilesBuildPhase dstSubfolderSpec for Embed Frameworks


def _make_xcframework(frameworks_dir, name):
    xc = frameworks_dir / f"{name}.xcframework"
    (xc / "ios-arm64").mkdir(parents=True)
    (xc / "ios-arm64" / name).write_text("binary")
    with open(xc / "Info.plist", "wb") as fh:
        plistlib.dump({"AvailableLibraries": [{"LibraryIdentifier": "ios-arm64"}]}, fh)
    return xc


def _locked(name, *, link, embed):
    return LockedXcframework(
        name=name,
        version="1.0.0",
        sha256="a" * 64,
        slices=("ios-arm64",),
        path=f"{name}.zip",
        link=link,
        embed=embed,
    )


def _ref_id(project, name):
    refs = project.get_files_by_path(
        f"Frameworks/{name}.xcframework", tree=TreeType.SOURCE_ROOT
    )
    return refs[0].get_id() if refs else None


def _phase_refs(project, target_name, isa, *, dst=None):
    target = project.get_target_by_name(target_name)
    out = []
    for pid in target.buildPhases:
        phase = project.get_object(pid)
        if phase.isa != isa:
            continue
        if dst is not None and getattr(phase, "dstSubfolderSpec", None) != dst:
            continue
        for bf_id in phase["files"]:
            bf = project.objects[bf_id]
            ref = bf["fileRef"] if "fileRef" in bf else None
            if ref:
                out.append(ref)
    return out


def _link_refs(project, target_name):
    return _phase_refs(project, target_name, "PBXFrameworksBuildPhase")


def _embed_refs(project, target_name):
    return _phase_refs(project, target_name, "PBXCopyFilesBuildPhase", dst=EMBED_DST)


def _regenerate(config, layout, xcframeworks=()):
    XcodeProjectGenerator(config, layout, xcframeworks=xcframeworks).generate()
    return XcodeProject.load(str(layout.xcodeproj / "project.pbxproj"))


class TestLinkEmbedIntent:
    def test_link_and_embed(self, config, project_root):
        layout = materialize_project(config, project_root)
        _make_xcframework(layout.frameworks, "Both")
        project = _regenerate(config, layout, (_locked("Both", link=True, embed=True),))
        ref = _ref_id(project, "Both")
        assert ref in _link_refs(project, "touchtracer")
        assert ref in _embed_refs(project, "touchtracer")

    def test_link_only(self, config, project_root):
        layout = materialize_project(config, project_root)
        _make_xcframework(layout.frameworks, "LinkOnly")
        project = _regenerate(
            config, layout, (_locked("LinkOnly", link=True, embed=False),)
        )
        ref = _ref_id(project, "LinkOnly")
        assert ref in _link_refs(project, "touchtracer")
        assert ref not in _embed_refs(project, "touchtracer")

    def test_embed_only(self, config, project_root):
        layout = materialize_project(config, project_root)
        _make_xcframework(layout.frameworks, "EmbedOnly")
        project = _regenerate(
            config, layout, (_locked("EmbedOnly", link=False, embed=True),)
        )
        ref = _ref_id(project, "EmbedOnly")
        assert ref not in _link_refs(project, "touchtracer")
        assert ref in _embed_refs(project, "touchtracer")

    def test_neither(self, config, project_root):
        layout = materialize_project(config, project_root)
        _make_xcframework(layout.frameworks, "RefOnly")
        project = _regenerate(
            config, layout, (_locked("RefOnly", link=False, embed=False),)
        )
        ref = _ref_id(project, "RefOnly")
        assert ref is not None  # still referenced in the navigator
        assert ref not in _link_refs(project, "touchtracer")
        assert ref not in _embed_refs(project, "touchtracer")

    def test_wheel_embedded_default_is_embed_and_sign(self, config, project_root):
        # No lock entry (SDL3/ANGLE ride inside wheels) -> Embed & Sign default.
        layout = materialize_project(config, project_root)
        _make_xcframework(layout.frameworks, "SDL3")
        project = _regenerate(config, layout, xcframeworks=())
        ref = _ref_id(project, "SDL3")
        assert ref in _link_refs(project, "touchtracer")
        assert ref in _embed_refs(project, "touchtracer")


class TestReconcileAndPrune:
    def test_flip_embed_off_removes_embed_build_file(self, config, project_root):
        layout = materialize_project(config, project_root)
        _make_xcframework(layout.frameworks, "Flip")
        project = _regenerate(config, layout, (_locked("Flip", link=True, embed=True),))
        assert _ref_id(project, "Flip") in _embed_refs(project, "touchtracer")

        # Re-lock with embed=False; the stale embed build file must be removed.
        project = _regenerate(
            config, layout, (_locked("Flip", link=True, embed=False),)
        )
        ref = _ref_id(project, "Flip")
        assert ref in _link_refs(project, "touchtracer")
        assert ref not in _embed_refs(project, "touchtracer")

    def test_stale_framework_pruned(self, config, project_root):
        import shutil

        layout = materialize_project(config, project_root)
        xc = _make_xcframework(layout.frameworks, "Gone")
        project = _regenerate(config, layout, (_locked("Gone", link=True, embed=True),))
        assert _ref_id(project, "Gone") is not None

        # Framework removed from disk -> reference and build files pruned.
        shutil.rmtree(xc)
        project = _regenerate(config, layout, xcframeworks=())
        assert _ref_id(project, "Gone") is None
        assert _embed_refs(project, "touchtracer") == []
        assert _link_refs(project, "touchtracer") == []

    def test_python_xcframework_not_pruned(self, config, project_root):
        # Pruning only targets Frameworks/*.xcframework, never the root
        # Python.xcframework reference.
        layout = materialize_project(config, project_root)
        layout.python_xcframework.mkdir(exist_ok=True)
        project = _regenerate(config, layout, xcframeworks=())
        assert project.get_files_by_name("Python.xcframework")
