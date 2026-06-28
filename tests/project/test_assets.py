"""Unit tests for modern iOS asset catalog and launch screen generation."""

from __future__ import annotations

import json

import pytest
from PIL import Image

from kivy_ios.project.assets import (
    _parse_hex_color,
    generate_asset_catalog,
    write_launch_screen,
)
from kivy_ios.project.icon import IconSourceError

from .test_icon import _write_minimal_png


class TestAppIcon:
    def test_rejects_wrong_size(self, make_config, tmp_path):
        (tmp_path / "assets").mkdir()
        _write_minimal_png(tmp_path / "assets" / "icon.png", 256, 256)
        cfg = make_config('\n[tool.kivy.ios.icons]\nsource = "assets/icon.png"')
        with pytest.raises(IconSourceError, match="256x256"):
            generate_asset_catalog(cfg, tmp_path / "Resources", project_root=tmp_path)

    def test_single_size_catalog(self, make_config, tmp_path):
        (tmp_path / "assets").mkdir()
        _write_minimal_png(tmp_path / "assets" / "icon.png", 1024, 1024)
        cfg = make_config('\n[tool.kivy.ios.icons]\nsource = "assets/icon.png"')
        resources = tmp_path / "Resources"
        catalog = generate_asset_catalog(cfg, resources, project_root=tmp_path)
        assert catalog is not None
        contents = json.loads(
            (catalog / "AppIcon.appiconset" / "Contents.json").read_text()
        )
        assert len(contents["images"]) == 1
        img = contents["images"][0]
        assert img["filename"] == "AppIcon.png"
        assert img["idiom"] == "universal"
        assert img["platform"] == "ios"
        assert img["size"] == "1024x1024"
        assert (catalog / "AppIcon.appiconset" / "AppIcon.png").is_file()


class TestSplash:
    def test_splash_imageset_and_launch_screen(self, make_config, tmp_path):
        (tmp_path / "assets").mkdir()
        Image.new("RGBA", (200, 100), (0, 0, 255, 255)).save(
            tmp_path / "assets" / "splash.png"
        )
        cfg = make_config(
            '\n[tool.kivy.ios.splash]\nsource = "assets/splash.png"\n'
            'background = "#112233"'
        )
        resources = tmp_path / "Resources"
        catalog = generate_asset_catalog(cfg, resources, project_root=tmp_path)
        assert catalog is not None
        assert (catalog / "Splash.imageset" / "Splash.png").is_file()
        assert not (catalog / "LaunchImage.launchimage").exists()
        # Single unscaled universal image -- no empty 1x/2x/3x slots in Xcode.
        manifest = json.loads(
            (catalog / "Splash.imageset" / "Contents.json").read_text()
        )
        assert manifest["images"] == [{"filename": "Splash.png", "idiom": "universal"}]

        storyboard = write_launch_screen(cfg, tmp_path, project_root=tmp_path)
        assert storyboard is not None
        xml = storyboard.read_text()
        assert 'image="Splash"' in xml
        assert 'red="0.066667"' in xml

    def test_background_only_launch_screen(self, make_config, tmp_path):
        cfg = make_config('\n[tool.kivy.ios.splash]\nbackground = "#ffffff"')
        assert (
            generate_asset_catalog(cfg, tmp_path / "Resources", project_root=tmp_path)
            is None
        )
        storyboard = write_launch_screen(cfg, tmp_path, project_root=tmp_path)
        assert storyboard is not None
        assert 'image="Splash"' not in storyboard.read_text()


class TestHexColor:
    def test_six_digit(self):
        assert _parse_hex_color("#112233") == pytest.approx(
            (17 / 255, 34 / 255, 51 / 255)
        )

    def test_three_digit(self):
        assert _parse_hex_color("#fff") == pytest.approx((1.0, 1.0, 1.0))

    def test_invalid(self):
        with pytest.raises(ValueError, match="invalid hex color"):
            _parse_hex_color("white")
