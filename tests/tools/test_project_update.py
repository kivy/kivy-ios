"""Real saved-project maintenance checks, with only build discovery replaced."""
from pathlib import Path
import shutil
from types import SimpleNamespace

from pbxproj import XcodeProject
import pytest

from kivy_ios import toolchain


FIXTURE = Path(__file__).parent / "fixtures" / "legacy_mrc"
COMPILER_SETTINGS = ("CLANG_ENABLE_OBJC_ARC", "CLANG_ENABLE_MODULES")
CHECKED_SETTINGS = COMPILER_SETTINGS + ("CI_CUSTOM_SETTING",)


@pytest.fixture
def legacy_project(tmp_path, monkeypatch):
    directory = tmp_path / "legacy_mrc"
    shutil.copytree(FIXTURE, directory)
    sources = [directory / name for name in ("main.m", "bridge.m")]
    for path in sources:
        with path.open("ab") as stream:
            stream.write(b"\n// CI native customization: keep my startup edits.\n")
    source_bytes = {path: path.read_bytes() for path in sources}
    monkeypatch.setattr(
        toolchain, "Context",
        lambda: SimpleNamespace(state={}, dist_dir=str(tmp_path / "dist")),
    )
    monkeypatch.setattr(toolchain.Recipe, "list_recipes", lambda: [])
    return directory / "legacy.xcodeproj" / "project.pbxproj", source_bytes


def owned_configurations(project):
    """Follow each owner's list; configuration names alone are not unique."""
    root = project.objects[project.rootObject]
    owners = [("project", root)]
    owners.extend((project.objects[key].name, project.objects[key])
                  for key in root.targets)
    result = {}
    for owner_name, owner in owners:
        configurations = project.objects[owner.buildConfigurationList]
        names = set()
        for key in configurations.buildConfigurations:
            configuration = project.objects[key]
            names.add(configuration.name)
            result[owner_name, configuration.name] = configuration.buildSettings
        assert names == {"Debug", "Release"}
    assert set(name for name, _ in result) == {
        "project", "legacy", "custom_helper",
    }
    assert len(result) == 6
    return result


def configure_settings(filename, arc, modules, inherited=False):
    project = XcodeProject.load(str(filename))
    for (owner, name), settings in owned_configurations(project).items():
        settings["CI_CUSTOM_SETTING"] = "{}-{}-keep".format(owner, name)
        if owner == "legacy":
            values = (arc, modules)
        elif owner == "custom_helper":
            # Contrast each primary value, including its absent case.
            opposite = {None: "NO", "NO": "YES", "YES": "NO"}
            values = (opposite[arc], opposite[modules])
        elif inherited:
            values = ("YES", "NO") if name == "Debug" else ("NO", "YES")
        else:
            values = (None, None)
        for key, value in zip(COMPILER_SETTINGS, values):
            if value is None:
                if key in settings:
                    del settings[key]
            else:
                settings[key] = value
    project.save()
    reloaded = XcodeProject.load(str(filename))
    return {
        owner: {key: settings[key] for key in CHECKED_SETTINGS
                if key in settings}
        for owner, settings in owned_configurations(reloaded).items()
    }


def verify_preserved(project, expected, sources):
    actual = owned_configurations(project)
    assert actual.keys() == expected.keys()
    for owner, settings in actual.items():
        for key in CHECKED_SETTINGS:
            assert (key in settings) == (key in expected[owner]), (owner, key)
            if key in expected[owner]:
                assert type(settings[key]) is str, (owner, key, settings[key])
                assert settings[key] == expected[owner][key], (owner, key)
    for path, original in sources.items():
        assert path.read_bytes() == original


@pytest.mark.parametrize("arc", [None, "NO", "YES"])
@pytest.mark.parametrize("modules", [None, "NO", "YES"])
def test_update_preserves_compiler_settings(legacy_project, arc, modules):
    filename, sources = legacy_project
    expected = configure_settings(filename, arc, modules)
    for _ in range(2):
        toolchain.update_pbxproj(str(filename))
        verify_preserved(XcodeProject.load(str(filename)), expected, sources)


def test_update_preserves_inherited_settings(legacy_project):
    filename, sources = legacy_project
    expected = configure_settings(filename, None, None, inherited=True)
    for _ in range(2):
        toolchain.update_pbxproj(str(filename))
        verify_preserved(XcodeProject.load(str(filename)), expected, sources)


def primary_phases(project):
    root = project.objects[project.rootObject]
    targets = [project.objects[key] for key in root.targets
               if project.objects[key].name == "legacy"]
    assert len(targets) == 1
    return [project.objects[key] for key in targets[0].buildPhases]


def source_links(project):
    phases = [phase for phase in primary_phases(project)
              if phase.isa == "PBXSourcesBuildPhase"]
    assert len(phases) == 1
    links = {}
    for key in phases[0].files:
        build_file = project.objects[key]
        assert build_file.isa == "PBXBuildFile"
        reference = project.objects[build_file.fileRef]
        assert reference.isa == "PBXFileReference"
        links[str(key)] = (str(build_file.fileRef), reference.path)
    assert sorted(path for _, path in links.values()) == ["bridge.m", "main.m"]
    return links


def verify_dependencies(project):
    phases = [phase for phase in primary_phases(project)
              if phase.isa == "PBXFrameworksBuildPhase"]
    assert len(phases) == 1
    for path in ("Security.framework", "libz.tbd"):
        references = [reference for reference in
                      project.objects.get_objects_in_section("PBXFileReference")
                      if reference.path == path]
        assert len(references) == 1, path
        reference = references[0]
        assert reference.sourceTree == "DEVELOPER_DIR"
        linked = []
        for key in phases[0].files:
            build_file = project.objects[key]
            assert build_file.isa == "PBXBuildFile"
            assert project.objects[build_file.fileRef].isa == "PBXFileReference"
            if build_file.fileRef == reference.get_id():
                linked.append(key)
        assert len(linked) == 1, (path, linked)


def test_update_links_built_dependencies(legacy_project, tmp_path, monkeypatch):
    filename, sources = legacy_project
    expected = configure_settings(filename, "NO", "NO")
    original_links = source_links(XcodeProject.load(str(filename)))
    monkeypatch.setattr(
        toolchain, "Context",
        lambda: SimpleNamespace(
            state={"ci_dependency.build_all": True},
            dist_dir=str(tmp_path / "dist"),
        ),
    )
    recipe = SimpleNamespace(
        name="ci_dependency", pbx_frameworks=["Security"], pbx_libraries=["libz"],
        dist_xcframeworks=[], frameworks=[], dist_embed_xcframeworks=[], sources=[],
        init_with_ctx=lambda ctx: None,
    )
    monkeypatch.setattr(toolchain.Recipe, "list_recipes", lambda: ["ci_dependency"])
    monkeypatch.setattr(toolchain.Recipe, "get_recipe", lambda name, ctx: recipe)
    for _ in range(2):
        toolchain.update_pbxproj(str(filename))
        reloaded = XcodeProject.load(str(filename))
        verify_preserved(reloaded, expected, sources)
        verify_dependencies(reloaded)
        assert source_links(reloaded) == original_links
