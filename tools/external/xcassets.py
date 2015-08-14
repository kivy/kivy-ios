"""
Icon and LaunchImage generator for iOS
======================================

.. author:: Mathieu Virbel <mat@meltingrocks.com>
"""

__all__ = ["launchimage"]

import sh
import json
import shutil
from os.path import join, exists
from os import makedirs


launchimage_json = {
  "images" : [
    {
      "extent" : "full-screen",
      "idiom" : "iphone",
      "subtype" : "736h",
      "filename" : "Default1242x2208.png",
      "minimum-system-version" : "8.0",
      "orientation" : "portrait",
      "scale" : "3x"
    },
    {
      "extent" : "full-screen",
      "idiom" : "iphone",
      "subtype" : "736h",
      "filename" : "Default2208x1242.png",
      "minimum-system-version" : "8.0",
      "orientation" : "landscape",
      "scale" : "3x"
    },
    {
      "extent" : "full-screen",
      "idiom" : "iphone",
      "subtype" : "667h",
      "filename" : "Default750x1334.png",
      "minimum-system-version" : "8.0",
      "orientation" : "portrait",
      "scale" : "2x"
    },
    {
      "orientation" : "portrait",
      "idiom" : "iphone",
      "extent" : "full-screen",
      "minimum-system-version" : "7.0",
      "filename" : "Default640x960.png",
      "scale" : "2x"
    },
    {
      "extent" : "full-screen",
      "idiom" : "iphone",
      "subtype" : "retina4",
      "filename" : "Default640x1136.png",
      "minimum-system-version" : "7.0",
      "orientation" : "portrait",
      "scale" : "2x"
    },
    {
      "orientation" : "portrait",
      "idiom" : "ipad",
      "extent" : "full-screen",
      "minimum-system-version" : "7.0",
      "filename" : "Default768x1024.png",
      "scale" : "1x"
    },
    {
      "orientation" : "landscape",
      "idiom" : "ipad",
      "extent" : "full-screen",
      "minimum-system-version" : "7.0",
      "filename" : "Default1024x768.png",
      "scale" : "1x"
    },
    {
      "orientation" : "portrait",
      "idiom" : "ipad",
      "extent" : "full-screen",
      "minimum-system-version" : "7.0",
      "filename" : "Default1536x2048.png",
      "scale" : "2x"
    },
    {
      "orientation" : "landscape",
      "idiom" : "ipad",
      "extent" : "full-screen",
      "minimum-system-version" : "7.0",
      "filename" : "Default2048x1536.png",
      "scale" : "2x"
    },
    {
      "orientation" : "portrait",
      "idiom" : "iphone",
      "extent" : "full-screen",
      "filename" : "Default320x480.png",
      "scale" : "1x"
    },
    {
      "orientation" : "portrait",
      "idiom" : "iphone",
      "extent" : "full-screen",
      "filename" : "Default640x960.png",
      "scale" : "2x"
    },
    {
      "orientation" : "portrait",
      "idiom" : "iphone",
      "extent" : "full-screen",
      "filename" : "Default640x1136.png",
      "subtype" : "retina4",
      "scale" : "2x"
    },
    {
      "orientation" : "portrait",
      "idiom" : "ipad",
      "extent" : "full-screen",
      "filename" : "Default768x1024.png",
      "scale" : "1x"
    },
    {
      "orientation" : "landscape",
      "idiom" : "ipad",
      "extent" : "full-screen",
      "filename" : "Default1024x768.png",
      "scale" : "1x"
    },
    {
      "orientation" : "portrait",
      "idiom" : "ipad",
      "extent" : "full-screen",
      "filename" : "Default1536x2048.png",
      "scale" : "2x"
    },
    {
      "orientation" : "landscape",
      "idiom" : "ipad",
      "extent" : "full-screen",
      "filename" : "Default2048x1536.png",
      "scale" : "2x"
    }
  ],
  "info" : {
    "version" : 1,
    "author" : "xcode"
  }
}


def launchimage(image_xcassets, image_fn):
    """Generate all the possible Launch Images from a single image_fn
    """
    launchimage_dir = join(image_xcassets, "LaunchImage.launchimage")
    if not exists(launchimage_dir):
        makedirs(launchimage_dir)
    with open(join(launchimage_dir, "Contents.json"), "w") as fd:
        json.dump(launchimage_json, fd)

    options = (
        # -Z, -c, -r, input, output
        # iPhone 3.5" @2x
        ("640 960", None, "Default640x960.png"),
        # iPhone 3.5" @1x
        ("320 480", "Default640x960.png", "Default320x480.png"),
        # iPhone 4.0" @2x
        ("640 1136", None, "Default640x1136.png"),
        # iPhone 5.5" @3x - landscape
        ("2208 1242", None, "Default2208x1242.png"),
        # iPhone 5.5" @3x - portrait
        ("1242 2208", "Default2208x1242.png", "Default1242x2208.png"),
        # iPhone 4.7" @2x
        ("750 1334", None, "Default750x1334.png"),
        # iPad @2x - landscape
        ("2048 1536", None, "Default2048x1536.png"),
        # iPad @2x - portrait
        ("1536 2048", "Default2048x1536.png", "Default1536x2048.png"),
        # iPad @1x - landscape
        ("1024 768", "Default2048x1536.png", "Default1024x768.png"),
        # iPad @1x - portrait
        ("768 1024", "Default1024x768.png", "Default768x1024.png"),
    )

    for c, in_fn, out_fn in options:
        args = []
        # ensure one side will not be bigger than the other (ie, the image will
        # fit to the screen)
        args += ["-Z", str(min(map(int, c.split())))]
        # if there is any left pixel, cover in black.
        args += ["-p"] + c.split()
        # and crop the image in necessary.
        args += ["-c"] + c.split()[::-1]
        if in_fn is not None:
            args += [join(image_xcassets, "LaunchImage.launchimage", in_fn)]
        else:
            args += [image_fn]
        args += [
            "--out",
            join(image_xcassets, "LaunchImage.launchimage", out_fn)
        ]
        print "sips", " ".join(args)
        sh.sips(*args)

