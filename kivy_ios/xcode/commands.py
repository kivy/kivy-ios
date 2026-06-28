"""xcodebuild command + ExportOptions.plist construction (spec 05 step 7).

Pure builders: no subprocess, no filesystem side effects beyond returning the
argv/plist the caller will execute or write. This keeps the signing pre-flight,
SDK selection, archive/export pipeline, and export-options mapping fully
unit-testable on any host.
"""

from __future__ import annotations

import os
import platform
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..config.model import Config


def default_simulator_arch() -> str:
    """The iOS-simulator CPU arch matching the host Mac.

    Apple-Silicon Macs run the simulator as ``arm64``; Intel Macs as ``x86_64``.
    This is the default when ``--arch`` is not given, so a bare or targeted
    simulator build collects (and ``xcodebuild`` builds) the slice the developer's
    own machine can actually run — collecting only ``arm64`` would break the very
    first simulator build on an Intel host even though the lock pinned ``x86_64``.
    ``platform.machine()`` reports ``x86_64`` under Rosetta too, which is correct:
    an x86_64 Python process drives an x86_64 simulator.
    """
    return "x86_64" if platform.machine() == "x86_64" else "arm64"


# build-target -> xcodebuild SDK.
SDK = {
    "simulator": "iphonesimulator",
    "device": "iphoneos",
    "release": "iphoneos",
}

TEAM_ID_ENV = "KIVY_IOS_TEAM_ID"
SIGNING_IDENTITY_ENV = "KIVY_IOS_SIGNING_IDENTITY"

# --export-method -> ExportOptions.plist `method` value.
EXPORT_METHOD = {
    "app-store": "app-store",
    "ad-hoc": "ad-hoc",
    "development": "development",
}


class SigningError(Exception):
    """Code signing is required but no team_id could be resolved."""


def sdk_for(target: str) -> str:
    try:
        return SDK[target]
    except KeyError:
        raise ValueError(f"unknown build target {target!r}") from None


def configuration_for(target: str) -> str:
    return "Release" if target == "release" else "Debug"


@dataclass(frozen=True)
class XcodeBuild:
    """Locates the generated project for a config under a project root."""

    project_root: Path
    scheme: str

    @classmethod
    def from_config(cls, config: Config, project_root: str | Path) -> XcodeBuild:
        return cls(project_root=Path(project_root), scheme=config.app_slug)

    @property
    def staging(self) -> Path:
        return self.project_root / f"{self.scheme}-ios"

    @property
    def project_path(self) -> Path:
        return self.staging / f"{self.scheme}.xcodeproj"

    @property
    def build_dir(self) -> Path:
        return self.staging / "build"

    @property
    def archive_path(self) -> Path:
        return self.build_dir / f"{self.scheme}.xcarchive"

    @property
    def ipa_path(self) -> Path:
        return self.build_dir / f"{self.scheme}.ipa"


def resolve_team_id(
    config: Config,
    *,
    team_id_flag: str | None = None,
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Resolve the effective team_id (flag → env → pyproject), or None."""
    effective_env: Mapping[str, str] = os.environ if env is None else env
    candidates = (
        team_id_flag,
        effective_env.get(TEAM_ID_ENV),
        config.ios_required.signing.team_id or None,
    )
    for value in candidates:
        if value:
            return value
    return None


def resolve_signing_identity(
    config: Config,
    *,
    identity_flag: str | None = None,
    env: Mapping[str, str] | None = None,
) -> str | None:
    effective_env: Mapping[str, str] = os.environ if env is None else env
    for value in (
        identity_flag,
        effective_env.get(SIGNING_IDENTITY_ENV),
        config.ios_required.signing.identity,
    ):
        if value:
            return value
    return None


def preflight_signing(
    config: Config,
    target: str,
    *,
    team_id_flag: str | None = None,
    env: dict | None = None,
) -> str | None:
    """Fail fast when --device/--release lack a team_id (spec 05 step 7).

    Returns the resolved team_id (None for --simulator, which does not sign).
    """
    if target == "simulator":
        return None
    team_id = resolve_team_id(config, team_id_flag=team_id_flag, env=env)
    if not team_id:
        raise SigningError(
            "code signing required for --device/--release, but no team_id is set.\n"
            "  Set it one of these ways:\n"
            '    - [tool.kivy.ios.signing].team_id = "ABCDE12345" in pyproject.toml, '
            "then re-lock\n"
            "    - toolchain build --release --team-id ABCDE12345\n"
            "    - export KIVY_IOS_TEAM_ID=ABCDE12345"
        )
    return team_id


def build_command(
    xb: XcodeBuild,
    target: str,
    *,
    arch: str | None = None,
    derived_data_path: str | Path | None = None,
    signing_identity: str | None = None,
) -> list[str]:
    """`xcodebuild build` argv for --simulator/--device (Debug).

    ``derived_data_path`` pins where the ``.app`` is written so ``toolchain run``
    can locate the product deterministically. ``signing_identity`` overrides the
    project's baked ``CODE_SIGN_IDENTITY`` for device builds (simulator builds are
    unsigned, so it is ignored there).
    """
    cmd = [
        "xcodebuild",
        "-project",
        str(xb.project_path),
        "-scheme",
        xb.scheme,
        "-configuration",
        configuration_for(target),
        "-sdk",
        sdk_for(target),
    ]
    if derived_data_path is not None:
        cmd += ["-derivedDataPath", str(derived_data_path)]
    # python.org's install_stdlib uses lib-$ARCHS; a universal simulator build
    # (arm64 x86_64) produces an invalid path. Pin a single arch for CLI builds.
    if target == "simulator":
        cmd += [f"ARCHS={arch or default_simulator_arch()}", "ONLY_ACTIVE_ARCH=NO"]
    elif signing_identity:
        cmd.append(f"CODE_SIGN_IDENTITY={signing_identity}")
    cmd.append("build")
    return cmd


def product_app_path(derived_data_path: str | Path, scheme: str, target: str) -> Path:
    """Path to the built ``<scheme>.app`` under a pinned DerivedData dir."""
    sdk = sdk_for(target)
    config = configuration_for(target)
    return (
        Path(derived_data_path)
        / "Build"
        / "Products"
        / f"{config}-{sdk}"
        / f"{scheme}.app"
    )


def archive_command(
    xb: XcodeBuild, *, signing_identity: str | None = None
) -> list[str]:
    """`xcodebuild archive` argv for --release (step 7.1).

    ``signing_identity`` overrides the project's baked ``CODE_SIGN_IDENTITY`` for
    the archive's signing step.
    """
    cmd = [
        "xcodebuild",
        "archive",
        "-project",
        str(xb.project_path),
        "-scheme",
        xb.scheme,
        "-configuration",
        "Release",
        "-sdk",
        "iphoneos",
        "-archivePath",
        str(xb.archive_path),
    ]
    if signing_identity:
        cmd.append(f"CODE_SIGN_IDENTITY={signing_identity}")
    return cmd


def export_command(xb: XcodeBuild, options_plist: Path) -> list[str]:
    """`xcodebuild -exportArchive` argv for --release (step 7.2)."""
    return [
        "xcodebuild",
        "-exportArchive",
        "-archivePath",
        str(xb.archive_path),
        "-exportPath",
        str(xb.build_dir),
        "-exportOptionsPlist",
        str(options_plist),
    ]


def export_options_plist(
    *,
    method: str,
    team_id: str,
    upload_symbols: bool = True,
    signing_identity: str | None = None,
) -> dict:
    """Map --export-method + signing to ExportOptions.plist keys (spec 05).

    ``signing_identity`` pins the certificate used to re-sign during export
    (``-exportArchive``); omitted, Xcode selects one for the export method.
    """
    if method not in EXPORT_METHOD:
        raise ValueError(f"unknown export method {method!r}")
    options: dict = {
        "method": EXPORT_METHOD[method],
        "teamID": team_id,
        "uploadSymbols": upload_symbols,
    }
    if signing_identity:
        options["signingCertificate"] = signing_identity
    return options
