from toolchain import Recipe, shprint
from os.path import join
import sh
import shutil


class LibSDL2TTFRecipe(Recipe):
    version = "2.0.12"
    url = "https://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-{version}.tar.gz"
    library = "Xcode-iOS/build/Release-{arch.sdk}/libSDL2_ttf.a"
    include_dir = "SDL_ttf.h"
    depends = ["sdl2", "freetype"]

    def build_arch(self, arch):
        build_env = arch.get_env()
        shprint(sh.xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "HEADER_SEARCH_PATHS={}".format(
                    join(self.ctx.include_dir, "common", "SDL2")),
                "OTHER_CFLAGS={}".format(build_env["OTHER_CFLAGS"]),
                "OTHER_LDFLAGS={}".format(build_env["OTHER_LDFLAGS"]),
                "-sdk", arch.sdk,
                "-project", "Xcode-iOS/SDL_ttf.xcodeproj",
                "-target", "Static Library",
                "-configuration", "Release")

    def install(self):
        for arch in self.filtered_archs:
            shutil.copy(
                join(self.get_build_dir(arch.arch), "SDL_ttf.h"),
                join(self.ctx.include_dir, "common", "SDL2"))

recipe = LibSDL2TTFRecipe()

