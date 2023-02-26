from kivy_ios.toolchain import CythonRecipe, shprint
from os.path import join
import sh
import os


class PillowRecipe(CythonRecipe):
    version = "8.2.0"
    url = "https://pypi.python.org/packages/source/P/Pillow/Pillow-{version}.tar.gz"
    library = "libpillow.a"
    depends = [
        "hostpython3",
        "host_setuptools3",
        "freetype",
        "libjpeg",
        "python3",
        "ios",
    ]
    python_depends = ["setuptools"]
    pbx_libraries = ["libz", "libbz2"]
    include_per_arch = True
    cythonize = False

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("bypass-find-library.patch")
        self.set_marker("patched")

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env["C_INCLUDE_PATH"] = join(arch.sysroot, "usr", "include")
        env["LIBRARY_PATH"] = join(arch.sysroot, "usr", "lib")
        env["CFLAGS"] += " ".join(
            [
                " -I{}".format(join(self.ctx.dist_dir, "include", arch.arch, "freetype"))
                + " -I{}".format(
                    join(self.ctx.dist_dir, "include", arch.arch, "libjpeg")
                )
                + " -arch {}".format(arch.arch)
            ]
        )
        env["PATH"] = os.environ["PATH"]
        env[
            "PKG_CONFIG"
        ] = "ios-pkg-config"  # ios-pkg-config does not exists, is needed to disable the pkg-config usage.
        return env

    def build_arch(self, arch):
        build_env = self.get_recipe_env(arch)
        hostpython3 = sh.Command(self.ctx.hostpython)
        shprint(
            hostpython3,
            "setup.py",
            "build_ext",
            "--disable-tiff",
            "--disable-webp",
            "--disable-jpeg2000",
            "--disable-lcms",
            "--disable-platform-guessing",
            "-g",
            _env=build_env,
        )
        self.biglink()


recipe = PillowRecipe()
