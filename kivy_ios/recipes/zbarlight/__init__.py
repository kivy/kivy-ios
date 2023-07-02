import os
import pathlib
import shutil
from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh
import fnmatch


class ZbarLightRecipe(Recipe):
    version = "3.0"
    url = "https://github.com/Polyconseil/zbarlight/archive/{version}.tar.gz"
    library = "zbarlight.a"
    depends = ["hostpython3", "python3", "libzbar"]
    pbx_libraries = ["libz", "libbz2", "libc++", "libsqlite3", "CoreMotion"]
    include_per_arch = True

    def get_zbar_env(self, arch):
        build_env = arch.get_env()
        build_env["ARCH"] = arch.arch
        build_env["ARM_LD"] = build_env["LD"]
        build_env["LDSHARED"] = join(self.ctx.root_dir, "tools", "liblink")
        return build_env

    def build_arch(self, arch):
        build_env = self.get_zbar_env(arch)
        hostpython = sh.Command(self.ctx.hostpython)
        self.apply_patch("zbarlight_hardcode_version.patch")
        shprint(hostpython, "setup.py", "build", _env=build_env)
        self.biglink()

    def install(self):
        arch = self.filtered_archs[0].arch
        source = next(pathlib.Path(
            self.get_build_dir(arch),
            "build"
        ).glob("lib.*")) / "zbarlight"
        destination = next(pathlib.Path(
            self.ctx.dist_dir,
            "root",
            "python3",
            "lib"
        ).glob("python3.*")) / "site-packages" / "zbarlight"

        shutil.rmtree(destination, ignore_errors=True)
        shutil.copytree(source, destination)
        (destination / "_zbarlight.c").unlink()

    def biglink(self):
        dirs = []
        for root, dirnames, filenames in os.walk(self.build_dir):
            if fnmatch.filter(filenames, "*.so.libs"):
                dirs.append(root)

        cmd = sh.Command(join(self.ctx.root_dir, "tools", "biglink"))
        shprint(cmd, join(self.build_dir, "zbarlight.a"), *dirs)


recipe = ZbarLightRecipe()
