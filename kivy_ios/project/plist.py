"""Generate ``<app>-Info.plist`` from the config (spec 06).

kivy-ios manages a fixed set of Info.plist keys (identity, version,
orientation, deployment floor) and merges the user's free-form
``[tool.kivy.ios.info_plist]`` on top — rejecting any attempt to set a managed
key (already enforced in the config loader, double-checked here).
"""

from __future__ import annotations

import plistlib
from pathlib import Path

from ..config.model import MANAGED_INFO_PLIST_KEYS, Config
from .assets import launch_screen_needed

ORIENTATION_TO_UIKEY = {
    "portrait": "UIInterfaceOrientationPortrait",
    "portrait-upside-down": "UIInterfaceOrientationPortraitUpsideDown",
    "landscape-left": "UIInterfaceOrientationLandscapeLeft",
    "landscape-right": "UIInterfaceOrientationLandscapeRight",
}


def build_info_plist(config: Config) -> dict:
    """Return the Info.plist dict (managed keys + merged user keys)."""
    ios = config.ios
    assert ios is not None
    orientations = [ORIENTATION_TO_UIKEY[o] for o in config.kivy.orientation]

    # Apple requires all four iPad orientations (Xcode 16+ / iOS 18+ policy).
    # UIRequiresFullScreen is deprecated and will be ignored by the OS.
    all_ipad_orientations = [
        "UIInterfaceOrientationPortrait",
        "UIInterfaceOrientationPortraitUpsideDown",
        "UIInterfaceOrientationLandscapeLeft",
        "UIInterfaceOrientationLandscapeRight",
    ]

    plist: dict[str, object] = {
        "CFBundleName": config.project.name,
        "CFBundleDisplayName": config.display_name,
        "CFBundleIdentifier": ios.bundle_id,
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleShortVersionString": config.project.version,
        "CFBundleVersion": str(ios.build),
        "CFBundlePackageType": "APPL",
        "CFBundleInfoDictionaryVersion": "6.0",
        "MinimumOSVersion": ios.deployment_target,
        "LSRequiresIPhoneOS": True,
        "UISupportedInterfaceOrientations": orientations,
        # iPad must declare all four orientations (Apple App Store requirement
        # as of Xcode 16; UIRequiresFullScreen is deprecated and ignored).
        "UISupportedInterfaceOrientations~ipad": all_ipad_orientations,
        # SDL3 on iOS 13.4+ expects this for indirect input / mouse events.
        "UIApplicationSupportsIndirectInputEvents": True,
        # SDL3 on iOS 13+ uses UIScene lifecycle.  Without this entry iOS
        # never foregrounds the scene and Metal rejects all GPU work with
        # kIOGPUCommandBufferCallbackErrorBackgroundExecutionNotPermitted.
        "UIApplicationSceneManifest": {
            "UIApplicationSupportsMultipleScenes": False,
            "UISceneConfigurations": {
                "UIWindowSceneSessionRoleApplication": [
                    {
                        "UISceneConfigurationName": "SDLSceneConfiguration",
                        "UISceneDelegateClassName": "SDLUIKitSceneDelegate",
                    }
                ]
            },
        },
    }

    if launch_screen_needed(config):
        plist["UILaunchStoryboardName"] = "LaunchScreen"

    # Merge user-supplied keys; managed keys were already rejected at config
    # load, but guard here too so the generator is safe in isolation.
    for key, value in ios.info_plist.items():
        if key in MANAGED_INFO_PLIST_KEYS:
            raise ValueError(f"info_plist key {key!r} is managed by kivy-ios")
        plist[key] = value

    return plist


def write_info_plist(config: Config, path: str | Path) -> Path:
    path = Path(path)
    with open(path, "wb") as f:
        plistlib.dump(build_info_plist(config), f, sort_keys=True)
    return path
