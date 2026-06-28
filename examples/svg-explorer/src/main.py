"""SVG Explorer — an interactive kivy-ios 3.0 example.

A richer Kivy app than ``hello-kivy``: it renders vector drawings with
:class:`~kivy.uix.svg.SvgWidget` and lets you manipulate them with multitouch.

Interactions
------------
* drag                 — pan the drawing
* pinch (two fingers)  — zoom
* twist (two fingers)  — rotate
* Prev / Next          — cycle through the bundled SVG drawings
* Reset                — fit the current drawing back to the view
* BG                   — toggle the canvas background (dark / light)

The drawings live in ``assets/*.svg`` and are loaded by path at runtime.
"""

import os

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
SVG_FILES = ["star.svg", "heart.svg", "hexagon.svg"]

DARK_BG = (0.10, 0.11, 0.14, 1)
LIGHT_BG = (0.95, 0.95, 0.97, 1)


def safe_area_insets():
    """Device safe-area insets as Kivy pixels: ``[left, top, right, bottom]``.

    Returns zeros off-iOS, or when the vendored ``ios`` shim is unavailable,
    so the app is unchanged on desktop and degrades gracefully.
    ``ios.get_safe_area()`` reports UIKit points; the window's pixel space uses
    the device scale, so points are converted with ``ios.get_scale()`` (the
    shim's own scale, rather than ``Metrics.density`` which may lag it).
    """
    if platform != "ios":
        return [0, 0, 0, 0]
    try:
        import ios
    except ImportError:
        return [0, 0, 0, 0]
    insets = ios.get_safe_area()  # UIKit points
    scale = ios.get_scale()  # -> Kivy window pixels
    return [
        insets["left"] * scale,
        insets["top"] * scale,
        insets["right"] * scale,
        insets["bottom"] * scale,
    ]


KV = """
<SvgExplorerRoot>:
    orientation: "vertical"

    BoxLayout:
        size_hint_y: None
        height: "56dp"
        spacing: "4dp"
        padding: "4dp"
        Button:
            text: "< Prev"
            font_size: "16sp"
            on_release: root.prev_svg()
        Button:
            text: "Next >"
            font_size: "16sp"
            on_release: root.next_svg()
        Button:
            text: "Reset"
            font_size: "16sp"
            on_release: root.fit_to_view()
        Button:
            text: "BG"
            font_size: "16sp"
            on_release: app.toggle_bg()

    FloatLayout:
        id: area
        canvas.before:
            Color:
                rgba: app.bg_rgba
            Rectangle:
                pos: area.pos
                size: area.size
        Scatter:
            id: scatter
            size_hint: None, None
            size: svg.viewbox_size
            SvgWidget:
                id: svg
                source: root.svg_path
                fit_mode: "contain"
                size_hint: None, None
                size: self.viewbox_size
                on_load: root.fit_to_view()

    Label:
        size_hint_y: None
        height: "30dp"
        font_size: "14sp"
        color: 1, 1, 1, 0.8
        text: root.status_text

SvgExplorerRoot:
"""


class SvgExplorerRoot(BoxLayout):
    svg_path = StringProperty()
    index = NumericProperty(0)
    status_text = StringProperty()

    def on_kv_post(self, base_widget):
        # index defaults to 0, so on_index never fires at startup — load the
        # first drawing once the widget tree (and SvgWidget id) exists.
        self._sync_from_index()
        # Inset content past the notch / Dynamic Island + home indicator. The
        # safe area isn't settled at kv_post and changes with orientation, so
        # refresh on the next frame and on every resize.
        Clock.schedule_once(self._refresh_safe_area, 0)
        Window.bind(on_resize=self._on_resize)

    def _on_resize(self, *_):
        Clock.schedule_once(self._refresh_safe_area, 0)

    def _refresh_safe_area(self, *_):
        base = dp(20)
        left, top, right, bottom = safe_area_insets()
        self.padding = [base + left, base + top, base + right, base + bottom]

    def on_index(self, *_):
        self._sync_from_index()

    def prev_svg(self):
        self.index = (self.index - 1) % len(SVG_FILES)

    def next_svg(self):
        self.index = (self.index + 1) % len(SVG_FILES)

    def _sync_from_index(self):
        filename = SVG_FILES[self.index]
        self.svg_path = os.path.join(ASSETS, filename)
        self.status_text = (
            f"{filename}   ({self.index + 1}/{len(SVG_FILES)})   drag · pinch · twist"
        )

    def fit_to_view(self, *_):
        scatter = self.ids.scatter
        area = self.ids.area
        if not scatter.width or not scatter.height:
            return
        if not area.width or not area.height:
            return
        scatter.rotation = 0
        scale = min(area.width / scatter.width, area.height / scatter.height) * 0.8
        scatter.scale = scale
        scatter.center = area.center


class SvgExplorerApp(App):
    bg_rgba = ListProperty(list(DARK_BG))

    def build(self):
        Window.clearcolor = DARK_BG
        return Builder.load_string(KV)

    def toggle_bg(self):
        if self.bg_rgba == list(DARK_BG):
            self.bg_rgba = list(LIGHT_BG)
        else:
            self.bg_rgba = list(DARK_BG)


SvgExplorerApp().run()
