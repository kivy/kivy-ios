from os.path import join
from toolchain import PythonRecipe
from toolchain import shprint
import os
import sh


class SixRecipe(PythonRecipe):
    version = "1.10.0"
    url = (
        "https://pypi.python.org/packages/b3/b2/"
        "238e2590826bfdd113244a40d9d3eb26918bd798fc187e2360a8367068db/"
        "six-{version}.tar.gz"
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

recipe = SixRecipe()
