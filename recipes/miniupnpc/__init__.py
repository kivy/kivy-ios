from toolchain import CythonRecipe, shprint
from os.path import join
import os
import sh


class MiniupnpcRecipe(CythonRecipe):
    name = "miniupnpc"
    version = "1.9"
    url = "https://pypi.python.org/packages/source/m/miniupnpc/miniupnpc-{version}.tar.gz"
    library = "libminiupnpc.a"
    depends = ["python", "setuptools"]
    cythonize = False

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = MiniupnpcRecipe()
