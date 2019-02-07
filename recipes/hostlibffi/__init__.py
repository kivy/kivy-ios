from toolchain import Recipe, shprint
import sh
from os.path import exists
import logging

logger = logging.getLogger(__name__)

class LibffiRecipe(Recipe):
    version = "3.2.1"
    url = "ftp://sourceware.org/pub/libffi/libffi-{version}.tar.gz"
    library = "build/Release-{arch.sdk}/libffi.a"
    include_per_arch = True
    include_dir = "build_{arch.sdk}-{arch.arch}/include"
    archs = ["x86_64"]

    def build_all(self):
        filtered_archs = self.filtered_archs
        logger.info("Build {} for {} (filtered)".format(
            self.name,
            ", ".join([x.arch for x in filtered_archs])))
        for arch in self.filtered_archs:
            self.build(arch)

        # since we don't run cache_execution, call this here for `status`
        self.update_state("{}.build_all".format(self.name), True)

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
        self.apply_patch("libffi-xcode10.patch")
        self.set_marker("patched")

    def build_arch(self, arch):
        if exists("generate-darwin-source-and-headers.py"):
            shprint(
                sh.mv,
                "generate-darwin-source-and-headers.py",
                "_generate-darwin-source-and-headers.py")
            shprint(sh.touch, "generate-darwin-source-and-headers.py")
        python27 = sh.Command("python2.7")
        shprint(python27, "_generate-darwin-source-and-headers.py", "--only-osx")
        shprint(sh.xcodebuild,
                self.ctx.concurrent_xcodebuild,
                "ONLY_ACTIVE_ARCH=NO",
                "ARCHS={}".format(arch.arch),
                "DSTROOT={}/hostlibffi".format(self.ctx.dist_dir),
                "-sdk", "macosx",
                "clean", "build", "installhdrs", "install",
                "-project", "libffi.xcodeproj",
                "-scheme", "libffi-Mac",
                "-configuration", "Release")

    def postbuild_arch(self, arch):
        pass

recipe = LibffiRecipe()
