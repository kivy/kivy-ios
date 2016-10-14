from os.path import join
from toolchain import PythonRecipe
from toolchain import shprint
import os
import sh


class Pyasn1Recipe(PythonRecipe):
    version = "0.1.9"
    url = (
        "https://pypi.python.org/packages/f7/83/"
        "377e3dd2e95f9020dbd0dfd3c47aaa7deebe3c68d3857a4e51917146ae8b/"
        "pyasn1-{version}.tar.gz"
    )
    depends = ["python"]

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

recipe = Pyasn1Recipe()
