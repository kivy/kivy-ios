"""Process execution + simctl/devicectl command builders (spec 05 run/open).

``run_command`` is the single execution funnel (injectable for tests). The
simctl/devicectl builders are pure argv factories so the run sequence is
unit-testable without a simulator or device.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


class CommandError(Exception):
    """A spawned tool exited non-zero."""

    def __init__(self, argv: list[str], returncode: int, output: str = "") -> None:
        self.argv = argv
        self.returncode = returncode
        self.output = output
        super().__init__(
            f"command failed ({returncode}): {' '.join(argv)}"
            + (f"\n{output}" if output else "")
        )


def run_command(argv: list[str], *, runner=subprocess.run, check: bool = True):
    proc = runner(argv, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise CommandError(argv, proc.returncode, proc.stderr or proc.stdout or "")
    return proc


def open_command(xcodeproj: str | Path) -> list[str]:
    return ["open", str(xcodeproj)]


# ---- simulator (simctl) -------------------------------------------------


def simctl_boot(destination: str) -> list[str]:
    return ["xcrun", "simctl", "boot", destination]


def simctl_install(destination: str, app_path: str | Path) -> list[str]:
    return ["xcrun", "simctl", "install", destination, str(app_path)]


def simctl_launch(
    destination: str, bundle_id: str, *, console: bool = True
) -> list[str]:
    cmd = ["xcrun", "simctl", "launch"]
    if console:
        cmd.append("--console-pty")
    cmd += [destination, bundle_id]
    return cmd


def simctl_list() -> list[str]:
    return ["xcrun", "simctl", "list", "devices", "available"]


def simctl_list_json(*, state: str = "available") -> list[str]:
    return ["xcrun", "simctl", "list", "devices", state, "-j"]


def open_simulator_app() -> list[str]:
    return ["open", "-a", "Simulator"]


@dataclass(frozen=True)
class SimulatorDevice:
    udid: str
    name: str
    state: str
    runtime: str


def parse_simctl_devices(payload: dict) -> list[SimulatorDevice]:
    """Flatten ``simctl list devices … -j`` output into a single device list."""
    devices: list[SimulatorDevice] = []
    for runtime_key, entries in payload.get("devices", {}).items():
        runtime = _runtime_label(runtime_key)
        for entry in entries:
            if not entry.get("isAvailable", True):
                continue
            devices.append(
                SimulatorDevice(
                    udid=entry["udid"],
                    name=entry["name"],
                    state=entry.get("state", "Shutdown"),
                    runtime=runtime,
                )
            )
    return devices


def pick_simulator(
    devices: list[SimulatorDevice], destination: str | None = None
) -> SimulatorDevice:
    """Choose a simulator by explicit destination, booted state, or best default."""
    if not devices:
        raise CommandError(
            ["simctl"],
            1,
            "no iOS simulators available (install one in Xcode > Settings > Components)",
        )
    if destination:
        return _match_simulator(devices, destination)
    booted = [d for d in devices if d.state == "Booted"]
    if booted:
        return booted[0]
    iphones = [d for d in devices if "iphone" in d.name.lower()]
    return max(iphones or devices, key=_default_simulator_sort_key)


def resolve_simulator_destination(
    destination: str | None,
    *,
    runner=subprocess.run,
) -> SimulatorDevice:
    """Return the simulator to target, booting a default when none is running."""
    proc = run_command(simctl_list_json(), runner=runner)
    devices = parse_simctl_devices(json.loads(proc.stdout))
    device = pick_simulator(devices, destination)
    if device.state != "Booted":
        run_command(simctl_boot(device.udid), runner=runner, check=False)
        run_command(open_simulator_app(), runner=runner, check=False)
    return device


def _match_simulator(
    devices: list[SimulatorDevice], destination: str
) -> SimulatorDevice:
    dest = destination.lower()
    for device in devices:
        if device.udid.lower() == dest:
            return device
    for device in devices:
        if device.name.lower() == dest:
            return device
    for device in devices:
        if dest in device.name.lower():
            return device
    raise CommandError(
        ["simctl"],
        1,
        f"no simulator matches {destination!r} (run `toolchain run --list-devices`)",
    )


def _runtime_label(runtime_key: str) -> str:
    # com.apple.CoreSimulator.SimRuntime.iOS-26-5 -> 26.5
    tail = runtime_key.rsplit(".", 1)[-1]
    if tail.startswith("iOS-"):
        return tail[4:].replace("-", ".")
    return tail


def _default_simulator_sort_key(device: SimulatorDevice) -> tuple:
    parts: list[int] = []
    for piece in device.runtime.split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            parts.append(0)
    return (tuple(parts), device.name)


# ---- device (devicectl) -------------------------------------------------


def devicectl_install(destination: str, app_path: str | Path) -> list[str]:
    return [
        "xcrun",
        "devicectl",
        "device",
        "install",
        "app",
        "--device",
        destination,
        str(app_path),
    ]


def devicectl_launch(destination: str, bundle_id: str) -> list[str]:
    return [
        "xcrun",
        "devicectl",
        "device",
        "process",
        "launch",
        "--device",
        destination,
        bundle_id,
    ]


def devicectl_list() -> list[str]:
    return ["xcrun", "devicectl", "list", "devices"]
