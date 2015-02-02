from toolchain import Recipe, shprint
import sh


class LibffiRecipe(Recipe):
    version = "3.0.13"
    url = "ftp://sourceware.org/pub/libffi/libffi-{version}.tar.gz"

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("ffi-3.0.13-sysv.S.patch")
        if arch in ("armv7", "armv7s", "arm64"):
            shprint(sh.sed,
                    "-i.bak",
                    "s/-miphoneos-version-min=4.0/-miphoneos-version-min=6.0/g",
                    "generate-ios-source-and-headers.py")
        self.set_marker("patched")

    def build_arch(self, arch):
        if arch == "i386":
            target_name = "libffi OS X"
        else:
            target_name = "libffi iOS"

        shprint(sh.xcodebuild,
                "-project", "libffi.xcodeproj",
                "-target", target_name,
                "-configuration", "Release",
                "-sdk", "iphoneos{}".format(self.ctx.sdkver),
                "OTHER_CFLAGS=-no-integrated-as")

recipe = LibffiRecipe()
