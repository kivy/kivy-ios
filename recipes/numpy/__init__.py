from toolchain import Recipe, shprint
from os.path import join, exists
import sh
import os
import shutil


class NumpyRecipe(Recipe):
    version = "1.9.1"
    url = "http://pypi.python.org/packages/source/n/numpy/numpy-{version}.tar.gz"
    library = "libnumpy.a"
    libraries = ["libnpymath.a", "libnpysort.a"]
    depends = ["python"]
    pbx_frameworks = ["Accelerate"]

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("numpy-1.9.1.patch")
        self.set_marker("patched")

    def get_kivy_env(self, arch):
        build_env = arch.get_env()
        build_env["KIVYIOSROOT"] = self.ctx.root_dir
        build_env["LDSHARED"] = join(self.ctx.root_dir, "tools", "liblink")
        build_env["ARM_LD"] = build_env["LD"]
        # CC must have the CFLAGS with arm arch, because numpy tries first to
        # compile and execute an empty C to see if the compiler works. This is
        # obviously not working when crosscompiling
        build_env["CC"] = "{} {}".format(
                build_env["CC"],
                build_env["CFLAGS"])
        build_env["ARCH"] = arch.arch
        # Numpy configuration. Don't try to compile anything related to it,
        # we're going to use the Accelerate framework
        build_env["NPYCONFIG"] = "env BLAS=None LAPACK=None ATLAS=None"
        return build_env

    def build_arch(self, arch):
        build_env = self.get_kivy_env(arch)
        hostpython = sh.Command(self.ctx.hostpython)
        shprint(hostpython, "setup.py", "build_ext", "-g", "-v",
                _env=build_env)
        sh.cp(sh.glob(join(self.build_dir, "build", "temp.*", "libnpy*.a")),
              self.build_dir)
        self.biglink()

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = self.get_kivy_env(arch)
        shprint(hostpython, "setup.py", "install", "-O2",
                "--prefix", join(build_dir, "iosbuild"),
                _env=build_env)
        dest_dir = join(self.ctx.dist_dir, "root", "python", "lib", "python2.7",
                "site-packages", "numpy")
        if exists(dest_dir):
            shutil.rmtree(dest_dir)
        shutil.copytree(
            join(build_dir, "iosbuild", "lib",
                 "python2.7", "site-packages", "numpy"),
            dest_dir)
        shutil.rmtree(join(dest_dir, "core", "include"))
        shutil.rmtree(join(dest_dir, "core", "tests"))
        shutil.rmtree(join(dest_dir, "distutils"))
        shutil.rmtree(join(dest_dir, "doc"))
        shutil.rmtree(join(dest_dir, "f2py", "tests"))
        shutil.rmtree(join(dest_dir, "fft", "tests"))
        shutil.rmtree(join(dest_dir, "lib", "tests"))
        shutil.rmtree(join(dest_dir, "ma", "tests"))
        shutil.rmtree(join(dest_dir, "matrixlib", "tests"))
        shutil.rmtree(join(dest_dir, "polynomial", "tests"))
        shutil.rmtree(join(dest_dir, "random", "tests"))
        shutil.rmtree(join(dest_dir, "tests"))

recipe = NumpyRecipe()


