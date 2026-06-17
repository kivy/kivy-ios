"""Minimal Kivy smoke app for kivy-ios 3.0."""

from kivy.app import App
from kivy.uix.label import Label


class HelloKivyApp(App):
    def build(self):
        return Label(text="Hello Kivy", font_size="48sp")


HelloKivyApp().run()
