from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class LibSDL2TTFRecipe(Recipe):
    version = "2.20.1"
    url = "https://github.com/libsdl-org/SDL_ttf/releases/download/release-{version}/SDL2_ttf-{version}.tar.gz"
    library = "Xcode/build/Release-{arch.sdk}/libSDL2_ttf.a"
    include_dir = "SDL_ttf.h"
    depends = ["sdl2"]

    def build_arch(self, arch):
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "BITCODE_GENERATION_MODE=bitcode",
                "HEADER_SEARCH_PATHS={}".format(
                    join(self.ctx.include_dir, "common", "sdl2")),
                "-sdk", arch.sdk,
                "-project", "Xcode/SDL_ttf.xcodeproj",
                "-target", "Static Library",
                "-configuration", "Release")


recipe = LibSDL2TTFRecipe()
