"""iOS platform bridge, placed at ``<app>-ios/platform/ios.py`` by ``toolchain build``.

Kivy defines the interface (``get_scale``, ``get_dpi``, ``get_kheight``);
this implementation ultimately belongs in the kivy repository alongside
Kivy's own iOS backend code.  It lives here in kivy-ios for development
convenience — kivy-ios controls the build pipeline and is the most effective
place to iterate on the device DPI table and ObjC-runtime wrappers before
the interface stabilises enough to move upstream.

See docs/proposals/05-cli-shape.md § "The vendored ios platform module".

Public API
----------
Tier 1 — cross-platform layout geometry (always available):

    get_dpi()                  -> float
    get_scale()                -> float
    get_density()              -> float   (alias for get_scale)
    get_keyboard_height()      -> float   (0 when keyboard hidden)
    get_kheight()              -> float   (alias for get_keyboard_height)
    get_safe_area()            -> {"top", "left", "bottom", "right"}
    subscribe_keyboard_height(cb)         register a callback for height changes

Tier 2 — platform-specific extras (iOS always returns None):

    get_display_cutout()       -> None    (Android concept; no iOS equivalent)
    get_system_bar_insets()    -> None    (Android concept; no iOS equivalent)

All geometry values are in UIKit points, which equal Kivy layout coordinates
on iOS (nativeScale applies only to rasterization, not layout).
"""

from __future__ import annotations

import ctypes

__version__ = (1, 1, 0)

# ---------------------------------------------------------------------------
# Device DPI table from legacy kivy-ios ios_utils.m (SDL UIKit modes lineage).
# ---------------------------------------------------------------------------

_DEVICE_DPI: dict[str, int] = {
    "iPhone1,1": 163,
    "iPhone1,2": 163,
    "iPhone2,1": 163,
    "iPhone3,1": 326,
    "iPhone3,2": 326,
    "iPhone3,3": 326,
    "iPhone4,1": 326,
    "iPhone5,1": 326,
    "iPhone5,2": 326,
    "iPhone5,3": 326,
    "iPhone5,4": 326,
    "iPhone6,1": 326,
    "iPhone6,2": 326,
    "iPhone7,1": 401,
    "iPhone7,2": 326,
    "iPhone8,1": 326,
    "iPhone8,2": 401,
    "iPhone8,4": 326,
    "iPhone9,1": 326,
    "iPhone9,2": 401,
    "iPhone9,3": 326,
    "iPhone9,4": 401,
    "iPhone10,1": 326,
    "iPhone10,2": 401,
    "iPhone10,3": 458,
    "iPhone10,4": 326,
    "iPhone10,5": 401,
    "iPhone10,6": 458,
    "iPhone11,2": 458,
    "iPhone11,4": 458,
    "iPhone11,6": 458,
    "iPhone11,8": 326,
    "iPhone12,1": 326,
    "iPhone12,3": 458,
    "iPhone12,5": 458,
    "iPhone12,8": 326,
    "iPhone13,1": 476,
    "iPhone13,2": 460,
    "iPhone13,3": 460,
    "iPhone13,4": 458,
    "iPhone14,2": 460,
    "iPhone14,3": 458,
    "iPhone14,4": 476,
    "iPhone14,5": 460,
    "iPhone14,6": 326,
    "iPad1,1": 132,
    "iPad2,1": 132,
    "iPad2,2": 132,
    "iPad2,3": 132,
    "iPad2,4": 132,
    "iPad2,5": 163,
    "iPad2,6": 163,
    "iPad2,7": 163,
    "iPad3,1": 264,
    "iPad3,2": 264,
    "iPad3,3": 264,
    "iPad3,4": 264,
    "iPad3,5": 264,
    "iPad3,6": 264,
    "iPad4,1": 264,
    "iPad4,2": 264,
    "iPad4,3": 264,
    "iPad4,4": 326,
    "iPad4,5": 326,
    "iPad4,6": 326,
    "iPad4,7": 326,
    "iPad4,8": 326,
    "iPad4,9": 326,
    "iPad5,1": 326,
    "iPad5,2": 326,
    "iPad5,3": 264,
    "iPad5,4": 264,
    "iPad6,3": 264,
    "iPad6,4": 264,
    "iPad6,7": 264,
    "iPad6,8": 264,
    "iPad6,11": 264,
    "iPad6,12": 264,
    "iPad7,1": 264,
    "iPad7,2": 264,
    "iPad7,3": 264,
    "iPad7,4": 264,
    "iPad7,5": 264,
    "iPad7,6": 264,
    "iPad7,11": 264,
    "iPad7,12": 264,
    "iPad8,1": 264,
    "iPad8,2": 264,
    "iPad8,3": 264,
    "iPad8,4": 264,
    "iPad8,5": 264,
    "iPad8,6": 264,
    "iPad8,7": 264,
    "iPad8,8": 264,
    "iPad11,1": 326,
    "iPad11,2": 326,
    "iPad11,3": 326,
    "iPad11,4": 326,
    "iPod1,1": 163,
    "iPod2,1": 163,
    "iPod3,1": 163,
    "iPod4,1": 326,
    "iPod5,1": 326,
    "iPod7,1": 326,
    "iPod9,1": 326,
}

# ---------------------------------------------------------------------------
# Low-level ObjC / ctypes helpers
# ---------------------------------------------------------------------------


class _Utsname(ctypes.Structure):
    _fields_ = [
        ("sysname", ctypes.c_char * 256),
        ("nodename", ctypes.c_char * 256),
        ("release", ctypes.c_char * 256),
        ("version", ctypes.c_char * 256),
        ("machine", ctypes.c_char * 256),
    ]


class _UIEdgeInsets(ctypes.Structure):
    _fields_ = [
        ("top", ctypes.c_double),
        ("left", ctypes.c_double),
        ("bottom", ctypes.c_double),
        ("right", ctypes.c_double),
    ]


class _CGSize(ctypes.Structure):
    _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]


class _CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class _CGRect(ctypes.Structure):
    _fields_ = [("origin", _CGPoint), ("size", _CGSize)]


def _device_model() -> str:
    """Return the Darwin machine string, e.g. ``'iPhone14,5'``."""
    libc = ctypes.CDLL(None)
    if not hasattr(libc, "uname"):
        return ""
    libc.uname.argtypes = [ctypes.POINTER(_Utsname)]
    libc.uname.restype = ctypes.c_int
    info = _Utsname()
    if libc.uname(ctypes.byref(info)) != 0:
        return ""
    return info.machine.decode("ascii", "ignore")


def _objc_runtime():
    """Return a namespace of typed objc_msgSend wrappers and helpers.

    All return types go through the single objc_msgSend entry point on
    ARM64 (device and simulator). UIEdgeInsets and CGRect are 4-double
    HFAs returned in d0–d3; libffi handles these correctly without stret.
    """
    lib = ctypes.CDLL(None)

    get_class = lib.objc_getClass
    get_class.restype = ctypes.c_void_p
    get_class.argtypes = [ctypes.c_char_p]

    sel = lib.sel_registerName
    sel.restype = ctypes.c_void_p
    sel.argtypes = [ctypes.c_char_p]

    alloc_cls = lib.objc_allocateClassPair
    alloc_cls.restype = ctypes.c_void_p
    alloc_cls.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]

    add_method = lib.class_addMethod
    add_method.restype = ctypes.c_bool
    add_method.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_char_p,
    ]

    reg_cls = lib.objc_registerClassPair
    reg_cls.restype = None
    reg_cls.argtypes = [ctypes.c_void_p]

    addr = ctypes.cast(lib.objc_msgSend, ctypes.c_void_p).value
    send_id = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(addr)
    send_id2 = ctypes.CFUNCTYPE(
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
    )(addr)
    send_f64 = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_void_p, ctypes.c_void_p)(addr)
    send_insets = ctypes.CFUNCTYPE(_UIEdgeInsets, ctypes.c_void_p, ctypes.c_void_p)(
        addr
    )

    class _ObjC:
        pass

    rt = _ObjC()
    rt.lib = lib
    rt.get_class = get_class
    rt.sel = sel
    rt.alloc_cls = alloc_cls
    rt.add_method = add_method
    rt.reg_cls = reg_cls
    rt.send_id = send_id
    rt.send_id2 = send_id2
    rt.send_f64 = send_f64
    rt.send_insets = send_insets
    return rt


def _ns_string(rt, text: bytes) -> ctypes.c_void_p:
    """Create an NSString from a UTF-8 bytes literal."""
    cls = rt.get_class(b"NSString")
    return rt.send_id2(
        cls,
        rt.sel(b"stringWithUTF8String:"),
        ctypes.cast(ctypes.c_char_p(text), ctypes.c_void_p),
    )


def _key_window(rt) -> ctypes.c_void_p:
    """Return the key UIWindow."""
    app_cls = rt.get_class(b"UIApplication")
    app = rt.send_id(app_cls, rt.sel(b"sharedApplication"))
    win = rt.send_id(app, rt.sel(b"keyWindow"))
    if not win:
        windows = rt.send_id(app, rt.sel(b"windows"))
        win = rt.send_id(windows, rt.sel(b"firstObject"))
    return win


# ---------------------------------------------------------------------------
# Tier-1 API — cross-platform layout geometry
# ---------------------------------------------------------------------------


def get_scale() -> float:
    """UIKit nativeScale of the main screen (e.g. 3.0 on iPhone Pro)."""
    try:
        rt = _objc_runtime()
        win = _key_window(rt)
        screen = rt.send_id(rt.send_id(win, rt.sel(b"windowScene")), rt.sel(b"screen"))
        return float(rt.send_f64(screen, rt.sel(b"nativeScale")))
    except Exception:
        return 2.0


def get_dpi() -> float:
    """Physical screen DPI (from lookup table or derived from nativeScale)."""
    model = _device_model()
    if model in _DEVICE_DPI:
        return float(_DEVICE_DPI[model])
    scale = get_scale()
    if model.startswith("iPad"):
        return 132.0 * scale
    if model.startswith(("iPhone", "iPod")):
        return 163.0 * scale
    return 160.0 * scale


def get_density() -> float:
    """Logical pixel density. Alias for get_scale()."""
    return get_scale()


def get_safe_area() -> dict[str, float]:
    """Safe area insets in UIKit points (== Kivy layout coordinates).

    Returns ``{"top", "left", "bottom", "right"}``.
    Covers the status bar / Dynamic Island (top), home indicator (bottom),
    and notch / rounded-corner overhang (left / right in landscape).
    """
    try:
        rt = _objc_runtime()
        win = _key_window(rt)
        insets = rt.send_insets(win, rt.sel(b"safeAreaInsets"))
        return {
            "top": float(insets.top),
            "left": float(insets.left),
            "bottom": float(insets.bottom),
            "right": float(insets.right),
        }
    except Exception:
        return {"top": 0.0, "left": 0.0, "bottom": 0.0, "right": 0.0}


# ---------------------------------------------------------------------------
# Keyboard height — ObjC NSNotificationCenter observer
# ---------------------------------------------------------------------------

_keyboard_height: float = 0.0
_kb_subscribers: list = []

# Strong Python references — must not be GC'd while the app is live.
_kb_imp_ref = None
_kb_observer_ref = None


def _install_keyboard_observer() -> None:
    """Register an ObjC observer for UIKeyboard notifications.

    Creates a small ObjC class (_KivyIOSKBObserver) at module import time
    and registers it with NSNotificationCenter for:

      * UIKeyboardWillChangeFrameNotification — keyboard appears / resizes
      * UIKeyboardWillHideNotification        — keyboard hides

    The observer reads UIKeyboardFrameEndUserInfoKey (a CGRect) from the
    notification userInfo, caches the height in _keyboard_height, and calls
    every registered subscriber.

    UIKit fires these notifications on the main thread; Kivy also runs on
    the main thread, so no cross-thread synchronisation is needed.
    """
    global _kb_imp_ref, _kb_observer_ref

    try:
        rt = _objc_runtime()

        ImpType = ctypes.CFUNCTYPE(
            None,
            ctypes.c_void_p,  # self
            ctypes.c_void_p,  # _cmd
            ctypes.c_void_p,  # NSNotification*
        )

        def _kb_imp(self_ptr, cmd_ptr, notif_ptr):
            global _keyboard_height
            try:
                user_info = rt.send_id(notif_ptr, rt.sel(b"userInfo"))
                key = _ns_string(rt, b"UIKeyboardFrameEndUserInfoKey")
                ns_value = rt.send_id2(user_info, rt.sel(b"objectForKey:"), key)

                if ns_value:
                    # CGRect is a 4-double HFA; returned in d0-d3 on ARM64.
                    rect_fn = ctypes.CFUNCTYPE(
                        _CGRect,
                        ctypes.c_void_p,
                        ctypes.c_void_p,
                    )(ctypes.cast(rt.lib.objc_msgSend, ctypes.c_void_p).value)
                    rect = rect_fn(ns_value, rt.sel(b"CGRectValue"))
                    height = float(rect.size.height)
                else:
                    height = 0.0

                notif_name = rt.send_id(notif_ptr, rt.sel(b"name"))
                hide_name = _ns_string(rt, b"UIKeyboardWillHideNotification")
                is_hide = bool(
                    rt.send_id2(notif_name, rt.sel(b"isEqualToString:"), hide_name)
                )
                _keyboard_height = 0.0 if is_hide else height

                for cb in list(_kb_subscribers):
                    try:
                        cb(_keyboard_height)
                    except Exception:
                        pass
            except Exception:
                pass

        imp = ImpType(_kb_imp)
        _kb_imp_ref = imp  # keep alive

        ns_object_cls = rt.get_class(b"NSObject")
        cls = rt.alloc_cls(ns_object_cls, b"_KivyIOSKBObserver", 0)
        if not cls:
            cls = rt.get_class(b"_KivyIOSKBObserver")
        rt.add_method(
            cls,
            rt.sel(b"keyboardEvent:"),
            ctypes.cast(imp, ctypes.c_void_p),
            b"v@:@",
        )
        rt.reg_cls(cls)

        observer = rt.send_id(cls, rt.sel(b"alloc"))
        observer = rt.send_id(observer, rt.sel(b"init"))
        _kb_observer_ref = observer  # keep alive

        nc = rt.send_id(
            rt.get_class(b"NSNotificationCenter"),
            rt.sel(b"defaultCenter"),
        )
        _add_obs = ctypes.CFUNCTYPE(
            None,
            ctypes.c_void_p,  # nc
            ctypes.c_void_p,  # SEL addObserver:selector:name:object:
            ctypes.c_void_p,  # observer
            ctypes.c_void_p,  # SEL keyboardEvent:
            ctypes.c_void_p,  # name NSString*
            ctypes.c_void_p,  # object (nil)
        )(ctypes.cast(rt.lib.objc_msgSend, ctypes.c_void_p).value)

        for notif_name_bytes in (
            b"UIKeyboardWillChangeFrameNotification",
            b"UIKeyboardWillHideNotification",
        ):
            _add_obs(
                nc,
                rt.sel(b"addObserver:selector:name:object:"),
                observer,
                rt.sel(b"keyboardEvent:"),
                _ns_string(rt, notif_name_bytes),
                None,
            )

    except Exception as exc:
        import warnings

        warnings.warn(
            f"ios: keyboard observer setup failed: {exc}",
            RuntimeWarning,
            stacklevel=1,
        )


def get_keyboard_height() -> float:
    """Current software keyboard height in UIKit points (0 when hidden)."""
    return _keyboard_height


def get_kheight() -> float:
    """Alias for get_keyboard_height(). Kept for backwards compatibility."""
    return get_keyboard_height()


def subscribe_keyboard_height(callback) -> None:
    """Register *callback(height: float)* for keyboard height changes.

    Called with the new height in UIKit points each time the keyboard frame
    changes. Called with 0.0 when the keyboard hides.

    Callbacks are fired on the UIKit main thread (same as Kivy's main thread).
    If you need to update Kivy properties from the callback, it is safe to
    do so directly or via ``kivy.clock.Clock.schedule_once``.
    """
    _kb_subscribers.append(callback)


# ---------------------------------------------------------------------------
# Tier-2 API — platform-specific extras (iOS always returns None)
# ---------------------------------------------------------------------------


def get_display_cutout():
    """Android display-cutout bounding rects. Always None on iOS.

    On Android this returns a list of ``{"left", "top", "right", "bottom"}``
    dicts (one per physical cutout). iOS folds cutout geometry into the
    safe area insets returned by get_safe_area().
    """
    return None


def get_system_bar_insets():
    """Android status-bar / nav-bar insets separated. Always None on iOS.

    On Android this returns ``{"status_bar": {...}, "nav_bar": {...}}``.
    iOS provides the equivalent data combined in get_safe_area().
    """
    return None


# ---------------------------------------------------------------------------
# Module init — install keyboard observer on import
# ---------------------------------------------------------------------------

_install_keyboard_observer()
