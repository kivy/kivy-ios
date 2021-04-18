from kivy_ios.toolchain import Recipe, shprint
import sh
from os.path import exists


class LibffiRecipe(Recipe):
    version = "3.2.1"
    url = "https://sourceware.org/pub/libffi/libffi-{version}.tar.gz"
    library = "build/Release-{arch.sdk}/libffi.a"
    include_per_arch = True
    include_dir = "build_{arch.sdk}-{arch.arch}/include"
    include_name = "ffi"
    archs = ["x86_64", "arm64"]

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        shprint(sh.sed,
                "-i.bak",
                "s/-miphoneos-version-min=5.1.1/-miphoneos-version-min=9.0/g",
                "generate-darwin-source-and-headers.py")
        self.apply_patch("fix-win32-unreferenced-symbol.patch")
        self.apply_patch("generate-darwin-source-and-headers-python3-items.patch")
        self.set_marker("patched")

    def build_arch(self, arch):
        if exists("generate-darwin-source-and-headers.py"):
            shprint(
                sh.mv,
                "generate-darwin-source-and-headers.py",
                "_generate-darwin-source-and-headers.py")
            shprint(sh.touch, "generate-darwin-source-and-headers.py")
        python3 = sh.Command("python3")
        shprint(python3, "_generate-darwin-source-and-headers.py", "--only-ios")
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "BITCODE_GENERATION_MODE=bitcode",
                "-sdk", arch.sdk,
                "-project", "libffi.xcodeproj",
                "-target", "libffi-iOS",
                "-configuration", "Release")


recipe = LibffiRecipe()
