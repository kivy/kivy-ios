from kivy_ios.toolchain import Recipe, shprint
import sh


class LibSDL2Recipe(Recipe):
    version = "2.28.5"
    url = "https://github.com/libsdl-org/SDL/releases/download/release-{version}/SDL2-{version}.tar.gz"
    library = "Xcode/SDL/build/Release-{plat.sdk}/libSDL2.a"
    include_dir = "include"
    pbx_frameworks = [
        "OpenGLES", "AudioToolbox", "QuartzCore", "CoreGraphics",
        "CoreMotion", "GameController", "AVFoundation", "Metal",
        "UIKit", "CoreHaptics"]

    def prebuild_platform(self, plat):
        if self.has_marker("patched"):
            return
        self.apply_patch("uikit-transparent.patch")
        self.apply_patch("disable-hidapi.patch")
        self.set_marker("patched")

    def build_platform(self, plat):
        env = plat.get_env()
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(plat.arch),
                "CC={}".format(env['CC']),
                "-sdk", plat.sdk,
                "-project", "Xcode/SDL/SDL.xcodeproj",
                "-target", "Static Library-iOS",
                "-configuration", "Release")


recipe = LibSDL2Recipe()
