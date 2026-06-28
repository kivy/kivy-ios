"""Wire ``Frameworks/*.xcframework`` into the generated ``.xcodeproj`` (spec 06).

``toolchain build`` runs ``sync_native_frameworks`` as part of the every-build,
idempotent project sync. For each ``.xcframework`` staged under ``Frameworks/``
it ensures a file reference (under the ``Frameworks`` group) and then wires the
**link** and **embed** phases independently:

* ``link``  -> a build file in the Frameworks (Link Binary) phase,
* ``embed`` -> a build file in the Embed Frameworks (Copy Files) phase, with
  ``CodeSignOnCopy``.

The link/embed intent comes from the locked ``[[tool.kivy_ios.xcframeworks]]``
entries (keyed by framework name). Wheel-embedded frameworks (SDL3/ANGLE, etc.)
have no lock entry and default to Embed & Sign (link + embed), preserving prior
behavior. Reconciliation is full each run, so flipping ``link``/``embed`` in the
lock removes the now-unwanted build file. Finally, references for frameworks no
longer present on disk are pruned so a removed dependency does not linger in the
project as a dangling reference.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pbxproj.pbxextensions.ProjectFiles import FileOptions, TreeType
from pbxproj.pbxsections.PBXBuildFile import PBXBuildFile

# pbxproj ships no type stubs and builds objects dynamically (PBXGenericObject),
# so the project graph is treated as ``Any`` throughout this interop module.

# PBXCopyFilesBuildPhase destination for frameworks (Embed Frameworks).
FRAMEWORKS_DST_SUBFOLDER_SPEC = "10"


def sync_native_frameworks(
    project: Any,
    target_name: str,
    *,
    frameworks_dir: Path,
    frameworks_group: Any,
    link_embed: dict[str, tuple[bool, bool]],
) -> None:
    """Reconcile ``Frameworks/*.xcframework`` refs + link/embed phases with disk.

    ``link_embed`` maps a framework's on-disk stem (e.g. ``"Sentry"`` for
    ``Sentry.xcframework``) to ``(link, embed)``. Frameworks not present in the
    map default to ``(True, True)``.
    """
    if frameworks_dir.is_dir():
        for xc in sorted(frameworks_dir.glob("*.xcframework")):
            rel = f"Frameworks/{xc.name}"
            ref = _ensure_file_ref(project, rel, target_name, frameworks_group)
            if ref is None:
                continue
            link, embed = link_embed.get(xc.stem, (True, True))
            if link:
                _ensure_link(project, target_name, ref)
            else:
                _remove_build_files(project, ref.get_id(), "PBXFrameworksBuildPhase")
            if embed:
                _ensure_embed(project, target_name, ref)
            else:
                _remove_build_files(project, ref.get_id(), "PBXCopyFilesBuildPhase")
    _prune(project, frameworks_dir)


# -- file reference ------------------------------------------------------------ #


def _ensure_file_ref(
    project: Any, rel: str, target_name: str, group: Any
) -> Any | None:
    existing = project.get_files_by_path(rel, tree=TreeType.SOURCE_ROOT)
    if existing:
        ref = existing[0]
        _ensure_under_group(project, ref, group)
        return ref
    # First add: let pbxproj create the file reference, place it under the group,
    # and register the framework search path. It also creates default link+embed
    # build files; the caller's reconciliation trims them to the lock's intent.
    project.add_file(
        rel,
        parent=group,
        target_name=target_name,
        tree=TreeType.SOURCE_ROOT,
        file_options=FileOptions(embed_framework=True, code_sign_on_copy=True),
    )
    refs = project.get_files_by_path(rel, tree=TreeType.SOURCE_ROOT)
    if not refs:
        return None
    ref = refs[0]
    _ensure_under_group(project, ref, group)
    return ref


def _ensure_under_group(project: Any, file_ref: Any, group: Any) -> None:
    """Move an existing file reference under ``group`` (idempotent)."""
    if group.has_child(file_ref):
        return
    for grp in project.objects.get_objects_in_section("PBXGroup"):
        if grp.has_child(file_ref):
            grp.remove_child(file_ref)
    group.add_child(file_ref)


# -- link / embed build files -------------------------------------------------- #


def _ensure_link(project: Any, target_name: str, file_ref: Any) -> None:
    phase = _link_phase(project, target_name)
    if phase is None or _has_build_file(project, phase, file_ref.get_id()):
        return
    build_file: Any = PBXBuildFile.create(file_ref)
    project.objects[build_file.get_id()] = build_file
    phase.add_build_file(build_file)


def _ensure_embed(project: Any, target_name: str, file_ref: Any) -> None:
    phase = _embed_phase(project, target_name)
    if _has_build_file(project, phase, file_ref.get_id()):
        return
    build_file: Any = PBXBuildFile.create(file_ref, attributes=["CodeSignOnCopy"])
    project.objects[build_file.get_id()] = build_file
    phase.add_build_file(build_file)


def _link_phase(project: Any, target_name: str) -> Any:
    target = project.get_target_by_name(target_name)
    if target is None:
        return None
    phases = target.get_or_create_build_phase("PBXFrameworksBuildPhase")
    return phases[0] if phases else None


def _embed_phase(project: Any, target_name: str) -> Any:
    target = project.get_target_by_name(target_name)
    if target is None:
        raise RuntimeError(f"target {target_name!r} not found in Xcode project")
    phases = target.get_or_create_build_phase(
        "PBXCopyFilesBuildPhase",
        search_parameters={"dstSubfolderSpec": FRAMEWORKS_DST_SUBFOLDER_SPEC},
        create_parameters=(
            "Embed Frameworks",
            [],
            "",
            FRAMEWORKS_DST_SUBFOLDER_SPEC,
        ),
    )
    return phases[0]


def _has_build_file(project: Any, phase: Any, ref_id: str) -> bool:
    for build_file_id in phase["files"]:
        build_file = project.objects[build_file_id]
        if _file_ref(build_file) == ref_id:
            return True
    return False


def _remove_build_files(project: Any, ref_id: str, section: str) -> None:
    for phase in project.objects.get_objects_in_section(section):
        for build_file_id in list(phase["files"]):
            build_file = project.objects[build_file_id]
            if _file_ref(build_file) == ref_id:
                phase.remove_build_file(build_file)


def _file_ref(build_file: Any) -> str | None:
    return build_file["fileRef"] if "fileRef" in build_file else None


# -- pruning ------------------------------------------------------------------- #


def _prune(project: Any, frameworks_dir: Path) -> None:
    """Remove references for ``Frameworks/*.xcframework`` no longer on disk."""
    for ref in list(project.objects.get_objects_in_section("PBXFileReference")):
        path = ref["path"] if "path" in ref else None
        if (
            not path
            or not path.startswith("Frameworks/")
            or not path.endswith(".xcframework")
        ):
            continue
        name = path.split("/", 1)[1]
        if not (frameworks_dir / name).is_dir():
            ref_id = ref.get_id()
            # Drop the link/embed build files first so remove_file_by_id sees no
            # remaining references and actually deletes the file reference (it
            # otherwise short-circuits while any build file still points at it).
            _remove_build_files(project, ref_id, "PBXFrameworksBuildPhase")
            _remove_build_files(project, ref_id, "PBXCopyFilesBuildPhase")
            project.remove_file_by_id(ref_id)
