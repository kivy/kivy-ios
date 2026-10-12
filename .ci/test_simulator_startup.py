#!/usr/bin/env python3
"""Build a Release simulator app and require two fresh event-loop completions."""
import argparse
import json
import math
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
CASES = {"ordinary": [], "native-option": ["-NSDocumentRevisionsDebugMode", "YES"]}


class SmokeError(RuntimeError):
    pass


def require(condition, reason):
    if not condition:
        raise SmokeError(reason)


def run_command(args, logfile, timeout=30, allow_failure=False):
    with logfile.open("w", encoding="utf-8") as stream:
        stream.write("Command: {!r}\nTimeout: {}s\n".format(args, timeout))
        stream.flush()
        process = subprocess.Popen(args, cwd=ROOT, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            process.wait(timeout=timeout)
        except BaseException:
            # xcodebuild children must not survive a timeout or interruption.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise
    output = logfile.read_text(encoding="utf-8", errors="replace").split("\n", 2)[2]
    require(allow_failure or process.returncode == 0,
            "Command failed ({}); see {}".format(process.returncode, logfile))
    return process.returncode, output


def terminate_app(udid, bundle, logfile, timeout=30):
    code, output = run_command(["xcrun", "simctl", "terminate", udid, bundle],
                               logfile, timeout, allow_failure=True)
    require(code == 0 or (code == 3 and any(message in output.lower() for message in (
        "found nothing to terminate", "not running", "no such process",
    ))), "Unexpected simctl terminate failure; see {}: {}".format(logfile, output))


def version_tuple(value):
    require(isinstance(value, str) and re.fullmatch(r"\d+(?:\.\d+)*", value),
            "Unsupported numeric version: {!r}".format(value))
    parts = tuple(int(part) for part in value.split("."))
    return parts + (0,) * max(0, 3 - len(parts))


def select_simulator(devices, runtimes, minimum):
    compatible = [runtime for runtime in runtimes["runtimes"]
                  if runtime.get("isAvailable") and
                  runtime.get("identifier", "").startswith("com.apple.CoreSimulator.SimRuntime.iOS-") and
                  version_tuple(runtime["version"]) >= version_tuple(minimum)]
    for runtime in sorted(compatible, key=lambda item: version_tuple(item["version"]), reverse=True):
        for device in devices["devices"].get(runtime["identifier"], []):
            iphone = ".iPhone-" in device.get("deviceTypeIdentifier", "")
            if device.get("isAvailable") and iphone:
                return dict(device, runtime_version=runtime["version"],
                            runtime_identifier=runtime["identifier"])
    raise SmokeError("No compatible available iPhone at or above iOS {}; see inventories".format(minimum))


def atomic_json(filename, value):
    temporary = filename.with_suffix(filename.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(filename)


def wait_for_result(filename, request, timeout, diagnostics, clock=time.monotonic, sleep=time.sleep):
    end = clock() + timeout
    stage = "no-result"
    while clock() < end:
        if filename.exists():
            try:
                result = json.loads(filename.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError) as error:
                raise SmokeError("Malformed result JSON in {}: {}".format(filename, error)) from error
            require(isinstance(result, dict), "Result must be an object: {}".format(filename))
            require(isinstance(result.get("launch_id"), str) and result["launch_id"] and
                    isinstance(result.get("case"), str) and result["case"],
                    "Invalid result launch_id/case identity: {}".format(filename))
            # Only this launch can pass; an old process may still leave output.
            if result["launch_id"] == request["launch_id"]:
                require(result["case"] == request["case"], "Wrong result case")
                stage = result.get("stage")
                require(isinstance(stage, str) and stage and
                        result.get("status") in ("running", "passed", "failed"), "Invalid result stage/status")
                if result["status"] == "failed":
                    raise SmokeError("App failed at {}: {}".format(stage, result.get("error", "no traceback")))
                if result["status"] == "passed":
                    # on_start runs before the event loop and cannot prove completion.
                    require(stage == "kivy-event-loop", "Passed result has not reached kivy-event-loop")
                    require(clock() < end, "Result arrived after deadline")
                    return result
            else:
                stage = "stale-result"
        sleep(min(0.5, max(0, end - clock())))
    raise SmokeError("{} timed out; last stage: {}; diagnostics: {}".format(request["case"], stage, diagnostics))


def execute(args):
    artifacts = Path(args.artifacts).resolve()
    require(not artifacts.exists() or (artifacts.is_dir() and not any(artifacts.iterdir())),
            "Preexisting artifact outputs; use a fresh directory: {}".format(artifacts))
    diagnostics = artifacts / "diagnostics"
    diagnostics.mkdir(parents=True)
    selected = None
    bundle = None
    installed = False
    owns_boot = False
    failed = True
    case = "setup"
    try:
        architecture = platform.machine()
        atomic_json(diagnostics / "host.json", {"architecture": architecture, "configuration": "Release"})
        require(platform.system() == "Darwin" and architecture == "arm64",
                "Startup smoke requires an Apple Silicon macOS host")
        run_command(["xcode-select", "-p"], diagnostics / "xcode-select.log")
        run_command(["xcodebuild", "-version"], diagnostics / "xcode-version.log")
        run_command(["xcrun", "--sdk", "iphonesimulator", "--show-sdk-version"], diagnostics / "sdk.log")
        generated = ROOT / "startupsmoke-ios"
        require(not generated.exists(), "Preexisting startupsmoke-ios; move/remove your disposable project before rerunning")
        run_command(["toolchain", "create", "StartupSmoke", str(ROOT / "tests/test_startup")], diagnostics / "create.log")
        derived = artifacts / "DerivedData"
        run_command(["xcodebuild", "-project", str(generated / "startupsmoke.xcodeproj"),
                     "-scheme", "startupsmoke", "-configuration", "Release",
                     "-destination", "generic/platform=iOS Simulator", "-derivedDataPath", str(derived),
                     "-resultBundlePath", str(artifacts / "build.xcresult"), "build",
                     "CODE_SIGNING_ALLOWED=NO", "ARCHS=arm64"], diagnostics / "build.log", timeout=600)
        product = derived / "Build/Products/Release-iphonesimulator/startupsmoke.app"
        with (product / "Info.plist").open("rb") as stream:
            info = plistlib.load(stream)
        bundle = info["CFBundleIdentifier"]
        require(isinstance(bundle, str) and bundle, "Built product has invalid bundle identifier")
        minimum = info["MinimumOSVersion"]
        atomic_json(diagnostics / "product.json", {"bundle": bundle, "minimum": minimum})
        _, devices = run_command(["xcrun", "simctl", "list", "devices", "--json"], diagnostics / "devices.log")
        _, runtimes = run_command(["xcrun", "simctl", "list", "runtimes", "--json"], diagnostics / "runtimes.log")
        (diagnostics / "devices.json").write_text(devices, encoding="utf-8")
        (diagnostics / "runtimes.json").write_text(runtimes, encoding="utf-8")
        selected = select_simulator(json.loads(devices), json.loads(runtimes), minimum)
        atomic_json(diagnostics / "selected.json", selected)
        udid = selected["udid"]
        if selected.get("state") != "Booted":
            owns_boot = True
            run_command(["xcrun", "simctl", "boot", udid], diagnostics / "boot.log")
        run_command(["xcrun", "simctl", "bootstatus", udid, "-b"], diagnostics / "bootstatus.log", timeout=180)
        # A partial installation must also be cleaned up.
        installed = True
        run_command(["xcrun", "simctl", "install", udid, str(product)], diagnostics / "install.log")
        _, data_path = run_command(["xcrun", "simctl", "get_app_container", udid, bundle, "data"],
                                   diagnostics / "data-container.log")
        result_dir = Path(data_path.strip()) / "Documents/ci-smoke"
        result_dir.mkdir(parents=True, exist_ok=True)
        for case, trailing_args in CASES.items():
            case_dir = diagnostics / case
            case_dir.mkdir()
            try:
                terminate_app(udid, bundle, case_dir / "terminate.log")
                for name in ("result.json", "result.json.tmp"):
                    path = result_dir / name
                    if path.exists():
                        path.unlink()
                request = {"launch_id": uuid.uuid4().hex, "case": case}
                atomic_json(result_dir / "request.json", request)
                atomic_json(case_dir / "request.json", request)
                run_command(["xcrun", "simctl", "launch", "--stdout=" + str(case_dir / "stdout.log"),
                             "--stderr=" + str(case_dir / "stderr.log"), udid, bundle] + trailing_args,
                            case_dir / "launch.log")
                wait_for_result(result_dir / "result.json", request, args.result_timeout, case_dir)
            finally:
                if (result_dir / "result.json").exists():
                    shutil.copyfile(result_dir / "result.json", case_dir / "result.json")
            print("{} passed on {} ({})".format(case, selected["name"], udid), flush=True)
        failed = False
    except BaseException as error:
        message = "{} on {}: {}; diagnostics: {}".format(case, selected, error, diagnostics)
        (diagnostics / "error.txt").write_text(message + "\n", encoding="utf-8")
        raise
    finally:
        cleanup_errors = []

        def best_effort(operation):
            try:
                operation()
            except BaseException as error:
                cleanup_errors.append(str(error))

        if selected:
            udid = selected["udid"]
            if installed:
                best_effort(lambda: terminate_app(udid, bundle, diagnostics / "cleanup-terminate.log", timeout=5))
                best_effort(lambda: run_command(["xcrun", "simctl", "uninstall", udid, bundle],
                                                diagnostics / "uninstall.log", timeout=5))
            if owns_boot:
                best_effort(lambda: run_command(["xcrun", "simctl", "shutdown", udid],
                                                diagnostics / "shutdown.log", timeout=5))
        best_effort(lambda: atomic_json(diagnostics / "cleanup.json", {"errors": cleanup_errors}))
        if cleanup_errors:
            print("Cleanup/diagnostics errors: " + repr(cleanup_errors), file=sys.stderr)
            if not failed:
                raise SmokeError("Smoke passed but cleanup failed; see {}".format(diagnostics / "cleanup.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-timeout", type=float, default=60)
    parser.add_argument("--artifacts", default="build/ci-startup")
    args = parser.parse_args()
    if not math.isfinite(args.result_timeout) or args.result_timeout <= 0:
        parser.error("result timeout must be positive finite seconds")
    try:
        execute(args)
    except (Exception, KeyboardInterrupt) as error:
        print("Startup smoke failed: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
