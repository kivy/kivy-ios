"""``toolchain run`` — build, install, and launch on a simulator/device (spec 05)."""

from __future__ import annotations

from pathlib import Path

import click

from ..config import ConfigError, load_config
from ..xcode import (
    CommandError,
    SigningError,
    XcodeBuild,
    build_command,
    devicectl_install,
    devicectl_launch,
    devicectl_list,
    preflight_signing,
    product_app_path,
    resolve_simulator_destination,
    run_command,
    simctl_install,
    simctl_launch,
    simctl_list,
)
from ._common import ToolchainError, find_pyproject
from .build import prepare_build


@click.command()
@click.option(
    "--simulator",
    "target",
    flag_value="simulator",
    default=True,
    help="Target the iOS simulator (default).",
)
@click.option(
    "--device", "target", flag_value="device", help="Target a connected device."
)
@click.option(
    "--destination", default=None, help="Specific simulator/device by name or UDID."
)
@click.option(
    "--list-devices",
    is_flag=True,
    help="Print available simulators and devices, then exit.",
)
@click.option(
    "--no-build",
    is_flag=True,
    help="Skip the implicit build; install + launch the existing app.",
)
def run(
    target: str, destination: str | None, list_devices: bool, no_build: bool
) -> None:
    """Build (unless --no-build), install, and launch the app."""
    if list_devices:
        _list_devices()
        return

    pyproject = find_pyproject()
    project_root = pyproject.parent
    try:
        config = load_config(pyproject)
    except ConfigError as exc:
        raise ToolchainError(exc.format()) from exc

    xb = XcodeBuild.from_config(config, project_root)
    derived_data = xb.build_dir / "DerivedData"

    try:
        if not no_build:
            if target == "device":
                preflight_signing(config, "device")
            prepare_build(
                config,
                project_root,
                target=target,
                arch=None,
                no_verify_lock=False,
                no_cache=False,
            )
            click.echo(f"xcodebuild build ({target}) ...")
            run_command(build_command(xb, target, derived_data_path=derived_data))

        app = product_app_path(derived_data, xb.scheme, target)
        if not app.exists():
            raise ToolchainError(
                f"built app not found at {app}.\n"
                "  Run without --no-build, or open the project in Xcode and build "
                "once to populate DerivedData."
            )

        bundle_id = config.ios_required.bundle_id
        if target == "simulator":
            _run_simulator(destination, app, bundle_id)
        else:
            _run_device(_resolve_device_destination(destination), app, bundle_id)
    except SigningError as exc:
        raise ToolchainError(str(exc)) from exc
    except CommandError as exc:
        raise ToolchainError(str(exc)) from exc


def _resolve_device_destination(destination: str | None) -> str:
    return destination or "first"


def _run_simulator(destination: str | None, app: Path, bundle_id: str) -> None:
    device = resolve_simulator_destination(destination)
    label = f"{device.name} ({device.udid})"
    click.echo(f"Installing on simulator {label} ...")
    run_command(simctl_install(device.udid, app))
    click.echo(f"Launching {bundle_id} ...")
    run_command(simctl_launch(device.udid, bundle_id))


def _run_device(dest: str, app: Path, bundle_id: str) -> None:
    click.echo(f"Installing on device {dest} ...")
    run_command(devicectl_install(dest, app))
    click.echo(f"Launching {bundle_id} ...")
    run_command(devicectl_launch(dest, bundle_id))


def _list_devices() -> None:
    for builder in (simctl_list, devicectl_list):
        proc = run_command(builder(), check=False)
        if proc.stdout:
            click.echo(proc.stdout)
