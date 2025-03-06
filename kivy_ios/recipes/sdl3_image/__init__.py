import os

import sh

from kivy_ios.toolchain import Recipe, shprint


class LibSDL3ImageRecipe(Recipe):
    version = "3.2.4"
    embed_xcframeworks = ["SDL3_image"]
    url = "https://github.com/libsdl-org/SDL_image/releases/download/release-{version}/SDL3_image-{version}.tar.gz"
    include_dir = "include"
    pbx_frameworks = [
        "CoreGraphics",
        "Foundation",
        "ImageIO",
        "MobileCoreServices",
        "UIKit"
    ]

    def build_platform(self, plat):

        if plat.sdk == "iphonesimulator":
            destination = "generic/platform=iOS Simulator"
        else:
            destination = "generic/platform=iOS"

        shprint(
            sh.xcodebuild, "archive",
            "-scheme", "SDL3_image",
            "-project", "Xcode/SDL_image.xcodeproj",
            "-archivePath", f"Xcode/build/Release-{plat.sdk}",
            "-destination", destination,
            "-configuration", "Release",
            "BUILD_LIBRARY_FOR_DISTRIBUTION=YES",
            "SKIP_INSTALL=NO",
        )

    def lipoize_libraries(self):
        pass

    def create_xcframeworks(self):

        frameworks = []

        xcframework_dest = os.path.join(self.ctx.dist_dir, "xcframework", "SDL3_image.xcframework")
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
                        f"Xcode/build/Release-{plat.sdk}.xcarchive/Products/Library/Frameworks/SDL3_image.framework",
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


recipe = LibSDL3ImageRecipe()
