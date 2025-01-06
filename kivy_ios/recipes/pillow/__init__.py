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
        "freetype",
        "libjpeg",
        "python3",
        "ios",
    ]
    python_depends = ["setuptools"]
    pbx_libraries = ["libz", "libbz2"]
    include_per_platform = True
    hostpython_prerequisites = ["Cython==0.29.37"]
    cythonize = False

    def prebuild_platform(self, plat):
        if self.has_marker("patched"):
            return
        self.apply_patch("bypass-find-library.patch")
        self.set_marker("patched")

    def get_recipe_env(self, plat):
        env = super().get_recipe_env(plat)
        env["C_INCLUDE_PATH"] = join(plat.sysroot, "usr", "include")
        env["LIBRARY_PATH"] = join(plat.sysroot, "usr", "lib")
        env["CFLAGS"] += " ".join(
            [
                " -I{}".format(join(self.ctx.dist_dir, "include", plat.name, "freetype"))
                + " -I{}".format(
                    join(self.ctx.dist_dir, "include", plat.name, "libjpeg")
                )
                + " -arch {}".format(plat.arch)
            ]
        )
        env["PATH"] = os.environ["PATH"]
        env[
            "PKG_CONFIG"
        ] = "ios-pkg-config"  # ios-pkg-config does not exists, is needed to disable the pkg-config usage.
        return env

    def build_platform(self, plat):
        build_env = self.get_recipe_env(plat)
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
