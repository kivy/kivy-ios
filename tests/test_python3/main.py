print("Python 3 running!")
import sys
print(f"sys.path: {sys.path}")
import traceback

modules_to_tests = [
    "math", "_sre", "array",
    "binascii", "multiprocessing",
    "subprocess"
]

for name in modules_to_tests:
    print(f"- import {name}: ", end="")
    try:
        __import__(name)
        print("OK")
    except ImportError:
        print("FAIL")
        traceback.print_exc()

# test pyobjus
print("- import pyobjus start")
import pyobjus  # noqa: F401
print("- import done")
from pyobjus import autoclass
NSNotificationCenter = autoclass("NSNotificationCenter")

# test ios
import ios  # noqa: F401

from kivy.app import App
from kivy.lang import Builder


class TestApp(App):
    def build(self):
        return Builder.load_string("""
RelativeLayout:
    GridLayout:
        cols: 2

        Button:
            text: "Hello Python 3!"
            font_size: dp(48)

        TextInput:
            font_size: dp(24)

        Widget
        Widget

""")


TestApp().run()
