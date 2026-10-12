"""Simulator startup selection and false-pass protection, without Xcode."""
import fcntl
import importlib.util
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("simulator_startup", ROOT / ".ci/test_simulator_startup.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


def udid(number):
    return "00000000-0000-0000-0000-{:012d}".format(number)


def inventories():
    runtimes = {"runtimes": []}
    devices = {"devices": {}}
    for index, version in enumerate(("14.0", "17.9", "17.10", "18.5", "19.0")):
        identifier = "com.apple.CoreSimulator.SimRuntime.iOS-" + version.replace(".", "-")
        runtimes["runtimes"].append({"identifier": identifier, "version": version,
                                     "isAvailable": version != "19.0"})
        devices["devices"][identifier] = [{
            "name": "iPhone Z", "udid": udid(index), "isAvailable": True,
            "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-16",
            "state": "Shutdown",
        }]
    return devices, runtimes


def test_selector_uses_newest_compatible_numeric_runtime():
    devices, runtimes = inventories()
    assert smoke.select_simulator(devices, runtimes, "15.0")["udid"] == udid(3)
    runtimes["runtimes"][4]["isAvailable"] = True
    assert smoke.select_simulator(devices, runtimes, "15.0")["udid"] == udid(4)
    runtimes["runtimes"][4]["isAvailable"] = False
    devices["devices"][runtimes["runtimes"][3]["identifier"]][0]["isAvailable"] = False
    assert smoke.select_simulator(devices, runtimes, "17.9")["udid"] == udid(2)


def test_selector_preserves_inventory_order_and_device_type():
    devices, runtimes = inventories()
    group = devices["devices"][runtimes["runtimes"][3]["identifier"]]
    group.append(dict(group[0], name="iPhone A", udid=udid(6)))
    assert smoke.select_simulator(devices, runtimes, "18.0")["udid"] == udid(3)
    group[0].update(name="iPhone renamed iPad", deviceTypeIdentifier="com.apple.CoreSimulator.SimDeviceType.iPad-Pro")
    assert smoke.select_simulator(devices, runtimes, "18.0")["udid"] == udid(6)
    group[1].update(name="Renamed device", deviceTypeIdentifier="com.apple.CoreSimulator.SimDeviceType.iPhone-16")
    assert smoke.select_simulator(devices, runtimes, "18.0")["udid"] == udid(6)


@pytest.mark.parametrize("excluded", ["runtime", "device", "ipad", "minimum", "empty", "non-ios", "missing-type"])
def test_selector_rejects_missing_candidates(excluded):
    devices, runtimes = inventories()
    runtime = runtimes["runtimes"][3]
    device = devices["devices"][runtime["identifier"]][0]
    minimum = "18.0"
    if excluded == "runtime":
        runtime["isAvailable"] = False
    elif excluded == "device":
        device["isAvailable"] = False
    elif excluded == "ipad":
        device.update(name="iPad Pro", deviceTypeIdentifier="com.apple.CoreSimulator.SimDeviceType.iPad-Pro")
    elif excluded == "minimum":
        minimum = "18.6"
    elif excluded == "empty":
        devices["devices"] = {}
    elif excluded == "non-ios":
        runtime["identifier"] = "com.apple.CoreSimulator.SimRuntime.tvOS-18-5"
    else:
        device.pop("deviceTypeIdentifier")
    with pytest.raises(smoke.SmokeError, match="No compatible available iPhone"):
        smoke.select_simulator(devices, runtimes, minimum)


@pytest.fixture
def valid_result():
    request = {"launch_id": "fresh", "case": "ordinary"}
    result = dict(request, status="passed", stage="kivy-event-loop")
    return result, request


class Clock:
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now

    def sleep(self, delay):
        self.now += delay


@pytest.mark.parametrize("case", ["ordinary", "native-option"])
def test_current_event_loop_completion_passes(tmp_path, valid_result, case):
    result, request = valid_result
    result["case"] = request["case"] = case
    filename = tmp_path / "result.json"
    smoke.atomic_json(filename, result)
    clock = Clock()
    assert smoke.wait_for_result(filename, request, 60, tmp_path, clock, clock.sleep) == result


@pytest.mark.parametrize("kind,stage", [
    ("missing", "no-result"), ("stale", "stale-result"), ("bootstrap", "bootstrap"),
])
def test_incomplete_results_expire(tmp_path, valid_result, kind, stage):
    result, request = valid_result
    filename = tmp_path / "result.json"
    if kind == "stale":
        result["launch_id"] = "old"
    elif kind == "bootstrap":
        result.update(stage="bootstrap", status="running")
    if kind != "missing":
        smoke.atomic_json(filename, result)
    clock = Clock()
    with pytest.raises(smoke.SmokeError, match="last stage: " + stage) as error:
        smoke.wait_for_result(filename, request, 1.2, tmp_path, clock, clock.sleep)
    assert str(tmp_path) in str(error.value)
    assert request["case"] in str(error.value)
    assert clock.now == pytest.approx(1.2)


@pytest.mark.parametrize("change,reason", [
    ({"status": "failed", "error": "controlled failure"}, "App failed at kivy-event-loop: controlled failure"),
    ({"case": "wrong"}, "Wrong result case"),
    ({"launch_id": None}, "launch_id/case identity"),
    ({"launch_id": ""}, "launch_id/case identity"),
    ({"case": 1}, "launch_id/case identity"),
    ({"case": ""}, "launch_id/case identity"),
    ({"stage": "bootstrap"}, "kivy-event-loop"),
    ({"stage": "kivy-run"}, "kivy-event-loop"),
    ({"stage": None}, "stage/status"),
    ({"stage": ""}, "stage/status"),
    ({"status": "unknown"}, "stage/status"),
])
def test_current_bad_result_fails_immediately(tmp_path, valid_result, change, reason):
    result, request = valid_result
    result.update(change)
    filename = tmp_path / "result.json"
    smoke.atomic_json(filename, result)
    clock = Clock()
    with pytest.raises(smoke.SmokeError, match=reason):
        smoke.wait_for_result(filename, request, 60, tmp_path, clock, clock.sleep)
    assert clock.now == 0


@pytest.mark.parametrize("document,reason", [
    ("{bad json", "Malformed result JSON"), ("[]", "Result must be an object"),
    ('{"case": "ordinary"}', "launch_id/case identity"),
])
def test_malformed_transport_fails(tmp_path, valid_result, document, reason):
    _, request = valid_result
    filename = tmp_path / "result.json"
    filename.write_text(document, encoding="utf-8")
    clock = Clock()
    with pytest.raises(smoke.SmokeError, match=reason):
        smoke.wait_for_result(filename, request, 60, tmp_path, clock, clock.sleep)
    assert clock.now == 0


def test_fresh_result_replaces_stale(tmp_path, valid_result):
    result, request = valid_result
    filename = tmp_path / "result.json"
    smoke.atomic_json(filename, dict(result, launch_id="old"))
    clock = Clock()

    def publish(delay):
        clock.sleep(delay)
        smoke.atomic_json(filename, result)

    assert smoke.wait_for_result(filename, request, 60, tmp_path, clock, publish) == result
    assert clock.now == 0.5


def test_command_timeout_kills_child_process(tmp_path):
    lockfile = tmp_path / "child.lock"
    ready = tmp_path / "ready"
    child = (
        "import fcntl, pathlib, time; "
        "lock = open({!r}, 'w'); fcntl.flock(lock, fcntl.LOCK_EX); "
        "pathlib.Path({!r}).touch(); time.sleep(60)"
    ).format(str(lockfile), str(ready))
    parent = "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {!r}]); time.sleep(60)".format(child)
    with pytest.raises(subprocess.TimeoutExpired):
        smoke.run_command([sys.executable, "-c", parent], tmp_path / "command.log", timeout=2)
    assert ready.exists(), "Child must start before timeout to verify group cleanup"
    # The lock is released when the child exits. The runner reaps the parent,
    # but the child may not have finished exiting yet.
    deadline = time.monotonic() + 5
    with lockfile.open("r") as stream:
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)


def test_command_error_propagates_and_preserves_output(tmp_path):
    logfile = tmp_path / "command.log"
    with pytest.raises(smoke.SmokeError, match="Command failed"):
        smoke.run_command([sys.executable, "-c", "print('failure evidence'); raise SystemExit(2)"], logfile)
    assert "failure evidence" in logfile.read_text()


def test_terminate_allows_only_documented_not_running_error(tmp_path, monkeypatch):
    monkeypatch.setattr(smoke, "run_command", lambda *args, **kwargs: (3, "found nothing to terminate"))
    smoke.terminate_app("udid", "bundle", tmp_path / "terminate.log")
    monkeypatch.setattr(smoke, "run_command", lambda *args, **kwargs: (1, "simulator unavailable"))
    with pytest.raises(smoke.SmokeError, match="Unexpected simctl terminate"):
        smoke.terminate_app("udid", "bundle", tmp_path / "terminate.log")


def test_unsupported_host_retains_diagnostics_without_commands(tmp_path, monkeypatch):
    monkeypatch.setattr(smoke.platform, "system", lambda: "Linux")

    def unexpected_command(*args, **kwargs):
        pytest.fail("Unsupported host must not invoke platform commands")

    monkeypatch.setattr(smoke, "run_command", unexpected_command)
    with pytest.raises(smoke.SmokeError, match="Apple Silicon"):
        smoke.execute(SimpleNamespace(artifacts=str(tmp_path), result_timeout=60))
    diagnostics = tmp_path / "diagnostics"
    assert "Apple Silicon" in (diagnostics / "error.txt").read_text()
    assert (diagnostics / "host.json").exists()
    assert (diagnostics / "cleanup.json").exists()
