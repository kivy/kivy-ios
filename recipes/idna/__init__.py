from os.path import join
from toolchain import PythonRecipe
from toolchain import shprint
import os
import sh


class IdnaRecipe(PythonRecipe):
    version = "2.1"
    url = (
        "https://pypi.python.org/packages/fb/84/"
        "8c27516fbaa8147acd2e431086b473c453c428e24e8fb99a1d89ce381851/"
        "idna-{version}.tar.gz"
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

recipe = IdnaRecipe()
