from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh
import shutil
import shlex


class LibSDL2TTFRecipe(Recipe):
    version = "2.0.15"
    url = "https://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-{version}.tar.gz"
    library = "libSDL2_ttf.a"
    include_dir = "SDL_ttf.h"
    depends = ["sdl2", "freetype"]

    def build_arch(self, arch):
        # XCode-iOS have shipped freetype that don't work with i386
        # ./configure require too much things to setup it correcly.
        # so build by hand.
        build_env = arch.get_env()
        cc = sh.Command(build_env["CC"])
        output = join(self.build_dir, "SDL_ttf.o")
        args = shlex.split(build_env["CFLAGS"])
        args += ["-c", "-o", output, "SDL_ttf.c"]
        shprint(cc, *args)
        shprint(sh.ar, "-q", join(self.build_dir, "libSDL2_ttf.a"), output)

    def install(self):
        for arch in self.filtered_archs:
            shutil.copy(
                join(self.get_build_dir(arch.arch), "SDL_ttf.h"),
                join(self.ctx.include_dir, "common", "SDL2"))


recipe = LibSDL2TTFRecipe()
