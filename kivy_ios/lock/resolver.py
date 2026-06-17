"""Dependency resolver backends (spec 02 §"Resolution semantics").

The resolver turns ``[project].dependencies`` into a fully-pinned set of
per-slice iOS wheels, **host-independent** — every compiled package is pinned
for all three iOS slices (device arm64, simulator arm64, simulator x86_64)
regardless of the architecture of the host running ``lock``.

``pip`` is the default backend (validated by the Phase 0 spike); ``uv`` is a
fallback behind the same ``Resolver`` protocol. The backend is abstracted so
the rest of the lock pipeline is backend-agnostic, and so unit tests can inject
a fake resolver and stay hermetic.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .model import canonical_name

# The three iOS slices every build can target (spec 02). Device + the two
# simulator architectures. Tag templates are formatted with the deployment
# target (dots -> underscores).
SLICE_SUFFIXES = (
    "arm64_iphoneos",
    "arm64_iphonesimulator",
    "x86_64_iphonesimulator",
)


class ResolverError(Exception):
    """A resolution failure (missing slice, no matching wheel, backend error)."""


@dataclass(frozen=True)
class ResolvedWheel:
    filename: str
    url: str
    sha256: str
    upload_time: str | None = None
    size: int | None = None


@dataclass
class ResolvedPackage:
    name: str
    version: str
    wheels: list[ResolvedWheel] = field(default_factory=list)
    requires_python: str | None = None
    dependencies: list[str] = field(default_factory=list)
    source_index: str | None = None


def slice_tags(deployment_target: str) -> tuple[str, ...]:
    dt = deployment_target.replace(".", "_")
    return tuple(f"ios_{dt}_{suffix}" for suffix in SLICE_SUFFIXES)


def pip_python_version(python_version: str) -> str:
    """``pip install --python-version`` accepts only integer dotted parts."""
    parts: list[str] = []
    for chunk in python_version.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        if not digits:
            break
        parts.append(digits)
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return python_version


def abi_tags(python_version: str) -> tuple[str, ...]:
    """ABI tags to offer pip; cp<XY> first, then the limited-API/none fallbacks.

    Per the Phase 0 findings we must not over-constrain abi (abi3 wheels would
    be missed otherwise).
    """
    major_minor = "".join(python_version.split(".")[:2])
    return (f"cp{major_minor}", "abi3", "none")


class Resolver(Protocol):
    def resolve(
        self,
        requirements: list[str],
        *,
        python_version: str,
        deployment_target: str,
        extra_index_urls: list[str],
        find_links: list[str] | None = None,
        offline: bool = False,
    ) -> list[ResolvedPackage]:
        """Resolve requirements to per-slice iOS wheels (all slices pinned)."""
        ...


class PipResolver:
    """Default backend: stock pip cross-resolution via ``pip install --report``.

    For each iOS slice we run pip in dry-run report mode with the slice's
    platform tag; the JSON report yields each resolved wheel's URL + sha256.
    Results are merged across slices into one ``ResolvedPackage`` per
    distribution. A package missing any compiled slice raises ``ResolverError``
    (fail fast at lock time, host-independent).
    """

    def __init__(self, python_executable: str | None = None) -> None:
        self._python = python_executable or sys.executable

    def resolve(
        self,
        requirements: list[str],
        *,
        python_version: str,
        deployment_target: str,
        extra_index_urls: list[str],
        find_links: list[str] | None = None,
        offline: bool = False,
    ) -> list[ResolvedPackage]:
        if not requirements:
            return []
        tags = slice_tags(deployment_target)
        abis = abi_tags(python_version)
        # name -> ResolvedPackage (merged across slices)
        merged: dict[str, ResolvedPackage] = {}
        seen_filenames: dict[str, set[str]] = {}

        for tag in tags:
            report = self._run_report(
                requirements,
                python_version=python_version,
                platform_tag=tag,
                abis=abis,
                extra_index_urls=extra_index_urls,
                find_links=find_links or [],
                offline=offline,
            )
            for item in report.get("install", []):
                self._absorb(item, merged, seen_filenames)

        return list(merged.values())

    def _absorb(self, item, merged, seen_filenames) -> None:
        meta = item.get("metadata", {})
        name = meta.get("name")
        version = meta.get("version")
        download = item.get("download_info", {})
        url = download.get("url", "")
        if not url.endswith(".whl"):
            # sdist/vcs/directory are refused (spec 02): wheels only.
            raise ResolverError(
                f"{name} {version} resolved to a non-wheel source ({url}); "
                "kivy-ios installs only iOS wheels (no on-device compile)."
            )
        archive = download.get("archive_info", {})
        hashes = archive.get("hashes", {})
        sha256 = hashes.get("sha256", "")
        filename = url.rsplit("/", 1)[-1]
        key = canonical_name(name)
        pkg = merged.get(key)
        if pkg is None:
            pkg = ResolvedPackage(
                name=name,
                version=version,
                requires_python=meta.get("requires_python"),
                dependencies=_dep_names(meta.get("requires_dist", [])),
            )
            merged[key] = pkg
            seen_filenames[key] = set()
        if filename not in seen_filenames[key]:
            seen_filenames[key].add(filename)
            pkg.wheels.append(ResolvedWheel(filename=filename, url=url, sha256=sha256))

    def _run_report(
        self,
        requirements: list[str],
        *,
        python_version: str,
        platform_tag: str,
        abis: tuple[str, ...],
        extra_index_urls: list[str],
        find_links: list[str],
        offline: bool,
    ) -> dict:
        with tempfile.TemporaryDirectory(prefix="kivy-lock-") as tmp:
            report_path = Path(tmp) / "report.json"
            cmd = [
                self._python,
                "-m",
                "pip",
                "install",
                "--dry-run",
                "--ignore-installed",
                "--only-binary=:all:",
                "--python-version",
                pip_python_version(python_version),
                "--implementation",
                "cp",
                "--platform",
                platform_tag,
                "--target",
                str(Path(tmp) / "target"),
                "--report",
                str(report_path),
            ]
            for abi in abis:
                cmd += ["--abi", abi]
            for index in extra_index_urls:
                cmd += ["--extra-index-url", index]
            for link in find_links:
                cmd += ["--find-links", link]
            if offline:
                cmd += ["--no-index"]
            cmd += list(requirements)

            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise ResolverError(
                    f"pip could not resolve the iOS slice {platform_tag!r}.\n"
                    f"  This usually means a dependency has no wheel for that "
                    f"slice upstream.\n  pip said:\n{_indent(proc.stderr or proc.stdout)}"
                )
            try:
                return json.loads(report_path.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise ResolverError(f"could not read pip report: {exc}") from exc


class UvResolver:
    """Fallback backend stub (spec 02 / Phase 0 findings).

    uv is kept as a documented fallback behind the same protocol. The full
    implementation lands only if a pip regression or perf need warrants it; for
    now it raises a clear error so the abstraction point exists and is testable.
    """

    def resolve(self, requirements, **kwargs) -> list[ResolvedPackage]:
        raise ResolverError(
            "the uv resolver backend is not implemented yet; pip is the default. "
            "See docs/dev/resolver-findings.md."
        )


def get_resolver(backend: str = "pip", **kwargs) -> Resolver:
    if backend == "pip":
        return PipResolver(**kwargs)
    if backend == "uv":
        return UvResolver()
    raise ResolverError(f"unknown resolver backend {backend!r} (expected pip|uv)")


def _dep_names(requires_dist: list[str]) -> list[str]:
    names: list[str] = []
    for raw in requires_dist or []:
        # Strip everything after the name: extras, specifiers, markers.
        name = raw.split(";", 1)[0].split("[", 1)[0]
        for sep in ("==", ">=", "<=", "~=", "!=", ">", "<", "(", " "):
            name = name.split(sep, 1)[0]
        name = name.strip()
        if name:
            names.append(name)
    return names


def _indent(text: str) -> str:
    return "\n".join(f"    {line}" for line in (text or "").splitlines())
