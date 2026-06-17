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
        # iPad gets the same managed set (spec 01: ~ipad is a managed key).
        "UISupportedInterfaceOrientations~ipad": orientations,
        # Kivy apps are full-screen by design; SDL3 cannot participate in iPad
        # Split View or Slide Over. This key suppresses the Xcode validation
        # warning that fires when not all 4 iPad orientations are declared.
        "UIRequiresFullScreen": True,
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
