"""pyobjus-ball — an interactive kivy-ios 3.0 example.

Demonstrates calling native iOS APIs from Python using ctypes bindings to the
Objective-C runtime.

Two native APIs are exercised:

  CMMotionManager (ctypes)
      Accelerometer data to steer the ball.  pyobjus cannot decode ObjC structs
      whose fields are ``double`` (CMAcceleration = ddd), so we call
      objc_msgSend via ctypes — the same technique used in ``ios.py`` for
      UIEdgeInsets.  This is a known pyobjus limitation (kivy/pyobjus#148).

  UIScreen (ctypes)
      Read and write screen brightness from a slider.  We use ctypes here as
      well because pyobjus triggers spurious ``AttributeError`` exceptions when
      introspecting UIScreen's property list on recent iOS versions.

Both usages are good examples of the ctypes / ObjC-runtime pattern that
kivy-ios apps can use for any Objective-C API that pyobjus cannot decode
correctly.

On the Simulator (or any environment where CoreMotion is unavailable) the app
falls back to touch/drag steering so the layout can still be exercised.
"""

from __future__ import annotations

import ctypes
from random import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

DARK_BG = (0.08, 0.09, 0.12, 1)

KV = """
<BallWidget>:
    size_hint: None, None
    size: "64dp", "64dp"
    canvas:
        Color:
            hsv: root.hue, 0.9, 1.0
        Ellipse:
            pos: self.pos
            size: self.size

<PyobjusBallRoot>:
    orientation: "vertical"
    padding: "16dp"
    spacing: "8dp"

    # Mode / status banner
    Label:
        size_hint_y: None
        height: "36dp"
        font_size: "14sp"
        color: 0.5, 0.85, 1.0, 1
        text: root.status_text

    # Brightness row — hidden when native APIs unavailable
    BoxLayout:
        size_hint_y: None
        height: "44dp"
        spacing: "12dp"
        opacity: 1 if root.has_native else 0
        disabled: not root.has_native
        Label:
            size_hint_x: None
            width: "110dp"
            font_size: "13sp"
            halign: "right"
            valign: "middle"
            text_size: self.size
            text: "Brightness"
        Slider:
            id: bright_slider
            min: 0.1
            max: 1.0
            value: 0.75
            on_value: root.set_brightness(self.value)

    # Play field — also handles fallback touch steering
    Widget:
        id: field
        on_touch_move: root.on_field_touch(args[1])
        BallWidget:
            id: ball
            hue: root.ball_hue
            center: field.center

    # Bounce counter
    Label:
        size_hint_y: None
        height: "28dp"
        font_size: "13sp"
        color: 0.6, 0.6, 0.6, 1
        text: f"Bounces: {root.bounces}"

PyobjusBallRoot:
"""


class BallWidget(Widget):
    hue = NumericProperty(0.55)


class _CMAcceleration(ctypes.Structure):
    """Mirror of the ObjC ``CMAcceleration`` struct (three doubles)."""

    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
    ]


class _ObjC:
    """Thin ctypes wrapper around the ObjC runtime (ARM64).

    Provides typed ``CFUNCTYPE`` wrappers for the argument/return-type
    combinations used by the two APIs in this example.  A single raw
    ``objc_msgSend`` pointer is cast to each wrapper type; this matches
    the ARM64 calling convention where the return type determines which
    registers are used.
    """

    def __init__(self) -> None:
        lib = ctypes.CDLL(None)

        _get_cls = lib.objc_getClass
        _get_cls.restype = ctypes.c_void_p
        _get_cls.argtypes = [ctypes.c_char_p]

        _sel = lib.sel_registerName
        _sel.restype = ctypes.c_void_p
        _sel.argtypes = [ctypes.c_char_p]

        raw = ctypes.cast(lib.objc_msgSend, ctypes.c_void_p).value

        self._get_cls = _get_cls
        self._sel = _sel
        # id  msg(id, SEL)
        self.send_id = ctypes.CFUNCTYPE(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )(raw)
        # bool msg(id, SEL)
        self.send_bool = ctypes.CFUNCTYPE(
            ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
        )(raw)
        # void msg(id, SEL)
        self.send_void = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)(raw)
        # CGFloat msg(id, SEL)  — CGFloat is double on 64-bit ARM
        self.send_cgfloat = ctypes.CFUNCTYPE(
            ctypes.c_double, ctypes.c_void_p, ctypes.c_void_p
        )(raw)
        # void msg(id, SEL, CGFloat)
        self.send_void_d = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_double
        )(raw)
        # CMAcceleration msg(id, SEL)  — 3-double HFA returned in d0-d2
        self.send_accel = ctypes.CFUNCTYPE(
            _CMAcceleration, ctypes.c_void_p, ctypes.c_void_p
        )(raw)

    def cls(self, name: bytes) -> ctypes.c_void_p:
        return self._get_cls(name)

    def sel(self, name: bytes) -> ctypes.c_void_p:
        return self._sel(name)


class _Accelerometer:
    """CMMotionManager via the ObjC runtime (ctypes).

    pyobjus currently cannot decode ObjC structs whose fields are ``double``
    (CMAcceleration = {CMAcceleration=ddd} in ObjC type encoding).  We bypass
    it here and call ``objc_msgSend`` via ctypes — the same technique used in
    ``ios.py`` for reading ``UIEdgeInsets``.
    """

    def __init__(self, objc: _ObjC) -> None:
        self._objc = objc
        mm_cls = objc.cls(b"CMMotionManager")
        self._mm = objc.send_id(
            objc.send_id(mm_cls, objc.sel(b"alloc")), objc.sel(b"init")
        )
        self._available: bool = bool(
            objc.send_bool(self._mm, objc.sel(b"isAccelerometerAvailable"))
        )
        if self._available:
            objc.send_void(self._mm, objc.sel(b"startAccelerometerUpdates"))

    @property
    def available(self) -> bool:
        return self._available

    @property
    def values(self) -> tuple[float, float]:
        """Return ``(x, y)`` tilt in *g* (positive x = tilt right)."""
        if not self._available:
            return 0.0, 0.0
        objc = self._objc
        data = objc.send_id(self._mm, objc.sel(b"accelerometerData"))
        if not data:
            return 0.0, 0.0
        acc = objc.send_accel(data, objc.sel(b"acceleration"))
        return float(acc.x), float(acc.y)

    def stop(self) -> None:
        if self._available:
            objc = self._objc
            objc.send_void(self._mm, objc.sel(b"stopAccelerometerUpdates"))


class _Screen:
    """UIScreen.mainScreen brightness read/write via ctypes.

    Using ctypes avoids the spurious ``AttributeError`` that pyobjus raises
    when it tries to introspect UIScreen's internal property list on recent
    iOS versions.
    """

    def __init__(self, objc: _ObjC) -> None:
        self._objc = objc
        screen_cls = objc.cls(b"UIScreen")
        self._screen = objc.send_id(screen_cls, objc.sel(b"mainScreen"))

    @property
    def brightness(self) -> float:
        return float(
            self._objc.send_cgfloat(self._screen, self._objc.sel(b"brightness"))
        )

    @brightness.setter
    def brightness(self, value: float) -> None:
        # The ObjC setter selector is "setBrightness:" (colon required).
        self._objc.send_void_d(
            self._screen, self._objc.sel(b"setBrightness:"), float(value)
        )


class PyobjusBallRoot(BoxLayout):
    ball_hue = NumericProperty(0.55)
    bounces = NumericProperty(0)
    has_native = NumericProperty(0)  # bool cast to number for KV opacity
    status_text = StringProperty("Initialising…")

    # Physics constants
    _ACCEL_SCALE = 350.0  # px/s² per g of tilt
    _MAX_SPEED = 700.0  # px/s

    # Initial velocity so the ball moves immediately at startup
    _vx: float = 220.0
    _vy: float = 160.0

    _accel: _Accelerometer | None = None
    _screen: _Screen | None = None

    def on_kv_post(self, _base_widget) -> None:
        try:
            objc = _ObjC()
            accel = _Accelerometer(objc)
            if accel.available:
                self._accel = accel
                self._screen = _Screen(objc)
                self.has_native = 1
                self.ids.bright_slider.value = self._screen.brightness
                self.status_text = "Tilt to steer · slide to adjust brightness"
            else:
                self.status_text = "Accelerometer unavailable — drag to steer"
        except Exception as exc:  # pragma: no cover — device-only path
            self.status_text = f"Native init error: {exc}"

        Clock.schedule_interval(self._update, 1.0 / 60.0)

    def __del__(self) -> None:
        if self._accel:
            self._accel.stop()

    # ------------------------------------------------------------------ #
    # Native API calls                                                     #
    # ------------------------------------------------------------------ #

    def set_brightness(self, value: float) -> None:
        """Write screen brightness via UIScreen (functional on iOS 16+)."""
        if self._screen is not None:
            self._screen.brightness = value

    # ------------------------------------------------------------------ #
    # Touch fallback (when accelerometer is absent)                        #
    # ------------------------------------------------------------------ #

    def on_field_touch(self, touch) -> None:
        """Give the ball a velocity impulse toward the touch point."""
        if self._accel:
            return
        ball = self.ids.ball
        dx = touch.x - ball.center_x
        dy = touch.y - ball.center_y
        self._vx = dx * 0.5
        self._vy = dy * 0.5

    # ------------------------------------------------------------------ #
    # Game loop                                                            #
    # ------------------------------------------------------------------ #

    def _update(self, dt: float) -> None:
        if self._accel:
            ax, ay = self._accel.values
            # Accumulate velocity from tilt (acceleration model).
            # Velocity is NOT overwritten each frame — this is what lets
            # bounces work: a reversed component stays reversed until tilt
            # in the opposite direction overcomes it.
            self._vx += ax * self._ACCEL_SCALE * dt
            self._vy += ay * self._ACCEL_SCALE * dt
            # Clamp to max speed while preserving direction.
            spd = (self._vx**2 + self._vy**2) ** 0.5
            if spd > self._MAX_SPEED:
                f = self._MAX_SPEED / spd
                self._vx *= f
                self._vy *= f

        field = self.ids.field
        ball = self.ids.ball

        new_x = ball.x + self._vx * dt
        new_y = ball.y + self._vy * dt

        bounced = False

        if new_x < field.x:
            new_x = field.x
            self._vx = abs(self._vx)
            bounced = True
        elif new_x + ball.width > field.right:
            new_x = field.right - ball.width
            self._vx = -abs(self._vx)
            bounced = True

        if new_y < field.y:
            new_y = field.y
            self._vy = abs(self._vy)
            bounced = True
        elif new_y + ball.height > field.top:
            new_y = field.top - ball.height
            self._vy = -abs(self._vy)
            bounced = True

        ball.pos = (new_x, new_y)

        if bounced:
            self.bounces += 1
            self.ball_hue = random()


class PyobjusBallApp(App):
    def build(self) -> PyobjusBallRoot:
        Window.clearcolor = DARK_BG
        return Builder.load_string(KV)


PyobjusBallApp().run()
