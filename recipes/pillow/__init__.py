from toolchain import Recipe, shprint
from os.path import join
import sh
import os
import fnmatch


class PillowRecipe(Recipe):
    version = "6.1.0"
    url = "https://pypi.python.org/packages/source/P/Pillow/Pillow-{version}.tar.gz"
    library = "libpillow.a"
    depends = ["hostpython3", "host_setuptools3", "freetype", "libjpeg", "python3", "ios"]
    pbx_libraries = ["libz", "libbz2"]
    include_per_arch = True

    def get_pil_env(self, arch):
        build_env = arch.get_env()
        build_env["IOSROOT"] = self.ctx.root_dir
        build_env["IOSSDKROOT"] = arch.sysroot
        build_env["LDSHARED"] = join(self.ctx.root_dir, "tools", "liblink")
        build_env["ARM_LD"] = build_env["LD"]
        build_env["ARCH"] = arch.arch
        build_env["C_INCLUDE_PATH"] = join(arch.sysroot, "usr", "include")
        build_env["LIBRARY_PATH"] = join(arch.sysroot, "usr", "lib")
        build_env["CFLAGS"] = " ".join([
            "-I{}".format(join(self.ctx.dist_dir, "include", arch.arch, "freetype")) +
            " -I{}".format(join(self.ctx.dist_dir, "include", arch.arch, "libjpeg")) +
            " -arch {}".format(arch.arch)
            ])
        build_env['PATH'] = os.environ['PATH']
        return build_env

    def build_arch(self, arch):
        build_env = self.get_pil_env(arch)
        hostpython3 = sh.Command(self.ctx.hostpython)
        shprint(hostpython3, "setup.py", "build_ext", "--disable-tiff",
            "--disable-webp", "-g", _env=build_env)
        self.biglink()

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython3 = sh.Command(self.ctx.hostpython)
        build_env = self.get_pil_env(arch)
        dest_dir = join(self.ctx.dist_dir, "root", "python3")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python3.7', 'site-packages')
        shprint(hostpython3, "setup.py", "install", "--prefix", dest_dir,
            _env=build_env)

    def biglink(self):
        dirs = []
        for root, dirnames, filenames in os.walk(self.build_dir):
            if fnmatch.filter(filenames, "*.so.libs"):
                dirs.append(root)
        cmd = sh.Command(join(self.ctx.root_dir, "tools", "biglink"))
        shprint(cmd, join(self.build_dir, "libpillow.a"), *dirs)

recipe = PillowRecipe()

