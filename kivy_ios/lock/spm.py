"""Swift Package Manager resolver (spec 07 §"Resolution semantics").

``toolchain lock`` resolves each declared remote SPM package to a concrete Git
**revision** (and resolved semantic version when tag-resolved) so the build is
reproducible. Xcode/SPM owns the lifecycle; this module only drives a throwaway
``swift package resolve`` and reads back the ``Package.resolved`` it produces.

The backend is abstracted behind the ``SpmResolver`` protocol so unit tests can
inject a fake and stay hermetic (no ``swift`` toolchain, no network). Local
(``path``) packages need no resolution and are skipped by the resolver.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..config.model import SwiftPackageDep


class SpmResolverError(Exception):
    """An SPM resolution failure surfaced with an actionable message."""


@dataclass(frozen=True)
class ResolvedSwiftPackage:
    """The concrete pin SPM produced for one declared remote package."""

    name: str
    revision: str
    version: str | None = None


class SpmResolver(Protocol):
    def resolve(
        self,
        packages: list[SwiftPackageDep],
        *,
        project_root: Path,
        offline: bool = False,
    ) -> list[ResolvedSwiftPackage]:
        """Resolve remote packages to concrete revisions (one per ``url`` entry)."""
        ...


class XcodeSpmResolver:
    """Default backend: ``swift package resolve`` in a throwaway package.

    Writes a minimal ``Package.swift`` listing the declared remote packages with
    their version rules, runs ``swift package resolve``, then parses the emitted
    ``Package.resolved`` for each package's revision + version. Packages are
    matched back to their declaration by normalized Git URL.
    """

    def __init__(self, swift_executable: str = "swift") -> None:
        self._swift = swift_executable

    def resolve(
        self,
        packages: list[SwiftPackageDep],
        *,
        project_root: Path,
        offline: bool = False,
    ) -> list[ResolvedSwiftPackage]:
        remote = [p for p in packages if p.url]
        if not remote:
            return []
        with tempfile.TemporaryDirectory(prefix="kivy-spm-") as tmp:
            tmpdir = Path(tmp)
            src = tmpdir / "Sources" / "spmresolve"
            src.mkdir(parents=True)
            (src / "empty.swift").write_text("")
            (tmpdir / "Package.swift").write_text(render_manifest(remote))

            cmd = [self._swift, "package", "resolve", "--package-path", str(tmpdir)]
            if offline:
                # Resolve from SPM's cache only; fail if it is incomplete.
                cmd.append("--disable-automatic-resolution")
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True)
            except FileNotFoundError as exc:
                raise SpmResolverError(
                    f"could not run {self._swift!r}; Xcode's Swift toolchain is "
                    "required to resolve Swift packages.\n"
                    "  Install Xcode and run `xcode-select --switch`, or remove the "
                    "[tool.kivy.ios.native.swift_packages] entries."
                ) from exc
            if proc.returncode != 0:
                raise SpmResolverError(
                    "swift could not resolve the declared Swift packages.\n"
                    f"  swift said:\n{_indent(proc.stderr or proc.stdout)}"
                )
            resolved_path = tmpdir / "Package.resolved"
            try:
                pins = parse_package_resolved(resolved_path.read_text())
            except OSError as exc:
                raise SpmResolverError(
                    f"swift package resolve produced no Package.resolved: {exc}"
                ) from exc

        out: list[ResolvedSwiftPackage] = []
        for pkg in remote:
            assert pkg.url is not None
            pin = _match_pin(pins, pkg.url)
            if pin is None or not pin.revision:
                raise SpmResolverError(
                    f"could not find a resolved revision for swift package "
                    f"{pkg.name!r} ({pkg.url}) in Package.resolved."
                )
            out.append(
                ResolvedSwiftPackage(
                    name=pkg.name, revision=pin.revision, version=pin.version
                )
            )
        return out


def get_spm_resolver(backend: str = "xcode", **kwargs) -> SpmResolver:
    if backend == "xcode":
        return XcodeSpmResolver(**kwargs)
    raise SpmResolverError(f"unknown SPM resolver backend {backend!r} (expected xcode)")


# --- pure helpers (unit-tested without a swift toolchain) ----------------------


def render_manifest(packages: list[SwiftPackageDep]) -> str:
    """Render a throwaway ``Package.swift`` that depends on every remote package."""
    deps = ",\n".join("        " + package_clause(p) for p in packages)
    return (
        "// swift-tools-version:5.9\n"
        "import PackageDescription\n\n"
        'let package = Package(\n    name: "spmresolve",\n'
        f"    dependencies: [\n{deps}\n    ],\n"
        '    targets: [.target(name: "spmresolve")]\n)\n'
    )


def package_clause(pkg: SwiftPackageDep) -> str:
    """The ``.package(url:, …)`` clause for one remote package's version rule."""
    url = pkg.url
    if not url or not pkg.requirement:
        raise SpmResolverError(
            f"swift package {pkg.name!r} is not a resolvable remote package"
        )
    ((kind, value),) = pkg.requirement.items()
    u = _swift_str(url)
    if kind == "exact" and isinstance(value, str):
        return f".package(url: {u}, exact: {_swift_str(value)})"
    if kind == "from" and isinstance(value, str):
        return f".package(url: {u}, from: {_swift_str(value)})"
    if kind == "up_to_next_minor" and isinstance(value, str):
        return f".package(url: {u}, .upToNextMinor(from: {_swift_str(value)}))"
    if kind == "range" and isinstance(value, list) and len(value) == 2:
        lo, hi = value
        return f".package(url: {u}, {_swift_str(str(lo))}..<{_swift_str(str(hi))})"
    if kind == "branch" and isinstance(value, str):
        return f".package(url: {u}, branch: {_swift_str(value)})"
    if kind == "revision" and isinstance(value, str):
        return f".package(url: {u}, revision: {_swift_str(value)})"
    raise SpmResolverError(
        f"swift package {pkg.name!r} has an unrenderable requirement {pkg.requirement!r}"
    )


@dataclass(frozen=True)
class _Pin:
    url: str
    revision: str
    version: str | None


def parse_package_resolved(text: str) -> list[_Pin]:
    """Parse a ``Package.resolved`` (schema v1/v2/v3) into URL→pin records."""
    data = json.loads(text)
    # v1 nests pins under "object"; v2/v3 keep them at the top level.
    raw_pins = data.get("pins")
    if raw_pins is None:
        raw_pins = data.get("object", {}).get("pins", [])
    pins: list[_Pin] = []
    for p in raw_pins:
        # v1: repositoryURL; v2/v3: location.
        url = p.get("location") or p.get("repositoryURL") or ""
        state = p.get("state", {})
        revision = state.get("revision", "")
        version = state.get("version")
        if url and revision:
            pins.append(_Pin(url=url, revision=revision, version=version))
    return pins


def _match_pin(pins: list[_Pin], url: str) -> _Pin | None:
    target = _normalize_git_url(url)
    for pin in pins:
        if _normalize_git_url(pin.url) == target:
            return pin
    return None


def _normalize_git_url(url: str) -> str:
    u = url.strip().lower().rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    return u.rstrip("/")


def _swift_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _indent(text: str) -> str:
    return "\n".join(f"    {line}" for line in (text or "").splitlines())
