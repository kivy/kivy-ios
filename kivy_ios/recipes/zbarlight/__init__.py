import os
from kivy_ios.toolchain import Recipe
from os.path import join
import sh
import fnmatch
from distutils.dir_util import copy_tree


class ZbarLightRecipe(Recipe):
    version = '1.2'
    url = 'https://github.com/Polyconseil/zbarlight/archive/{version}.tar.gz'
    library = "zbarlight.a"
    depends = ['hostpython3', 'python3', 'libzbar']
    pbx_libraries = ["libz", "libbz2", 'libc++', 'libsqlite3', 'CoreMotion']
    include_per_arch = True

    def get_zbar_env(self, arch):
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env["IOSROOT"] = self.ctx.root_dir
        build_env["IOSSDKROOT"] = arch.sysroot
        build_env["LDSHARED"] = join(self.ctx.root_dir, "tools", "liblink")
        build_env["ARM_LD"] = build_env["LD"]
        build_env["ARCH"] = arch.arch
        build_env["C_INCLUDE_PATH"] = join(arch.sysroot, "usr", "include")
        build_env["LIBRARY_PATH"] = join(arch.sysroot, "usr", "lib")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python3.7', 'site-packages')
        build_env["CFLAGS"] = " ".join([
            " -I{}".format(join(self.ctx.dist_dir, "include", arch.arch, "libzbar", 'zbar')) +
            " -arch {}".format(arch.arch)
            ])
        build_env['LDFLAGS'] += " -lios -lpython -lzbar"
        return build_env

    def build_arch(self, arch):
        build_env = self.get_zbar_env(arch)
        hostpython = sh.Command(self.ctx.hostpython)
        shprint(hostpython, "setup.py", "build",   # noqa: F821
                _env=build_env)
        self.apply_patch("zbarlight_1_2.patch")  # Issue getting the version, hard coding for now
        self.biglink()

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = join(self.get_build_dir(arch.arch), 'build',
                         'lib.macosx-10.13-x86_64-2.7', 'zbarlight')
        dist_dir = join(self.ctx.dist_dir, 'root', 'python3', 'lib',
                        'python3.7', 'site-packages', 'zbarlight')
        # Patch before Copying
        # self.apply_patch("zbarlight_1_2.patch")#Issue getting the version, hard coding for now
        copy_tree(build_dir, dist_dir)
        os.remove(join(dist_dir, '_zbarlight.c'))

    def _patch__init__(self):
        init = join(self.ctx.dist_dir, 'root', 'python3', 'lib', 'python3.7',
                    'site-packages', 'zbarlight', "__init__.py")
        shprint(  # noqa: F821
            sh.sed, "-i.bak",
            "s/__version__ = pkg_resources.get_distribution('zbarlight').version'"
            "/__version__ = '{version}'/g",
            init)

    def biglink(self):
        dirs = []
        for root, dirnames, filenames in os.walk(self.build_dir):
            if fnmatch.filter(filenames, "*.so.libs"):
                dirs.append(root)
        cmd = sh.Command(join(self.ctx.root_dir, "tools", "biglink"))
        shprint(cmd, join(self.build_dir, "zbarlight.a"), *dirs)  # noqa: F821


recipe = ZbarLightRecipe()
