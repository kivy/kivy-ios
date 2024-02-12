from kivy_ios.toolchain import Recipe, shprint
import sh


class LibffiRecipe(Recipe):
    version = "3.4.4"
    url = "https://github.com/libffi/libffi/releases/download/v{version}/libffi-{version}.tar.gz"
    library = "build/Release-{plat.sdk}/libffi.a"
    include_per_platform = True
    include_dir = "build_{plat.name}/include"
    include_name = "ffi"

    def prebuild_platform(self, plat):
        if self.has_marker("patched"):
            return
        self.apply_patch("enable-tramp-build.patch")
        shprint(sh.sed,
                "-i.bak",
                "s/-miphoneos-version-min=7.0/-miphoneos-version-min=9.0/g",
                "generate-darwin-source-and-headers.py")
        shprint(sh.sed,
                "-i.bak",
                "s/build_target(ios_simulator_i386_platform, platform_headers)/print('Skipping i386')/g",
                "generate-darwin-source-and-headers.py")
        self.set_marker("patched")

    def build_platform(self, plat):
        python3 = sh.Command("python3")
        shprint(python3, "generate-darwin-source-and-headers.py", "--only-ios")
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(plat.arch),
                "-sdk", plat.sdk,
                "-project", "libffi.xcodeproj",
                "-target", "libffi-iOS",
                "-configuration", "Release")


recipe = LibffiRecipe()
