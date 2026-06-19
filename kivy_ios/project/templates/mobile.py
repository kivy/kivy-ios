"""mobile.py — cross-platform bridge for mobile window/display geometry.

Placed at ``<app>-ios/platform/mobile.py`` by ``toolchain build``.

This module previews the ``kivy.mobile`` public API that will live in
Kivy core once the interface stabilises (see docs/proposals/05-cli-shape.md).
On iOS it delegates entirely to ``ios.py``; on desktop it returns safe
fallback values so the same app code runs unmodified during development.

Public API
----------
Tier 1 — cross-platform (always available):

    get_dpi()                   -> float
    get_scale()                 -> float
    get_density()               -> float
    get_keyboard_height()       -> float   (0 when hidden)
    get_kheight()               -> float   (alias)
    get_safe_area()             -> {"top", "left", "bottom", "right"}
    subscribe_keyboard_height(cb)          register a keyboard-height callback

Tier 2 — platform extras (iOS always returns None, Android fills these in):

    get_display_cutout()        -> list[dict] | None
    get_system_bar_insets()     -> dict | None
"""

from __future__ import annotations

try:
    from kivy.utils import platform as _platform  # type: ignore[import-not-found]
    _is_ios = _platform == "ios"
except ImportError:
    # Running inside an iOS app bundle before Kivy's environment is fully
    # initialised, or in a pure-Python context without Kivy installed.
    # Default to iOS behaviour (the normal deployment scenario).
    _is_ios = True

if _is_ios:
    from ios import (  # type: ignore[import-not-found]  # noqa: F401
        get_density,
        get_display_cutout,
        get_dpi,
        get_keyboard_height,
        get_kheight,
        get_safe_area,
        get_scale,
        get_system_bar_insets,
        subscribe_keyboard_height,
    )
else:
    # Desktop / CI fallbacks — safe defaults that keep the app runnable.

    def get_dpi() -> float:
        """Fallback DPI for desktop / unsupported platforms."""
        return 96.0

    def get_scale() -> float:
        """Fallback scale for desktop / unsupported platforms."""
        return 1.0

    def get_density() -> float:
        """Fallback density for desktop / unsupported platforms."""
        return 1.0

    def get_keyboard_height() -> float:
        """Fallback keyboard height (always 0 on desktop)."""
        return 0.0

    def get_kheight() -> float:
        """Alias for get_keyboard_height()."""
        return 0.0

    def get_safe_area() -> dict:
        """Fallback safe area (all zeros on desktop)."""
        return {"top": 0.0, "left": 0.0, "bottom": 0.0, "right": 0.0}

    def subscribe_keyboard_height(callback) -> None:
        """No-op on desktop; callback is stored but never called."""
        pass

    def get_display_cutout():
        """Not applicable on desktop."""
        return None

    def get_system_bar_insets():
        """Not applicable on desktop."""
        return None
