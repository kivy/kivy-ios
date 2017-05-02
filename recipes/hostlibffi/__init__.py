from toolchain import Recipe, shprint
import sh


class LibffiRecipe(Recipe):
    version = "3.2.1"
    url = "ftp://sourceware.org/pub/libffi/libffi-{version}.tar.gz"
    library = "build/Release-{arch.sdk}/libffi.a"
    include_per_arch = True
    include_dir = "build_{arch.sdk}-{arch.arch}/include"
    archs = ["x86_64"]

    def build_all(self):
        filtered_archs = self.filtered_archs
        print("Build {} for {} (filtered)".format(
            self.name,
            ", ".join([x.arch for x in filtered_archs])))
        for arch in self.filtered_archs:
            self.build(arch)

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        # necessary as it doesn't compile with XCode 6.0. If we use 5.1.1, the
        # compiler for i386 is not working.
        #shprint(sh.sed,
        #        "-i.bak",
        #        "s/-miphoneos-version-min=5.1.1/-miphoneos-version-min=6.0/g",
        #        "generate-darwin-source-and-headers.py")
        self.apply_patch("fix-win32-unreferenced-symbol.patch")
        self.apply_patch("public_include.patch")
        self.apply_patch("staticlib.patch")
        self.apply_patch("staticlib2.patch")
        self.set_marker("patched")

    def build_arch(self, arch):
        shprint(sh.xcodebuild, self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "-sdk", "macosx",
                "install", "installhdrs",
                "-project", "libffi.xcodeproj",
                "-target", "libffi-Mac",
                "-configuration", "Release",
                "DSTROOT={}/hostlibffi".format(self.ctx.dist_dir))
        

    def postbuild_arch(self, arch):
        pass

recipe = LibffiRecipe()

