from os.path import join
from toolchain import PythonRecipe
from toolchain import shprint
import os
import sh


class Enum34Recipe(PythonRecipe):
    version = "1.1.6"
    url = (
        "https://pypi.python.org/packages/bf/3e/"
        "31d502c25302814a7c2f1d3959d2a3b3f78e509002ba91aea64993936876/"
        "enum34-{version}.tar.gz"
    )
    depends = ["python", "host_setuptools"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        pythonpath = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        build_env['PYTHONPATH'] = pythonpath
        args = [hostpython, "setup.py", "install", "--prefix", dest_dir]
        shprint(*args, _env=build_env)

recipe = Enum34Recipe()
