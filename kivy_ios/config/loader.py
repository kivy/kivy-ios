"""Load and validate a kivy-ios ``pyproject.toml`` (spec 01).

Implements the spec's validation rules. tomllib surfaces line numbers for
*syntax* errors; for *semantic* errors we report the dotted key path plus a
best-effort source line located by scanning the raw text.
"""

from __future__ import annotations

import keyword
import re
import tomllib
from os.path import isabs, normpath
from pathlib import Path, PurePosixPath

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from .errors import ConfigError
from .model import (
    DEFAULT_SIMULATOR_ARCHS,
    MANAGED_INFO_PLIST_KEYS,
    RESERVED_BUILD_SETTINGS,
    SUPPORTED_IOS_SCHEMA_VERSION,
    VALID_ORIENTATIONS,
    VALID_SIMULATOR_ARCHS,
    Author,
    Config,
    IconConfig,
    IosConfig,
    KivyMeta,
    ProjectMeta,
    SigningConfig,
    SplashConfig,
    XcframeworkDep,
)


def load_config(path: str | Path, *, require_ios: bool = True) -> Config:
    """Parse and validate ``pyproject.toml`` at ``path``.

    ``require_ios`` enforces the presence of ``[tool.kivy.ios]`` (rule 2) —
    every iOS command needs it; set it False for contexts that only inspect
    the cross-platform tables.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    return load_config_from_text(
        text, require_ios=require_ios, project_root=path.parent
    )


def load_config_from_text(
    text: str, *, require_ios: bool = True, project_root: Path | None = None
) -> Config:
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        # tomllib embeds the line in the message; surface it directly.
        raise ConfigError(f"invalid TOML: {exc}") from exc

    finder = _LineFinder(text)
    project = _parse_project(raw, finder)
    kivy = _parse_kivy(raw, finder)
    ios = _parse_ios(raw, finder, project, project_root=project_root)

    if ios is None and require_ios:
        raise ConfigError(
            "missing [tool.kivy.ios] table",
            key_path="tool.kivy.ios",
            hint="add a [tool.kivy.ios] overlay; [tool.kivy] alone is not a "
            "buildable iOS target. Run `toolchain init`.",
        )

    return Config(project=project, kivy=kivy, ios=ios)


# --------------------------------------------------------------------------- #
# [project]
# --------------------------------------------------------------------------- #
def _parse_project(raw: dict, finder: _LineFinder) -> ProjectMeta:
    project = raw.get("project")
    if not isinstance(project, dict):
        raise ConfigError(
            "missing [project] table (PEP 621)",
            key_path="project",
            hint="every kivy-ios app needs a [project] table with at least "
            "name and version.",
        )

    name = project.get("name")
    if not name or not isinstance(name, str):
        raise ConfigError(
            "missing or empty [project].name",
            key_path="project.name",
            line=finder.line("project"),
        )
    version = project.get("version")
    if not version or not isinstance(version, str):
        raise ConfigError(
            "missing or empty [project].version",
            key_path="project.version",
            line=finder.line("project"),
        )

    deps = project.get("dependencies", [])
    if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
        raise ConfigError(
            "[project].dependencies must be a list of PEP 508 strings",
            key_path="project.dependencies",
        )

    authors: list[Author] = []
    for entry in project.get("authors", []) or []:
        if isinstance(entry, dict):
            authors.append(Author(name=entry.get("name"), email=entry.get("email")))

    return ProjectMeta(
        name=name,
        version=version,
        description=project.get("description"),
        requires_python=project.get("requires-python"),
        dependencies=tuple(deps),
        authors=tuple(authors),
    )


# --------------------------------------------------------------------------- #
# [tool.kivy]
# --------------------------------------------------------------------------- #
def _parse_kivy(raw: dict, finder: _LineFinder) -> KivyMeta:
    tool = raw.get("tool", {})
    kivy = tool.get("kivy") if isinstance(tool, dict) else None
    if not isinstance(kivy, dict):
        raise ConfigError(
            "missing [tool.kivy] table",
            key_path="tool.kivy",
            hint="run `toolchain init` to scaffold it.",
        )

    app_dir = _validate_app_dir(kivy.get("app_dir"), finder)

    entry_point = kivy.get("entry_point", "main")
    _validate_entry_point(entry_point, finder)

    orientation = kivy.get("orientation", ["portrait"])
    _validate_orientation(orientation, finder)

    return KivyMeta(
        app_dir=app_dir,
        display_name=kivy.get("display_name"),
        entry_point=entry_point,
        orientation=tuple(orientation),
    )


def _validate_app_dir(app_dir: object, finder: _LineFinder) -> str:
    # Rule 6: app_dir is required and must name a subdirectory.
    if app_dir is None:
        raise ConfigError(
            "missing required [tool.kivy].app_dir",
            key_path="tool.kivy.app_dir",
            hint='set app_dir to a subdirectory such as "src".',
        )
    if not isinstance(app_dir, str) or app_dir.strip() == "":
        raise ConfigError(
            "[tool.kivy].app_dir must be a non-empty string",
            key_path="tool.kivy.app_dir",
            line=finder.line("app_dir"),
        )
    if app_dir == "." or normpath(app_dir) == ".":
        raise ConfigError(
            'app_dir = "." (project root) is not allowed',
            key_path="tool.kivy.app_dir",
            line=finder.line("app_dir"),
            hint="keep app code in a subdirectory (e.g. src/) so the bundle "
            "excludes .git/, .venv/, and the <app>-ios/ build output.",
        )
    if isabs(app_dir):
        raise ConfigError(
            "app_dir must be relative, not an absolute path",
            key_path="tool.kivy.app_dir",
            line=finder.line("app_dir"),
        )
    parts = PurePosixPath(normpath(app_dir)).parts
    if parts and parts[0] == "..":
        raise ConfigError(
            "app_dir must not escape the project directory",
            key_path="tool.kivy.app_dir",
            line=finder.line("app_dir"),
        )
    return app_dir


def _validate_entry_point(entry_point: object, finder: _LineFinder) -> None:
    # Rule 5: entry_point must be a valid (dotted) Python identifier.
    if not isinstance(entry_point, str) or entry_point == "":
        raise ConfigError(
            "[tool.kivy].entry_point must be a non-empty string",
            key_path="tool.kivy.entry_point",
            line=finder.line("entry_point"),
        )
    parts = entry_point.split(".")
    if not all(p.isidentifier() and not keyword.iskeyword(p) for p in parts):
        raise ConfigError(
            f"entry_point {entry_point!r} is not a valid dotted Python identifier",
            key_path="tool.kivy.entry_point",
            line=finder.line("entry_point"),
            hint='e.g. "main" for src/main.py, or "pkg.start" for src/pkg/start.py.',
        )


def _validate_orientation(orientation: object, finder: _LineFinder) -> None:
    # Rule 7: orientation values must be within the allowed set.
    if not isinstance(orientation, list) or not orientation:
        raise ConfigError(
            "[tool.kivy].orientation must be a non-empty list",
            key_path="tool.kivy.orientation",
            line=finder.line("orientation"),
        )
    bad = [o for o in orientation if o not in VALID_ORIENTATIONS]
    if bad:
        raise ConfigError(
            f"invalid orientation value(s): {', '.join(map(str, bad))}",
            key_path="tool.kivy.orientation",
            line=finder.line("orientation"),
            hint=f"allowed: {', '.join(sorted(VALID_ORIENTATIONS))}.",
        )


# --------------------------------------------------------------------------- #
# [tool.kivy.ios]
# --------------------------------------------------------------------------- #
def _parse_ios(
    raw: dict,
    finder: _LineFinder,
    project: ProjectMeta,
    *,
    project_root: Path | None = None,
) -> IosConfig | None:
    tool = raw.get("tool", {})
    kivy = tool.get("kivy", {}) if isinstance(tool, dict) else {}
    ios = kivy.get("ios") if isinstance(kivy, dict) else None
    if ios is None:
        return None
    if not isinstance(ios, dict):
        raise ConfigError("[tool.kivy.ios] must be a table", key_path="tool.kivy.ios")

    # Rule 3: schema_version required + supported.
    schema_version = ios.get("schema_version")
    if schema_version is None:
        raise ConfigError(
            "missing required [tool.kivy.ios].schema_version",
            key_path="tool.kivy.ios.schema_version",
        )
    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        raise ConfigError(
            "[tool.kivy.ios].schema_version must be an integer",
            key_path="tool.kivy.ios.schema_version",
            line=finder.line("schema_version"),
        )
    if schema_version > SUPPORTED_IOS_SCHEMA_VERSION:
        raise ConfigError(
            f"[tool.kivy.ios].schema_version {schema_version} is newer than this "
            f"kivy-ios understands (max {SUPPORTED_IOS_SCHEMA_VERSION})",
            key_path="tool.kivy.ios.schema_version",
            line=finder.line("schema_version"),
            hint="upgrade kivy-ios.",
        )
    if schema_version < 1:
        raise ConfigError(
            f"unsupported [tool.kivy.ios].schema_version {schema_version}",
            key_path="tool.kivy.ios.schema_version",
            line=finder.line("schema_version"),
        )

    # Rule 4: bundle_id required.
    bundle_id = ios.get("bundle_id")
    if not bundle_id or not isinstance(bundle_id, str):
        raise ConfigError(
            "missing required [tool.kivy.ios].bundle_id",
            key_path="tool.kivy.ios.bundle_id",
            hint='e.g. bundle_id = "org.example.myapp".',
        )
    # A bundle identifier is a UTI: only alphanumerics, hyphen, and period are
    # allowed.  Catch invalid characters (commonly an underscore copied from a
    # Python package name) here rather than as a cryptic Xcode build failure.
    if not re.fullmatch(r"[A-Za-z0-9.-]+", bundle_id):
        raise ConfigError(
            f"invalid character in [tool.kivy.ios].bundle_id {bundle_id!r}",
            key_path="tool.kivy.ios.bundle_id",
            line=finder.line("bundle_id"),
            hint=(
                "bundle identifiers may contain only letters, digits, hyphen "
                "(-), and period (.). Replace underscores with hyphens, e.g. "
                '"org.example.hello-world".'
            ),
        )

    build = ios.get("build", 1)
    if not isinstance(build, int) or isinstance(build, bool):
        raise ConfigError(
            "[tool.kivy.ios].build must be an integer",
            key_path="tool.kivy.ios.build",
            line=finder.line("build"),
        )

    deployment_target = ios.get("deployment_target", "13.0")
    if not isinstance(deployment_target, str):
        raise ConfigError(
            "[tool.kivy.ios].deployment_target must be a string",
            key_path="tool.kivy.ios.deployment_target",
            line=finder.line("deployment_target"),
        )

    simulator_archs = _parse_simulator_archs(ios, finder)

    extra_index_urls = ios.get("extra_index_urls", [])
    if not isinstance(extra_index_urls, list) or not all(
        isinstance(u, str) for u in extra_index_urls
    ):
        raise ConfigError(
            "[tool.kivy.ios].extra_index_urls must be a list of strings",
            key_path="tool.kivy.ios.extra_index_urls",
            line=finder.line("extra_index_urls"),
        )

    find_links = _parse_find_links(ios, finder, project_root=project_root)
    exclude = _parse_exclude(ios, finder)

    python_version = _parse_python_version(ios)
    _check_requires_python(project, python_version, finder)

    icons = _parse_icons(ios)
    splash = _parse_splash(ios)
    xcframeworks = _parse_xcframeworks(ios)
    signing = _parse_signing(ios)
    info_plist = _parse_info_plist(ios, finder)
    build_settings = _parse_build_settings(ios, finder)
    privacy_source = _parse_privacy(ios)
    entitlements = _parse_entitlements(ios)

    return IosConfig(
        schema_version=schema_version,
        bundle_id=bundle_id,
        build=build,
        deployment_target=deployment_target,
        simulator_archs=simulator_archs,
        extra_index_urls=tuple(extra_index_urls),
        find_links=tuple(find_links),
        exclude=tuple(exclude),
        python_version=python_version,
        icons=icons,
        splash=splash,
        xcframeworks=tuple(xcframeworks),
        entitlements=entitlements,
        signing=signing,
        privacy_manifest_source=privacy_source,
        info_plist=info_plist,
        build_settings=build_settings,
    )


def _parse_simulator_archs(ios: dict, finder: _LineFinder) -> tuple[str, ...]:
    """``[tool.kivy.ios].simulator_archs`` — which simulator slices to pin.

    Defaults to device-arm64-plus both simulator arches; a project that no longer
    targets Intel simulator hosts may set ``["arm64"]`` to stop pinning x86_64.
    """
    raw = ios.get("simulator_archs")
    if raw is None:
        return DEFAULT_SIMULATOR_ARCHS
    line = finder.line("simulator_archs")
    if not isinstance(raw, list) or not all(isinstance(a, str) for a in raw):
        raise ConfigError(
            "[tool.kivy.ios].simulator_archs must be a list of strings",
            key_path="tool.kivy.ios.simulator_archs",
            line=line,
        )
    if not raw:
        raise ConfigError(
            "[tool.kivy.ios].simulator_archs must not be empty",
            key_path="tool.kivy.ios.simulator_archs",
            line=line,
            hint='at least one of "arm64", "x86_64" is required.',
        )
    unknown = [a for a in raw if a not in VALID_SIMULATOR_ARCHS]
    if unknown:
        valid = ", ".join(sorted(VALID_SIMULATOR_ARCHS))
        raise ConfigError(
            f"unknown simulator arch(es) {unknown} in [tool.kivy.ios].simulator_archs",
            key_path="tool.kivy.ios.simulator_archs",
            line=line,
            hint=f"valid values are: {valid}.",
        )
    # De-dupe while preserving declared order (stable, deterministic slices).
    seen: set[str] = set()
    ordered: list[str] = []
    for arch in raw:
        if arch not in seen:
            seen.add(arch)
            ordered.append(arch)
    return tuple(ordered)


def _parse_python_version(ios: dict) -> str | None:
    python = ios.get("python")
    if python is None:
        return None
    if not isinstance(python, dict):
        raise ConfigError(
            "[tool.kivy.ios.python] must be a table", key_path="tool.kivy.ios.python"
        )
    version = python.get("version")
    if version is None:
        raise ConfigError(
            "missing required [tool.kivy.ios.python].version",
            key_path="tool.kivy.ios.python.version",
        )
    if not isinstance(version, str):
        raise ConfigError(
            "[tool.kivy.ios.python].version must be a string",
            key_path="tool.kivy.ios.python.version",
        )
    return version


def _check_requires_python(
    project: ProjectMeta, python_version: str | None, finder: _LineFinder
) -> None:
    # Rule 10: requires-python must not exclude the selected python version.
    if not project.requires_python or not python_version:
        return
    try:
        spec = SpecifierSet(project.requires_python)
    except InvalidSpecifier:
        raise ConfigError(
            f"[project].requires-python is not a valid specifier: "
            f"{project.requires_python!r}",
            key_path="project.requires-python",
        ) from None
    try:
        ver = Version(python_version)
    except InvalidVersion:
        raise ConfigError(
            f"[tool.kivy.ios.python].version is not a valid version: "
            f"{python_version!r}",
            key_path="tool.kivy.ios.python.version",
        ) from None
    if not spec.contains(ver, prereleases=True):
        hint = "align requires-python with the iOS Python version."
        if ver.is_prerelease:
            hint = (
                f"pre-release runtimes such as {python_version} need an explicit "
                f'floor (e.g. requires-python = ">={python_version}"), not '
                f'">=3.15" alone.'
            )
        raise ConfigError(
            f"[project].requires-python ({project.requires_python}) excludes the "
            f"selected Python.xcframework version {python_version}",
            key_path="tool.kivy.ios.python.version",
            line=finder.line("requires-python"),
            hint=hint,
        )


def _parse_find_links(
    ios: dict, finder: _LineFinder, *, project_root: Path | None = None
) -> list[str]:
    raw = ios.get("find_links", [])
    if not isinstance(raw, list) or not all(isinstance(p, str) for p in raw):
        raise ConfigError(
            "[tool.kivy.ios].find_links must be a list of strings",
            key_path="tool.kivy.ios.find_links",
            line=finder.line("find_links"),
        )
    out: list[str] = []
    for path in raw:
        if isabs(path) or normpath(path) == "..":
            raise ConfigError(
                "find_links entries must be repo-relative paths",
                key_path="tool.kivy.ios.find_links",
                line=finder.line("find_links"),
            )
        normalized = normpath(path).replace("\\", "/")
        if project_root is not None:
            _validate_find_link_scope(project_root, normalized, finder)
        out.append(normalized)
    return out


def _validate_find_link_scope(
    project_root: Path, entry: str, finder: _LineFinder
) -> None:
    """Allow in-project paths and sibling dirs under the same parent (e.g. ../wheels)."""
    resolved = (project_root / entry).resolve()
    root = project_root.resolve()
    try:
        resolved.relative_to(root)
        return
    except ValueError:
        pass
    try:
        resolved.relative_to(root.parent)
    except ValueError:
        raise ConfigError(
            "find_links entries must stay within the project directory or a "
            "sibling directory under the same parent",
            key_path="tool.kivy.ios.find_links",
            line=finder.line("find_links"),
            hint='e.g. "wheels" inside the project or "../wheels" for a shared '
            "examples/wheels/ directory.",
        ) from None


def _parse_exclude(ios: dict, finder: _LineFinder) -> list[str]:
    raw = ios.get("exclude", [])
    if not isinstance(raw, list) or not all(isinstance(p, str) for p in raw):
        raise ConfigError(
            "[tool.kivy.ios].exclude must be a list of package-name strings",
            key_path="tool.kivy.ios.exclude",
            line=finder.line("exclude"),
        )
    return [str(p) for p in raw]


def _parse_icons(ios: dict) -> IconConfig:
    icons = ios.get("icons")
    if icons is None:
        return IconConfig()
    if not isinstance(icons, dict):
        raise ConfigError(
            "[tool.kivy.ios.icons] must be a table", key_path="tool.kivy.ios.icons"
        )
    return IconConfig(source=icons.get("source"))


def _parse_splash(ios: dict) -> SplashConfig:
    splash = ios.get("splash")
    if splash is None:
        return SplashConfig()
    if not isinstance(splash, dict):
        raise ConfigError(
            "[tool.kivy.ios.splash] must be a table", key_path="tool.kivy.ios.splash"
        )
    return SplashConfig(
        source=splash.get("source"), background=splash.get("background")
    )


def _parse_xcframeworks(ios: dict) -> list[XcframeworkDep]:
    native = ios.get("native")
    if not isinstance(native, dict):
        return []
    table = native.get("xcframeworks")
    if table is None:
        return []
    if not isinstance(table, dict):
        raise ConfigError(
            "[tool.kivy.ios.native.xcframeworks] must be a table",
            key_path="tool.kivy.ios.native.xcframeworks",
        )
    out: list[XcframeworkDep] = []
    for name, entry in table.items():
        if not isinstance(entry, dict):
            raise ConfigError(
                f"xcframework {name!r} must be an inline table with version + source",
                key_path=f"tool.kivy.ios.native.xcframeworks.{name}",
            )
        version = entry.get("version")
        source = entry.get("source")
        if not isinstance(version, str) or not version:
            raise ConfigError(
                f"xcframework {name!r} requires a string 'version'",
                key_path=f"tool.kivy.ios.native.xcframeworks.{name}",
            )
        if not isinstance(source, str) or not source:
            raise ConfigError(
                f"xcframework {name!r} requires an explicit 'source' (URL or "
                f"repo-relative path)",
                key_path=f"tool.kivy.ios.native.xcframeworks.{name}",
            )
        if isabs(source):
            raise ConfigError(
                f"xcframework {name!r} source must not be an absolute path",
                key_path=f"tool.kivy.ios.native.xcframeworks.{name}",
            )
        out.append(
            XcframeworkDep(
                name=name,
                version=version,
                source=source,
                link=bool(entry.get("link", True)),
                embed=bool(entry.get("embed", True)),
            )
        )
    return out


def _parse_signing(ios: dict) -> SigningConfig:
    signing = ios.get("signing")
    if signing is None:
        return SigningConfig()
    if not isinstance(signing, dict):
        raise ConfigError(
            "[tool.kivy.ios.signing] must be a table",
            key_path="tool.kivy.ios.signing",
        )
    return SigningConfig(
        team_id=signing.get("team_id", ""),
        identity=signing.get("identity", "Apple Development"),
        provisioning_profile=signing.get("provisioning_profile", ""),
        auto_signing=bool(signing.get("auto_signing", True)),
        upload_symbols=bool(signing.get("upload_symbols", True)),
    )


def _parse_info_plist(ios: dict, finder: _LineFinder) -> dict[str, object]:
    info = ios.get("info_plist")
    if info is None:
        return {}
    if not isinstance(info, dict):
        raise ConfigError(
            "[tool.kivy.ios.info_plist] must be a table",
            key_path="tool.kivy.ios.info_plist",
        )
    conflicts = sorted(set(info) & MANAGED_INFO_PLIST_KEYS)
    if conflicts:
        raise ConfigError(
            f"[tool.kivy.ios.info_plist] sets kivy-ios-managed key(s): "
            f"{', '.join(conflicts)}",
            key_path="tool.kivy.ios.info_plist",
            line=finder.line("info_plist"),
            hint="set these via their dedicated schema fields instead.",
        )
    return dict(info)


def _parse_build_settings(ios: dict, finder: _LineFinder) -> dict[str, str]:
    # Rule 8: reserved keys under xcode.build_settings are rejected.
    xcode = ios.get("xcode")
    if not isinstance(xcode, dict):
        return {}
    settings = xcode.get("build_settings")
    if settings is None:
        return {}
    if not isinstance(settings, dict):
        raise ConfigError(
            "[tool.kivy.ios.xcode.build_settings] must be a table",
            key_path="tool.kivy.ios.xcode.build_settings",
        )
    conflicts = sorted(set(settings) & RESERVED_BUILD_SETTINGS)
    if conflicts:
        raise ConfigError(
            f"[tool.kivy.ios.xcode.build_settings] sets toolchain-reserved key(s): "
            f"{', '.join(conflicts)}",
            key_path="tool.kivy.ios.xcode.build_settings",
            line=finder.line("build_settings"),
            hint="these are managed by the toolchain and cannot be overridden.",
        )
    return {str(k): str(v) for k, v in settings.items()}


def _parse_privacy(ios: dict) -> str | None:
    privacy = ios.get("privacy_manifest")
    if privacy is None:
        return None
    if not isinstance(privacy, dict):
        raise ConfigError(
            "[tool.kivy.ios.privacy_manifest] must be a table",
            key_path="tool.kivy.ios.privacy_manifest",
        )
    return privacy.get("source")


def _parse_entitlements(ios: dict) -> dict[str, object]:
    ent = ios.get("entitlements")
    if ent is None:
        return {}
    if not isinstance(ent, dict):
        raise ConfigError(
            "[tool.kivy.ios.entitlements] must be a table",
            key_path="tool.kivy.ios.entitlements",
        )
    return dict(ent)


class _LineFinder:
    """Best-effort source-line lookup for a bare key name.

    tomllib does not expose per-key positions for semantically-valid TOML, so
    we scan the raw text for the first ``key =`` (or ``[table]``) occurrence.
    Returns None when not found; callers fall back to the dotted key path.
    """

    def __init__(self, text: str) -> None:
        self._lines = text.splitlines()

    def line(self, key: str) -> int | None:
        key_re = re.compile(rf"^\s*(\[*\s*){re.escape(key)}\b")
        for i, line in enumerate(self._lines, start=1):
            if key_re.search(line):
                return i
        return None
