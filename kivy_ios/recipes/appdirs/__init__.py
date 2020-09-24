from toolchain import PythonRecipe, shprint
from os.path import join
import sh, os

class AppdirsRecipe(PythonRecipe):
    version = "1.4.3"
    url = "https://pypi.python.org/packages/source/a/appdirs/appdirs-{version}.tar.gz"
    depends = ["python", "setuptools"]
    
    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)

recipe = AppdirsRecipe()
