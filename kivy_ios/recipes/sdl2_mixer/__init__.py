from kivy_ios.toolchain import Recipe, shprint
import sh


class LibSDL2MixerRecipe(Recipe):
    version = "2.6.3"
    url = "https://github.com/libsdl-org/SDL_mixer/releases/download/release-{version}/SDL2_mixer-{version}.tar.gz"
    library = "Xcode/build/Release-{plat.sdk}/libSDL2_mixer.a"
    include_dir = "include/SDL_mixer.h"
    depends = ["sdl2"]
    pbx_frameworks = ["ImageIO"]
    pbx_libraries = ["libc++"]

    def build_platform(self, plat):
        # endian.h is in /usr/include/machine/ (Since MacOs Mojave?)
        # header is needed by libvorbis, so We're adding that folder
        # to HEADER_SEARCH_PATHS
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(plat.arch),
                "HEADER_SEARCH_PATHS=$HEADER_SEARCH_PATHS /usr/include/machine {} ".format(" ".join(plat.include_dirs)),
                "-sdk", plat.sdk,
                "-project", "Xcode/SDL_mixer.xcodeproj",
                "-target", "Static Library",
                "-configuration", "Release")


recipe = LibSDL2MixerRecipe()
