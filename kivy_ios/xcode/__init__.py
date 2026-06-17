"""xcodebuild / simctl / devicectl command construction and execution (spec 05).

The command builders are pure functions returning ``argv`` lists (and the
``ExportOptions.plist`` dict), so they unit-test hermetically. Actual process
execution funnels through a single injectable ``run`` helper.
"""

from __future__ import annotations

from .commands import (
    SigningError,
    XcodeBuild,
    archive_command,
    build_command,
    export_command,
    export_options_plist,
    preflight_signing,
    product_app_path,
    resolve_team_id,
    sdk_for,
)
from .runner import (
    CommandError,
    SimulatorDevice,
    devicectl_install,
    devicectl_launch,
    devicectl_list,
    open_command,
    parse_simctl_devices,
    pick_simulator,
    resolve_simulator_destination,
    run_command,
    simctl_boot,
    simctl_install,
    simctl_launch,
    simctl_list,
)

__all__ = [
    "XcodeBuild",
    "SigningError",
    "build_command",
    "archive_command",
    "export_command",
    "export_options_plist",
    "preflight_signing",
    "product_app_path",
    "resolve_team_id",
    "sdk_for",
    "run_command",
    "open_command",
    "CommandError",
    "SimulatorDevice",
    "parse_simctl_devices",
    "pick_simulator",
    "resolve_simulator_destination",
    "simctl_boot",
    "simctl_install",
    "simctl_launch",
    "simctl_list",
    "devicectl_install",
    "devicectl_launch",
    "devicectl_list",
]
