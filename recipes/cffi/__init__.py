from os.path import join
from toolchain import CythonRecipe
from toolchain import shprint
import os
import sh


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

recipe = CffiRecipe()
