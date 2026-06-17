"""Mobile Geometry — kivy.mobile API prototype validation app.

Displays live values for every function in mobile_bridge.py:

  * DPI, scale, density
  * Safe area insets (top / bottom / left / right) with a visual overlay
  * Keyboard height — updates in real time as the keyboard appears / hides

How to run
----------
Desktop (quick smoke-test)::

    cd examples/mobile-geometry
    python src/main.py

iOS device / simulator::

    cd examples/mobile-geometry
    toolchain build .
    toolchain run .

Tap the TextInput at the bottom to show/hide the software keyboard and watch
the "Keyboard height" row and bar update.
"""

import os
import sys

# Allow running directly from the repo without installing kivy-ios.
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from mobile_bridge import (
    get_dpi,
    get_density,
    get_scale,
    get_safe_area,
    get_keyboard_height,
    subscribe_keyboard_height,
)

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import DictProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout


_SAFE_AREA_ZERO = {"top": 0.0, "left": 0.0, "bottom": 0.0, "right": 0.0}


class MobileGeometryRoot(BoxLayout):
    pass


class MobileGeometryApp(App):
    keyboard_height = NumericProperty(0)
    safe_area = DictProperty(_SAFE_AREA_ZERO.copy())
    # Fraction 0-1 used by the KV keyboard-bar widget
    kb_bar_width = NumericProperty(0)

    def build(self):
        kv_path = os.path.join(_src_dir, "main.kv")
        Builder.load_file(kv_path)
        return MobileGeometryRoot()

    def on_start(self):
        # Populate static values immediately.
        self._refresh_labels()

        # Live keyboard height via subscription.
        subscribe_keyboard_height(self._on_keyboard_height)

        # Refresh safe area after each rotation.
        Window.bind(on_rotate=self._on_rotate)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_keyboard_height(self, height: float) -> None:
        """Called from the ObjC notification; schedule onto Kivy main thread."""
        Clock.schedule_once(lambda dt: self._apply_keyboard_height(height), 0)

    def _apply_keyboard_height(self, height: float) -> None:
        self.keyboard_height = height
        root = self.root
        root.ids.lbl_kb.text = f"{height:.1f} pt"
        # Scale bar width: max expected keyboard height ~350 pt
        self.kb_bar_width = min(1.0, height / 350.0)

    def _on_rotate(self, window, rotation) -> None:
        # UIKit updates safeAreaInsets asynchronously — defer one frame.
        Clock.schedule_once(lambda dt: self._refresh_safe_area(), 0)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _refresh_labels(self) -> None:
        ids = self.root.ids
        ids.lbl_dpi.text     = f"{get_dpi():.1f}"
        ids.lbl_scale.text   = f"{get_scale():.2f}x"
        ids.lbl_density.text = f"{get_density():.2f}"
        self._refresh_safe_area()
        ids.lbl_kb.text      = f"{get_keyboard_height():.1f} pt"

    def _refresh_safe_area(self) -> None:
        sa = get_safe_area()
        self.safe_area = sa
        ids = self.root.ids
        ids.lbl_sa_top.text    = f"{sa['top']:.1f} pt"
        ids.lbl_sa_bottom.text = f"{sa['bottom']:.1f} pt"
        ids.lbl_sa_left.text   = f"{sa['left']:.1f} pt"
        ids.lbl_sa_right.text  = f"{sa['right']:.1f} pt"


MobileGeometryApp().run()
