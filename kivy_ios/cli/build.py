"""``toolchain build`` — materialize the lock into an Xcode project (specs 05/06).

Build performs, in order:

1. **Drift check** — the lock must be in sync with ``pyproject.toml``.
2-5. **Artifact collection** — Python.xcframework, pinned wheels into
   ``pip-deps/``, wheel-embedded + native ``.xcframework`` into ``Frameworks/``.
6. **Project materialization** — generate ``<app>-ios/`` and the ``.xcodeproj``.
7. **xcodebuild** — only when a target flag is given (Phase 6); a bare
   ``toolchain build`` stops after step 6 with a ready-to-open project.
"""

from __future__ import annotations

import plistlib
import re
from pathlib import Path

import click

from ..artifacts.collect import CollectError, collect_artifacts
from ..artifacts.wheels import BuildSlice
from ..config import ConfigError, load_config
from ..lock import LockError, is_in_sync, load
from ..project.icon import IconSourceError
from ..project.materialize import materialize_project
from ..project.staging import StagingError, create_staging
from ..xcode import (
    CommandError,
    SigningError,
    XcodeBuild,
    archive_command,
    build_command,
    default_simulator_arch,
    export_command,
    export_options_plist,
    run_command,
)
from ..xcode.commands import preflight_signing
from ._common import (
    LOCKFILE_NAME,
    MIGRATION_URL,
    ToolchainError,
    find_pyproject,
    lockfile_path,
)


@click.command(context_settings={"ignore_unknown_options": True})
@click.option(
    "--simulator",
    "target",
    flag_value="simulator",
    help="Build for the iOS simulator (Debug).",
)
@click.option(
    "--device", "target", flag_value="device", help="Build for a device (Debug)."
)
@click.option(
    "--release", "target", flag_value="release", help="Archive + export a .ipa."
)
@click.option(
    "--arch",
    type=click.Choice(["arm64", "x86_64"]),
    default=None,
    help="Override the simulator architecture.",
)
@click.option(
    "--no-verify-lock", is_flag=True, help="Skip the pyproject drift check (CI only)."
)
@click.option("--no-cache", is_flag=True, help="Force re-download of every artifact.")
@click.option(
    "--team-id", default=None, help="Override [tool.kivy.ios.signing].team_id."
)
@click.option(
    "--signing-identity",
    default=None,
    help="Override [tool.kivy.ios.signing].identity.",
)
@click.option(
    "--export-method",
    type=click.Choice(["app-store", "ad-hoc", "development"]),
    default="app-store",
    help="Export method (only meaningful with --release).",
)
@click.argument("legacy_args", nargs=-1, type=click.UNPROCESSED)
def build(
    target: str | None,
    arch: str | None,
    no_verify_lock: bool,
    no_cache: bool,
    team_id: str | None,
    signing_identity: str | None,
    export_method: str,
    legacy_args: tuple[str, ...],
) -> None:
    """Download artifacts, generate the Xcode project, and optionally build it."""
    if legacy_args:
        # 2.x form: `toolchain build python3 kivy`. No backward compatibility.
        raise ToolchainError(
            "`toolchain build <recipe>...` is the kivy-ios 2.x form and no longer "
            "exists.\n"
            "  3.0 builds from pyproject.toml + pylock.ios.toml — no recipe "
            "arguments.\n"
            "  Migration: toolchain init && toolchain lock && toolchain build\n"
            f"  See: {MIGRATION_URL}"
        )

    # Signing pre-flight runs before any artifact work so --device/--release
    # fail fast on a missing team_id (spec 05 step 7).
    config, project_root = _load_project()
    if target is not None:
        try:
            preflight_signing(config, target, team_id_flag=team_id)
        except SigningError as exc:
            raise ToolchainError(str(exc)) from exc

    prepare_build(
        config,
        project_root,
        target=target,
        arch=arch,
        no_verify_lock=no_verify_lock,
        no_cache=no_cache,
    )

    if target is None:
        click.echo(
            "Project ready. Open it with `toolchain open` or build with "
            "`toolchain build --simulator`."
        )
        return

    xb = XcodeBuild.from_config(config, project_root)
    try:
        _xcodebuild_step7(
            xb,
            config,
            target=target,
            arch=arch,
            team_id_flag=team_id,
            export_method=export_method,
        )
    except (CommandError, SigningError) as exc:
        raise ToolchainError(str(exc)) from exc


def prepare_build(
    config,
    project_root: Path,
    *,
    target: str | None,
    arch: str | None,
    no_verify_lock: bool,
    no_cache: bool,
) -> BuildSlice:
    """Run build steps 1-6 (drift, artifact collection, project generation).

    Shared by ``toolchain build`` and ``toolchain run``. A bare ``toolchain
    build`` (no target) collects both the device and simulator pip-deps slices
    so the generated project builds either Xcode destination without re-running
    the toolchain; a targeted build collects only its slice. Returns the primary
    slice (the targeted one, or the device slice for a bare build).
    """
    pyproject = project_root / "pyproject.toml"
    lock = _load_lock(project_root)
    if not no_verify_lock and not is_in_sync(lock, pyproject.read_text("utf-8")):
        raise ToolchainError(
            f"{LOCKFILE_NAME} is out of date with pyproject.toml.\n"
            "  Run `toolchain lock` to regenerate it (or pass --no-verify-lock "
            "to build against the stale lock anyway)."
        )

    build_slices = _resolve_slices(target, arch, config.ios.deployment_target)
    tags = ", ".join(s.platform_tag for s in build_slices)
    try:
        layout = create_staging(config, project_root)
        click.echo(f"Collecting artifacts for {tags} ...")
        collect_artifacts(
            lock,
            layout,
            build_slices=build_slices,
            project_root=project_root,
            no_cache=no_cache,
        )
        materialize_project(
            config,
            project_root,
            layout=layout,
            python_version=lock.python_xcframework.version,
            last_upgrade_check=_xcode_last_upgrade_check(),
            swift_packages=lock.swift_packages,
        )
    except CollectError as exc:
        raise ToolchainError(str(exc)) from exc
    except IconSourceError as exc:
        raise ToolchainError(str(exc)) from exc
    except StagingError as exc:
        raise ToolchainError(str(exc)) from exc

    staging = project_root / f"{config.app_slug}-ios"
    click.echo(f"Generated {staging.relative_to(project_root)}")
    return build_slices[0]


def _xcodebuild_step7(
    xb: XcodeBuild,
    config,
    *,
    target: str,
    arch: str | None,
    team_id_flag: str | None,
    export_method: str,
) -> None:
    if target in ("simulator", "device"):
        sim_arch = arch if target == "simulator" else None
        click.echo(f"xcodebuild build ({target}) ...")
        run_command(build_command(xb, target, arch=sim_arch))
        return

    # --release: archive, then export a signed .ipa (spec 05 step 7).
    resolved_team_id = preflight_signing(config, "release", team_id_flag=team_id_flag)
    if resolved_team_id is None:
        # preflight_signing only returns None for --simulator; unreachable here.
        raise SigningError(
            "code signing required for --release, but no team_id is set."
        )
    xb.build_dir.mkdir(parents=True, exist_ok=True)
    click.echo("xcodebuild archive ...")
    run_command(archive_command(xb))

    options = export_options_plist(
        method=export_method,
        team_id=resolved_team_id,
        upload_symbols=config.ios.signing.upload_symbols,
    )
    options_path = xb.build_dir / "ExportOptions.plist"
    with open(options_path, "wb") as fh:
        plistlib.dump(options, fh)

    click.echo("xcodebuild -exportArchive ...")
    run_command(export_command(xb, options_path))
    click.echo(f"Exported {xb.ipa_path.relative_to(xb.project_root)}")


def _resolve_slices(
    target: str | None, arch: str | None, deployment_target: str
) -> list[BuildSlice]:
    """Slices to collect for *target*.

    A bare ``toolchain build`` (``target is None``) collects both device and
    simulator so the "ready to open" project builds either Xcode destination —
    Xcode's default destination is usually a simulator, so collecting only the
    device slice would make the very first in-Xcode build fail. A targeted build
    collects only the slice it is about to build.

    The simulator slice defaults to the host's native arch (``--arch`` overrides):
    a single ``pip-deps-simulator`` directory holds one arch's compiled ``.so``
    files, so the right one to stage is the arch the developer's machine actually
    runs — ``x86_64`` on Intel, ``arm64`` on Apple Silicon. The lock pins both
    simulator arches; the build picks the host's.
    """
    sim_arch = arch or default_simulator_arch()
    if target is None:
        return [
            BuildSlice("device", "arm64", deployment_target),
            BuildSlice("simulator", sim_arch, deployment_target),
        ]
    return [_resolve_slice(target, arch, deployment_target)]


def _resolve_slice(
    target: str | None, arch: str | None, deployment_target: str
) -> BuildSlice:
    if target == "simulator":
        return BuildSlice(
            "simulator", arch or default_simulator_arch(), deployment_target
        )
    # device or release builds target device/arm64.
    return BuildSlice("device", "arm64", deployment_target)


def _xcode_last_upgrade_check() -> str | None:
    """LastUpgradeCheck for the installed Xcode (e.g. Xcode 26.5 -> "2650").

    Setting the generated project's ``LastUpgradeCheck`` to the running Xcode's
    version suppresses the "Update to recommended settings" banner. Returns
    ``None`` when Xcode can't be queried, in which case the generator falls back
    to its built-in constant.
    """
    from ..doctor.probe import RealProbe

    version = RealProbe().xcode_version()
    return _encode_last_upgrade_check(version) if version else None


def _encode_last_upgrade_check(version: str) -> str | None:
    """Encode an Xcode version string ("26.5", "16.2.1") as Xcode's integer
    LastUpgradeCheck code (major*100 + minor*10 + patch), or ``None``.
    """
    match = re.search(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", version)
    if match is None:
        return None
    major, minor, patch = (int(match.group(i) or 0) for i in (1, 2, 3))
    return str(major * 100 + minor * 10 + patch)


def _load_project():
    pyproject = find_pyproject()
    return _load_config(pyproject), pyproject.parent


def _load_config(pyproject: Path):
    try:
        return load_config(pyproject)
    except ConfigError as exc:
        raise ToolchainError(exc.format()) from exc


def _load_lock(project_root: Path):
    path = lockfile_path(project_root)
    if not path.is_file():
        raise ToolchainError(f"no {LOCKFILE_NAME} found. Run `toolchain lock` first.")
    try:
        return load(path)
    except LockError as exc:
        raise ToolchainError(str(exc)) from exc
