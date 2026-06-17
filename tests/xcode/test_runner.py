"""Phase 6 — process funnel + simctl/devicectl/open argv builders."""

from __future__ import annotations

import pytest

from kivy_ios.xcode.runner import (
    CommandError,
    devicectl_install,
    devicectl_launch,
    open_command,
    parse_simctl_devices,
    pick_simulator,
    resolve_simulator_destination,
    run_command,
    simctl_boot,
    simctl_install,
    simctl_launch,
)


class _Proc:
    def __init__(self, rc, out="", err=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err


class TestRunCommand:
    def test_success_returns_proc(self):
        proc = run_command(["true"], runner=lambda *a, **k: _Proc(0, "ok"))
        assert proc.stdout == "ok"

    def test_failure_raises(self):
        with pytest.raises(CommandError) as exc:
            run_command(["false"], runner=lambda *a, **k: _Proc(2, err="boom"))
        assert exc.value.returncode == 2
        assert "boom" in str(exc.value)

    def test_check_false_swallows(self):
        proc = run_command(["x"], runner=lambda *a, **k: _Proc(1, "out"), check=False)
        assert proc.returncode == 1


class TestArgvBuilders:
    def test_open(self, tmp_path):
        assert open_command(tmp_path / "x.xcodeproj") == [
            "open",
            str(tmp_path / "x.xcodeproj"),
        ]

    def test_simctl(self):
        assert simctl_boot("UDID")[:3] == ["xcrun", "simctl", "boot"]
        assert simctl_install("UDID", "/a.app")[-1] == "/a.app"
        launch = simctl_launch("UDID", "org.x.app")
        assert "--console-pty" in launch
        assert launch[-2:] == ["UDID", "org.x.app"]

    def test_simctl_launch_no_console(self):
        assert "--console-pty" not in simctl_launch("U", "b", console=False)

    def test_devicectl(self):
        inst = devicectl_install("UDID", "/a.app")
        assert inst[:4] == ["xcrun", "devicectl", "device", "install"]
        assert "--device" in inst
        launch = devicectl_launch("UDID", "org.x.app")
        assert launch[:5] == [
            "xcrun",
            "devicectl",
            "device",
            "process",
            "launch",
        ]
        assert launch[-1] == "org.x.app"


class TestSimulatorSelection:
    _PAYLOAD = {
        "devices": {
            "com.apple.CoreSimulator.SimRuntime.iOS-17-2": [
                {
                    "udid": "OLD-UDID",
                    "name": "iPhone 15",
                    "state": "Shutdown",
                    "isAvailable": True,
                }
            ],
            "com.apple.CoreSimulator.SimRuntime.iOS-26-5": [
                {
                    "udid": "NEW-UDID",
                    "name": "iPhone 17",
                    "state": "Shutdown",
                    "isAvailable": True,
                },
                {
                    "udid": "BOOT-UDID",
                    "name": "iPhone 15 Pro",
                    "state": "Booted",
                    "isAvailable": True,
                },
            ],
        }
    }

    def test_parse_devices(self):
        devices = parse_simctl_devices(self._PAYLOAD)
        assert len(devices) == 3
        assert devices[0].runtime == "17.2"

    def test_pick_booted_simulator(self):
        devices = parse_simctl_devices(self._PAYLOAD)
        picked = pick_simulator(devices)
        assert picked.udid == "BOOT-UDID"

    def test_pick_newest_iphone_when_none_booted(self):
        payload = {
            "devices": {
                k: [d for d in v if d["state"] != "Booted"]
                for k, v in self._PAYLOAD["devices"].items()
            }
        }
        devices = parse_simctl_devices(payload)
        picked = pick_simulator(devices)
        assert picked.udid == "NEW-UDID"

    def test_pick_by_name(self):
        devices = parse_simctl_devices(self._PAYLOAD)
        picked = pick_simulator(devices, "iPhone 15")
        assert picked.udid == "OLD-UDID"

    def test_resolve_boots_default(self):
        calls: list[list[str]] = []

        def fake(argv, capture_output=True, text=True):
            calls.append(argv)
            if "-j" in argv:
                import json

                return _Proc(0, json.dumps(self._PAYLOAD))
            return _Proc(0)

        device = resolve_simulator_destination(None, runner=fake)
        assert device.udid == "BOOT-UDID"
        assert simctl_boot("x")[:3] == ["xcrun", "simctl", "boot"]  # sanity
        assert not any(c[:3] == ["xcrun", "simctl", "boot"] for c in calls)

    def test_resolve_boots_shutdown_default(self):
        payload = {
            "devices": {
                "com.apple.CoreSimulator.SimRuntime.iOS-26-5": [
                    {
                        "udid": "NEW-UDID",
                        "name": "iPhone 17",
                        "state": "Shutdown",
                        "isAvailable": True,
                    }
                ]
            }
        }
        calls: list[list[str]] = []

        def fake(argv, capture_output=True, text=True):
            calls.append(argv)
            if "-j" in argv:
                import json

                return _Proc(0, json.dumps(payload))
            return _Proc(0)

        device = resolve_simulator_destination(None, runner=fake)
        assert device.udid == "NEW-UDID"
        assert ["xcrun", "simctl", "boot", "NEW-UDID"] in calls
        assert ["open", "-a", "Simulator"] in calls
