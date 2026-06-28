"""Wire locked Swift packages into the generated ``.xcodeproj`` (spec 07 §"Xcode
project generation").

``toolchain build`` runs ``sync_swift_packages`` as part of the every-build,
idempotent project sync. For each ``[[tool.kivy_ios.swift_packages]]`` entry it
ensures:

* a package reference (``XCRemoteSwiftPackageReference`` for ``url`` entries,
  ``XCLocalSwiftPackageReference`` for ``path`` entries),
* one ``XCSwiftPackageProductDependency`` per product, linked into the
  Frameworks (Link) phase when ``link`` is set, and
* an **explicit** Embed Frameworks / Copy Files entry (with ``CodeSignOnCopy``)
  when ``embed`` is set — required because ``pbxproj`` only wires the *link*
  step and Xcode does not auto-embed dynamic SPM products in our generated,
  non-GUI project (see docs/dev/swift-spm-findings.md).

References/dependencies for entries no longer in the lock are pruned, and a
``Package.resolved`` is written from the pinned revisions so Xcode resolves to
the locked commits without network drift.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pbxproj import PBXGenericObject, PBXList
from pbxproj.pbxsections.PBXBuildFile import PBXBuildFile
from pbxproj.pbxsections.XCLocalSwiftPackageReference import (
    XCLocalSwiftPackageReference,
)

from ..lock.model import LockedSwiftPackage

# pbxproj ships no type stubs and builds objects dynamically (PBXGenericObject),
# so the project graph is treated as ``Any`` throughout this interop module.

# PBXCopyFilesBuildPhase destination for frameworks (Embed Frameworks).
FRAMEWORKS_DST_SUBFOLDER_SPEC = "10"
PACKAGE_RESOLVED_VERSION = 2


def sync_swift_packages(
    project: Any,
    target_name: str,
    packages: tuple[LockedSwiftPackage, ...],
    *,
    staging_root: Path | None = None,
) -> None:
    """Idempotently reconcile the project's SPM graph with ``packages``.

    ``staging_root`` is the ``<app>-ios/`` directory that holds the generated
    ``.xcodeproj``. Local package ``path`` entries are stored in the lock
    relative to the *project root* (where ``pyproject.toml`` lives), but Xcode
    resolves ``XCLocalSwiftPackageReference.relativePath`` relative to the
    project file's own directory — one level deeper. We translate the path
    accordingly (e.g. ``swift-shims`` -> ``../swift-shims``).
    """
    for sp in packages:
        ref = _ensure_reference(project, sp, staging_root)
        for product in sp.products:
            dep: Any = project.get_or_create_package_dependency(
                product, target_name, (ref, product)
            )
            if dep is None:
                continue
            # Repoint at the ensured reference: an existing dependency is reused
            # by product name, so if the reference id changed (e.g. a local
            # path was corrected and the old reference pruned) the stale pointer
            # would otherwise dangle.
            dep["package"] = ref.get_id()
            if sp.link:
                _ensure_link(project, target_name, dep)
            else:
                _remove_build_files(project, dep.get_id(), "PBXFrameworksBuildPhase")
            if sp.embed:
                _ensure_embed(project, target_name, dep)
            else:
                _remove_build_files(project, dep.get_id(), "PBXCopyFilesBuildPhase")
    _prune(project, target_name, packages, staging_root)


# -- references ---------------------------------------------------------------- #


def local_relative_path(path: str, staging_root: Path | None) -> str:
    """Translate a project-root-relative local package ``path`` into one
    relative to the ``<app>-ios/`` staging root (where the ``.xcodeproj`` lives),
    which is how Xcode interprets ``XCLocalSwiftPackageReference.relativePath``.

    With ``staging_root`` unset the path is returned unchanged (used by callers
    that already provide a project-relative path).
    """
    if staging_root is None:
        return path
    target = (staging_root.parent / path).resolve()
    return os.path.relpath(target, staging_root.resolve())


def _ensure_reference(
    project: Any, sp: LockedSwiftPackage, staging_root: Path | None
) -> Any:
    if sp.url:
        requirement = xcode_requirement(sp.requirement or {})
        ref = project.get_or_create_package_reference(sp.url, (sp.url, requirement))
        # Reflect a changed requirement rule on re-lock (get_or_create won't).
        ref["requirement"] = PBXGenericObject().parse(requirement)
        return ref
    return _get_or_create_local_reference(
        project, local_relative_path(sp.path or "", staging_root)
    )


def _get_or_create_local_reference(project: Any, relative_path: str) -> Any:
    for ref in project.objects.get_objects_in_section("XCLocalSwiftPackageReference"):
        if ref["relativePath"] == relative_path:
            return ref
    ref: Any = XCLocalSwiftPackageReference.create(relative_path)
    project.objects[ref.get_id()] = ref
    for proj in project.objects.get_objects_in_section("PBXProject"):
        if "packageReferences" not in proj:
            proj["packageReferences"] = PBXList()
        if ref.get_id() not in proj["packageReferences"]:
            proj["packageReferences"].append(ref.get_id())
    return ref


def xcode_requirement(rule: dict[str, object]) -> dict[str, str]:
    """Map a lock ``requirement`` rule to the Xcode ``requirement`` object."""
    if not rule:
        raise ValueError("remote swift package is missing a requirement rule")
    ((kind, value),) = rule.items()
    if kind == "exact":
        return {"kind": "exactVersion", "version": str(value)}
    if kind == "from":
        return {"kind": "upToNextMajorVersion", "minimumVersion": str(value)}
    if kind == "up_to_next_minor":
        return {"kind": "upToNextMinorVersion", "minimumVersion": str(value)}
    if kind == "range" and isinstance(value, list) and len(value) == 2:
        return {
            "kind": "versionRange",
            "minimumVersion": str(value[0]),
            "maximumVersion": str(value[1]),
        }
    if kind == "branch":
        return {"kind": "branch", "branch": str(value)}
    if kind == "revision":
        return {"kind": "revision", "revision": str(value)}
    raise ValueError(f"unrenderable swift package requirement {rule!r}")


# -- link / embed build files -------------------------------------------------- #


def _ensure_link(project: Any, target_name: str, dep: Any) -> None:
    phase = _link_phase(project, target_name)
    if phase is None or _has_build_file(project, phase, dep.get_id()):
        return
    build_file: Any = PBXBuildFile.create(dep, is_product=True)
    project.objects[build_file.get_id()] = build_file
    phase.add_build_file(build_file)


def _ensure_embed(project: Any, target_name: str, dep: Any) -> None:
    phase = _embed_phase(project, target_name)
    if _has_build_file(project, phase, dep.get_id()):
        return
    build_file: Any = PBXBuildFile.create(
        dep, attributes=["CodeSignOnCopy"], is_product=True
    )
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


def _has_build_file(project: Any, phase: Any, dep_id: str) -> bool:
    for build_file_id in phase["files"]:
        build_file = project.objects[build_file_id]
        if _product_ref(build_file) == dep_id:
            return True
    return False


# -- pruning ------------------------------------------------------------------- #


def _prune(
    project: Any,
    target_name: str,
    packages: tuple[LockedSwiftPackage, ...],
    staging_root: Path | None,
) -> None:
    desired_products = {p for sp in packages for p in sp.products}
    desired_remote = {_normalize_url(sp.url) for sp in packages if sp.url}
    desired_local = {
        local_relative_path(sp.path, staging_root) for sp in packages if sp.path
    }

    for dep in list(
        project.objects.get_objects_in_section("XCSwiftPackageProductDependency")
    ):
        if dep["productName"] not in desired_products:
            _remove_product_dependency(project, target_name, dep)

    for ref in list(
        project.objects.get_objects_in_section("XCRemoteSwiftPackageReference")
    ):
        if _normalize_url(ref["repositoryURL"]) not in desired_remote:
            _remove_reference(project, ref)

    for ref in list(
        project.objects.get_objects_in_section("XCLocalSwiftPackageReference")
    ):
        if ref["relativePath"] not in desired_local:
            _remove_reference(project, ref)


def _remove_product_dependency(project: Any, target_name: str, dep: Any) -> None:
    dep_id = dep.get_id()
    _remove_build_files(project, dep_id, "PBXFrameworksBuildPhase")
    _remove_build_files(project, dep_id, "PBXCopyFilesBuildPhase")
    for target in project.objects.get_targets(target_name):
        if "packageProductDependencies" not in target:
            continue
        deps = target["packageProductDependencies"]
        if dep_id in deps:
            deps.remove(dep_id)
    del project.objects[dep_id]


def _remove_reference(project: Any, ref: Any) -> None:
    ref_id = ref.get_id()
    for proj in project.objects.get_objects_in_section("PBXProject"):
        if "packageReferences" in proj and ref_id in proj["packageReferences"]:
            proj["packageReferences"].remove(ref_id)
    del project.objects[ref_id]


def _remove_build_files(project: Any, dep_id: str, section: str) -> None:
    for phase in project.objects.get_objects_in_section(section):
        for build_file_id in list(phase["files"]):
            build_file = project.objects[build_file_id]
            if _product_ref(build_file) == dep_id:
                phase.remove_build_file(build_file)


def _product_ref(build_file: Any) -> str | None:
    return build_file["productRef"] if "productRef" in build_file else None


# -- Package.resolved ---------------------------------------------------------- #


def package_resolved_json(packages: tuple[LockedSwiftPackage, ...]) -> str:
    """Render a ``Package.resolved`` (schema v2) from the pinned revisions."""
    pins = []
    remote = [p for p in packages if p.url and p.revision]
    for sp in sorted(remote, key=lambda p: _identity(p.url or "")):
        state: dict[str, str] = {"revision": sp.revision or ""}
        if sp.version:
            state["version"] = sp.version
        pins.append(
            {
                "identity": _identity(sp.url or ""),
                "kind": "remoteSourceControl",
                "location": sp.url,
                "state": state,
            }
        )
    return (
        json.dumps({"pins": pins, "version": PACKAGE_RESOLVED_VERSION}, indent=2) + "\n"
    )


def write_package_resolved(
    path: str | Path, packages: tuple[LockedSwiftPackage, ...]
) -> None:
    """Write (or remove) ``Package.resolved`` for the project's remote packages."""
    path = Path(path)
    remote = [p for p in packages if p.url and p.revision]
    if not remote:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(package_resolved_json(packages), encoding="utf-8")


def _identity(url: str) -> str:
    name = _normalize_url(url).rsplit("/", 1)[-1]
    return name


def _normalize_url(url: str) -> str:
    u = url.strip().lower().rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    return u.rstrip("/")
