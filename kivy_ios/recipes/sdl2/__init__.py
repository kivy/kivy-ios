from kivy_ios.toolchain import Recipe, shprint
import sh


class LibSDL2Recipe(Recipe):
    # version = "2.0.9"
    # url = "https://www.libsdl.org/release/SDL2-{version}.tar.gz"
    version = "7cc4fc886d9e"
    url = "https://hg.libsdl.org/SDL/archive/{version}.tar.gz"
    library = "Xcode-iOS/SDL/build/Release-{arch.sdk}/libSDL2.a"
    include_dir = "include"
    pbx_frameworks = [
        "OpenGLES", "AudioToolbox", "QuartzCore", "CoreGraphics",
        "CoreMotion", "GameController", "AVFoundation", "Metal",
        "UIKit"]

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("uikit-transparent.patch")
        self.set_marker("patched")

    def build_arch(self, arch):
        env = arch.get_env()
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "BITCODE_GENERATION_MODE=bitcode",
                "CC={}".format(env['CC']),
                "-sdk", arch.sdk,
                "-project", "Xcode-iOS/SDL/SDL.xcodeproj",
                "-target", "libSDL-iOS",
                "-configuration", "Release")


recipe = LibSDL2Recipe()
