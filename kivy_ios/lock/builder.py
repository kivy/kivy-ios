"""Assemble a ``Lockfile`` from a validated ``Config`` (spec 02 §"Resolution semantics")."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from .. import __version__
from ..artifacts.verify import sha256_file
from ..config.model import Config, SwiftPackageDep
from .find_links import (
    FindLinksError,
    find_links_resolution_hint,
    resolve_find_links,
    validate_find_links,
    wheel_path_from_project_root,
)
from .model import (
    LockedPackage,
    LockedSwiftPackage,
    LockedWheel,
    Lockfile,
    PackageDep,
    PythonXcframework,
    canonical_name,
)
from .python_meta import PythonOrgProvider, PythonXcframeworkProvider
from .reader import compute_pyproject_sha256
from .resolver import Resolver, ResolverError, get_resolver
from .spm import (
    ResolvedSwiftPackage,
    SpmResolver,
    SpmResolverError,
    get_spm_resolver,
)


class BuildError(Exception):
    """A lock build failure surfaced with an actionable message."""


def build_lockfile(
    config: Config,
    pyproject_text: str,
    *,
    project_root: Path | None = None,
    resolver: Resolver | None = None,
    python_provider: PythonXcframeworkProvider | None = None,
    spm_resolver: SpmResolver | None = None,
    offline: bool = False,
    now: datetime | None = None,
) -> Lockfile:
    if config.ios is None:
        raise BuildError(
            "pyproject.toml has no [tool.kivy.ios] table; nothing to lock."
        )

    resolver = resolver or get_resolver("pip")
    python_provider = python_provider or PythonOrgProvider()
    root = (project_root or Path.cwd()).resolve()

    python_version = config.ios.python_version or "3.15.0"
    find_links_entries = config.ios.find_links
    try:
        validate_find_links(root, find_links_entries)
    except FindLinksError as exc:
        raise BuildError(str(exc)) from exc
    find_links = resolve_find_links(root, find_links_entries)
    py_info = python_provider.get(python_version, offline=offline)

    # Rule 11: deployment_target must not be below the xcframework floor.
    if _version_tuple(config.ios.deployment_target) < _version_tuple(py_info.ios_floor):
        raise BuildError(
            f"deployment_target {config.ios.deployment_target} is below the "
            f"minimum iOS {py_info.ios_floor} required by Python "
            f"{python_version}'s xcframework.\n"
            f"  Raise [tool.kivy.ios].deployment_target to at least "
            f"{py_info.ios_floor}."
        )

    direct = {canonical_name(_req_name(d)) for d in config.project.dependencies}
    excluded = {canonical_name(e) for e in config.ios.exclude}

    # Excluded names that are also direct requirements are silently dropped from
    # the exclusion set — you can't exclude what you explicitly depend on.
    excluded -= direct

    try:
        resolved = resolver.resolve(
            list(config.project.dependencies),
            python_version=python_version,
            deployment_target=config.ios.deployment_target,
            extra_index_urls=list(config.ios.extra_index_urls),
            find_links=find_links,
            offline=offline,
            simulator_archs=tuple(config.ios.simulator_archs),
        )
    except ResolverError as exc:
        hint = find_links_resolution_hint(
            root,
            find_links_entries,
            pip_stderr=str(exc),
        )
        if hint:
            raise BuildError(f"{exc}\n{hint}") from exc
        raise BuildError(str(exc)) from exc

    packages = []
    for rp in resolved:
        if canonical_name(rp.name) in excluded:
            continue
        wheels = tuple(
            _locked_wheel_from_resolved(w, project_root=root) for w in rp.wheels
        )
        _check_slices_complete(
            rp.name,
            wheels,
            config.ios.deployment_target,
            config.ios.simulator_archs,
        )
        packages.append(
            LockedPackage(
                name=rp.name,
                version=rp.version,
                wheels=wheels,
                requires_python=rp.requires_python,
                dependencies=tuple(PackageDep(name=d) for d in rp.dependencies),
                direct_requirement=canonical_name(rp.name) in direct,
                source_index=rp.source_index,
            )
        )

    swift_packages = _resolve_swift_packages(
        config.ios.swift_packages, spm_resolver, root, offline
    )

    return Lockfile(
        requires_python=config.project.requires_python or ">=3.15",
        packages=tuple(packages),
        python_xcframework=PythonXcframework(
            version=py_info.version, url=py_info.url, sha256=py_info.sha256
        ),
        toolchain_version=__version__,
        generated_at=(now or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        pyproject_sha256=compute_pyproject_sha256(pyproject_text),
        tool_kivy_ios_schema_version=config.ios.schema_version,
        xcframeworks=(),  # native xcframework resolution lands in Phase 4
        swift_packages=tuple(swift_packages),
    )


def _resolve_swift_packages(
    declared: tuple[SwiftPackageDep, ...],
    spm_resolver: SpmResolver | None,
    project_root: Path,
    offline: bool,
) -> list[LockedSwiftPackage]:
    """Resolve remote SPM packages to pins; assemble lock entries (sorted by name).

    Local (``path``) packages need no resolution. The resolver is only built and
    invoked when at least one remote package is declared, so a pure-wheel (or
    local-only) project never requires the Swift toolchain.
    """
    if not declared:
        return []
    remote = [p for p in declared if p.url]
    resolved: dict[str, ResolvedSwiftPackage] = {}
    if remote:
        resolver = spm_resolver or get_spm_resolver()
        try:
            for r in resolver.resolve(
                remote, project_root=project_root, offline=offline
            ):
                resolved[r.name] = r
        except SpmResolverError as exc:
            raise BuildError(str(exc)) from exc

    out: list[LockedSwiftPackage] = []
    for pkg in declared:
        pin = resolved.get(pkg.name)
        if pkg.url and pin is None:
            raise BuildError(
                f"swift package {pkg.name!r} resolved to no revision; re-run lock "
                f"with network access."
            )
        out.append(
            LockedSwiftPackage(
                name=pkg.name,
                products=pkg.products,
                url=pkg.url,
                path=pkg.path,
                requirement=pkg.requirement if pkg.url else None,
                revision=pin.revision if pin else None,
                version=pin.version if pin else None,
                link=pkg.link,
                embed=pkg.embed,
            )
        )
    out.sort(key=lambda s: s.name)
    return out


def _locked_wheel_from_resolved(w, *, project_root: Path) -> LockedWheel:
    url, path = _normalize_wheel_source(w.url, project_root=project_root)
    sha256 = w.sha256
    if not sha256 and path:
        sha256 = sha256_file((project_root / path).resolve())
    if not sha256:
        raise BuildError(
            f"could not determine SHA-256 for wheel {w.filename!r}; "
            f"re-run lock with network access or check the vendored file."
        )
    return LockedWheel(
        name=w.filename,
        url=url,
        path=path,
        sha256=sha256,
        upload_time=w.upload_time,
        size=w.size,
    )


def _normalize_wheel_source(
    url: str, *, project_root: Path
) -> tuple[str | None, str | None]:
    if url.startswith(("http://", "https://")):
        return url, None
    if url.startswith("file:"):
        local = Path(unquote(urlparse(url).path))
    else:
        local = Path(url)
    resolved = local.resolve()
    root = project_root.resolve()
    try:
        rel = wheel_path_from_project_root(root, resolved)
    except FindLinksError as exc:
        raise BuildError(
            f"wheel resolved to {resolved}, which is outside the allowed "
            f"find_links scope for project directory {root}.\n"
            f"  Vendored wheels must live under the project directory or a "
            f"shared sibling directory (e.g. examples/wheels/)."
        ) from exc
    return None, rel


def _check_slices_complete(
    name, wheels, deployment_target, simulator_archs=None
) -> None:
    """Fail fast if a compiled package is missing an iOS slice (spec 02).

    The required slices are the device slice plus one per configured simulator
    architecture (``[tool.kivy.ios].simulator_archs``), so a project that drops
    ``x86_64`` is not held to a slice it no longer targets.

    Compatibility rule: a wheel tagged ios_<M>_<N>_<arch>_<sdk> satisfies a
    required slice when M.N <= deployment_target AND the arch+sdk suffix
    matches exactly.  This mirrors select_wheel's logic: python.org's iOS
    Python binary always tags wheels at its own minimum OS (currently 13.0)
    regardless of IPHONEOS_DEPLOYMENT_TARGET used when compiling the extension.
    """
    if any(w.is_pure_python for w in wheels):
        return  # pure-Python: single py3-none-any entry is complete

    from .resolver import slice_suffixes

    required = slice_suffixes(simulator_archs)
    dt_parts = _version_tuple(deployment_target)
    covered: set[str] = set()
    for wheel in wheels:
        tag = wheel.platform_tag  # e.g. "ios_13_0_arm64_iphoneos"
        parts = tag.split("_")  # ["ios", "13", "0", "arm64", "iphoneos"]
        if parts[0] != "ios" or len(parts) < 3:
            continue
        # Find where the arch+sdk suffix starts (last two underscore-joined segments).
        for suffix in required:
            if tag.endswith(f"_{suffix}"):
                prefix_parts = tag[: -(len(suffix) + 1)].split("_")  # ["ios","13","0"]
                try:
                    wheel_ver = tuple(int(x) for x in prefix_parts[1:])
                except ValueError:
                    break
                if wheel_ver <= dt_parts:
                    covered.add(suffix)
                break

    missing_suffixes = set(required) - covered
    if missing_suffixes:
        dt = deployment_target.replace(".", "_")
        missing_tags = sorted(f"ios_{dt}_{s}" for s in missing_suffixes)
        raise BuildError(
            f"{name} is missing iOS wheel slice(s): {', '.join(missing_tags)}.\n"
            f"  A compiled package must publish every targeted iOS slice "
            f"(device + each configured simulator arch) to be locked reproducibly."
        )


def semantic_equal(a: Lockfile, b: Lockfile) -> bool:
    """Compare two lockfiles ignoring the volatile ``generated_at`` field.

    Used by ``lock --check`` so a re-resolve that produces identical pins (but
    a new timestamp) still reports "in sync".
    """
    return dataclasses.replace(a, generated_at="") == dataclasses.replace(
        b, generated_at=""
    )


def diff_summary(old: Lockfile, new: Lockfile) -> list[str]:
    """Human-readable summary of what changed between two locks (for --check)."""
    out: list[str] = []
    old_pkgs = {canonical_name(p.name): p for p in old.packages}
    new_pkgs = {canonical_name(p.name): p for p in new.packages}
    for name in sorted(new_pkgs.keys() - old_pkgs.keys()):
        out.append(f"  + {new_pkgs[name].name} {new_pkgs[name].version} (added)")
    for name in sorted(old_pkgs.keys() - new_pkgs.keys()):
        out.append(f"  - {old_pkgs[name].name} {old_pkgs[name].version} (removed)")
    for name in sorted(old_pkgs.keys() & new_pkgs.keys()):
        if old_pkgs[name].version != new_pkgs[name].version:
            out.append(
                f"  ~ {new_pkgs[name].name}: "
                f"{old_pkgs[name].version} -> {new_pkgs[name].version}"
            )
    if old.python_xcframework.version != new.python_xcframework.version:
        out.append(
            f"  ~ Python.xcframework: {old.python_xcframework.version} -> "
            f"{new.python_xcframework.version}"
        )
    return out


def _req_name(requirement: str) -> str:
    from packaging.requirements import InvalidRequirement, Requirement

    try:
        return Requirement(requirement).name
    except InvalidRequirement:
        return requirement


def _version_tuple(v: str) -> tuple[int, ...]:
    parts = []
    for chunk in v.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)
