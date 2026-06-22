"""keychain-spm — a kivy-ios 3.0 Swift Package Manager example.

Demonstrates the full SPM feature plus the `@objc` shim pattern:

  * A *remote* SPM package (``KeychainAccess``) is declared in
    ``pyproject.toml``, resolved + pinned by ``toolchain lock``, and embedded
    into the app by ``toolchain build``.
  * A *local* shim package (``KeychainBridge``, under ``swift-shims/``) wraps
    KeychainAccess's pure-Swift API behind a small ``@objc`` class.
  * This Python app calls that shim through ``pyobjus`` to store, load, and
    delete a secret in the iOS **Keychain** — secure, on-device storage that
    has no pure-Python equivalent on iOS.

On the Simulator or desktop, where the native bridge is unavailable, the app
falls back to an in-memory dict so the UI can still be exercised. The status
banner makes clear which backend is active.
"""

from __future__ import annotations

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

DARK_BG = (0.08, 0.09, 0.12, 1)
SERVICE_KEY = "github_token"  # the demo stores one named secret


def _objc_str(value) -> str | None:
    """Convert a pyobjus NSString result into a Python ``str`` (or None)."""
    if value is None:
        return None
    # pyobjus returns an NSString proxy; UTF8String() yields a C string.
    try:
        raw = value.UTF8String()
    except AttributeError:
        return str(value)
    return raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)


class KeychainStore:
    """Secret storage backed by the KeychainBridge SPM shim on iOS.

    Falls back to a process-local dict everywhere else so the example runs on
    the Simulator and on desktop. ``native`` reports which backend is live.
    """

    def __init__(self) -> None:
        self._bridge = None
        self._fallback: dict[str, str] = {}
        self.native = False
        try:
            from kivy.utils import platform

            if platform == "ios":
                from pyobjus import autoclass

                # Looked up by the @objc(KeychainBridge) runtime name; the
                # framework is loaded at launch via the link+embed wiring.
                self._bridge = autoclass("KeychainBridge")
                self.native = True
        except Exception:
            self._bridge = None
            self.native = False

    def store(self, key: str, value: str) -> bool:
        if self._bridge is not None:
            return bool(self._bridge.storeString_forKey_(value, key))
        self._fallback[key] = value
        return True

    def load(self, key: str) -> str | None:
        if self._bridge is not None:
            return _objc_str(self._bridge.stringForKey_(key))
        return self._fallback.get(key)

    def delete(self, key: str) -> bool:
        if self._bridge is not None:
            return bool(self._bridge.deleteKey_(key))
        return self._fallback.pop(key, None) is not None


KV = """
<KeychainRoot>:
    orientation: "vertical"
    padding: "20dp"
    spacing: "14dp"

    Label:
        size_hint_y: None
        height: "40dp"
        font_size: "15sp"
        color: 0.5, 0.85, 1.0, 1
        text: root.backend_text

    Label:
        size_hint_y: None
        height: "24dp"
        font_size: "13sp"
        color: 0.6, 0.6, 0.6, 1
        halign: "left"
        valign: "middle"
        text_size: self.size
        text: "Secret value"

    TextInput:
        id: secret
        size_hint_y: None
        height: "44dp"
        multiline: False
        hint_text: "type a token, then Save"

    BoxLayout:
        size_hint_y: None
        height: "48dp"
        spacing: "12dp"
        Button:
            text: "Save"
            on_release: root.save()
        Button:
            text: "Load"
            on_release: root.load()
        Button:
            text: "Delete"
            on_release: root.delete()

    Label:
        font_size: "14sp"
        halign: "center"
        valign: "top"
        text_size: self.width, None
        text: root.status_text

    Widget:

KeychainRoot:
"""


class KeychainRoot(BoxLayout):
    backend_text = StringProperty("")
    status_text = StringProperty("Enter a value and tap Save.")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._store = KeychainStore()
        self.backend_text = (
            "Backend: iOS Keychain (KeychainAccess via @objc shim)"
            if self._store.native
            else "Backend: in-memory fallback (not on iOS)"
        )

    def save(self) -> None:
        value = self.ids.secret.text.strip()
        if not value:
            self.status_text = "Nothing to save — the field is empty."
            return
        ok = self._store.store(SERVICE_KEY, value)
        self.status_text = (
            f"Saved {len(value)} characters to {SERVICE_KEY!r}."
            if ok
            else "Save failed."
        )

    def load(self) -> None:
        value = self._store.load(SERVICE_KEY)
        if value is None:
            self.status_text = f"No value stored for {SERVICE_KEY!r}."
        else:
            self.ids.secret.text = value
            self.status_text = f"Loaded {len(value)} characters from the keychain."

    def delete(self) -> None:
        removed = self._store.delete(SERVICE_KEY)
        self.ids.secret.text = ""
        self.status_text = (
            f"Deleted {SERVICE_KEY!r}." if removed else "Nothing to delete."
        )


class KeychainApp(App):
    def build(self) -> KeychainRoot:
        Window.clearcolor = DARK_BG
        return Builder.load_string(KV)


KeychainApp().run()
