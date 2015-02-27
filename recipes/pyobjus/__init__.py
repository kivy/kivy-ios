from toolchain import CythonRecipe, shprint
from os.path import join
import sh


class PyobjusRecipe(CythonRecipe):
    version = "master"
    url = "https://github.com/kivy/pyobjus/archive/{version}.zip"
    library = "libpyobjus.a"
    depends = ["python"]
    pre_build_ext = True

    def get_recipe_env(self, arch):
        env = super(PyobjusRecipe, self).get_recipe_env(arch)
        env["CC"] += " -I{}".format(
                join(self.ctx.dist_dir, "include", arch.arch, "libffi"))
        return env

    def cythonize_build(self):
        # don't use the cythonize, pyobjus don't support method rewriting
        shprint(sh.find, self.build_dir, "-iname", "*.pyx",
                "-exec", "cython", "{}", ";")
        # ffi is installed somewhere else, this include doesn't work
        # XXX ideally, we need to fix libffi installation...
        shprint(sh.sed,
                "-i.bak",
                "s/ffi\///g",
                "pyobjus/pyobjus.c")

recipe = PyobjusRecipe()


