from os.path import join
from toolchain import CythonRecipe
from toolchain import shprint
import os
import sh


class CryptographyRecipe(CythonRecipe):
    name = "cryptography"
    version = "1.5.2"
    url = (
        "https://pypi.python.org/packages/03/1a/"
        "60984cb85cc38c4ebdfca27b32a6df6f1914959d8790f5a349608c78be61/"
        "cryptography-{version}.tar.gz"
    )
    library = "libcryptography.a"
    depends = ["host_setuptools", "cffi", "six", "idna", "pyasn1", "enum34"]
    cythonize = False

    def get_recipe_env(self, arch):
        env = super(CryptographyRecipe, self).get_recipe_env(arch)
        env["CC"] += " -I{}".format(
            join(self.ctx.dist_dir, "include", arch.arch, "libffi"))
        env["CFLAGS"] += " -I{}".format(
            join(self.ctx.dist_dir, "include", arch.arch, "openssl", "openssl"))
        return env

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        # manually create expected directory in build directory
        scripts_dir = join("build", "scripts-2.7")
        if not os.path.exists(scripts_dir):
            os.makedirs(scripts_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        pythonpath = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        build_env['PYTHONPATH'] = pythonpath
        args = [hostpython, "setup.py", "install", "--prefix", dest_dir]
        shprint(*args, _env=build_env)
        args = [hostpython, "setup.py", "install"]
        shprint(*args, _env=build_env)

recipe = CryptographyRecipe()

