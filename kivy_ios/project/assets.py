"""Generate iOS app icons, splash assets, and launch screen (spec 01 / 06).

Uses Xcode 14+ single-size ``AppIcon`` (1024x1024; Xcode scales at build time)
and a ``LaunchScreen.storyboard`` with an optional ``Splash`` image set — not the
deprecated ``LaunchImage.launchimage`` catalog.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from ..config.model import Config
from .icon import validate_icon_source

_DEFAULT_SPLASH_BACKGROUND = "#ffffff"
_HEX_COLOR = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def catalog_needed(config: Config) -> bool:
    """True when ``Assets.xcassets`` should be emitted."""
    ios = config.ios
    return bool(ios and (ios.icons.source or ios.splash.source))


def launch_screen_needed(config: Config) -> bool:
    """True when ``LaunchScreen.storyboard`` should be emitted."""
    ios = config.ios
    return bool(ios and (ios.splash.source or ios.splash.background))


def generate_asset_catalog(
    config: Config, resources_dir: str | Path, *, project_root: Path | None = None
) -> Path | None:
    """Create ``Assets.xcassets`` when icons and/or splash image are configured.

    Returns the catalog path, or None when no catalog entries are needed.
    """
    if not catalog_needed(config):
        return None

    assert config.ios is not None
    root = project_root or Path.cwd()
    catalog = Path(resources_dir) / "Assets.xcassets"
    catalog.mkdir(parents=True, exist_ok=True)
    _write_catalog_root(catalog)

    if config.ios.icons.source:
        _generate_app_icon(catalog, (root / config.ios.icons.source).resolve())
    if config.ios.splash.source:
        _generate_splash_imageset(catalog, (root / config.ios.splash.source).resolve())
    return catalog


def write_launch_screen(
    config: Config, project_dir: str | Path, *, project_root: Path | None = None
) -> Path | None:
    """Write ``LaunchScreen.storyboard`` when splash is configured."""
    if not launch_screen_needed(config):
        return None

    assert config.ios is not None
    project_dir = Path(project_dir)
    background = config.ios.splash.background or _DEFAULT_SPLASH_BACKGROUND
    rgb = _parse_hex_color(background)
    has_image = bool(config.ios.splash.source)

    path = project_dir / "LaunchScreen.storyboard"
    path.write_text(_launch_screen_xml(rgb=rgb, has_image=has_image), encoding="utf-8")
    return path


def _write_catalog_root(catalog: Path) -> None:
    (catalog / "Contents.json").write_text(
        json.dumps({"info": {"author": "kivy-ios", "version": 1}}, indent=2),
        encoding="utf-8",
    )


def _generate_app_icon(catalog: Path, source: Path) -> None:
    validate_icon_source(source)

    appicon_dir = catalog / "AppIcon.appiconset"
    appicon_dir.mkdir(parents=True, exist_ok=True)

    contents = {
        "images": [
            {
                "filename": "AppIcon.png",
                "idiom": "universal",
                "platform": "ios",
                "size": "1024x1024",
            }
        ],
        "info": {"author": "xcode", "version": 1},
    }
    (appicon_dir / "Contents.json").write_text(
        json.dumps(contents, indent=2), encoding="utf-8"
    )
    shutil.copy2(source, appicon_dir / "AppIcon.png")


def _generate_splash_imageset(catalog: Path, source: Path) -> None:
    imageset = catalog / "Splash.imageset"
    imageset.mkdir(parents=True, exist_ok=True)
    # Single unscaled "universal" image (one high-res asset Xcode scales as
    # needed), matching the AppIcon set. Declaring 1x/2x/3x slots but filling
    # only 1x left empty 2x/3x slots in Xcode.
    contents = {
        "images": [
            {
                "filename": "Splash.png",
                "idiom": "universal",
            }
        ],
        "info": {"author": "xcode", "version": 1},
    }
    (imageset / "Contents.json").write_text(
        json.dumps(contents, indent=2), encoding="utf-8"
    )
    shutil.copy2(source, imageset / "Splash.png")


def _parse_hex_color(value: str) -> tuple[float, float, float]:
    if not _HEX_COLOR.match(value):
        raise ValueError(f"invalid hex color {value!r}; expected #rrggbb or #rgb")
    digits = value[1:]
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    return (
        int(digits[0:2], 16) / 255.0,
        int(digits[2:4], 16) / 255.0,
        int(digits[4:6], 16) / 255.0,
    )


def _launch_screen_xml(*, rgb: tuple[float, float, float], has_image: bool) -> str:
    r, g, b = rgb
    color = (
        f'<color key="backgroundColor" red="{r:.6f}" green="{g:.6f}" '
        f'blue="{b:.6f}" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>'
    )
    image_block = ""
    image_constraints = ""
    resources_block = ""
    if has_image:
        image_block = """
                            <imageView clipsSubviews="YES" userInteractionEnabled="NO" contentMode="scaleAspectFit" horizontalHuggingPriority="251" verticalHuggingPriority="251" image="Splash" translatesAutoresizingMaskIntoConstraints="NO" id="splash-image">
                                <rect key="frame" x="0.0" y="0.0" width="393" height="852"/>
                            </imageView>"""
        image_constraints = """
                            <constraint firstItem="splash-image" firstAttribute="centerX" secondItem="Ze5-6b-2t3" secondAttribute="centerX" id="c1"/>
                            <constraint firstItem="splash-image" firstAttribute="centerY" secondItem="Ze5-6b-2t3" secondAttribute="centerY" id="c2"/>
                            <constraint firstItem="splash-image" firstAttribute="width" relation="lessThanOrEqual" secondItem="Ze5-6b-2t3" secondAttribute="width" id="c3"/>
                            <constraint firstItem="splash-image" firstAttribute="height" relation="lessThanOrEqual" secondItem="Ze5-6b-2t3" secondAttribute="height" id="c4"/>"""
        resources_block = """
    <resources>
        <image name="Splash" width="128" height="128"/>
    </resources>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0" toolsVersion="21701" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" launchScreen="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES" initialViewController="01J-lp-oVM">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <deployment identifier="iOS"/>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="21678"/>
        <capability name="Safe area layout guides" minToolsVersion="9.0"/>
        <capability name="documents saved in the Xcode 8 format" minToolsVersion="8.0"/>
    </dependencies>
    <scenes>
        <scene sceneID="EHf-IW-A2E">
            <objects>
                <viewController id="01J-lp-oVM" sceneMemberID="viewController">
                    <view key="view" contentMode="scaleToFill" id="Ze5-6b-2t3">
                        <rect key="frame" x="0.0" y="0.0" width="393" height="852"/>
                        <autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
                        <subviews>{image_block}
                        </subviews>
                        <viewLayoutGuide key="safeArea" id="safe-area"/>
                        {color}
                        <constraints>{image_constraints}
                        </constraints>
                    </view>
                </viewController>
                <placeholder placeholderIdentifier="IBFirstResponder" id="iYj-Kq-Ea1" userLabel="First Responder" sceneMemberID="firstResponder"/>
            </objects>
            <point key="canvasLocation" x="53" y="375"/>
        </scene>
    </scenes>{resources_block}
</document>
"""
