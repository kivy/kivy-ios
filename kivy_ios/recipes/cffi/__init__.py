# pure-python package, this can be removed when we'll support any python package
from kivy_ios.toolchain import PythonRecipe, shprint
import shutil
import sh
import os

from os import chdir
import logging

logger = logging.getLogger(__name__)


class CFFIRecipe(PythonRecipe):
    version = "1.15.1"
    url = "https://files.pythonhosted.org/packages/2b/a8/050ab4f0c3d4c1b8aaa805f70e26e84d0e27004907c5b8ecc1d31815f92a/cffi-{version}.tar.gz"
    depends = ["python3", "libffi"]
    libraries = [
        "lib_cffi_backend.a"
    ]

    def prebuild_arch(self, arch):
        # common to all archs
        if self.has_marker("patched"):
            return

        self.copy_file("CMakeLists.txt", "c")
        self.copy_file("ios.toolchain.cmake", ".")
        self.set_marker("patched")

    def build_arch(self, arch):
        build_dir = self.get_build_dir(arch.arch)
        logger.info("Building cffi {} in {}".format(arch.arch, build_dir))
        chdir(build_dir)

        os.environ["PATH"] = "/opt/local/bin:/opt/local/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/go/bin:/Library/Apple/usr/bin"

        cmake = sh.Command("/usr/local/bin/cmake")
        if arch.arch in ["x86_64"]:
            shprint(cmake, "-Hc", "-G", "Xcode", "-Bbuild",
                    "-DCMAKE_TOOLCHAIN_FILE=" + os.path.join(build_dir, "ios.toolchain.cmake"),
                    "-DPLATFORM=SIMULATOR64")
        else:
            shprint(cmake, "-Hc", "-G", "Xcode", "-Bbuild",
                    "-DCMAKE_TOOLCHAIN_FILE=" + os.path.join(build_dir, "ios.toolchain.cmake"),
                    "-DPLATFORM=OS64")

        shprint(cmake, "--build", "build", "--config", "Release")
        print("build " + arch.arch)

    def postbuild_arch(self, arch):
        build_dir = self.get_build_dir(arch.arch)

        libraries = [
            "build/Release-iphoneos/lib_cffi_backend.a",
        ]

        for fp in libraries:
            fpl = fp.split("/")
            if arch.arch == "x86_64":
                fpl[-2] = "Release-iphonesimulator"
            else:
                fpl[-2] = "Release-iphoneos"

            fp = "/".join(fpl)
            src = os.path.join(build_dir, fp)

            fn = fpl[-1]
            dst = os.path.join(build_dir, fn)
            shutil.copyfile(src, dst)

    def install(self):
        pass


recipe = CFFIRecipe()
