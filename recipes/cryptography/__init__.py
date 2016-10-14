from os.path import join
from toolchain import CythonRecipe


class CryptographyRecipe(CythonRecipe):
    name = "cryptography"
    version = "1.5.2"
    url = (
        "https://pypi.python.org/packages/03/1a/"
        "60984cb85cc38c4ebdfca27b32a6df6f1914959d8790f5a349608c78be61/"
        "cryptography-{version}.tar.gz"
    )
    depends = ["host_setuptools", "six", "idna", "pyasn1"]
    cythonize = False

    def get_recipe_env(self, arch):
        env = super(CryptographyRecipe, self).get_recipe_env(arch)
        env["CC"] += " -I{}".format(
            join(self.ctx.dist_dir, "include", arch.arch, "libffi"))
        return env

recipe = CryptographyRecipe()
