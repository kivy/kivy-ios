from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class LibSDL2TTFRecipe(Recipe):
    version = "2.20.2"
    url = "https://github.com/libsdl-org/SDL_ttf/releases/download/release-{version}/SDL2_ttf-{version}.tar.gz"
    library = "Xcode/build/Release-{arch.sdk}/libSDL2_ttf.a"
    include_dir = "SDL_ttf.h"
    depends = ["libpng", "sdl2"]

    def build_arch(self, arch):
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "BITCODE_GENERATION_MODE=bitcode",
                "GENERATE_MASTER_OBJECT_FILE=YES",
                "HEADER_SEARCH_PATHS={sdl_include_dir} {libpng_include_dir}".format(
                    sdl_include_dir=join(self.ctx.include_dir, "common", "sdl2"),
                    libpng_include_dir=join(self.ctx.include_dir, "common", "libpng"),
                ),
                "GCC_PREPROCESSOR_DEFINITIONS=$(GCC_PREPROCESSOR_DEFINITIONS) FT_CONFIG_OPTION_USE_PNG=1",
                "-sdk", arch.sdk,
                "-project", "Xcode/SDL_ttf.xcodeproj",
                "-target", "Static Library",
                "-configuration", "Release")


recipe = LibSDL2TTFRecipe()
