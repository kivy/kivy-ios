import datetime
from kivy.lang import Builder
from kivy.app import App

kv = """
#:import XCamera kivy.garden.xcamera.XCamera

FloatLayout:
    orientation: 'vertical'

    XCamera:
        id: xcamera
        on_picture_taken: app.picture_taken(*args)

    BoxLayout:
        orientation: 'horizontal'
        size_hint: 1, None
        height: sp(50)

        Button:
            text: 'Set landscape'
            on_release: xcamera.force_landscape()

        Button:
            text: 'Restore orientation'
            on_release: xcamera.restore_orientation()
"""


class CameraApp(App):
    def build(self):
        return Builder.load_string(kv)

    def picture_taken(self, obj, filename):
        print 'Picture taken and saved to', filename

if __name__ == '__main__':
    CameraApp().run()
