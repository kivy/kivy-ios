from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class LibSDL2ImageRecipe(Recipe):
    version = "2.0.5"
    url = "https://www.libsdl.org/projects/SDL_image/release/SDL2_image-{version}.tar.gz"
    library = "Xcode-iOS/build/Release-{arch.sdk}/libSDL2_image.a"
    include_dir = "SDL_image.h"
    depends = ["sdl2", "libwebp"]
    pbx_frameworks = ["CoreGraphics", "MobileCoreServices"]

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("webp.patch")
        self.set_marker("patched")

    def build_arch(self, arch):
        header_paths = [
            "$HEADER_SEARCH_PATHS",
            join(self.ctx.include_dir, "common", "sdl2"),
        ]
        framework_paths = [
            "$FRAMEWORK_SEARCH_PATHS",
            join(self.ctx.dist_dir, "frameworks"),
        ]
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "BITCODE_GENERATION_MODE=bitcode",
                "HEADER_SEARCH_PATHS={}".format(" ".join(header_paths)),
                "FRAMEWORK_SEARCH_PATHS={}".format(" ".join(framework_paths)),
                "-sdk", arch.sdk,
                "-project", "Xcode-iOS/SDL_image.xcodeproj",
                "-target", "libSDL_image-iOS",
                "-configuration", "Release")


recipe = LibSDL2ImageRecipe()
