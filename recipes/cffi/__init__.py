from os.path import join
from toolchain import CythonRecipe


class CffiRecipe(CythonRecipe):
    name = "cffi"
    version = "1.8.3"
    url = (
        "https://pypi.python.org/packages/0a/f3/"
        "686af8873b70028fccf67b15c78fd4e4667a3da995007afc71e786d61b0a/"
        "cffi-{version}.tar.gz"
    )
    depends = ["libffi", "host_setuptools", "pycparser"]
    cythonize = False

    def get_recipe_env(self, arch):
        env = super(CffiRecipe, self).get_recipe_env(arch)
        env["CC"] += " -I{}".format(
            join(self.ctx.dist_dir, "include", arch.arch, "libffi"))
        return env

recipe = CffiRecipe()
