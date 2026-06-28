"""pyobjus-deviceinfo — a working pyobjus example for kivy-ios 3.0.

Reads device and OS facts from two stock Apple frameworks using pyobjus'
``autoclass`` — no Swift, no SPM, no hand-rolled ctypes:

  UIDevice (UIKit)
      name, model, system name/version, battery level + charging state.

  NSProcessInfo (Foundation)
      OS version string, physical memory, CPU core counts, thermal state.

Why this works (and pyobjus-ball uses ctypes instead): pyobjus handles
Objective-C methods that return objects (``NSString``) and plain scalars
(``BOOL``, ``NSInteger``, ``float``, ``unsigned long long``) cleanly. It
struggles only with C structs of doubles (e.g. ``CMAcceleration``) and with
introspecting a few classes' property lists — none of which this app uses.

pyobjus exposes Objective-C *properties* as plain attributes (no call):
``device.systemVersion`` returns an ``NSString`` proxy and
``proc.processorCount`` returns an int directly. Real *methods* are called:
class methods like ``UIDevice.currentDevice()`` and the setter
``device.setBatteryMonitoringEnabled_(True)`` (trailing ``_`` per colon).

On desktop (no pyobjus / no UIKit) the app shows a small Python ``platform``
fallback so the layout can still be exercised. On the iOS Simulator the
native path runs — only ``batteryLevel`` is unavailable there (reported -1).
"""

from __future__ import annotations

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

DARK_BG = (0.08, 0.09, 0.12, 1)

_BATTERY_STATE = {0: "unknown", 1: "unplugged", 2: "charging", 3: "full"}
_THERMAL_STATE = {0: "nominal", 1: "fair", 2: "serious", 3: "critical"}


def _nsstr(value) -> str:
    """Convert a pyobjus NSString proxy (or anything) into a Python str."""
    if value is None:
        return ""
    try:
        raw = value.UTF8String()
    except AttributeError:
        return str(value)
    return raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)


def _format_bytes(num: int) -> str:
    size = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{num} B"


def read_device_info() -> tuple[bool, list[tuple[str, str]]]:
    """Return ``(native, rows)`` where rows is a list of (label, value).

    Uses pyobjus on iOS; falls back to the Python ``platform`` module
    everywhere else so the UI still renders.
    """
    try:
        from kivy.utils import platform

        if platform != "ios":
            return False, _desktop_rows()

        from pyobjus import autoclass

        # currentDevice / processInfo are class *methods* -> call them.
        device = autoclass("UIDevice").currentDevice()
        device.setBatteryMonitoringEnabled_(True)  # setter method (takes an arg)
        proc = autoclass("NSProcessInfo").processInfo()

        # Everything below is an Objective-C *property*: pyobjus exposes these
        # as plain attributes (no parentheses). NSString properties return a
        # proxy on which we call UTF8String(); scalars come back directly.
        battery_level = float(device.batteryLevel)
        battery = (
            "n/a (Simulator)"
            if battery_level < 0
            else f"{battery_level * 100:.0f}%  "
            f"({_BATTERY_STATE.get(int(device.batteryState), 'unknown')})"
        )

        rows = [
            ("Name", _nsstr(device.name)),
            ("Model", _nsstr(device.model)),
            (
                "System",
                f"{_nsstr(device.systemName)} {_nsstr(device.systemVersion)}",
            ),
            ("OS string", _nsstr(proc.operatingSystemVersionString)),
            ("Battery", battery),
            ("Memory", _format_bytes(int(proc.physicalMemory))),
            (
                "CPU cores",
                f"{int(proc.activeProcessorCount)} active / "
                f"{int(proc.processorCount)} total",
            ),
            (
                "Thermal",
                _THERMAL_STATE.get(int(proc.thermalState), "unknown"),
            ),
        ]
        return True, rows
    except Exception as exc:  # pragma: no cover — device-only path
        return False, [("pyobjus error", str(exc))]


def _desktop_rows() -> list[tuple[str, str]]:
    import os
    import platform as py_platform

    return [
        ("Name", py_platform.node()),
        ("Model", py_platform.machine()),
        ("System", f"{py_platform.system()} {py_platform.release()}"),
        ("OS string", py_platform.platform()),
        ("Battery", "n/a (desktop)"),
        ("Memory", "n/a (desktop)"),
        ("CPU cores", str(os.cpu_count() or "?")),
        ("Thermal", "n/a (desktop)"),
    ]


KV = """
<InfoRow@BoxLayout>:
    label: ""
    value: ""
    size_hint_y: None
    height: "36dp"
    spacing: "12dp"
    Label:
        size_hint_x: None
        width: "120dp"
        font_size: "14sp"
        color: 0.6, 0.6, 0.6, 1
        halign: "right"
        valign: "middle"
        text_size: self.size
        text: root.label
    Label:
        font_size: "14sp"
        halign: "left"
        valign: "middle"
        text_size: self.size
        text: root.value

<DeviceInfoRoot>:
    orientation: "vertical"
    padding: "20dp"
    spacing: "10dp"

    Label:
        size_hint_y: None
        height: "48dp"
        font_size: "16sp"
        color: 0.5, 0.85, 1.0, 1
        halign: "center"
        valign: "middle"
        text_size: self.size
        text: root.backend_text

    BoxLayout:
        id: rows
        orientation: "vertical"
        spacing: "2dp"

    Button:
        size_hint_y: None
        height: "48dp"
        text: "Refresh"
        on_release: root.refresh()

DeviceInfoRoot:
"""


class DeviceInfoRoot(BoxLayout):
    backend_text = StringProperty("")

    def on_kv_post(self, _base_widget) -> None:
        self.refresh()

    def refresh(self) -> None:
        from kivy.factory import Factory

        native, rows = read_device_info()
        self.backend_text = (
            "Source: pyobjus -> UIDevice / NSProcessInfo"
            if native
            else "Source: desktop fallback (pyobjus not on iOS)"
        )
        container = self.ids.rows
        container.clear_widgets()
        for label, value in rows:
            row = Factory.InfoRow()
            row.label = label
            row.value = value
            container.add_widget(row)


class DeviceInfoApp(App):
    def build(self) -> DeviceInfoRoot:
        Window.clearcolor = DARK_BG
        return Builder.load_string(KV)


DeviceInfoApp().run()
