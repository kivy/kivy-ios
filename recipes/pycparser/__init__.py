from os.path import join
from toolchain import PythonRecipe
from toolchain import shprint
import os
import sh


class PycparserRecipe(PythonRecipe):
    version = "2.14"
    url = (
        "https://pypi.python.org/packages/6d/31/"
        "666614af3db0acf377876d48688c5d334b6e493b96d21aa7d332169bee50/"
        "pycparser-{version}.tar.gz"
    )
    depends = ["python"]

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

recipe = PycparserRecipe()
