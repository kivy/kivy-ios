from kivy_ios.toolchain import CythonRecipe
from os.path import join
import sh
import shutil


class NumpyRecipe(CythonRecipe):
    version = "1.20.2"
    url = "https://pypi.python.org/packages/source/n/numpy/numpy-{version}.zip"
    library = "libnumpy.a"
    libraries = ["libnpymath.a", "libnpyrandom.a"]
    include_dir = "numpy/core/include"
    depends = ["python"]
    hostpython_prerequisites = ["Cython"]
    cythonize = False

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("duplicated_symbols.patch")
        self.set_marker("patched")

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        # CC must have the CFLAGS with arm arch, because numpy tries first to
        # compile and execute an empty C to see if the compiler works. This is
        # obviously not working when crosscompiling
        env["CC"] = "{} {}".format(env["CC"], env["CFLAGS"])
        # Disable Accelerate.framework by disabling the optimized BLAS and LAPACK libraries cause it's now unsupported
        env["NPY_BLAS_ORDER"] = ""
        env["NPY_LAPACK_ORDER"] = ""
        return env

    def build_arch(self, arch):
        super().build_arch(arch)
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
        shutil.rmtree(join(dest_dir, "linalg", "tests"))
        shutil.rmtree(join(dest_dir, "ma", "tests"))
        shutil.rmtree(join(dest_dir, "matrixlib", "tests"))
        shutil.rmtree(join(dest_dir, "polynomial", "tests"))
        shutil.rmtree(join(dest_dir, "random", "tests"))
        shutil.rmtree(join(dest_dir, "tests"))


recipe = NumpyRecipe()
