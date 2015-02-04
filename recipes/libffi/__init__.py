from toolchain import Recipe, shprint
from os.path import join, exists
import sh
import shutil


class LibffiRecipe(Recipe):
    version = "3.2.1"
    url = "ftp://sourceware.org/pub/libffi/libffi-{version}.tar.gz"
    library = "build/Release-{arch.sdk}/libffi.a"

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        # necessary as it doesn't compile with XCode 6.0. If we use 5.1.1, the
        # compiler for i386 is not working.
        shprint(sh.sed,
                "-i.bak",
                "s/-miphoneos-version-min=5.1.1/-miphoneos-version-min=6.0/g",
                "generate-darwin-source-and-headers.py")
        self.set_marker("patched")

    def build_arch(self, arch):
        shprint(sh.xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "-sdk", arch.sdk,
                "-project", "libffi.xcodeproj",
                "-target", "libffi-iOS",
                "-configuration", "Release")

    def install(self):
        for sdkarch, arch in (
            ("iphoneos-arm64", "arm64"),
            ("iphoneos-armv7", "armv7"),
            ("iphonesimulator-i386", "i386"),
            ("iphonesimulator-x86_64", "x86_64")):
            dest_dir = join(self.ctx.dist_dir, "include", arch)
            if exists(dest_dir):
                continue
            shutil.copytree(join(
                self.get_build_dir(arch),
                "build_{}/include".format(sdkarch)),
                dest_dir)


recipe = LibffiRecipe()

