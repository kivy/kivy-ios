from toolchain import Recipe, shprint
import sh


class LibSDL2MixerRecipe(Recipe):
    version = "2.0.0"
    url = "http://www.libsdl.org/projects/SDL_mixer/release/SDL2_mixer-{version}.tar.gz"
    library = "Xcode-iOS/build/Release-{arch.sdk}/libSDL2_mixer.a"
    include_dir = "SDL_mixer.h"
    depends = ["sdl2"]
    pbx_frameworks = ["ImageIO"]
    pbx_libraries = ["libc++"]

    def build_arch(self, arch):
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "HEADER_SEARCH_PATHS=$HEADER_SEARCH_PATHS {}".format(" ".join(arch.include_dirs)),
                "-sdk", arch.sdk,
                "-project", "Xcode-iOS/SDL_mixer.xcodeproj",
                "-target", "Static Library",
                "-configuration", "Release")


recipe = LibSDL2MixerRecipe()

