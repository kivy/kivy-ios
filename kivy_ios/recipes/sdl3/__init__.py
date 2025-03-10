import os

import sh

from kivy_ios.toolchain import Recipe, shprint


class LibSDL3Recipe(Recipe):
    version = "3.2.8"
    embed_xcframeworks = ["SDL3"]
    url = "https://github.com/libsdl-org/SDL/releases/download/release-{version}/SDL3-{version}.tar.gz"
    include_dir = "include"
    pbx_frameworks = [
        "AudioToolbox",
        "CoreAudio",
        "CoreFoundation",
        "CoreHaptics",
        "CoreVideo",
        "GameController",
        "IOKit",
        "Metal",
        "QuartzCore",
        "UniformTypeIdentifiers",
    ]

    def prebuild_platform(self, plat):
        if self.has_marker("patched"):
            return
        self.apply_patch("uikit-transparent.patch")
        # self.apply_patch("disable-hidapi.patch")
        self.set_marker("patched")

    def build_platform(self, plat):

        if plat.sdk == "iphonesimulator":
            destination = "generic/platform=iOS Simulator"
        else:
            destination = "generic/platform=iOS"

        shprint(
            sh.xcodebuild, "archive",
            "-scheme", "SDL3",
            "-project", "Xcode/SDL/SDL.xcodeproj",
            "-archivePath", f"Xcode/SDL/build/Release-{plat.sdk}",
            "-destination", destination,
            "-configuration", "Release",
            "BUILD_LIBRARY_FOR_DISTRIBUTION=YES",
            "SKIP_INSTALL=NO",
        )

    def lipoize_libraries(self):
        pass

    def create_xcframeworks(self):

        frameworks = []

        xcframework_dest = os.path.join(self.ctx.dist_dir, "xcframework", "SDL3.xcframework")
        if os.path.exists(xcframework_dest):
            # Delete the existing xcframework
            sh.rm("-rf", xcframework_dest)

        for plat in self.platforms_to_build:
            build_dir = self.get_build_dir(plat)
            frameworks.extend(
                [
                    "-framework",
                    os.path.join(
                        build_dir,
                        f"Xcode/SDL/build/Release-{plat.sdk}.xcarchive/Products/Library/Frameworks/SDL3.framework",
                    ),
                ]
            )

        shprint(
            sh.xcodebuild,
            "-create-xcframework",
            *frameworks,
            "-output",
            xcframework_dest,
        )


recipe = LibSDL3Recipe()
