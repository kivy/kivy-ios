from toolchain import CythonRecipe, shprint
from os.path import join
from os import chdir, listdir
import sh
import shutil


class NumpyRecipe(CythonRecipe):
    version = "1.16.4"
    url = "https://pypi.python.org/packages/source/n/numpy/numpy-{version}.zip"
    library = "libnumpy.a"
    libraries = ["libnpymath.a", "libnpysort.a"]
    include_dir = "numpy/core/include"
    depends = ["python"]
    pbx_frameworks = ["Accelerate"]
    cythonize = False

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("numpy-1.16.4.patch")
        self.set_marker("patched")

    def get_recipe_env(self, arch):
        env = super(NumpyRecipe, self).get_recipe_env(arch)
        # CC must have the CFLAGS with arm arch, because numpy tries first to
        # compile and execute an empty C to see if the compiler works. This is
        # obviously not working when crosscompiling
        env["CC"] = "{} {}".format(env["CC"], env["CFLAGS"])
        # Numpy configuration. Don't try to compile anything related to it,
        # we're going to use the Accelerate framework
        env["NPYCONFIG"] = "env BLAS=None LAPACK=None ATLAS=None"
        return env

    def build_arch(self, arch):
        super(NumpyRecipe, self).build_arch(arch)
        sh.cp(sh.glob(join(self.build_dir, "build", "temp.*", "libnpy*.a")),
              self.build_dir)

    def reduce_python_package(self):
        dest_dir = join(self.ctx.site_packages_dir, "numpy")
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
