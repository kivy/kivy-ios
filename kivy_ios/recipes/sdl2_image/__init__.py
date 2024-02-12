from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class LibSDL2ImageRecipe(Recipe):
    version = "2.8.0"
    url = "https://github.com/libsdl-org/SDL_image/releases/download/release-{version}/SDL2_image-{version}.tar.gz"
    library = "Xcode/build/Release-{plat.sdk}/libSDL2_image.a"
    include_dir = "include/SDL_image.h"
    depends = ["sdl2"]
    pbx_frameworks = ["CoreGraphics", "MobileCoreServices"]

    def build_platform(self, plat):
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(plat.arch),
                "HEADER_SEARCH_PATHS={}".format(
                    join(self.ctx.include_dir, "common", "sdl2")),
                "-sdk", plat.sdk,
                "-project", "Xcode/SDL_image.xcodeproj",
                "-target", "Static Library",
                "-configuration", "Release")


recipe = LibSDL2ImageRecipe()
