"""Unit tests for kivy_ios.tools.external.xcassets.

These cover the Python-side pieces that can be exercised without macOS's
`sips` binary: the Pillow-based `_buildimage` (used by launch images) and
the argument list built by `_generate` for the sips invocation.
"""
from os.path import join
from unittest.mock import patch

from PIL import Image

from kivy_ios.tools.external import xcassets


def _save_palette_png(path):
    """Write a tiny palette-mode ("P") PNG — triggers the original crash."""
    im = Image.new("P", (20, 20), color=5)
    palette = []
    for i in range(256):
        palette.extend((i, i, i))
    im.putpalette(palette)
    im.save(path)


def _save_rgb_png(path, size=(20, 20), color=(10, 20, 30)):
    Image.new("RGB", size, color).save(path)


class TestBuildImage:
    def test_palette_mode_does_not_crash(self, tmp_path):
        """Palette-mode PNGs must not raise, regression for PR #994.

        Before the `.convert("RGBA")` fix, `im.getpixel((0, 0))` returns an
        int for "P" mode and `bgcolor[:3]` raises TypeError.
        """
        src = tmp_path / "in.png"
        dst = tmp_path / "out.png"
        _save_palette_png(str(src))

        xcassets._buildimage(str(src), str(dst), [100, 100])

        assert dst.exists()
        with Image.open(dst) as out:
            assert out.size == (100, 100)
            assert out.mode == "RGB"

    def test_rgb_centers_and_pads(self, tmp_path):
        """RGB source smaller than target is centered on a bg-color canvas."""
        src = tmp_path / "in.png"
        dst = tmp_path / "out.png"
        _save_rgb_png(str(src), size=(10, 10), color=(10, 20, 30))

        xcassets._buildimage(str(src), str(dst), [30, 30])

        with Image.open(dst) as out:
            assert out.size == (30, 30)
            assert out.getpixel((0, 0)) == (10, 20, 30)
            assert out.getpixel((15, 15)) == (10, 20, 30)

    def test_resizes_oversized_source(self, tmp_path):
        """Source larger than target is scaled down preserving aspect ratio."""
        src = tmp_path / "in.png"
        dst = tmp_path / "out.png"
        _save_rgb_png(str(src), size=(200, 100))

        xcassets._buildimage(str(src), str(dst), [50, 50])

        with Image.open(dst) as out:
            assert out.size == (50, 50)

    def test_accepts_list_size(self, tmp_path):
        """`size` arrives as a list from _generate — Image.new wants a tuple.

        Regression for the `tuple(size)` hunk in PR #994.
        """
        src = tmp_path / "in.png"
        dst = tmp_path / "out.png"
        _save_rgb_png(str(src))

        xcassets._buildimage(str(src), str(dst), [40, 40])
        assert dst.exists()


class TestGenerateIcon:
    def test_forces_exact_dimensions(self, tmp_path):
        """Icon generation must call sips with `-z H W`, not `-Z max`.

        Apple rejects non-square icons. The old `-Z` only bounded the
        largest side and kept aspect ratio, producing rectangular output
        for rectangular sources. PR #994 switches to `-z c c` to force an
        exact square.
        """
        image_xcassets = tmp_path
        (image_xcassets / "AppIcon.appiconset").mkdir()

        options = (("120", None, "Icon120.png"),)
        src_image = tmp_path / "src.png"
        _save_rgb_png(str(src_image))

        with patch.object(xcassets.sh, "sips", create=True) as mock_sips:
            xcassets._generate(
                "AppIcon.appiconset",
                str(image_xcassets),
                str(src_image),
                options,
                icon=True,
            )

        mock_sips.assert_called_once()
        args = mock_sips.call_args.args

        assert "-z" in args, f"expected -z flag, got: {args}"
        assert "-Z" not in args, f"legacy -Z flag still present: {args}"

        z_index = args.index("-z")
        assert args[z_index + 1] == "120"
        assert args[z_index + 2] == "120"

        assert "--out" in args
        out_index = args.index("--out")
        assert args[out_index + 1] == join(
            str(image_xcassets), "AppIcon.appiconset", "Icon120.png"
        )

    def test_uses_in_fn_when_provided(self, tmp_path):
        """When `in_fn` is set, sips reads from the already-generated larger
        icon in the appiconset dir rather than the user-provided source."""
        image_xcassets = tmp_path
        (image_xcassets / "AppIcon.appiconset").mkdir()

        options = (("60", "Icon120.png", "Icon60.png"),)
        src_image = tmp_path / "src.png"
        _save_rgb_png(str(src_image))

        with patch.object(xcassets.sh, "sips", create=True) as mock_sips:
            xcassets._generate(
                "AppIcon.appiconset",
                str(image_xcassets),
                str(src_image),
                options,
                icon=True,
            )

        args = mock_sips.call_args.args
        assert args[0] == join(
            str(image_xcassets), "AppIcon.appiconset", "Icon120.png"
        )


class TestGenerateLaunchImage:
    def test_calls_buildimage(self, tmp_path):
        """Non-icon path skips sips and routes through Pillow-based _buildimage."""
        image_xcassets = tmp_path
        (image_xcassets / "LaunchImage.launchimage").mkdir()

        options = (("40 30", None, "Default40x30.png"),)
        src_image = tmp_path / "src.png"
        _save_rgb_png(str(src_image), size=(10, 10))

        xcassets._generate(
            "LaunchImage.launchimage",
            str(image_xcassets),
            str(src_image),
            options,
            icon=False,
        )

        out = image_xcassets / "LaunchImage.launchimage" / "Default40x30.png"
        assert out.exists()
        with Image.open(out) as im:
            assert im.size == (40, 30)
