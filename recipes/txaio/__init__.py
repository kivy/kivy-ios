from os.path import join
from toolchain import PythonRecipe
from toolchain import shprint
import os
import sh


class TxaioRecipe(PythonRecipe):
    version = "2.5.1"
    url = (
        "https://pypi.python.org/packages/45/e1/"
        "f7d88767d65dbfc20d4b4aa0dad657dbbe8ca629ead2bef24da04630a12a/"
        "txaio-{version}.tar.gz"
    )
    depends = ["six"]

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

recipe = TxaioRecipe()
