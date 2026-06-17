"""Serialize a ``Lockfile`` to ``pylock.ios.toml`` text (spec 02).

Hand-rolled emitter (rather than a generic TOML writer) so we control the
exact PEP 751 layout — inline ``hashes`` tables, ``[packages.tool.kivy_ios]``
placement, and a deterministic ordering (packages sorted by name/version,
wheels by filename) so diffs across runs show only real changes.
"""

from __future__ import annotations

from .model import LockedPackage, LockedWheel, LockedXcframework, Lockfile


def dumps(lock: Lockfile) -> str:
    lines: list[str] = []

    # --- PEP 751 top-level scalars ---
    lines.append(f"lock-version = {_s(lock.lock_version)}")
    lines.append(f"created-by = {_s(lock.created_by)}")
    lines.append(f"requires-python = {_s(lock.requires_python)}")
    lines.append(f"extras = {_arr(lock.extras)}")
    lines.append(f"dependency-groups = {_arr(lock.dependency_groups)}")
    lines.append(f"default-groups = {_arr(lock.default_groups)}")
    lines.append("")

    # --- [[packages]] (deterministic order) ---
    for pkg in sorted(lock.packages, key=lambda p: p.sort_key):
        _emit_package(lines, pkg)

    # --- [tool.kivy_ios] extension ---
    lines.append("[tool.kivy_ios]")
    lines.append(f"schema_version = {lock.schema_version}")
    lines.append(f"toolchain_version = {_s(lock.toolchain_version)}")
    lines.append(f"generated_at = {_s(lock.generated_at)}")
    lines.append(f"pyproject_sha256 = {_s(lock.pyproject_sha256)}")
    lines.append(f"tool_kivy_ios_schema_version = {lock.tool_kivy_ios_schema_version}")
    lines.append("")
    lines.append("[tool.kivy_ios.python_xcframework]")
    lines.append(f"version = {_s(lock.python_xcframework.version)}")
    lines.append(f"url = {_s(lock.python_xcframework.url)}")
    lines.append(f"sha256 = {_s(lock.python_xcframework.sha256)}")

    # --- [[tool.kivy_ios.xcframeworks]] (deterministic order) ---
    for xc in sorted(lock.xcframeworks, key=lambda x: (x.name.lower(), x.version)):
        lines.append("")
        _emit_xcframework(lines, xc)

    return "\n".join(lines) + "\n"


def _emit_package(lines: list[str], pkg: LockedPackage) -> None:
    lines.append("[[packages]]")
    lines.append(f"name = {_s(pkg.name)}")
    lines.append(f"version = {_s(pkg.version)}")
    if pkg.requires_python:
        lines.append(f"requires-python = {_s(pkg.requires_python)}")
    if pkg.marker:
        lines.append(f"marker = {_s(pkg.marker)}")
    if pkg.dependencies:
        deps = ", ".join(_dep_inline(d) for d in pkg.dependencies)
        lines.append(f"dependencies = [{deps}]")

    if pkg.direct_requirement or pkg.source_index:
        lines.append("")
        lines.append("[packages.tool.kivy_ios]")
        if pkg.direct_requirement:
            lines.append("direct_requirement = true")
        if pkg.source_index:
            lines.append(f"source_index = {_s(pkg.source_index)}")

    for wheel in sorted(pkg.wheels, key=lambda w: w.name):
        lines.append("")
        _emit_wheel(lines, wheel)
    lines.append("")


def _emit_wheel(lines: list[str], wheel: LockedWheel) -> None:
    lines.append("[[packages.wheels]]")
    lines.append(f"name = {_s(wheel.name)}")
    if wheel.upload_time:
        lines.append(f"upload-time = {_s(wheel.upload_time)}")
    if wheel.url:
        lines.append(f"url = {_s(wheel.url)}")
    else:
        path = wheel.path
        assert path is not None
        lines.append(f"path = {_s(path)}")
    lines.append(f"hashes = {{ sha256 = {_s(wheel.sha256)} }}")
    if wheel.size is not None:
        lines.append(f"size = {wheel.size}")


def _emit_xcframework(lines: list[str], xc: LockedXcframework) -> None:
    lines.append("[[tool.kivy_ios.xcframeworks]]")
    lines.append(f"name = {_s(xc.name)}")
    lines.append(f"version = {_s(xc.version)}")
    if xc.url:
        lines.append(f"url = {_s(xc.url)}")
    else:
        path = xc.path
        assert path is not None
        lines.append(f"path = {_s(path)}")
    lines.append(f"sha256 = {_s(xc.sha256)}")
    lines.append(f"slices = {_arr(xc.slices)}")
    lines.append(f"archive_format = {_s(xc.archive_format)}")
    if xc.archive_member:
        lines.append(f"archive_member = {_s(xc.archive_member)}")
    if xc.privacy_manifest_path:
        lines.append(f"privacy_manifest_path = {_s(xc.privacy_manifest_path)}")
    lines.append(f"link = {_b(xc.link)}")
    lines.append(f"embed = {_b(xc.embed)}")
    if xc.source:
        lines.append(f"source = {_s(xc.source)}")


def _dep_inline(dep) -> str:
    if dep.marker:
        return f"{{ name = {_s(dep.name)}, marker = {_s(dep.marker)} }}"
    return f"{{ name = {_s(dep.name)} }}"


def _s(value: str) -> str:
    """Emit a TOML basic string with minimal escaping."""
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _arr(values) -> str:
    if not values:
        return "[]"
    return "[" + ", ".join(_s(v) for v in values) + "]"


def _b(value: bool) -> str:
    return "true" if value else "false"
