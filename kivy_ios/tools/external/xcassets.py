"""
Icon and LaunchImage generator for iOS
======================================

.. author:: Mathieu Virbel <mat@meltingrocks.com>
"""
# flake8: noqa (E121 mainly)

__all__ = ["launchimage"]

import sh
import json
from PIL import Image
from os.path import join, exists
from os import makedirs

appicon_json = {
  "images": [
    {
      "idiom": "iphone",
      "size": "20x20",
      "scale": "2x",
      "filename": "Icon40.png"
    },
    {
      "idiom": "iphone",
      "size": "20x20",
      "scale": "3x",
      "filename": "Icon60.png"
    },
    {
      "size": "29x29",
      "idiom": "iphone",
      "filename": "Icon29.png",
      "scale": "1x"
    },
    {
      "size": "29x29",
      "idiom": "iphone",
      "filename": "Icon58.png",
      "scale": "2x"
    },
    {
      "size": "29x29",
      "idiom": "iphone",
      "filename": "Icon87.png",
      "scale": "3x"
    },
    {
      "size": "40x40",
      "idiom": "iphone",
      "filename": "Icon80.png",
      "scale": "2x"
    },
    {
      "size": "40x40",
      "idiom": "iphone",
      "filename": "Icon120.png",
      "scale": "3x"
    },
    {
      "size": "57x57",
      "idiom": "iphone",
      "filename": "Icon57.png",
      "scale": "1x"
    },
    {
      "size": "57x57",
      "idiom": "iphone",
      "filename": "Icon114.png",
      "scale": "2x"
    },
    {
      "size": "60x60",
      "idiom": "iphone",
      "filename": "Icon120.png",
      "scale": "2x"
    },
    {
      "size": "60x60",
      "idiom": "iphone",
      "filename": "Icon180.png",
      "scale": "3x"
    },
    {
      "idiom": "ipad",
      "size": "20x20",
      "filename": "Icon20.png",
      "scale": "1x"
    },
    {
      "idiom": "ipad",
      "size": "20x20",
      "filename": "Icon40.png",
      "scale": "2x"
    },
    {
      "size": "29x29",
      "idiom": "ipad",
      "filename": "Icon29.png",
      "scale": "1x"
    },
    {
      "size": "29x29",
      "idiom": "ipad",
      "filename": "Icon58.png",
      "scale": "2x"
    },
    {
      "size": "40x40",
      "idiom": "ipad",
      "filename": "Icon40.png",
      "scale": "1x"
    },
    {
      "size": "40x40",
      "idiom": "ipad",
      "filename": "Icon80.png",
      "scale": "2x"
    },
    {
      "size": "50x50",
      "idiom": "ipad",
      "filename": "Icon50.png",
      "scale": "1x"
    },
    {
      "size": "50x50",
      "idiom": "ipad",
      "filename": "Icon100.png",
      "scale": "2x"
    },
    {
      "size": "72x72",
      "idiom": "ipad",
      "filename": "Icon72.png",
      "scale": "1x"
    },
    {
      "size": "72x72",
      "idiom": "ipad",
      "filename": "Icon144.png",
      "scale": "2x"
    },
    {
      "size": "76x76",
      "idiom": "ipad",
      "filename": "Icon76.png",
      "scale": "1x"
    },
    {
      "size": "76x76",
      "idiom": "ipad",
      "filename": "Icon152.png",
      "scale": "2x"
    },
    # If activated, we got a submission error:
    # "Error ITMS-9000: Invalid Image Path - No image found at the path
    # referenced under key 'CFBundleIcons': 'AppIcon120x120'"
    # {
    #   "size": "120x120",
    #   "idiom": "car",
    #   "filename": "Icon120.png",
    #   "scale": "1x"
    # },
    {
      "size": "24x24",
      "idiom": "watch",
      "scale": "2x",
      "filename": "Icon48.png",
      "role": "notificationCenter",
      "subtype": "38mm"
    },
    {
      "size": "27.5x27.5",
      "idiom": "watch",
      "scale": "2x",
      "filename": "Icon55.png",
      "role": "notificationCenter",
      "subtype": "42mm"
    },
    {
      "size": "29x29",
      "idiom": "watch",
      "filename": "Icon58.png",
      "role": "companionSettings",
      "scale": "2x"
    },
    {
      "size": "29x29",
      "idiom": "watch",
      "filename": "Icon87.png",
      "role": "companionSettings",
      "scale": "3x"
    },
    {
      "size": "40x40",
      "idiom": "watch",
      "scale": "2x",
      "filename": "Icon80.png",
      "role": "appLauncher",
      "subtype": "38mm"
    },
    {
      "size": "44x44",
      "idiom": "watch",
      "scale": "2x",
      "filename": "Icon88.png",
      "role": "longLook",
      "subtype": "42mm"
    },
    {
      "size": "86x86",
      "idiom": "watch",
      "scale": "2x",
      "filename": "Icon172.png",
      "role": "quickLook",
      "subtype": "38mm"
    },
    {
      "size": "44x44",
      "idiom": "watch",
      "scale": "2x",
      "filename": "Icon88.png",
      "role": "appLauncher",
      "subtype": "40mm"
    },
    {
      "size": "50x50",
      "idiom": "watch",
      "scale": "2x",
      "filename": "Icon100.png",
      "role": "appLauncher",
      "subtype": "44mm"
    },
    {
      "size": "98x98",
      "idiom": "watch",
      "scale": "2x",
      "filename": "Icon196.png",
      "role": "quickLook",
      "subtype": "42mm"
    },
    {
      "size": "108x108",
      "idiom": "watch",
      "scale": "2x",
      "filename": "Icon216.png",
      "role": "quickLook",
      "subtype": "44mm"
    },
    {
      "size": "16x16",
      "idiom": "mac",
      "filename": "Icon16.png",
      "scale": "1x"
    },
    {
      "size": "16x16",
      "idiom": "mac",
      "filename": "Icon32.png",
      "scale": "2x"
    },
    {
      "size": "32x32",
      "idiom": "mac",
      "filename": "Icon32.png",
      "scale": "1x"
    },
    {
      "size": "32x32",
      "idiom": "mac",
      "filename": "Icon64.png",
      "scale": "2x"
    },
    {
      "size": "128x128",
      "idiom": "mac",
      "filename": "Icon128.png",
      "scale": "1x"
    },
    {
      "size": "128x128",
      "idiom": "mac",
      "filename": "Icon256.png",
      "scale": "2x"
    },
    {
      "size": "256x256",
      "idiom": "mac",
      "filename": "Icon256.png",
      "scale": "1x"
    },
    {
      "size": "256x256",
      "idiom": "mac",
      "filename": "Icon512.png",
      "scale": "2x"
    },
    {
      "size": "512x512",
      "idiom": "mac",
      "filename": "Icon512.png",
      "scale": "1x"
    },
    {
      "size": "512x512",
      "idiom": "mac",
      "filename": "Icon1024.png",
      "scale": "2x"
    },
    {
      "size": "83.5x83.5",
      "idiom": "ipad",
      "filename": "Icon167.png",
      "scale": "2x"
    },
    {
      "idiom": "ios-marketing",
      "size": "1024x1024",
      "scale": "1x",
      "filename": "Icon1024.png"
    },
    {
      "idiom": "watch-marketing",
      "size": "1024x1024",
      "scale": "1x",
      "filename": "Icon1024.png"
    },
  ],
  "info": {
    "version": 1,
    "author": "xcode"
  },
  # "properties": {
  #   "pre-rendered": True
  # }
}


launchimage_json = {
  "images": [
    {
      "extent": "full-screen",
      "idiom": "iphone",
      "subtype": "736h",
      "filename": "Default1242x2208.png",
      "minimum-system-version": "8.0",
      "orientation": "portrait",
      "scale": "3x"
    },
    {
      "extent": "full-screen",
      "idiom": "iphone",
      "subtype": "736h",
      "filename": "Default2208x1242.png",
      "minimum-system-version": "8.0",
      "orientation": "landscape",
      "scale": "3x"
    },
    {
      "extent": "full-screen",
      "idiom": "iphone",
      "subtype": "667h",
      "filename": "Default750x1334.png",
      "minimum-system-version": "8.0",
      "orientation": "portrait",
      "scale": "2x"
    },
    {
      "orientation": "portrait",
      "idiom": "iphone",
      "extent": "full-screen",
      "minimum-system-version": "7.0",
      "filename": "Default640x960.png",
      "scale": "2x"
    },
    {
      "extent": "full-screen",
      "idiom": "iphone",
      "subtype": "retina4",
      "filename": "Default640x1136.png",
      "minimum-system-version": "7.0",
      "orientation": "portrait",
      "scale": "2x"
    },
    {
      "orientation": "portrait",
      "idiom": "ipad",
      "extent": "full-screen",
      "minimum-system-version": "7.0",
      "filename": "Default768x1024.png",
      "scale": "1x"
    },
    {
      "orientation": "landscape",
      "idiom": "ipad",
      "extent": "full-screen",
      "minimum-system-version": "7.0",
      "filename": "Default1024x768.png",
      "scale": "1x"
    },
    {
      "orientation": "portrait",
      "idiom": "ipad",
      "extent": "full-screen",
      "minimum-system-version": "7.0",
      "filename": "Default1536x2048.png",
      "scale": "2x"
    },
    {
      "orientation": "landscape",
      "idiom": "ipad",
      "extent": "full-screen",
      "minimum-system-version": "7.0",
      "filename": "Default2048x1536.png",
      "scale": "2x"
    },
    {
      "orientation": "portrait",
      "idiom": "iphone",
      "extent": "full-screen",
      "filename": "Default320x480.png",
      "scale": "1x"
    },
    {
      "orientation": "portrait",
      "idiom": "iphone",
      "extent": "full-screen",
      "filename": "Default640x960.png",
      "scale": "2x"
    },
    {
      "orientation": "portrait",
      "idiom": "iphone",
      "extent": "full-screen",
      "filename": "Default640x1136.png",
      "subtype": "retina4",
      "scale": "2x"
    },
    {
      "orientation": "portrait",
      "idiom": "ipad",
      "extent": "full-screen",
      "filename": "Default768x1024.png",
      "scale": "1x"
    },
    {
      "orientation": "landscape",
      "idiom": "ipad",
      "extent": "full-screen",
      "filename": "Default1024x768.png",
      "scale": "1x"
    },
    {
      "orientation": "portrait",
      "idiom": "ipad",
      "extent": "full-screen",
      "filename": "Default1536x2048.png",
      "scale": "2x"
    },
    {
      "orientation": "landscape",
      "idiom": "ipad",
      "extent": "full-screen",
      "filename": "Default2048x1536.png",
      "scale": "2x"
    },
  ],
  "info": {
    "version": 1,
    "author": "xcode"
  }
}


def icon(image_xcassets, image_fn):
    """Generate all the possible Icon from a single image_fn
    """
    appicon_dir = join(image_xcassets, "AppIcon.appiconset")
    if not exists(appicon_dir):
        makedirs(appicon_dir)
    with open(join(appicon_dir, "Contents.json"), "w") as fd:
        json.dump(appicon_json, fd)

    options = (
        # iPhone
        # Spotlight - iOS 5,6
        # Settings - iOS 5-8
        # 29pt - 1x,2x,3x
        ("87", None, "Icon87.png"),
        ("58", None, "Icon58.png"),
        ("29", "Icon58.png", "Icon29.png"),

        # iPhone notification
        # 20pt - 2x,3x
        # ("40", None, "Icon40.png"),
        ("60", None, "Icon60.png"),

        # iPhone
        # Spotlight - iOS 7-8
        # 40pt 2x,3x
        ("120", None, "Icon120.png"),
        ("80", None, "Icon80.png"),

        # iPhone
        # App - iOS 5,6
        # 57pt 1x,2x
        ("114", None, "Icon114.png"),
        ("57", "Icon114.png", "Icon57.png"),

        # iPhone
        # App - iOS 7,8
        # 60pt 2x,3x
        ("180", None, "Icon180.png"),
        # ("120", None, "Icon120.png # duplicate"),

        # iPad
        # Notifications
        # 20pt 1x,2x
        ("20", "Icon80.png", "Icon20.png"),
        ("40", "Icon80.png", "Icon40.png"),

        # iPad
        # Settings iOS 5-8
        # ("58", None, "Icon58.png # duplicate"),
        # ("29", "Icon58.png", "Icon29.png # duplicate"),

        # iPad
        # Spotlight iOS 7,8
        # 40pt 1x,2x
        # ("80", None, "Icon80.png # duplicate"),
        ("40", "Icon80.png", "Icon40.png"),

        # iPad
        # Spotlight iOS 5,6
        # 50pt 1x,2x
        ("100", None, "Icon100.png"),
        ("50", "Icon100.png", "Icon50.png"),

        # iPad
        # App iOS 5,6
        # 72pt 1x,2x
        ("144", None, "Icon144.png"),
        ("72", "Icon144.png", "Icon72.png"),

        # iPad
        # App iOS 7,8
        # 76pt 1x,2x
        ("152", None, "Icon152.png"),
        ("76", "Icon152.png", "Icon76.png"),

        # iPad
        # App iOS 9
        # 83.5pt 2x
        ("167", None, "Icon167.png"),


        # CarPlay
        # App iOS 8
        # 120pt 1x
        # ("120", None, "Icon120.png # duplicate"),


        # Apple Watch
        # Notification Center
        # 38mm, 42mm
        ("48", None, "Icon48.png"),
        ("55", None, "Icon55.png"),

        # Apple Watch
        # Companion Settings
        # 29pt 2x,3x
        # ("58", None, "Icon58.png # duplicate"),
        # ("87", None, "Icon87.png # duplicate"),

        # Apple Watch
        # Home Screen (All)
        # Long Look (38mm)
        # ("80", None, "Icon80.png # duplicate"),

        # Apple Watch
        # Long Look (42mm)
        ("88", None, "Icon88.png"),

        # Apple Watch
        # Short Look
        # 38mm, 42mm, 44mm
        ("172", None, "Icon172.png"),
        ("196", None, "Icon196.png"),
        ("216", None, "Icon216.png"),


        # OS X
        # 512pt 1x,2x
        ("1024", None, "Icon1024.png"),
        ("512", "Icon1024.png", "Icon512.png"),

        # OS X
        # 256pt 1x,2x
        # ("512", "Icon1024.png", "Icon512.png # duplicate"),
        ("256", "Icon512.png", "Icon256.png"),

        # OS X
        # 128pt 1x,2x
        # ("256", "Icon512.png", "Icon256.png # duplicate"),
        ("128", "Icon256.png", "Icon128.png"),

        # OS X
        # 32pt 1x,2x
        ("64", "Icon128.png", "Icon64.png"),
        ("32", "Icon64.png", "Icon32.png"),

        # OS X
        # 16pt 1x,2x
        # ("32", "Icon64.png", "Icon32.png # duplicate"),
        ("16", "Icon32.png", "Icon16.png"))

    _generate("AppIcon.appiconset", image_xcassets, image_fn, options, icon=True)


def launchimage(image_xcassets, image_fn):
    """Generate all the possible Launch Images from a single image_fn
    """
    launchimage_dir = join(image_xcassets, "LaunchImage.launchimage")
    if not exists(launchimage_dir):
        makedirs(launchimage_dir)
    with open(join(launchimage_dir, "Contents.json"), "w") as fd:
        json.dump(launchimage_json, fd)

    options = (
        # size, input, output
        # iPhone 3.5" @2x
        ("640 960", None, "Default640x960.png"),
        # iPhone 3.5" @1x
        ("320 480", None, "Default320x480.png"),
        # iPhone 4.0" @2x
        ("640 1136", None, "Default640x1136.png"),
        # iPhone 5.5" @3x - landscape
        ("2208 1242", None, "Default2208x1242.png"),
        # iPhone 5.5" @3x - portrait
        ("1242 2208", None, "Default1242x2208.png"),
        # iPhone 4.7" @2x
        ("750 1334", None, "Default750x1334.png"),
        # iPad @2x - landscape
        ("2048 1536", None, "Default2048x1536.png"),
        # iPad @2x - portrait
        ("1536 2048", None, "Default1536x2048.png"),
        # iPad @1x - landscape
        ("1024 768", None, "Default1024x768.png"),
        # iPad @1x - portrait
        ("768 1024", None, "Default768x1024.png"),
    )

    _generate("LaunchImage.launchimage", image_xcassets, image_fn, options)


def _buildimage(in_fn, out_fn, size, padcolor=None):
    im = Image.open(in_fn)

    # read the first left/bottom pixel
    bgcolor = im.getpixel((0, 0))

    # ensure the image fit in the destination size
    if im.size[0] > size[0] or im.size[1] > size[1]:
        f = max(im.size[0] / size[0], im.size[1] / size[1])
        newsize = int(im.size[0] / f), int(im.size[1] / f)
        im = im.resize(newsize)

    # create final image
    outim = Image.new("RGB", size, bgcolor[:3])
    x = (size[0] - im.size[0]) // 2
    y = (size[1] - im.size[1]) // 2
    outim.paste(im, (x, y))

    # save the image
    outim.save(out_fn)


def _generate(d, image_xcassets, image_fn, options, icon=False):
    for c, in_fn, out_fn in options:
        args = []
        if in_fn is not None:
            filename = join(image_xcassets, d, in_fn)
        else:
            filename = image_fn

        if icon:
            args += [filename, "-Z", c]
            args += [
                "--out",
                join(image_xcassets, d, out_fn)
            ]
            print("sips", " ".join(args))
            sh.sips(*args)
        else:
            size = [int(x) for x in c.split()]
            _buildimage(filename, join(image_xcassets, d, out_fn), size)
