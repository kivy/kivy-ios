from __future__ import absolute_import

import os
import datetime
from kivy.lang import Builder
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import ObjectProperty
from kivy.resources import resource_add_path
from .platform_api import take_picture, set_orientation, LANDSCAPE

ROOT = os.path.dirname(os.path.abspath(__file__))
resource_add_path(ROOT)

def darker(color, factor=0.5):
    r, g, b, a = color
    r *= factor
    g *= factor
    b *= factor
    return r, g, b, a

kv = """
#:import xcamera kivy.garden.xcamera

<XCameraIconButton>
    icon_color: (0, 0, 0, 1)
    _down_color: xcamera.darker(self.icon_color)
    icon_size: dp(50)

    canvas.before:
        Color:
            rgba: self.icon_color if self.state == 'normal' else self._down_color
        Ellipse:
            pos: self.pos
            size: self.size

    size_hint: None, None
    size: self.icon_size, self.icon_size
    font_size: self.icon_size/2


<XCamera>:
    # \ue800 corresponds to the camera icon in the font
    icon: u"[font=data/xcamera/icons.ttf]\ue800[/font]"
    icon_color: (0.13, 0.58, 0.95, 0.8)
    icon_size: dp(70)

    id: camera
    resolution: 640, 480 # 1920, 1080
    allow_stretch: True

    # Shoot button
    XCameraIconButton:
        markup: True
        text: root.icon
        icon_color: root.icon_color
        icon_size: root.icon_size
        on_release: root.shoot()

        # position
        right: root.width - dp(10)
        center_y: root.center_y
"""
Builder.load_string(kv)

class XCameraIconButton(ButtonBehavior, Label):
    pass


class XCamera(Camera):
    directory = ObjectProperty(None)
    _previous_orientation = None
    __events__ = ('on_picture_taken',)

    def on_picture_taken(self, filename):
        """
        This event is fired every time a picture has been taken
        """

    def get_filename(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S.jpg')

    def shoot(self):
        def on_success(filename):
            self.dispatch('on_picture_taken', filename)
        #
        filename = self.get_filename()
        if self.directory:
            filename = os.path.join(self.directory, filename)
        take_picture(self, filename, on_success)

    def force_landscape(self):
        self._previous_orientation = set_orientation(LANDSCAPE)

    def restore_orientation(self):
        if self._previous_orientation is not None:
            set_orientation(self._previous_orientation)

