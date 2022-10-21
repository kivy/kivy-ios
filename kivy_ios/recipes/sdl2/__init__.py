from kivy_ios.toolchain import Recipe, shprint
import sh


class LibSDL2Recipe(Recipe):
    version = "2.24.1"
    url = "https://github.com/libsdl-org/SDL/releases/download/release-{version}/SDL2-{version}.tar.gz"
    library = "Xcode/SDL/build/Release-{arch.sdk}/libSDL2.a"
    include_dir = "include"
    pbx_frameworks = [
        "OpenGLES", "AudioToolbox", "QuartzCore", "CoreGraphics",
        "CoreMotion", "GameController", "AVFoundation", "Metal",
        "UIKit", "CoreHaptics", "CoreBluetooth"]

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
                "-project", "Xcode/SDL/SDL.xcodeproj",
                "-target", "Static Library-iOS",
                "-configuration", "Release")


recipe = LibSDL2Recipe()
