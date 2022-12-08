from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class LibSDL2ImageRecipe(Recipe):
    version = "2.6.2"
    url = "https://github.com/libsdl-org/SDL_image/releases/download/release-{version}/SDL2_image-{version}.tar.gz"
    library = "Xcode/build/Release-{arch.sdk}/libSDL2_image.a"
    include_dir = "SDL_image.h"
    depends = ["sdl2"]
    pbx_frameworks = ["CoreGraphics", "MobileCoreServices"]

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        # fix-ios-xcodebuild is a patch taken from the SDL2_image repo
        # (See: https://github.com/libsdl-org/SDL_image/pull/292)
        # We will need to remove it once is included into a release
        self.apply_patch("fix-ios-xcodebuild.patch")
        self.set_marker("patched")

    def build_arch(self, arch):
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "BITCODE_GENERATION_MODE=bitcode",
                "HEADER_SEARCH_PATHS={}".format(
                    join(self.ctx.include_dir, "common", "sdl2")),
                "-sdk", arch.sdk,
                "-project", "Xcode/SDL_image.xcodeproj",
                "-target", "Static Library",
                "-configuration", "Release")


recipe = LibSDL2ImageRecipe()
