
from toolchain import Recipe, shprint
from os.path import join, exists
import sh
import shutil


class LibSDL2Recipe(Recipe):
    version = "2.0.3"
    url = "https://www.libsdl.org/release/SDL2-{version}.tar.gz"
    library = "Xcode-iOS/SDL/build/Release-{arch.sdk}/libSDL2.a"

    def build_arch(self, arch):
        shprint(sh.xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "-sdk", arch.sdk,
                "-project", "Xcode-iOS/SDL/SDL.xcodeproj",
                "-target", "libSDL",
                "-configuration", "Release")

    def install(self):
        for arch in self.filtered_archs:
            dest_dir = join(self.ctx.include_dir, "common", "SDL2")
            if exists(dest_dir):
                shutil.rmtree(dest_dir)
            shutil.copytree(
                join(self.get_build_dir(arch.arch), "include"),
                dest_dir)

recipe = LibSDL2Recipe()

