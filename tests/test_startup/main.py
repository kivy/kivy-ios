"""Generated-app startup probe; success requires a running Kivy Clock callback."""
import sys

original_argv = list(sys.argv)

# Capture native argv before any other imports can inspect it.
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
from pathlib import Path  # noqa: E402
import traceback  # noqa: E402


result_dir = Path.home() / "Documents" / "ci-smoke"
payload = None


def write_result():
    temporary = result_dir / "result.json.tmp"
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream)
    os.replace(str(temporary), str(result_dir / "result.json"))


def report_failure():
    # Before a valid request, no result can be attributed to this launch.
    if payload is not None:
        payload.update(status="failed", error=traceback.format_exc())
        write_result()


try:
    with (result_dir / "request.json").open(encoding="utf-8") as stream:
        request = json.load(stream)
    cases = {"ordinary": [], "native-option": ["-NSDocumentRevisionsDebugMode", "YES"]}
    if (not isinstance(request, dict) or
            not isinstance(request.get("launch_id"), str) or not request["launch_id"] or
            not isinstance(request.get("case"), str) or request["case"] not in cases):
        raise RuntimeError("Invalid startup request")
    payload = {"launch_id": request["launch_id"], "case": request["case"],
               "stage": "bootstrap", "status": "running"}
    write_result()
    expected_args = cases[request["case"]]
    if not original_argv or not original_argv[0]:
        raise RuntimeError("Missing executable argv[0]")
    if original_argv[1:] != expected_args:
        raise RuntimeError("Native argv was consumed or changed: {!r}".format(original_argv))

    # This disables only Kivy's parser, after native CPython initialization.
    os.environ["KIVY_NO_ARGS"] = "1"
    payload["stage"] = "bundled-imports"
    write_result()
    import sqlite3
    import ssl
    import zlib

    sample = {"startup": [1, "ios"]}
    if json.loads(json.dumps(sample)) != sample:
        raise RuntimeError("JSON round trip failed")
    if zlib.decompress(zlib.compress(b"startup")) != b"startup":
        raise RuntimeError("zlib round trip failed")
    connection = sqlite3.connect(":memory:")
    try:
        if connection.execute("select 1").fetchone() != (1,):
            raise RuntimeError("SQLite operation failed")
    finally:
        connection.close()
    if not ssl.OPENSSL_VERSION:
        raise RuntimeError("SSL version missing")
    payload["stage"] = "kivy-import"
    write_result()
    from kivy.app import App
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.uix.widget import Widget

    class StartupSmokeApp(App):
        def build(self):
            return Widget()

        def on_start(self):
            Clock.schedule_once(self.report_event_loop, 0)

        def report_event_loop(self, dt):
            try:
                payload["stage"] = "kivy-event-loop"
                if Window is None or type(Window).__name__ != "WindowSDL":
                    raise RuntimeError("Expected an SDL2 window")
                if len(Window.size) != 2 or not all(
                        math.isfinite(value) and value > 0 for value in Window.size):
                    raise RuntimeError("Expected positive finite window dimensions")
                payload["status"] = "passed"
                write_result()
            except BaseException:
                report_failure()
            finally:
                self.stop()

    payload["stage"] = "kivy-run"
    write_result()
    StartupSmokeApp().run()
    if payload["status"] == "running":
        raise RuntimeError("App returned without event-loop completion")
except BaseException:
    report_failure()
    raise
