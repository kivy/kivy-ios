from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import os
import sh


class LibSDL2Recipe(Recipe):
    version = "ios-use-metalangle"
    url = "https://github.com/misl6/SDL/archive/refs/heads/feature/{version}.zip"

    metalangle_baseurl = (
        "https://github.com/kakashidinho/metalangle/releases/download/gles3-0.0.6"
    )
    metalangle_arch_map = dict(
        x86_64="MetalANGLE.framework.ios.simulator.zip",
        arm64="MetalANGLE.framework.ios.zip",
    )

    library = "Xcode/SDL/build/Release-{arch.sdk}/libSDL2.a"
    include_dir = "include"
    pbx_frameworks = [
        "AudioToolbox",
        "QuartzCore",
        "CoreGraphics",
        "CoreMotion",
        "GameController",
        "AVFoundation",
        "Metal",
        "UIKit",
        "CoreHaptics",
    ]

    def __init__(self):
        if os.environ.get("KIVYIOS_USE_METALANGLE"):
            self.frameworks = ["MetalANGLE"]
            self.pbx_frameworks.append("MetalANGLE")
        else:
            self.pbx_frameworks.append("OpenGLES")

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("uikit-transparent.patch")
        if os.environ.get("KIVYIOS_USE_METALANGLE"):
            self.apply_patch("enable-metalangle.patch")
            downloaded_file = self.download_file(
                join(self.metalangle_baseurl, self.metalangle_arch_map[arch.arch]),
                self.metalangle_arch_map[arch.arch],
            )
            self.extract_file(
                downloaded_file,
                join(self.get_build_dir(arch.arch), "Xcode/SDL/third-party/frameworks"),
            )
            if arch.arch == "arm64":
                self.extract_file(
                    downloaded_file,
                    join(self.ctx.dist_dir, "frameworks"),
                )
        self.set_marker("patched")

    def install_frameworks(self):
        pass

    def build_arch(self, arch):
        env = arch.get_env()
        shprint(
            sh.xcodebuild,
            self.ctx.concurrent_xcodebuild,
            "ONLY_ACTIVE_ARCH=NO",
            "ARCHS={}".format(arch.arch),
            "BITCODE_GENERATION_MODE=bitcode",
            "CC={}".format(env["CC"]),
            "-sdk",
            arch.sdk,
            "-project",
            "Xcode/SDL/SDL.xcodeproj",
            "-target",
            "Static Library-iOS",
            "-configuration",
            "Release",
        )


recipe = LibSDL2Recipe()
